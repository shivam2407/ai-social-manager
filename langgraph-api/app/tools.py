"""Tools available to agents in the content generation pipeline.

Hardened with distributed systems patterns:
- Per-tool timeouts (prevent slow dependencies from blocking the pipeline)
- Circuit breaker on web_search (fail fast when DuckDuckGo is degraded)
- Cache with TTL on search results (avoid stale data, reduce redundant calls)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
from langchain_core.tools import tool

from app.circuit_breaker import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

# Platform character limits
PLATFORM_LIMITS = {
    "twitter": 280,
    "linkedin": 3000,
    "instagram": 2200,
}

# ── Search cache with TTL ────────────────────────────────────────
SEARCH_CACHE_TTL_SECONDS = 300  # 5-minute TTL for trending data

_search_cache: dict[str, dict[str, Any]] = {}


def _get_cached_search(query: str) -> dict[str, Any] | None:
    """Return cached result if it exists and hasn't expired."""
    entry = _search_cache.get(query)
    if entry and (time.time() - entry["timestamp"]) < SEARCH_CACHE_TTL_SECONDS:
        return entry
    # Expired or missing — evict stale entry
    _search_cache.pop(query, None)
    return None


def _set_cached_search(query: str, results: str) -> None:
    """Store a search result with a timestamp for TTL checks."""
    _search_cache[query] = {"results": results, "timestamp": time.time()}


# ── Circuit breaker for DuckDuckGo ───────────────────────────────
_search_circuit = CircuitBreaker(failure_threshold=3, reset_timeout=30, name="web_search")

# Per-tool timeout (seconds) — prevents a slow API from blocking the pipeline
SEARCH_TIMEOUT_SECONDS = 5


@_search_circuit
async def _async_search(query: str) -> str:
    """Execute the DuckDuckGo search with an async timeout."""
    async with httpx.AsyncClient(
        timeout=SEARCH_TIMEOUT_SECONDS,
        follow_redirects=False,
        max_redirects=0,
    ) as client:
        resp = await client.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        if data.get("Abstract"):
            results.append(f"Summary: {data['Abstract']}")

        for topic in data.get("RelatedTopics", [])[:5]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(f"- {topic['Text']}")

        if results:
            return "\n".join(results)
        return (
            f"No structured results found for '{query}'. "
            "Use your knowledge to identify trends in this space."
        )


@tool
def web_search(query: str) -> str:
    """Search the web for trending topics, news, and competitor content.

    Args:
        query: The search query to find relevant trends and content.
    """
    query = query[:500]

    # Check cache first (avoid redundant calls, respect TTL)
    cached = _get_cached_search(query)
    if cached:
        age = int(time.time() - cached["timestamp"])
        logger.info("Search cache HIT for '%s' (age: %ds)", query[:80], age)
        return f"{cached['results']}\n\n[cached result, {age}s old]"

    # Run async search with circuit breaker + timeout
    try:
        result = asyncio.get_event_loop().run_until_complete(
            asyncio.wait_for(_async_search(query), timeout=SEARCH_TIMEOUT_SECONDS)
        )
        _set_cached_search(query, result)
        return result
    except asyncio.TimeoutError:
        logger.warning("Search TIMEOUT for '%s' after %ds", query[:80], SEARCH_TIMEOUT_SECONDS)
        return (
            "[UNAVAILABLE: search tool timed out] "
            "Use your training knowledge to identify relevant trends."
        )
    except CircuitOpenError:
        logger.warning("Search CIRCUIT OPEN — failing fast for '%s'", query[:80])
        return (
            "[UNAVAILABLE: search tool degraded — circuit breaker open] "
            "Use your training knowledge to identify relevant trends."
        )
    except Exception as e:
        logger.warning("Search FAILED for '%s': %s", query[:80], e)
        return (
            f"[UNAVAILABLE: search error ({type(e).__name__})] "
            "Use your training knowledge to identify relevant trends."
        )


@tool
def check_character_count(text: str, platform: str) -> str:
    """Check if content fits within a platform's character limit.

    Args:
        text: The content text to check.
        platform: The target platform (twitter, linkedin, instagram).
    """
    limit = PLATFORM_LIMITS.get(platform.lower())
    if not limit:
        return f"Unknown platform '{platform}'. Supported: {list(PLATFORM_LIMITS.keys())}"

    count = len(text)
    if count <= limit:
        return f"OK: {count}/{limit} characters ({limit - count} remaining)"
    else:
        return f"OVER LIMIT: {count}/{limit} characters (need to cut {count - limit} characters)"


@tool
def get_platform_best_practices(platform: str) -> str:
    """Get current best practices and algorithm tips for a social platform.

    Args:
        platform: The target platform (twitter, linkedin, instagram).
    """
    practices = {
        "twitter": """Twitter/X Best Practices (2026):
- Threads outperform single tweets for reach (3-5 tweets ideal)
- First tweet is the hook — must stand alone and provoke curiosity
- Engagement in first 30 min determines viral potential
- Use 1-2 hashtags max (more hurts reach)
- Questions and hot takes drive replies
- Images boost engagement 35%
- Best times: Tue-Thu 9-11am EST, lunch breaks
- Avoid: links in first tweet (kills reach), excessive hashtags""",
        "linkedin": """LinkedIn Best Practices (2026):
- First 150 chars appear before "see more" — this IS your hook
- Personal stories + professional insight format works best
- Posts with "I" outperform "we" or brand-voice posts
- Carousel documents get 3x reach vs text posts
- Avoid external links (LinkedIn deprioritizes them)
- Comment engagement in first hour is critical
- Use 3-5 hashtags
- Best times: Tue-Thu 7-8am and 12pm
- Avoid: generic motivational quotes, AI-sounding listicles""",
        "instagram": """Instagram Best Practices (2026):
- Reels get 2x reach vs static posts
- Carousel posts get highest saves (algorithm loves saves)
- First line of caption must hook — only ~125 chars visible
- Use 5-15 hashtags (mix of broad + niche)
- Stories for engagement, Reels for reach, Carousels for saves
- Alt text improves discoverability
- Best times: Mon-Fri 11am-1pm, Thu-Fri evenings
- Avoid: stock-photo aesthetics, overly polished content (raw > perfect)""",
    }
    return practices.get(
        platform.lower(),
        f"Unknown platform '{platform}'. Supported: twitter, linkedin, instagram",
    )


# Collect all tools for agent binding
all_tools = [web_search, check_character_count, get_platform_best_practices]
research_tools = [web_search, get_platform_best_practices]
writing_tools = [check_character_count, get_platform_best_practices]
