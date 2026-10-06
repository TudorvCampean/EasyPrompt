"""Pipeline orchestrator chaining PromptCrafter -> LogicVerifier -> Executor."""

import time
from typing import Optional
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

        # Stage 1: PromptCrafter (Gemini)
        self.console.print("[bold blue]➔ Stage 1: PromptCrafter running...[/bold blue]")
        crafter_res = self.crafter.run(input_text=user_goal)
        self.console.print(
            f"✔ [blue]PromptCrafter completed in {crafter_res.execution_time_seconds:.2f}s[/blue]"
        )

        # Stage 2: LogicVerifier (Groq)
        self.console.print("[bold magenta]➔ Stage 2: LogicVerifier running...[/bold magenta]")
        verifier_context = {"user_goal": user_goal}
        verifier_res = self.verifier.run(
            input_text=crafter_res.content,
            context=verifier_context,
        )
        self.console.print(
            f"✔ [magenta]LogicVerifier completed in {verifier_res.execution_time_seconds:.2f}s[/magenta]"
        )

        # Stage 3: Executor (Gemini)
        self.console.print("[bold green]➔ Stage 3: Executor running...[/bold green]")
        executor_context = {
            "user_goal": user_goal,
            "crafted_plan": crafter_res.content,
        }
        executor_res = self.executor.run(
            input_text=verifier_res.content,
            context=executor_context,
        )
        self.console.print(
            f"✔ [green]Executor completed in {executor_res.execution_time_seconds:.2f}s[/green]"
        )

        total_elapsed = time.perf_counter() - total_start

        return PipelineResult(
            domain_key=self.domain_key,
            user_goal=user_goal,
            crafter_response=crafter_res,
            verifier_response=verifier_res,
            executor_response=executor_res,
            total_duration_seconds=total_elapsed,
        )
