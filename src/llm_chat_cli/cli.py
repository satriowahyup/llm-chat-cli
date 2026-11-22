import argparse
import sys
from datetime import datetime

from google.genai import errors

from .client import ChatSession
from .config import DEFAULT_SYSTEM_PROMPT, Settings, load_settings
from .storage import export_transcript_json, export_transcript_markdown
from .ui import (
    console,
    print_banner,
    print_error,
    print_help,
    print_metrics,
    print_status,
    print_turn_summary,
    render_stream,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="llm-chat-cli",
        description="Production-grade AI terminal chatbot powered by Google Gemini API.",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=None,
        help="Gemini model name (overrides GEMINI_MODEL in .env)",
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (0.0 - 2.0)",
    )
    parser.add_argument(
        "-s",
        "--system",
        type=str,
        default=None,
        help="Initial system persona / instruction",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        default=None,
        help="One-shot mode: send prompt, stream output to stdout, and exit",
    )
    return parser


def run_one_shot(session: ChatSession, prompt: str) -> int:
    """Execute non-interactive one-shot query for shell scripts and automated pipelines."""
    try:
        render_stream(session.send(prompt))
        if session.last_turn_metrics is not None:
            print_turn_summary(session.last_turn_metrics)
        return 0
    except errors.APIError as e:
        print_error(e.message, code=e.code)
        return 1


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base_settings = load_settings()
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(1)

    model = args.model or base_settings.model
    temperature = (
        args.temperature if args.temperature is not None else base_settings.temperature
    )
    system_prompt = args.system or DEFAULT_SYSTEM_PROMPT

    settings = Settings(
        api_key=base_settings.api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=base_settings.max_output_tokens,
    )

    session = ChatSession(settings, system_prompt)

    # Check for one-shot mode (--prompt)
    if args.prompt:
        exit_code = run_one_shot(session, args.prompt)
        sys.exit(exit_code)

    print_banner(settings.model)

    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/bold blue] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            command, _, arg = user_input.partition(" ")
            arg = arg.strip()

            if command in {"/exit", "/quit"}:
                console.print("[dim]Goodbye![/dim]")
                break
            elif command == "/help":
                print_help()
            elif command == "/metrics":
                print_metrics(session.metrics, session.last_turn_metrics)
            elif command == "/reset":
                session.reset()
                print_status("Conversation history and session metrics cleared.")
            elif command == "/system":
                if arg:
                    session.set_system_prompt(arg)
                    print_status("System persona updated; conversation history reset.")
                else:
                    console.print(
                        "[yellow]Usage:[/yellow] [dim]/system You are an expert Python tutor.[/dim]"
                    )
            elif command == "/tokens":
                print_status(
                    f"Total tokens used: [bold cyan]{session.total_tokens}[/bold cyan] "
                    f"(Prompt: {session.metrics.total_prompt_tokens}, Candidates: {session.metrics.total_candidate_tokens}) | "
                    f"Cost: [bold green]${session.metrics.total_cost_usd:.6f}[/bold green]",
                    style="yellow",
                )
            elif command == "/export":
                if not session.history:
                    console.print(
                        "[yellow]No conversation history to export yet.[/yellow]"
                    )
                    continue

                if not arg:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"chat_transcript_{ts}.md"
                else:
                    filename = arg

                if filename.lower().endswith(".json"):
                    saved_path = export_transcript_json(
                        filename,
                        session.settings.model,
                        session.system_prompt,
                        session.history,
                        session.metrics,
                    )
                else:
                    saved_path = export_transcript_markdown(
                        filename,
                        session.settings.model,
                        session.system_prompt,
                        session.history,
                        session.metrics,
                    )
                print_status(
                    f"Transcript successfully exported to: [bold]{saved_path}[/bold]"
                )
            else:
                console.print(
                    "[red]Unknown command.[/red] Type [bold cyan]/help[/bold cyan]."
                )
            continue

        try:
            render_stream(session.send(user_input))
            if session.last_turn_metrics is not None:
                print_turn_summary(session.last_turn_metrics)
        except errors.APIError as e:
            print_error(e.message, code=e.code)
