"""LLM factory — maps provider + key + model to a LangChain chat model."""

from __future__ import annotations

import json
from typing import Any, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration

# Per-agent defaults for temperature and max_tokens
_AGENT_CONFIGS: dict[str, dict[str, int | float]] = {
    "writer": {"temperature": 0.8, "max_tokens": 4096},
    "critic": {"temperature": 0.3, "max_tokens": 2048},
}
_DEFAULT_CONFIG = {"temperature": 0.7, "max_tokens": 2048}


# ── Mock LLM for testing without API calls ──────────────────────

_MOCK_RESPONSES: dict[str, str] = {
    "trend_researcher": json.dumps({
        "trending_topics": [
            {"topic": "Behind-the-scenes content", "relevance_score": 0.95, "source": "industry_trends", "description": "Audiences love raw, unpolished looks at how things are made"},
            {"topic": "Founder storytelling", "relevance_score": 0.9, "source": "platform_analysis", "description": "Personal origin stories drive 3x more engagement"},
            {"topic": "Limited drops and scarcity", "relevance_score": 0.85, "source": "competitor_analysis", "description": "Small-batch announcements create urgency and FOMO"},
        ],
        "competitor_insights": [
            {"competitor_name": "Similar brands in niche", "content_theme": "Day-in-the-life content", "engagement_notes": "High save rates on carousel posts", "opportunity": "More authentic, less polished content would stand out"},
        ],
    }),
    "strategist": json.dumps({
        "theme": "Authentic brand launch story",
        "content_pillars": ["founder story", "product quality", "community building"],
        "campaign_context": "Launch campaign to build trust and excitement",
        "angles": [
            {"platform": "twitter", "hook": "Hot take on the industry", "content_type": "thread", "reasoning": "Twitter rewards bold opinions and threads get algorithmic boost", "best_posting_time": "Tuesday 9am EST"},
            {"platform": "linkedin", "hook": "Personal founder journey story", "content_type": "single_post", "reasoning": "LinkedIn audience loves vulnerable founder stories", "best_posting_time": "Wednesday 8am EST"},
            {"platform": "instagram", "hook": "Visual behind-the-scenes", "content_type": "carousel", "reasoning": "Carousels get highest save rates on Instagram", "best_posting_time": "Thursday 12pm EST"},
        ],
    }),
    "writer": json.dumps({
        "drafts": {
            "twitter": {
                "platform": "twitter",
                "content": "I spent 6 months perfecting one recipe before I sold a single thing.\n\nNot because I'm a perfectionist — because I kept eating all the test batches.\n\nFinally taking orders this week. If you're local, DM me before they're gone.",
                "hashtags": ["SmallBusiness", "FoodLover", "LocalEats"],
                "call_to_action": "DM to order",
                "character_count": 245,
                "content_type": "single_post",
                "image_prompt": "Flat lay of fresh baked goods on rustic wooden table, warm lighting",
            },
            "linkedin": {
                "platform": "linkedin",
                "content": "I quit my corporate job 8 months ago to start something that scared me.\n\nNot a tech startup. Not a consulting firm.\n\nA home bakery.\n\nPeople thought I was crazy. Honestly? Some days I agreed with them. The 2am wake-ups, the flour-covered kitchen, the 47th attempt at getting sourdough right.\n\nBut here's what nobody tells you about following a passion — the hard days still feel better than the easy days at a job you've outgrown.\n\nToday I'm officially open for orders. It's small, it's scrappy, and every single item is made from scratch.\n\nIf you're in the area, I'd love to bake for you.",
                "hashtags": ["Entrepreneurship", "SmallBusiness", "FollowYourPassion"],
                "call_to_action": "Link in comments to order",
                "character_count": 620,
                "content_type": "single_post",
                "image_prompt": "Founder in kitchen, candid shot, smiling while kneading dough",
            },
            "instagram": {
                "platform": "instagram",
                "content": "47 failed batches. 6 months of testing. 1 very supportive (and very full) taste-testing crew.\n\nWe're officially open for orders and I can't believe I'm typing this.\n\nEvery loaf, every pastry, every cookie — made from scratch in my kitchen with ingredients I actually trust. No shortcuts, no preservatives, just the real thing.\n\nSwipe to see the journey from burnt first attempt to what I'm making now.\n\nLocal delivery available — link in bio to order. First 20 orders get a free cookie because honestly I just want to share this with people.",
                "hashtags": ["HomeBakery", "BakedFromScratch", "SmallBatchBaking", "FoodieFinds", "SupportLocal"],
                "call_to_action": "Link in bio to order",
                "character_count": 540,
                "content_type": "carousel",
                "image_prompt": "Before/after grid: burnt bread vs beautiful golden loaf, bright natural lighting",
            },
        }
    }),
    "critic": json.dumps({
        "scores": [
            {"platform": "twitter", "brand_voice_score": 9, "engagement_score": 8, "platform_fit_score": 9, "clarity_score": 8, "overall_score": 8.5, "feedback": "Strong conversational tone. The self-deprecating humor works perfectly for Twitter.", "approved": True},
            {"platform": "linkedin", "brand_voice_score": 8, "engagement_score": 9, "platform_fit_score": 9, "clarity_score": 8, "overall_score": 8.5, "feedback": "Great founder vulnerability story. The hook line creates curiosity.", "approved": True},
            {"platform": "instagram", "brand_voice_score": 9, "engagement_score": 8, "platform_fit_score": 8, "clarity_score": 9, "overall_score": 8.5, "feedback": "Good use of specific numbers. Carousel format is smart for this story.", "approved": True},
        ],
        "summary": "All drafts approved. Authentic voice throughout, strong platform-native formatting, specific details make it feel genuinely human-written.",
    }),
}


class MockChatModel(BaseChatModel):
    """Fake LLM that returns canned responses per agent. Zero API calls."""

    agent_name: str = ""

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        text = _MOCK_RESPONSES.get(self.agent_name, '{"mock": true}')
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


# ── Factory ──────────────────────────────────────────────────────

def create_llm(
    provider: str,
    api_key: str,
    model: str,
    agent_name: str = "",
) -> BaseChatModel:
    if provider == "mock":
        return MockChatModel(agent_name=agent_name)

    cfg = _AGENT_CONFIGS.get(agent_name, _DEFAULT_CONFIG)
    temperature = cfg["temperature"]
    max_tokens = cfg["max_tokens"]

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model,
            anthropic_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    if provider == "grok":
        from langchain_xai import ChatXAI

        return ChatXAI(
            model=model,
            xai_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "chatgpt":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ValueError(f"Unsupported provider: {provider}")
