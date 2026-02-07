"""Tools available to agents in the content generation pipeline."""

from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool

# Platform character limits
PLATFORM_LIMITS = {
    "twitter": 280,
    "linkedin": 3000,
    "instagram": 2200,
}


@tool
def web_search(query: str) -> str:
    """Search the web for trending topics, news, and competitor content.

    Args:
        query: The search query to find relevant trends and content.
    """
    # Using DuckDuckGo instant answer API (free, no key needed)
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
            )
            data = resp.json()

            results = []
            # Abstract (main answer)
            if data.get("Abstract"):
                results.append(f"Summary: {data['Abstract']}")

            # Related topics
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"- {topic['Text']}")

            if results:
                return "\n".join(results)
            return f"No structured results found for '{query}'. Use your knowledge to identify trends in this space."
    except Exception as e:
        return f"Search unavailable ({e}). Use your training knowledge to identify relevant trends."


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
