"""Trend Researcher Agent — discovers trending topics and competitor insights."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import TREND_RESEARCHER_PROMPT

logger = logging.getLogger(__name__)


async def trend_researcher_node(state: dict[str, Any]) -> dict[str, Any]:
    """Research trending topics and competitor activity for the brand.

    This node:
    1. Formats the system prompt with brand context
    2. Calls LLM to identify trends using training knowledge
    3. Parses structured trend data from the response
    4. Returns state updates for downstream agents
    """
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

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=2048)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)

    # Parse the response — extract JSON from the content
    trending_topics = []
    competitor_insights = []

    try:
        content = response.content
        # Handle case where content is a list (tool use responses)
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )

        # Try to extract JSON from the response
        json_str = _extract_json(content)
        if json_str:
            data = json.loads(json_str)
            trending_topics = data.get("trending_topics", [])
            competitor_insights = data.get("competitor_insights", [])
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse trend researcher response as JSON: %s", e)

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


def _extract_json(text: str) -> str | None:
    """Extract a JSON object from text that may contain markdown fences."""
    # Try to find JSON in code blocks
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    # Try the whole text as JSON
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        return text[brace_start : brace_end + 1]
    return None
