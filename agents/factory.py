"""Factory for creating agents configured with domain-specific personas and routing chains."""

from typing import List, Tuple
from core.router import RouterClient
from core.combos import RoutingProfile
from domain.profiles import DomainProfile
from agents.prompt_crafter import PromptCrafter
from agents.logic_verifier import LogicVerifier
from agents.executor import Executor


class AgentFactory:
    """Factory creating configured multi-agent instances based on domain profiles and routing combos."""

    @staticmethod
    def create_pipeline_agents(
        domain_profile: DomainProfile,
        router: RouterClient,
        routing_profile: RoutingProfile,
    ) -> Tuple[PromptCrafter, LogicVerifier, Executor]:
        """Instantiate all pipeline agents with domain personas and routing chains.

        Args:
            domain_profile: Domain-specific personas/prompts for each agent.
            router: The unified RouterClient instance.
            routing_profile: The selected routing combo with fallback chains.

        Returns:
            Tuple of (PromptCrafter, LogicVerifier, Executor).
        """
        crafter = PromptCrafter(
            name=f"PromptCrafter [{domain_profile.display_name}]",
            router=router,
            model_chain=routing_profile.crafter_chain,
            system_instruction=domain_profile.crafter_system_prompt,
        )

        verifier = LogicVerifier(
            name=f"LogicVerifier [{domain_profile.display_name}]",
            router=router,
            model_chain=routing_profile.verifier_chain,
            system_instruction=domain_profile.verifier_system_prompt,
        )

        executor = Executor(
            name=f"Executor [{domain_profile.display_name}]",
            router=router,
            model_chain=routing_profile.executor_chain,
            system_instruction=domain_profile.executor_system_prompt,
        )

        return crafter, verifier, executor
