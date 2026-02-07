"""Pydantic models for the AI Social Media Manager."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class Platform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


# --- Brand ---

class BrandProfile(BaseModel):
    name: str = Field(description="Brand or business name")
    niche: str = Field(description="Industry or niche (e.g., 'developer tools', 'fitness coaching')")
    target_audience: str = Field(description="Who the brand speaks to")
    voice_description: str = Field(
        default="Professional yet approachable. Clear, concise, and helpful.",
        description="Description of how the brand communicates",
    )
    tone_keywords: list[str] = Field(
        default_factory=lambda: ["authentic", "knowledgeable", "conversational"],
        description="Keywords that define the brand tone",
    )
    example_posts: list[str] = Field(
        default_factory=list,
        description="Example posts that represent the brand voice",
    )


# --- Research ---

class TrendItem(BaseModel):
    topic: str
    relevance_score: float = Field(ge=0, le=1, description="How relevant to the brand niche (0-1)")
    source: str = Field(default="web_search", description="Where this trend was found")
    description: str = Field(default="", description="Brief description of the trend")


class CompetitorInsight(BaseModel):
    competitor_name: str
    content_theme: str
    engagement_notes: str
    opportunity: str = Field(description="What we can do better or differently")


# --- Strategy ---

class ContentAngle(BaseModel):
    platform: Platform
    hook: str = Field(description="The opening hook or angle")
    content_type: str = Field(description="e.g., 'thread', 'single post', 'carousel', 'story'")
    reasoning: str = Field(description="Why this angle works for this platform")
    best_posting_time: str = Field(default="", description="Recommended posting time")


class ContentPlan(BaseModel):
    theme: str = Field(description="Overall content theme")
    angles: list[ContentAngle] = Field(description="Platform-specific angles")
    content_pillars: list[str] = Field(
        default_factory=list,
        description="Content pillars this post aligns with",
    )
    campaign_context: str = Field(
        default="",
        description="How this fits into the broader content strategy",
    )


# --- Writing ---

class PlatformDraft(BaseModel):
    platform: Platform
    content: str = Field(description="The actual post content")
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = Field(default="")
    character_count: int = Field(default=0)
    content_type: str = Field(default="single_post", description="thread, single_post, carousel, story")
    image_prompt: str = Field(
        default="",
        description="AI image generation prompt if visual is needed",
    )


# --- Critic ---

class CriticScore(BaseModel):
    platform: Platform
    brand_voice_score: int = Field(ge=1, le=10, description="How well it matches brand voice")
    engagement_score: int = Field(ge=1, le=10, description="Predicted engagement potential")
    platform_fit_score: int = Field(ge=1, le=10, description="How native it feels to the platform")
    clarity_score: int = Field(ge=1, le=10, description="How clear the message is")
    overall_score: float = Field(ge=1, le=10, description="Weighted average score")
    feedback: str = Field(description="Specific, actionable feedback for improvement")
    approved: bool = Field(description="Whether this draft passes quality gate (>=7)")


class CriticReview(BaseModel):
    scores: list[CriticScore] = Field(description="Score per platform draft")
    summary: str = Field(description="Overall review summary")


# --- Final Output ---

class FinalPost(BaseModel):
    platform: Platform
    content: str
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = Field(default="")
    content_type: str = Field(default="single_post")
    image_prompt: str = Field(default="")
    critic_score: float = Field(default=0)
    status: PostStatus = Field(default=PostStatus.DRAFT)
    scheduled_at: Optional[datetime] = None


# --- API Request/Response ---

class GenerateRequest(BaseModel):
    brand_name: str
    niche: str
    target_audience: str = "general audience"
    voice_description: str = "Professional yet approachable. Clear, concise, and helpful."
    tone_keywords: list[str] = Field(default_factory=lambda: ["authentic", "knowledgeable"])
    example_posts: list[str] = Field(default_factory=list)
    content_request: str = Field(description="What to write about")
    target_platforms: list[Platform] = Field(
        default_factory=lambda: [Platform.TWITTER, Platform.LINKEDIN],
    )


class GenerateResponse(BaseModel):
    thread_id: str
    status: str
    posts: list[FinalPost] = Field(default_factory=list)
    revision_count: int = 0
    critic_summary: str = ""
