"""Pipeline orchestrator chaining PromptCrafter -> LogicVerifier -> Executor."""

import time
from typing import Generator, Optional, Tuple
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel

from agents.base_agent import AgentResponse
from agents.prompt_crafter import PromptCrafter
from agents.logic_verifier import LogicVerifier
from agents.executor import Executor


class PipelineResult(BaseModel):
    """Encapsulates the end-to-end execution results across all pipeline stages."""

    domain_key: str
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
        crafter: PromptCrafter,
        verifier: LogicVerifier,
        executor: Executor,
        console: Optional[Console] = None,
    ) -> None:
        self.domain_key = domain_key
        self.crafter = crafter
        self.verifier = verifier
        self.executor = executor
        self.console = console or Console()

    def run_stages(
        self, user_goal: str
    ) -> Generator[Tuple[str, AgentResponse], None, PipelineResult]:
        """Generator that yields results step-by-step as each stage completes."""
        total_start = time.perf_counter()

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

        total_elapsed = time.perf_counter() - total_start
        return PipelineResult(
            domain_key=self.domain_key,
            user_goal=user_goal,
            crafter_response=crafter_res,
            verifier_response=verifier_res,
            executor_response=executor_res,
            total_duration_seconds=total_elapsed,
        )

    def run(self, user_goal: str) -> PipelineResult:
        """Execute the multi-agent sequential pipeline with progress logging."""
        total_start = time.perf_counter()

        self.console.print(
            Panel(
                f"[bold cyan]Selected Domain:[/bold cyan] [green]{self.domain_key}[/green]\n"
                f"[bold cyan]User Goal:[/bold cyan] {user_goal}",
                title="[bold yellow]EasyPrompt Multi-Agent Pipeline[/bold yellow]",
                border_style="yellow",
            )
        )

        stage_generator = self.run_stages(user_goal)
        crafter_res: Optional[AgentResponse] = None
        verifier_res: Optional[AgentResponse] = None
        executor_res: Optional[AgentResponse] = None

        for stage_name, res in stage_generator:
            if stage_name == "crafter":
                crafter_res = res
                self.console.print(
                    f"✔ [blue]PromptCrafter completed in {res.execution_time_seconds:.2f}s[/blue]"
                )
            elif stage_name == "verifier":
                verifier_res = res
                self.console.print(
                    f"✔ [magenta]LogicVerifier completed in {res.execution_time_seconds:.2f}s[/magenta]"
                )
            elif stage_name == "executor":
                executor_res = res
                self.console.print(
                    f"✔ [green]Executor completed in {res.execution_time_seconds:.2f}s[/green]"
                )

        total_elapsed = time.perf_counter() - total_start
        return PipelineResult(
            domain_key=self.domain_key,
            user_goal=user_goal,
            crafter_response=crafter_res,  # type: ignore
            verifier_response=verifier_res,  # type: ignore
            executor_response=executor_res,  # type: ignore
            total_duration_seconds=total_elapsed,
        )
