from collections.abc import Iterator

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .metrics import SessionMetrics, TurnMetrics

console = Console()
error_console = Console(stderr=True)


def print_banner(model: str) -> None:
    """Display application header banner."""
    title = Text("llm-chat-cli", style="bold cyan")
    subtitle = Text(f"Model: {model} | Type /help for available commands", style="dim")
    banner_content = Text.assemble(title, "\n", subtitle)
    console.print(
        Panel(
            banner_content,
            border_style="cyan",
            expand=False,
            padding=(0, 2),
        )
    )


def print_help() -> None:
    """Display table of available interactive commands."""
    table = Table(
        title="Interactive Commands",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        expand=False,
    )
    table.add_column("Command", style="bold cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("/help", "Display this help menu")
    table.add_row("/metrics", "View detailed telemetry (TTFT, throughput, cost in USD)")
    table.add_row(
        "/export [file]",
        "Export conversation transcript to Markdown (.md) or JSON (.json)",
    )
    table.add_row(
        "/tokens", "View summary of token usage and estimated cost for this session"
    )
    table.add_row("/reset", "Clear conversation history and reset session metrics")
    table.add_row(
        "/system <prompt>", "Update system persona/instructions (resets conversation)"
    )
    table.add_row("/exit, /quit", "Exit the application")

    console.print(table)


def print_status(message: str, style: str = "dim green") -> None:
    """Display a status or action confirmation message."""
    console.print(f"[{style}]✔ {message}[/{style}]")


def print_error(message: str, code: int | str | None = None) -> None:
    """Display a formatted error panel."""
    prefix = f"[Error {code}] " if code is not None else "[Error] "
    error_console.print(
        Panel(
            f"[bold red]{prefix}[/bold red]{message}",
            border_style="red",
            expand=False,
            padding=(0, 1),
        )
    )


def print_turn_summary(turn: TurnMetrics) -> None:
    """Display a subtle one-line telemetry summary for the last response."""
    summary = (
        f"[dim]↳ TTFT: [cyan]{turn.ttft_ms:.0f}ms[/cyan] | "
        f"Speed: [cyan]{turn.tokens_per_second:.1f} tok/s[/cyan] | "
        f"Tokens: [yellow]{turn.total_tokens}[/yellow] "
        f"([dim]{turn.prompt_tokens} in / {turn.candidate_tokens} out[/dim]) | "
        f"Cost: [green]${turn.estimated_cost_usd:.6f}[/green][/dim]"
    )
    console.print(summary)


def print_metrics(
    session_metrics: SessionMetrics, last_turn: TurnMetrics | None = None
) -> None:
    """Display comprehensive performance and token economics table."""
    table = Table(
        title=f"Telemetry & Token Economics (Model: {session_metrics.model})",
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        expand=False,
    )
    table.add_column("Metric", style="bold white")
    table.add_column("Last Turn", style="cyan", justify="right")
    table.add_column("Session Total", style="green", justify="right")

    if last_turn is not None:
        table.add_row(
            "Time to First Token (TTFT)",
            f"{last_turn.ttft_ms:.1f} ms",
            f"{session_metrics.average_ttft_ms:.1f} ms (avg)",
        )
        table.add_row(
            "Generation Speed",
            f"{last_turn.tokens_per_second:.1f} tok/s",
            f"{session_metrics.average_tokens_per_second:.1f} tok/s (avg)",
        )
        table.add_row(
            "Prompt Tokens (Input)",
            str(last_turn.prompt_tokens),
            str(session_metrics.total_prompt_tokens),
        )
        table.add_row(
            "Candidate Tokens (Output)",
            str(last_turn.candidate_tokens),
            str(session_metrics.total_candidate_tokens),
        )
        table.add_row(
            "Total Tokens",
            str(last_turn.total_tokens),
            str(session_metrics.total_tokens),
        )
        table.add_row(
            "Estimated Cost (USD)",
            f"${last_turn.estimated_cost_usd:.6f}",
            f"${session_metrics.total_cost_usd:.6f}",
        )
    else:
        table.add_row("Total Turns", "-", str(session_metrics.turn_count))
        table.add_row("Total Tokens", "-", str(session_metrics.total_tokens))
        table.add_row(
            "Estimated Cost (USD)", "-", f"${session_metrics.total_cost_usd:.6f}"
        )

    console.print(table)


def render_stream(stream: Iterator[str]) -> str:
    """Render streaming LLM text live with Rich Markdown and syntax highlighting."""
    accumulated_text = ""

    # 1. Display thinking spinner before the first chunk arrives
    with console.status("[dim cyan]Thinking...[/dim cyan]", spinner="dots") as status:
        iterator = iter(stream)
        try:
            first_chunk = next(iterator)
        except StopIteration:
            return ""

        accumulated_text += first_chunk
        status.stop()

    # 2. Render live Markdown stream
    console.print("[bold green]AI:[/bold green]")
    with Live(
        Markdown(accumulated_text),
        console=console,
        refresh_per_second=15,
        vertical_overflow="visible",
    ) as live:
        for chunk in iterator:
            accumulated_text += chunk
            live.update(Markdown(accumulated_text))

    console.print()
    return accumulated_text
