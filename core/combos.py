"""Routing Combos / Presets for EasyPrompt pipeline.

Each RoutingProfile defines a named strategy with fallback chains for
each pipeline stage (PromptCrafter, LogicVerifier, Executor).

Models that lack a configured API key are automatically filtered out
by RouterClient.filter_chain(), so combos gracefully degrade when
not all providers are set up.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class RoutingProfile(BaseModel):
    """A named routing preset with per-stage fallback chains."""

    id: str
    name: str
    icon: str = "🎯"
    description: str
    crafter_chain: List[str] = Field(
        description="Ordered model chain for PromptCrafter (first = primary)"
    )
    verifier_chain: List[str] = Field(
        description="Ordered model chain for LogicVerifier (first = primary)"
    )
    executor_chain: List[str] = Field(
        description="Ordered model chain for Executor (first = primary)"
    )


# ─────────────────────── Predefined Combos ───────────────────────

ROUTING_PROFILES: Dict[str, RoutingProfile] = {
    "coding_pro": RoutingProfile(
        id="coding_pro",
        name="Best for Coding",
        icon="💻",
        description=(
            "Quality-first routing for software engineering. "
            "Prioritizes strong reasoning models (DeepSeek, Claude) with "
            "Gemini and Groq as reliable fallbacks."
        ),
        crafter_chain=[
            "deepseek/deepseek-chat",
            "gemini/gemini-3.8-flash",
            "groq/llama-3.3-70b-versatile",
        ],
        verifier_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
        ],
        executor_chain=[
            "deepseek/deepseek-chat",
            "gemini/gemini-3.8-flash",
            "groq/llama-3.3-70b-versatile",
        ],
    ),
    "fast_throughput": RoutingProfile(
        id="fast_throughput",
        name="Ultra Fast / Low Latency",
        icon="⚡",
        description=(
            "Speed-first routing using Groq's LPU hardware for near-instant "
            "inference. Falls back to Gemini and DeepSeek for resilience."
        ),
        crafter_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
        ],
        verifier_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
        ],
        executor_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
        ],
    ),
    "free_tier": RoutingProfile(
        id="free_tier",
        name="Free Tier Optimized",
        icon="🆓",
        description=(
            "Uses only free-tier models. Groq and Gemini AI Studio offer "
            "generous free quotas. OpenRouter ':free' models as last resort."
        ),
        crafter_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        ],
        verifier_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        ],
        executor_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        ],
    ),
    "balanced": RoutingProfile(
        id="balanced",
        name="Balanced Reasoning",
        icon="⚖️",
        description=(
            "Well-rounded routing balancing quality, speed, and cost. "
            "Gemini as primary with Groq speed and DeepSeek depth as fallbacks."
        ),
        crafter_chain=[
            "gemini/gemini-3.8-flash",
            "groq/llama-3.3-70b-versatile",
            "deepseek/deepseek-chat",
        ],
        verifier_chain=[
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
        ],
        executor_chain=[
            "gemini/gemini-3.8-flash",
            "deepseek/deepseek-chat",
            "groq/llama-3.3-70b-versatile",
        ],
    ),
    "deep_reasoning": RoutingProfile(
        id="deep_reasoning",
        name="Deep Reasoning & Analysis",
        icon="🧠",
        description=(
            "Optimized for complex reasoning tasks like mathematics, proofs, "
            "and multi-step analysis. Prioritizes DeepSeek Reasoner and Gemini Pro."
        ),
        crafter_chain=[
            "deepseek/deepseek-reasoner",
            "gemini/gemini-3.8-flash",
            "groq/llama-3.3-70b-versatile",
        ],
        verifier_chain=[
            "deepseek/deepseek-reasoner",
            "groq/llama-3.3-70b-versatile",
            "gemini/gemini-3.8-flash",
        ],
        executor_chain=[
            "deepseek/deepseek-chat",
            "gemini/gemini-3.8-flash",
            "groq/llama-3.3-70b-versatile",
        ],
    ),
}


def get_routing_profile(profile_id: str) -> RoutingProfile:
    """Retrieve a routing profile by ID."""
    normalized = profile_id.strip().lower()
    if normalized not in ROUTING_PROFILES:
        available = ", ".join(ROUTING_PROFILES.keys())
        raise ValueError(f"Unknown routing profile '{profile_id}'. Available: {available}")
    return ROUTING_PROFILES[normalized]


def list_routing_profiles() -> List[RoutingProfile]:
    """Return all available routing profiles."""
    return list(ROUTING_PROFILES.values())
