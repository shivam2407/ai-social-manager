"""Strategist Agent — plans content angles and strategy per platform."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_llm
from app.prompts import STRATEGIST_PROMPT
from app.response_parser import parse_json_response

logger = logging.getLogger(__name__)


async def strategist_node(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze trends and plan platform-specific content strategy."""
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

    llm_cfg = state["llm_config"]
    llm = create_llm(
        provider=llm_cfg["provider"], api_key=llm_cfg["api_key"],
        model=llm_cfg["model"], agent_name="strategist",
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)
    data = parse_json_response(response.content)

    content_plan = {
        "theme": data.get("theme", ""),
        "content_pillars": data.get("content_pillars", []),
        "campaign_context": data.get("campaign_context", ""),
        "angles": data.get("angles", []),
    }
    selected_angles = data.get("angles", [])

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
