"""Critic Agent — reviews drafts and decides approve vs. revise."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import CRITIC_PROMPT

logger = logging.getLogger(__name__)

# Quality gate threshold
APPROVAL_THRESHOLD = 7.0
MAX_REVISIONS = 3


async def critic_node(state: dict[str, Any]) -> dict[str, Any]:
    """Review content drafts and score them against quality criteria.

    This node:
    1. Takes writer drafts and brand context
    2. Scores each draft on voice, engagement, platform fit, clarity
    3. Decides approve (>= 7) or revise (< 7)
    4. Returns scores and approval status that controls the graph cycle
    """
    brand = state["brand_profile"]
    drafts = state.get("drafts", {})
    revision_count = state.get("revision_count", 0)

    if not drafts:
        logger.warning("Critic received no drafts to review")
        return {
            "critic_scores": {},
            "critic_summary": "No drafts to review.",
            "approved": True,  # Nothing to reject
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

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,  # Lower temperature for consistent scoring
        max_tokens=2048,
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    response = await llm.ainvoke(messages)

    # Parse critic response
    critic_scores: dict[str, dict[str, Any]] = {}
    critic_summary = ""
    all_approved = True

    try:
        content = response.content
        if isinstance(content, list):
            content = " ".join(
                block.get("text", "") for block in content if isinstance(block, dict)
            )

        json_str = _extract_json(content)
        if json_str:
            data = json.loads(json_str)
            scores_list = data.get("scores", [])
            critic_summary = data.get("summary", "")

            for score in scores_list:
                platform = score.get("platform", "unknown")
                # Calculate overall score if not provided
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
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse critic response as JSON: %s", e)
        # If we can't parse, approve to avoid infinite loop
        all_approved = True
        critic_summary = "Could not parse critic response — auto-approving."

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


def _sanitize_json(text: str) -> str:
    """Fix common LLM JSON issues: control chars inside strings."""
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
