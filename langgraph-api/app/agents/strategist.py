"""Strategist Agent — plans content angles and strategy per platform."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import STRATEGIST_PROMPT

logger = logging.getLogger(__name__)


async def strategist_node(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze trends and plan platform-specific content strategy.

    This node:
    1. Takes research output (trends, competitor insights)
    2. Plans a content strategy with per-platform angles
    3. Returns a content plan for the writer agent
    """
    brand = state["brand_profile"]
    content_request = state["content_request"]
    trending_topics = state.get("trending_topics", [])
    competitor_insights = state.get("competitor_insights", [])

    system_prompt = STRATEGIST_PROMPT.format(
        brand_name=brand["name"],
        niche=brand["niche"],
        target_audience=brand["target_audience"],
        voice_description=brand.get("voice_description", "Professional yet approachable"),
        tone_keywords=", ".join(brand.get("tone_keywords", ["authentic"])),
    )

    user_message = f"""Content Request: {content_request}

Target Platforms: {', '.join(state['target_platforms'])}

## Research Data

### Trending Topics
{json.dumps(trending_topics, indent=2) if trending_topics else "No trends data available — use your expertise."}

### Competitor Insights
{json.dumps(competitor_insights, indent=2) if competitor_insights else "No competitor data available — use your expertise."}

Create a content plan with DIFFERENT angles for each platform. \
Do NOT just reformat the same message."""

    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        temperature=0.7,
        max_tokens=2048,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)

    # Parse strategy response
    content_plan: dict[str, Any] = {}
    selected_angles: list[dict[str, Any]] = []

    try:
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )

        json_str = _extract_json(content)
        if json_str:
            data = json.loads(json_str)
            content_plan = {
                "theme": data.get("theme", ""),
                "content_pillars": data.get("content_pillars", []),
                "campaign_context": data.get("campaign_context", ""),
                "angles": data.get("angles", []),
            }
            selected_angles = data.get("angles", [])
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse strategist response as JSON: %s", e)

    logger.info(
        "Strategist planned %d platform angles for theme: %s",
        len(selected_angles),
        content_plan.get("theme", "unknown"),
    )

    return {
        "content_plan": content_plan,
        "selected_angles": selected_angles,
        "messages": [response],
    }


def _extract_json(text: str) -> str | None:
    """Extract a JSON object from text that may contain markdown fences."""
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        return text[brace_start : brace_end + 1]
    return None
