import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .metrics import SessionMetrics

DEFAULT_TRANSCRIPT_DIR = Path("transcripts")


def resolve_export_path(filepath: Path | str, default_suffix: str) -> Path:
    """Resolve target path, placing in transcripts/ directory by default if filename only."""
    path = Path(filepath)
    if not path.parent or str(path.parent) == ".":
        path = DEFAULT_TRANSCRIPT_DIR / path.name

    if path.suffix.lower() != default_suffix:
        path = path.with_suffix(default_suffix)

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def export_transcript_markdown(
    filepath: Path | str,
    model: str,
    system_prompt: str,
    history: list[dict[str, str]],
    metrics: SessionMetrics,
) -> Path:
    """Export the current conversation transcript to a formatted Markdown file."""
    target_path = resolve_export_path(filepath, ".md")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Chat Transcript: llm-chat-cli",
        "",
        f"- **Date:** {now_str}",
        f"- **Model:** `{model}`",
        f"- **System Prompt:** {system_prompt}",
        f"- **Total Turns:** {metrics.turn_count}",
        f"- **Total Tokens:** {metrics.total_tokens} (Prompt: {metrics.total_prompt_tokens}, Candidate: {metrics.total_candidate_tokens})",
        f"- **Estimated Cost:** ${metrics.total_cost_usd:.6f} USD",
        f"- **Average TTFT:** {metrics.average_ttft_ms:.1f} ms",
        f"- **Average Speed:** {metrics.average_tokens_per_second:.1f} tokens/s",
        "",
        "---",
        "",
    ]

    for item in history:
        role_title = "User" if item["role"] == "user" else "Assistant (AI)"
        lines.append(f"### {role_title}")
        lines.append("")
        lines.append(item["content"].strip())
        lines.append("")

    target_path.write_text("\n".join(lines), encoding="utf-8")
    return target_path


def export_transcript_json(
    filepath: Path | str,
    model: str,
    system_prompt: str,
    history: list[dict[str, str]],
    metrics: SessionMetrics,
) -> Path:
    """Export conversation session data and metadata to a structured JSON file."""
    target_path = resolve_export_path(filepath, ".json")
    data: dict[str, Any] = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "system_prompt": system_prompt,
            "turn_count": metrics.turn_count,
            "total_tokens": metrics.total_tokens,
            "prompt_tokens": metrics.total_prompt_tokens,
            "candidate_tokens": metrics.total_candidate_tokens,
            "estimated_cost_usd": metrics.total_cost_usd,
            "average_ttft_ms": metrics.average_ttft_ms,
            "average_tokens_per_second": metrics.average_tokens_per_second,
        },
        "messages": history,
    }

    target_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return target_path
