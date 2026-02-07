"""Writer Agent — generates platform-specific content that sounds human."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import WRITER_PROMPT

logger = logging.getLogger(__name__)


async def writer_node(state: dict[str, Any]) -> dict[str, Any]:
    """Write platform-specific social media content.

    This node:
    1. Takes the content plan and brand context
    2. Generates platform-native content (different for each platform)
    3. On revision cycles, incorporates critic feedback
    4. Returns drafts keyed by platform
    """
    brand = state["brand_profile"]
    content_request = state["content_request"]
    content_plan = state.get("content_plan", {})
    selected_angles = state.get("selected_angles", [])
    target_platforms = state["target_platforms"]

    # Check if this is a revision cycle
    critic_scores = state.get("critic_scores", {})
    critic_summary = state.get("critic_summary", "")
    revision_count = state.get("revision_count", 0)
    previous_drafts = state.get("drafts", {})

    system_prompt = WRITER_PROMPT.format(
        brand_name=brand["name"],
        niche=brand["niche"],
        target_audience=brand["target_audience"],
        voice_description=brand.get("voice_description", "Professional yet approachable"),
        tone_keywords=", ".join(brand.get("tone_keywords", ["authentic"])),
        example_posts="\n".join(brand.get("example_posts", ["(no examples provided)"])),
    )

    # Build the user message based on whether this is first draft or revision
    if revision_count > 0 and critic_scores:
        user_message = _build_revision_message(
            content_request=content_request,
            target_platforms=target_platforms,
            content_plan=content_plan,
            selected_angles=selected_angles,
            previous_drafts=previous_drafts,
            critic_scores=critic_scores,
            critic_summary=critic_summary,
            revision_number=revision_count,
        )
    else:
        user_message = _build_first_draft_message(
            content_request=content_request,
            target_platforms=target_platforms,
            content_plan=content_plan,
            selected_angles=selected_angles,
        )

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.8, max_tokens=4096)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)

    # Parse drafts from response
    drafts: dict[str, dict[str, Any]] = {}

    try:
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )

        json_str = _extract_json(content)
        if json_str:
            data = json.loads(json_str)
            raw_drafts = data.get("drafts", data)
            for platform in target_platforms:
                if platform in raw_drafts:
                    draft = raw_drafts[platform]
                    # Ensure character count is set
                    if "character_count" not in draft or draft["character_count"] == 0:
                        draft["character_count"] = len(draft.get("content", ""))
                    draft["platform"] = platform
                    drafts[platform] = draft
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse writer response as JSON: %s", e)

    logger.info(
        "Writer generated drafts for %d platforms (revision #%d)",
        len(drafts),
        revision_count,
    )

    return {
        "drafts": drafts,
        "messages": [response],
        "revision_count": 1,  # This gets ADDED via the operator.add reducer
    }


def _build_first_draft_message(
    content_request: str,
    target_platforms: list[str],
    content_plan: dict[str, Any],
    selected_angles: list[dict[str, Any]],
) -> str:
    return f"""Content Request: {content_request}

Target Platforms: {', '.join(target_platforms)}

## Content Plan
{json.dumps(content_plan, indent=2) if content_plan else "No plan available — use your best judgment."}

## Platform Angles
{json.dumps(selected_angles, indent=2) if selected_angles else "No angles specified — create platform-native content."}

Write content for EACH target platform. Each platform gets DIFFERENT content \
tailored to its culture and audience. Do NOT copy-paste across platforms."""


def _build_revision_message(
    content_request: str,
    target_platforms: list[str],
    content_plan: dict[str, Any],
    selected_angles: list[dict[str, Any]],
    previous_drafts: dict[str, dict[str, Any]],
    critic_scores: dict[str, dict[str, Any]],
    critic_summary: str,
    revision_number: int,
) -> str:
    return f"""REVISION #{revision_number} — Address the critic's feedback below.

Content Request: {content_request}
Target Platforms: {', '.join(target_platforms)}

## Your Previous Drafts
{json.dumps(previous_drafts, indent=2)}

## Critic Feedback
{critic_summary}

### Detailed Scores Per Platform
{json.dumps(critic_scores, indent=2)}

## Instructions
Revise ONLY the drafts that scored below 7.0. For approved drafts (>= 7.0), \
return them unchanged. Address EACH piece of feedback specifically — don't \
just rephrase the same content."""


def _sanitize_json(text: str) -> str:
    """Fix common LLM JSON issues: control chars inside strings."""
    # Replace literal newlines/tabs inside JSON string values with escaped versions
    return re.sub(r'(?<=": ")(.*?)(?=")', lambda m: m.group(0).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'), text, flags=re.DOTALL)


def _extract_json(text: str) -> str | None:
    """Extract a JSON object from text that may contain markdown fences."""
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return _sanitize_json(text[start:end].strip())
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return _sanitize_json(text[start:end].strip())
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1:
        return _sanitize_json(text[brace_start : brace_end + 1])
    return None
