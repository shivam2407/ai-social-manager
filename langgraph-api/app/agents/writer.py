"""Writer Agent — generates platform-specific content that sounds human."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_llm
from app.prompts import WRITER_PROMPT
from app.response_parser import parse_json_response

logger = logging.getLogger(__name__)


async def writer_node(state: dict[str, Any]) -> dict[str, Any]:
    """Write platform-specific social media content."""
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

    llm_cfg = state["llm_config"]
    llm = create_llm(
        provider=llm_cfg["provider"], api_key=llm_cfg["api_key"],
        model=llm_cfg["model"], agent_name="writer",
    )

    reference_images = state.get("reference_images", [])
    if reference_images:
        content_blocks = [{"type": "text", "text": user_message}]
        for img_uri in reference_images:
            content_blocks.append({"type": "image_url", "image_url": {"url": img_uri}})
        human_msg = HumanMessage(content=content_blocks)
    else:
        human_msg = HumanMessage(content=user_message)

    messages = [SystemMessage(content=system_prompt), human_msg]

    response = await llm.ainvoke(messages)
    data = parse_json_response(response.content)

    logger.debug("Writer raw parsed data keys: %s", list(data.keys()))

    # Parse drafts from response
    drafts: dict[str, dict[str, Any]] = {}
    raw_drafts = data.get("drafts", data)
    for platform in target_platforms:
        if platform in raw_drafts:
            draft = raw_drafts[platform]
            logger.info("Writer draft for %s keys: %s", platform, list(draft.keys()) if isinstance(draft, dict) else type(draft))

            # Some providers nest content under different keys
            if isinstance(draft, dict) and not draft.get("content"):
                # Try common alternative keys (including Instagram-specific ones)
                for alt_key in ("caption", "text", "body", "post", "copy",
                                "reel_script", "reel_caption", "reel",
                                "story", "description", "main_caption"):
                    if alt_key in draft:
                        val = draft[alt_key]
                        if isinstance(val, str) and val.strip():
                            draft["content"] = val
                            break
                        elif isinstance(val, dict):
                            # e.g. {"reel": {"script": "...", "caption": "..."}}
                            draft["content"] = val.get("caption", val.get("script", val.get("text", str(val))))
                            break

                # If still no content, try joining sub-posts (carousel/thread)
                if not draft.get("content"):
                    for key in ("posts", "slides", "items", "thread", "tweets",
                                "carousel_slides", "carousel", "reels"):
                        if isinstance(draft.get(key), list):
                            parts = []
                            for item in draft[key]:
                                if isinstance(item, str):
                                    parts.append(item)
                                elif isinstance(item, dict):
                                    parts.append(item.get("content", item.get("caption", item.get("text", str(item)))))
                            # Use --- for carousels, \n\n for threads
                            sep = "\n\n---\n\n" if key in ("slides", "items", "carousel_slides", "carousel") else "\n\n"
                            draft["content"] = sep.join(parts)
                            break

                # Last resort: concatenate all string values in the draft
                if not draft.get("content"):
                    string_vals = [v for k, v in draft.items()
                                   if isinstance(v, str) and v.strip()
                                   and k not in ("platform", "content_type", "image_prompt")]
                    if string_vals:
                        draft["content"] = "\n\n".join(string_vals)
                        logger.warning(
                            "Writer: no recognized content key for %s, "
                            "concatenated %d string fields as fallback",
                            platform, len(string_vals),
                        )

            if isinstance(draft, str):
                draft = {"content": draft}

            if "character_count" not in draft or draft.get("character_count", 0) == 0:
                draft["character_count"] = len(draft.get("content", ""))
            draft["platform"] = platform
            drafts[platform] = draft

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
