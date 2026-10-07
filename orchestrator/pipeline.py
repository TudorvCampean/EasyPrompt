"""Pipeline orchestrator chaining PromptCrafter -> LogicVerifier -> Executor.

Supports both CLI (rich console) and progressive UI (generator-based) execution.
Now includes full fallback metadata in pipeline results.
"""

import time
from typing import Generator, List, Optional, Tuple
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel

from agents.base_agent import AgentResponse
from agents.prompt_crafter import PromptCrafter
from agents.logic_verifier import LogicVerifier
from agents.executor import Executor


class PipelineResult(BaseModel):
    """Encapsulates the end-to-end execution results across all pipeline stages."""

    domain_key: str
    routing_profile_id: str
    user_goal: str
    crafter_response: AgentResponse
    verifier_response: AgentResponse
    executor_response: AgentResponse
    total_duration_seconds: float


class AgentPipeline:
    """Coordinates sequential data flow between PromptCrafter, LogicVerifier, and Executor."""

    def __init__(
        self,
        domain_key: str,
        routing_profile_id: str,
        crafter: PromptCrafter,
        verifier: LogicVerifier,
        executor: Executor,
        console: Optional[Console] = None,
    ) -> None:
        self.domain_key = domain_key
        self.routing_profile_id = routing_profile_id
        self.crafter = crafter
        self.verifier = verifier
        self.executor = executor
        self.console = console or Console()

    def run_stages(
        self, user_goal: str
    ) -> Generator[Tuple[str, AgentResponse], None, None]:
        """Generator that yields results step-by-step as each stage completes."""
        # Stage 1: PromptCrafter
        crafter_res = self.crafter.run(input_text=user_goal)
        yield ("crafter", crafter_res)

        # Stage 2: LogicVerifier
        verifier_context = {"user_goal": user_goal}
        verifier_res = self.verifier.run(
            input_text=crafter_res.content,
            context=verifier_context,
        )
        yield ("verifier", verifier_res)

        # Stage 3: Executor
        executor_context = {
            "user_goal": user_goal,
            "crafted_plan": crafter_res.content,
        }
        executor_res = self.executor.run(
            input_text=verifier_res.content,
            context=executor_context,
        )
        yield ("executor", executor_res)

    def run(self, user_goal: str) -> PipelineResult:
        """Execute the multi-agent sequential pipeline with progress logging."""
        total_start = time.perf_counter()

        self.console.print(
            Panel(
                f"[bold cyan]Domain:[/bold cyan] [green]{self.domain_key}[/green]\n"
                f"[bold cyan]Routing:[/bold cyan] [green]{self.routing_profile_id}[/green]\n"
                f"[bold cyan]Goal:[/bold cyan] {user_goal}",
                title="[bold yellow]EasyPrompt Multi-Agent Pipeline[/bold yellow]",
                border_style="yellow",
            )
        )

        crafter_res: Optional[AgentResponse] = None
        verifier_res: Optional[AgentResponse] = None
        executor_res: Optional[AgentResponse] = None

        for stage_name, res in self.run_stages(user_goal):
            fallback_tag = ""
            if res.was_fallback:
                fallback_tag = f" [yellow]⚠ fallback → {res.provider_used}/{res.model_used}[/yellow]"

            if stage_name == "crafter":
                crafter_res = res
                self.console.print(
                    f"✔ [blue]PromptCrafter[/blue] [{res.provider_used}/{res.model_used}] "
                    f"{res.execution_time_seconds:.2f}s{fallback_tag}"
                )
            elif stage_name == "verifier":
                verifier_res = res
                self.console.print(
                    f"✔ [magenta]LogicVerifier[/magenta] [{res.provider_used}/{res.model_used}] "
                    f"{res.execution_time_seconds:.2f}s{fallback_tag}"
                )
            elif stage_name == "executor":
                executor_res = res
                self.console.print(
                    f"✔ [green]Executor[/green] [{res.provider_used}/{res.model_used}] "
                    f"{res.execution_time_seconds:.2f}s{fallback_tag}"
                )

        total_elapsed = time.perf_counter() - total_start
        return PipelineResult(
            domain_key=self.domain_key,
            routing_profile_id=self.routing_profile_id,
            user_goal=user_goal,
            crafter_response=crafter_res,  # type: ignore
            verifier_response=verifier_res,  # type: ignore
            executor_response=executor_res,  # type: ignore
            total_duration_seconds=total_elapsed,
        )
