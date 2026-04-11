"""Pydantic models for the AI Social Media Manager."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

import re

from pydantic import BaseModel, Field, field_validator


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
    raw_data: dict = Field(default_factory=dict)


# --- API Request/Response ---

class GenerateRequest(BaseModel):
    brand_name: str = Field(min_length=1, max_length=200)
    niche: str = Field(min_length=1, max_length=200)
    target_audience: str = Field(default="general audience", max_length=500)
    voice_description: str = Field(
        default="Professional yet approachable. Clear, concise, and helpful.",
        max_length=1000,
    )
    tone_keywords: list[str] = Field(default_factory=lambda: ["authentic", "knowledgeable"], max_length=20)
    example_posts: list[str] = Field(default_factory=list, max_length=10)
    content_request: str = Field(description="What to write about", min_length=1, max_length=2000)
    target_platforms: list[Platform] = Field(
        default_factory=lambda: [Platform.TWITTER, Platform.LINKEDIN],
        min_length=1,
        max_length=3,
    )
    images: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Up to 4 reference images as data URIs",
    )

    @field_validator("images")
    @classmethod
    def validate_images(cls, v: list[str]) -> list[str]:
        _DATA_URI_RE = re.compile(r"^data:image/(jpeg|png|webp|gif);base64,")
        for img in v:
            if not _DATA_URI_RE.match(img):
                raise ValueError("Each image must be a data:image/(jpeg|png|webp|gif);base64,... URI")
            if len(img) > 7_000_000:
                raise ValueError("Each image must be ≤ 7MB as a data URI (~5MB binary)")
        return v


class GenerateResponse(BaseModel):
    thread_id: str
    status: str
    posts: list[FinalPost] = Field(default_factory=list)
    revision_count: int = 0
    critic_summary: str = ""


# --- Auth ---

class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    onboarding_completed: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OnboardingUpdate(BaseModel):
    onboarding_completed: bool


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=1)


class GitHubAuthRequest(BaseModel):
    code: str = Field(min_length=1)


# --- Brand CRUD ---

class BrandProfileCreate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=200)
    niche: str = Field(min_length=1, max_length=200)
    target_audience: str = Field(default="general audience", max_length=500)
    voice_description: str = Field(default="", max_length=1000)
    tone_keywords: list[str] = Field(default_factory=list, max_length=20)
    example_posts: list[str] = Field(default_factory=list, max_length=10)


class BrandProfileResponse(BaseModel):
    id: int
    brand_name: str
    niche: str
    target_audience: str
    voice_description: str
    tone_keywords: list[str]
    example_posts: list[str]
    created_at: str = ""
    updated_at: str = ""


# --- History ---

class PostResponse(BaseModel):
    id: int
    platform: str
    content: str
    hashtags: list[str] = Field(default_factory=list)
    call_to_action: str = ""
    content_type: str = "single_post"
    image_prompt: str = ""
    critic_score: float = 0


class GenerationHistoryResponse(BaseModel):
    id: int
    thread_id: str
    content_request: str
    brand_name: str = ""
    status: str = "completed"
    revision_count: int = 0
    critic_summary: str = ""
    created_at: str = ""
    posts: list[PostResponse] = Field(default_factory=list)


class DashboardStats(BaseModel):
    total_generations: int = 0
    total_posts: int = 0
    avg_critic_score: float = 0


# --- LLM Providers ---

class ProviderEnum(str, Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROK = "grok"
    CHATGPT = "chatgpt"
    MOCK = "mock"


PROVIDER_MODELS: dict[str, list[str]] = {
    "claude": ["claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"],
    "gemini": ["gemini-2.0-flash", "gemini-2.5-pro"],
    "grok": ["grok-3", "grok-3-mini"],
    "chatgpt": ["gpt-4o", "gpt-4o-mini"],
    "mock": ["mock-v1"],
}

PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "claude": "claude-sonnet-4-5-20250929",
    "gemini": "gemini-2.0-flash",
    "grok": "grok-3",
    "chatgpt": "gpt-4o",
    "mock": "mock-v1",
}


class ApiKeyCreate(BaseModel):
    provider: ProviderEnum
    api_key: Optional[str] = Field(default=None, max_length=500)
    model: Optional[str] = None
    is_default: bool = False


class ApiKeyResponse(BaseModel):
    provider: str
    model: str
    is_default: bool
    key_hint: str = ""
    created_at: str = ""
    updated_at: str = ""


class ApiKeyTestRequest(BaseModel):
    provider: ProviderEnum
    api_key: str = Field(min_length=1, max_length=500)
    model: Optional[str] = None


class ApiKeyTestResponse(BaseModel):
    success: bool
    message: str


class ProviderInfo(BaseModel):
    provider: str
    models: list[str]
    default_model: str
