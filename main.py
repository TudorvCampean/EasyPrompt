"""CLI Entry point for EasyPrompt using unified RouterClient and Routing Combos."""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from core.config import settings
from core.router import RouterClient
from core.combos import ROUTING_PROFILES, get_routing_profile
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


def display_combos(console: Console) -> None:
    """Display available routing combos in a rich formatted table."""
    table = Table(title="Available Routing Combos (OmniRoute Auto-Fallback)", border_style="magenta")
    table.add_column("ID", style="bold yellow")
    table.add_column("Name", style="bold green")
    table.add_column("Description", style="white")

    for combo in ROUTING_PROFILES.values():
        table.add_row(combo.id, f"{combo.icon} {combo.name}", combo.description)

    console.print(table)


def main() -> None:
    """Main CLI routine."""
    console = Console()
    console.print(
        Panel(
            "[bold cyan]Welcome to EasyPrompt[/bold cyan]\n"
            "Domain-Adaptive Multi-Agent System with OmniRoute Auto-Fallback\n"
            "(PromptCrafter ➔ LogicVerifier ➔ Executor)",
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

    display_combos(console)

    # Prompt user for routing combo
    combo_choices = list(ROUTING_PROFILES.keys())
    default_combo = "coding_pro" if domain_key == "coding" else ("deep_reasoning" if domain_key == "math" else "balanced")
    combo_id = Prompt.ask(
        "\nSelect routing combo",
        choices=combo_choices,
        default=default_combo,
    )
    routing_profile = get_routing_profile(combo_id)

    # Prompt user for goal/task
    user_goal = Prompt.ask("\nEnter your task or prompt")
    if not user_goal.strip():
        console.print("[red]Task description cannot be empty. Exiting.[/red]")
        sys.exit(1)

    # Initialize RouterClient
    api_keys = {
        "gemini": settings.gemini_api_key,
        "groq": settings.groq_api_key,
        "deepseek": settings.deepseek_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    router = RouterClient(api_keys=api_keys)

    available = router.available_providers
    if not available:
        console.print("[red]Error: No API keys configured in .env! Please add at least one key.[/red]")
        sys.exit(1)
    console.print(f"[dim]Active providers detected: {', '.join(available)}[/dim]")

    # Factory generates domain-specific agents with routing fallback chains
    crafter, verifier, executor = AgentFactory.create_pipeline_agents(
        domain_profile=profile,
        router=router,
        routing_profile=routing_profile,
    )

    # Build and execute pipeline
    pipeline = AgentPipeline(
        domain_key=domain_key,
        routing_profile_id=routing_profile.id,
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
    except Exception as e:
        console.print(f"\n[bold red]Pipeline Error:[/bold red] {e}")


if __name__ == "__main__":
    main()
