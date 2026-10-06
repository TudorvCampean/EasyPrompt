"""Factory for creating agents configured with domain-specific personas."""

from typing import Optional, Tuple
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
        crafter_client: BaseLLMClient,
        verifier_client: BaseLLMClient,
        executor_client: Optional[BaseLLMClient] = None,
    ) -> Tuple[PromptCrafter, LogicVerifier, Executor]:
        """Instantiate Crafter, Verifier, and Executor with domain personas and injected LLM clients."""
        final_executor_client = executor_client if executor_client is not None else crafter_client

        crafter = PromptCrafter(
            name=f"PromptCrafter [{domain_profile.display_name}]",
            llm_client=crafter_client,
            system_instruction=domain_profile.crafter_system_prompt,
        )

        verifier = LogicVerifier(
            name=f"LogicVerifier [{domain_profile.display_name}]",
            llm_client=verifier_client,
            system_instruction=domain_profile.verifier_system_prompt,
        )

        executor = Executor(
            name=f"Executor [{domain_profile.display_name}]",
            llm_client=final_executor_client,
            system_instruction=domain_profile.executor_system_prompt,
        )

        return crafter, verifier, executor
