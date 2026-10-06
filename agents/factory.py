"""Factory for creating agents configured with domain-specific personas."""

from typing import Tuple
from core.llm_clients import BaseLLMClient
from domain.profiles import DomainProfile
from agents.prompt_crafter import PromptCrafter
from agents.logic_verifier import LogicVerifier
from agents.executor import Executor


class AgentFactory:
    """Factory creating configured multi-agent instances based on domain profiles."""

    @staticmethod
    def create_pipeline_agents(
        domain_profile: DomainProfile,
        gemini_client: BaseLLMClient,
        groq_client: BaseLLMClient,
    ) -> Tuple[PromptCrafter, LogicVerifier, Executor]:
        """Instantiate Crafter (Gemini), Verifier (Groq), and Executor (Gemini) with domain personas."""
        crafter = PromptCrafter(
            name=f"PromptCrafter [{domain_profile.display_name}]",
            llm_client=gemini_client,
            system_instruction=domain_profile.crafter_system_prompt,
        )

        verifier = LogicVerifier(
            name=f"LogicVerifier [{domain_profile.display_name}]",
            llm_client=groq_client,
            system_instruction=domain_profile.verifier_system_prompt,
        )

        executor = Executor(
            name=f"Executor [{domain_profile.display_name}]",
            llm_client=gemini_client,
            system_instruction=domain_profile.executor_system_prompt,
        )

        return crafter, verifier, executor
