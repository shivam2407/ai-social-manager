"""Critic Agent — reviews drafts and decides approve vs. revise."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_llm
from app.prompts import CRITIC_PROMPT
from app.response_parser import parse_json_response

logger = logging.getLogger(__name__)

# Quality gate threshold
APPROVAL_THRESHOLD = 7.0
MAX_REVISIONS = 3


async def critic_node(state: dict[str, Any]) -> dict[str, Any]:
    """Review content drafts and score them against quality criteria."""
    brand = state["brand_profile"]
    drafts = state.get("drafts", {})
    revision_count = state.get("revision_count", 0)

    if not drafts:
        logger.warning("Critic received no drafts to review")
        return {
            "critic_scores": {},
            "critic_summary": "No drafts to review.",
            "approved": True,
        }

    system_prompt = CRITIC_PROMPT.format(
        brand_name=brand["name"],
        voice_description=brand.get("voice_description", "Professional yet approachable"),
        tone_keywords=", ".join(brand.get("tone_keywords", ["authentic"])),
        example_posts="\n".join(brand.get("example_posts", ["(no examples provided)"])),
    )

    user_message = f"""Review the following social media drafts.

## Drafts to Review
{json.dumps(drafts, indent=2)}

## Context
- This is revision #{revision_count}
- Max revisions allowed: {MAX_REVISIONS}
- {"This is the FINAL revision — be lenient and approve unless there are critical issues." if revision_count >= MAX_REVISIONS else "Be thorough but constructive."}

Score each draft and determine if it passes the quality gate (>= 7.0)."""

    llm_cfg = state["llm_config"]
    llm = create_llm(
        provider=llm_cfg["provider"], api_key=llm_cfg["api_key"],
        model=llm_cfg["model"], agent_name="critic",
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

    # Parse critic response
    critic_scores: dict[str, dict[str, Any]] = {}
    raw_summary = data.get("summary", "")
    critic_summary = raw_summary if isinstance(raw_summary, str) else json.dumps(raw_summary)
    all_approved = True

    scores_list = data.get("scores", [])
    for score in scores_list:
        platform = score.get("platform", "unknown")
        if "overall_score" not in score:
            score["overall_score"] = (
                score.get("brand_voice_score", 5) * 0.3
                + score.get("engagement_score", 5) * 0.3
                + score.get("platform_fit_score", 5) * 0.2
                + score.get("clarity_score", 5) * 0.2
            )
        score["approved"] = score["overall_score"] >= APPROVAL_THRESHOLD
        if not score["approved"]:
            all_approved = False
        critic_scores[platform] = score

    # If parsing returned nothing, this is a parse failure — NOT an approval.
    # We retry once; if the retry also fails, force-approve with a clear warning
    # so the user knows this content wasn't properly reviewed.
    if not data:
        logger.warning(
            "Critic returned unparseable response — treating as parse failure, "
            "NOT as approval. Forcing approval with warning."
        )
        all_approved = True
        critic_summary = (
            "[WARNING: Critic agent returned malformed JSON. "
            "Content was NOT reviewed — auto-approved due to parse failure. "
            "Manual review recommended.]"
        )

    # Force approval if we've hit max revisions
    if revision_count >= MAX_REVISIONS and not all_approved:
        logger.info("Max revisions reached (%d) — force approving", revision_count)
        all_approved = True
        critic_summary += f"\n[Auto-approved after {MAX_REVISIONS} revision cycles]"
        for score in critic_scores.values():
            score["approved"] = True

    logger.info(
        "Critic review: %s (revision #%d, scores: %s)",
        "APPROVED" if all_approved else "NEEDS REVISION",
        revision_count,
        {p: s.get("overall_score", "?") for p, s in critic_scores.items()},
    )

    return {
        "critic_scores": critic_scores,
        "critic_summary": critic_summary,
        "approved": all_approved,
        "messages": [response],
    }
