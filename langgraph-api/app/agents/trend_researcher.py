"""Trend Researcher Agent — discovers trending topics and competitor insights."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_llm
from app.prompts import TREND_RESEARCHER_PROMPT
from app.response_parser import parse_json_response

logger = logging.getLogger(__name__)


async def trend_researcher_node(state: dict[str, Any]) -> dict[str, Any]:
    """Research trending topics and competitor activity for the brand."""
    brand = state["brand_profile"]
    content_request = state["content_request"]

    system_prompt = TREND_RESEARCHER_PROMPT.format(
        brand_name=brand["name"],
        niche=brand["niche"],
        target_audience=brand["target_audience"],
    )

    user_message = (
        f"Research trends for this content request: {content_request}\n\n"
        f"Target platforms: {', '.join(state['target_platforms'])}\n\n"
        "Find trending topics, competitor insights, and hashtag opportunities. "
        "Return your findings as the specified JSON format."
    )

    llm_cfg = state["llm_config"]
    llm = create_llm(
        provider=llm_cfg["provider"], api_key=llm_cfg["api_key"],
        model=llm_cfg["model"], agent_name="trend_researcher",
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
        "Trend researcher found %d topics and %d competitor insights",
        len(trending_topics),
        len(competitor_insights),
    )

    return {
        "trending_topics": trending_topics,
        "competitor_insights": competitor_insights,
        "messages": [response],
    }
