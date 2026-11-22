import json
from pathlib import Path

from llm_chat_cli.metrics import SessionMetrics, TurnMetrics
from llm_chat_cli.storage import (
    DEFAULT_TRANSCRIPT_DIR,
    export_transcript_json,
    export_transcript_markdown,
    resolve_export_path,
)


def make_dummy_session():
    metrics = SessionMetrics(model="gemini-2.5-flash")
    turn = TurnMetrics(
        prompt_tokens=20,
        candidate_tokens=10,
        total_tokens=30,
        time_to_first_token=0.1,
        total_duration=0.5,
        tokens_per_second=20.0,
        estimated_cost_usd=0.000005,
    )
    metrics.record_turn(turn)
    history = [
        {"role": "user", "content": "Hello, who are you?"},
        {"role": "assistant", "content": "I am an AI assistant."},
    ]
    return history, metrics


def test_resolve_export_path_bare_filename():
    resolved = resolve_export_path("session_notes", ".md")
    assert resolved.parent == DEFAULT_TRANSCRIPT_DIR
    assert resolved.name == "session_notes.md"


def test_export_transcript_markdown(tmp_path: Path):
    history, metrics = make_dummy_session()
    export_file = tmp_path / "transcripts" / "test_chat.md"

    saved_path = export_transcript_markdown(
        export_file,
        model="gemini-2.5-flash",
        system_prompt="You are an AI assistant.",
        history=history,
        metrics=metrics,
    )

    assert saved_path.exists()
    content = saved_path.read_text(encoding="utf-8")
    assert "# Chat Transcript: llm-chat-cli" in content
    assert "gemini-2.5-flash" in content
    assert "Hello, who are you?" in content
    assert "I am an AI assistant." in content
    assert "Total Tokens:** 30" in content
    assert "Date:**" in content


def test_export_transcript_json(tmp_path: Path):
    history, metrics = make_dummy_session()
    export_file = tmp_path / "test_chat.json"

    saved_path = export_transcript_json(
        export_file,
        model="gemini-2.5-flash",
        system_prompt="You are an AI assistant.",
        history=history,
        metrics=metrics,
    )

    assert saved_path.exists()
    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["metadata"]["model"] == "gemini-2.5-flash"
    assert data["metadata"]["total_tokens"] == 30
    assert len(data["messages"]) == 2
    assert data["messages"][0]["content"] == "Hello, who are you?"
