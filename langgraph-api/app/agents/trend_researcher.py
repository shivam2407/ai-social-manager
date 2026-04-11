"""Trend Researcher Agent — searches for real public posts from famous accounts.

Instead of asking the LLM to imagine trends, this agent:
1. Runs platform-specific web searches to find real posts from successful accounts
2. Feeds those results into the LLM for analysis
3. Tracks results freshness (live/cached/unavailable) in graph state
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_llm
from app.prompts import TREND_RESEARCHER_PROMPT
from app.response_parser import parse_json_response
from app.tools import web_search

logger = logging.getLogger(__name__)

# Platform-specific search query templates
# These target real public posts from famous/successful accounts
_PLATFORM_QUERIES = {
    "twitter": [
        "site:twitter.com OR site:x.com {niche} viral tweet {topic} 2025 2026",
        "{niche} best tweets popular accounts {topic}",
    ],
    "linkedin": [
        "site:linkedin.com {niche} viral post {topic} 2025 2026",
        "{niche} top linkedin creators posts {topic}",
    ],
    "instagram": [
        "site:instagram.com {niche} popular post {topic} 2025 2026",
        "{niche} instagram influencers viral content {topic}",
    ],
}


def _build_search_queries(
    platforms: list[str], niche: str, topic: str
) -> list[tuple[str, str]]:
    """Build (platform, query) pairs for each target platform."""
    queries = []
    for platform in platforms:
        templates = _PLATFORM_QUERIES.get(platform.lower(), [])
        for template in templates:
            q = template.format(niche=niche, topic=topic)
            queries.append((platform, q))
    return queries


def _run_searches(queries: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Run all search queries and group results by platform.

    Uses the hardened web_search tool (circuit breaker + timeout + cache).
    """
    results_by_platform: dict[str, list[str]] = {}
    for platform, query in queries:
        result = web_search.invoke(query)
        if result and "[UNAVAILABLE" not in result:
            results_by_platform.setdefault(platform, []).append(result)
    return results_by_platform


def _format_search_results(results_by_platform: dict[str, list[str]]) -> str:
    """Format grouped search results into a readable block for the LLM prompt."""
    if not results_by_platform:
        return (
            "[No search results available — search tool may be degraded. "
            "Use your training knowledge to identify trends and successful posts.]"
        )

    sections = []
    for platform, results in results_by_platform.items():
        sections.append(f"### {platform.upper()} search results:")
        for i, r in enumerate(results, 1):
            sections.append(f"**Search {i}:**\n{r}\n")
    return "\n".join(sections)


async def trend_researcher_node(state: dict[str, Any]) -> dict[str, Any]:
    """Search for real public posts from famous accounts, then analyze them."""
    brand = state["brand_profile"]
    content_request = state["content_request"]
    platforms = state["target_platforms"]

    # ── Step 1: Run platform-specific web searches ───────────────
    search_queries = _build_search_queries(
        platforms=platforms,
        niche=brand["niche"],
        topic=content_request[:100],  # truncate long requests
    )

    logger.info(
        "Trend researcher running %d searches across %s",
        len(search_queries),
        platforms,
    )

    results_by_platform = _run_searches(search_queries)
    search_results_text = _format_search_results(results_by_platform)

    # Determine freshness
    total_results = sum(len(v) for v in results_by_platform.values())
    if total_results == 0:
        freshness = "unavailable"
    elif any("[cached result" in r for rs in results_by_platform.values() for r in rs):
        freshness = "cached"
    else:
        freshness = "live"

    logger.info(
        "Search complete: %d results across %d platforms (freshness: %s)",
        total_results,
        len(results_by_platform),
        freshness,
    )

    # ── Step 2: Feed search results to LLM for analysis ──────────
    system_prompt = TREND_RESEARCHER_PROMPT.format(
        brand_name=brand["name"],
        niche=brand["niche"],
        target_audience=brand["target_audience"],
        search_results=search_results_text,
    )

    user_message = (
        f"Content request: {content_request}\n\n"
        f"Target platforms: {', '.join(platforms)}\n\n"
        "Analyze the search results above. Find real examples of successful "
        "public posts from famous accounts in this niche. Identify what hooks, "
        "formats, and content angles are working. Return your findings as the "
        "specified JSON format."
    )

    llm_cfg = state["llm_config"]
    llm = create_llm(
        provider=llm_cfg["provider"],
        api_key=llm_cfg["api_key"],
        model=llm_cfg["model"],
        agent_name="trend_researcher",
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)
    data = parse_json_response(response.content)

    trending_topics = data.get("trending_topics", [])
    competitor_insights = data.get("competitor_insights", [])

    logger.info(
        "Trend researcher found %d topics and %d competitor examples (freshness: %s)",
        len(trending_topics),
        len(competitor_insights),
        freshness,
    )

    return {
        "trending_topics": trending_topics,
        "competitor_insights": competitor_insights,
        "results_freshness": freshness,
        "cache_age_seconds": 0,
        "messages": [response],
    }
