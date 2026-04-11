"""LangGraph state definition for the social media content pipeline."""

from __future__ import annotations

import operator
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class SocialMediaState(TypedDict):
    """Full state flowing through the multi-agent content generation graph.

    Senior-level patterns demonstrated:
    - Annotated reducers for message accumulation
    - Typed fields for every phase of the pipeline
    - Clear separation of input / intermediate / output state
    """

    # ── Input (set once at the start) ──────────────────────────────
    brand_profile: dict[str, Any]          # serialized BrandProfile
    content_request: str                    # user's content brief
    target_platforms: list[str]             # ["twitter", "linkedin", ...]
    llm_config: dict[str, str]             # {"provider", "api_key", "model"}
    reference_images: list[str]             # data URI strings for vision input

    # ── Agent messages (accumulated via reducer) ───────────────────
    messages: Annotated[list[BaseMessage], add_messages]

    # ── Research phase ─────────────────────────────────────────────
    trending_topics: list[dict[str, Any]]   # list of TrendItem dicts
    competitor_insights: list[dict[str, Any]]
    results_freshness: str                   # "live", "cached", or "unavailable"
    cache_age_seconds: int                   # age of cached search results

    # ── Strategy phase ─────────────────────────────────────────────
    content_plan: dict[str, Any]            # serialized ContentPlan
    selected_angles: list[dict[str, Any]]   # per-platform angles

    # ── Writing phase ──────────────────────────────────────────────
    drafts: dict[str, dict[str, Any]]       # platform -> PlatformDraft dict

    # ── Review phase ───────────────────────────────────────────────
    critic_scores: dict[str, dict[str, Any]]  # platform -> CriticScore dict
    critic_summary: str
    revision_count: Annotated[int, operator.add]  # accumulates across cycles
    approved: bool

    # ── Output ─────────────────────────────────────────────────────
    final_posts: dict[str, dict[str, Any]]  # platform -> FinalPost dict
