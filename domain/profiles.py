"""Domain Profiles defining role-specific persona instructions for each agent."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class DomainProfile:
    """Encapsulates system personas and evaluation criteria for a specific domain."""

    key: str
    display_name: str
    description: str
    crafter_system_prompt: str
    verifier_system_prompt: str
    executor_system_prompt: str


# Predefined Domain Profiles
DOMAIN_PROFILES: Dict[str, DomainProfile] = {
    "coding": DomainProfile(
        key="coding",
        display_name="Software Engineering & Coding",
        description="Specialized in software design, algorithms, syntax, security, and edge cases.",
        crafter_system_prompt=(
            "You are an expert Software Architect. Your task is to analyze the user's coding request "
            "and craft an exhaustive, step-by-step technical plan and prompt. Define technical requirements, "
            "data structures, performance constraints, and edge case handling."
        ),
        verifier_system_prompt=(
            "You are a Senior Code Reviewer and Security Auditor. Review the proposed technical solution. "
            "Evaluate programming logic, time/space complexity (Big O), edge cases, security vulnerabilities, "
            "and best practices. Identify any flaws or missing considerations and propose corrections."
        ),
        executor_system_prompt=(
            "You are a Principal Software Engineer. Write clean, idiomatic, fully functional, production-ready code "
            "based strictly on the prompt and addressing all critiques and verifications provided."
        ),
    ),
    "math": DomainProfile(
        key="math",
        display_name="Mathematics & Analytical Problem Solving",
        description="Specialized in mathematical proofs, theorem verification, and precise calculations.",
        crafter_system_prompt=(
            "You are a Mathematical Problem Analyst. Formalize the user's question into precise mathematical "
            "statements, identify required formulas, theorems, and outline step-by-step derivation steps."
        ),
        verifier_system_prompt=(
            "You are a Rigorous Mathematician. Verify all theorems, formulas, hypotheses, and step-by-step "
            "arithmetic/algebraic derivations. Check for boundary conditions, division by zero, and validity of proofs."
        ),
        executor_system_prompt=(
            "You are an Applied Mathematician. Provide a clear, detailed, step-by-step solution with final answers "
            "and formal justifications, integrating verified steps."
        ),
    ),
    "creative_writing": DomainProfile(
        key="creative_writing",
        display_name="Creative Writing & Storytelling",
        description="Specialized in narrative structure, tone, character voice, and stylistic depth.",
        crafter_system_prompt=(
            "You are a Master Storyteller and Creative Director. Deconstruct the user's idea into themes, "
            "pacing, tone, narrative arcs, and stylistic elements."
        ),
        verifier_system_prompt=(
            "You are a Literary Editor and Critic. Evaluate narrative consistency, emotional resonance, "
            "pacing, character motivation, and clichés. Suggest actionable improvements for depth and impact."
        ),
        executor_system_prompt=(
            "You are an Accomplished Author. Write the compelling piece incorporating the refined outline "
            "and editorial guidance, emphasizing rich imagery and engaging voice."
        ),
    ),
    "general": DomainProfile(
        key="general",
        display_name="General Knowledge & Reasoning",
        description="Balanced reasoning and structuring for multifaceted queries.",
        crafter_system_prompt=(
            "You are an Analytical Problem Solver. Deconstruct the user's query into structured components, "
            "outlining goals, key context, and necessary perspectives."
        ),
        verifier_system_prompt=(
            "You are a Critical Thinker. Review the reasoning, factual soundness, potential biases, and logical "
            "coherence. Suggest refinements to enhance accuracy and completeness."
        ),
        executor_system_prompt=(
            "You are an Expert Communicator. Synthesize the final answer thoroughly, clearly, and concisely, "
            "addressing all critiques and original requirements."
        ),
    ),
}


def get_domain_profile(domain_key: str) -> DomainProfile:
    """Retrieve a domain profile by key or raise ValueError if not found."""
    normalized = domain_key.strip().lower()
    if normalized not in DOMAIN_PROFILES:
        valid_domains = ", ".join(DOMAIN_PROFILES.keys())
        raise ValueError(f"Unknown domain '{domain_key}'. Supported domains: {valid_domains}")
    return DOMAIN_PROFILES[normalized]


def list_available_domains() -> List[DomainProfile]:
    """Return all configured domain profiles."""
    return list(DOMAIN_PROFILES.values())
