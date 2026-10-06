"""CLI Entry point for EasyPrompt."""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from core.config import settings
from core.llm_clients import GeminiClient, GroqClient
from domain.profiles import DOMAIN_PROFILES, get_domain_profile
from agents.factory import AgentFactory
from orchestrator.pipeline import AgentPipeline


def display_domains(console: Console) -> None:
    """Display available domain profiles in a rich formatted table."""
    table = Table(title="Available Domain Profiles", border_style="cyan")
    table.add_column("Key", style="bold yellow")
    table.add_column("Name", style="bold green")
    table.add_column("Description", style="white")

    for domain in DOMAIN_PROFILES.values():
        table.add_row(domain.key, domain.display_name, domain.description)

    console.print(table)


def main() -> None:
    """Main CLI routine."""
    console = Console()
    console.print(
        Panel(
            "[bold cyan]Welcome to EasyPrompt[/bold cyan]\n"
            "Domain-Adaptive Multi-Agent System (PromptCrafter ➔ LogicVerifier ➔ Executor)",
            border_style="cyan",
        )
    )

    display_domains(console)

    # Prompt user for domain selection
    domain_choices = list(DOMAIN_PROFILES.keys())
    domain_key = Prompt.ask(
        "\nSelect domain",
        choices=domain_choices,
        default="coding",
    )
    profile = get_domain_profile(domain_key)

    # Prompt user for goal/task
    user_goal = Prompt.ask("\nEnter your task or prompt")
    if not user_goal.strip():
        console.print("[red]Task description cannot be empty. Exiting.[/red]")
        sys.exit(1)

    # Validate settings
    try:
        settings.validate_keys()
    except ValueError as e:
        console.print(f"[yellow]Warning: {e}[/yellow]")
        console.print("[dim]Continuing in scaffold mode...[/dim]")

    # Initialize LLM Clients
    gemini_client = GeminiClient(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
    )
    groq_client = GroqClient(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
    )

    # Factory generates domain-specific agents
    crafter, verifier, executor = AgentFactory.create_pipeline_agents(
        domain_profile=profile,
        gemini_client=gemini_client,
        groq_client=groq_client,
    )

    # Build and execute pipeline
    pipeline = AgentPipeline(
        domain_key=domain_key,
        crafter=crafter,
        verifier=verifier,
        executor=executor,
        console=console,
    )

    try:
        result = pipeline.run(user_goal=user_goal)
        console.print("\n[bold green]Final Result:[/bold green]")
        console.print(Panel(result.executor_response.content, border_style="green"))
        console.print(
            f"[dim]Total pipeline execution time: {result.total_duration_seconds:.2f}s[/dim]"
        )
    except NotImplementedError as e:
        console.print(
            f"\n[bold yellow]Ready for LLM implementation:[/bold yellow] {e}"
        )


if __name__ == "__main__":
    main()
