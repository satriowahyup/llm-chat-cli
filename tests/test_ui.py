from rich.console import Console

from llm_chat_cli import ui
from llm_chat_cli.metrics import SessionMetrics, TurnMetrics


def test_ui_print_banner():
    test_console = Console(record=True)
    orig_console = ui.console
    ui.console = test_console
    try:
        ui.print_banner("gemini-test-model")
        output = test_console.export_text()
        assert "llm-chat-cli" in output
        assert "gemini-test-model" in output
    finally:
        ui.console = orig_console


def test_ui_print_help():
    test_console = Console(record=True)
    orig_console = ui.console
    ui.console = test_console
    try:
        ui.print_help()
        output = test_console.export_text()
        assert "/help" in output
        assert "/metrics" in output
        assert "/export" in output
        assert "/reset" in output
        assert "/tokens" in output
        assert "/system" in output
    finally:
        ui.console = orig_console


def test_ui_print_error():
    test_console = Console(record=True)
    orig_error_console = ui.error_console
    ui.error_console = test_console
    try:
        ui.print_error("Test error message", code=429)
        output = test_console.export_text()
        assert "[Error 429]" in output
        assert "Test error message" in output
    finally:
        ui.error_console = orig_error_console


def test_ui_print_turn_summary():
    test_console = Console(record=True)
    orig_console = ui.console
    ui.console = test_console
    try:
        turn = TurnMetrics(
            prompt_tokens=10,
            candidate_tokens=20,
            total_tokens=30,
            time_to_first_token=0.15,
            total_duration=0.5,
            tokens_per_second=40.0,
            estimated_cost_usd=0.000025,
        )
        ui.print_turn_summary(turn)
        output = test_console.export_text()
        assert "TTFT:" in output
        assert "150ms" in output
        assert "40.0 tok/s" in output
        assert "Cost:" in output
    finally:
        ui.console = orig_console


def test_ui_print_metrics():
    test_console = Console(record=True)
    orig_console = ui.console
    ui.console = test_console
    try:
        session_metrics = SessionMetrics(model="gemini-2.5-flash")
        turn = TurnMetrics(
            prompt_tokens=100,
            candidate_tokens=50,
            total_tokens=150,
            time_to_first_token=0.2,
            total_duration=1.0,
            tokens_per_second=50.0,
            estimated_cost_usd=0.00005,
        )
        session_metrics.record_turn(turn)
        ui.print_metrics(session_metrics, turn)
        output = test_console.export_text()
        assert "Telemetry & Token Economics" in output
        assert "Time to First Token (TTFT)" in output
        assert "Generation Speed" in output
        assert "Estimated Cost" in output
    finally:
        ui.console = orig_console


def test_ui_render_stream_empty():
    def empty_stream():
        if False:
            yield ""

    res = ui.render_stream(empty_stream())
    assert res == ""


def test_ui_render_stream_chunks():
    test_console = Console(record=True)
    orig_console = ui.console
    ui.console = test_console
    try:

        def sample_stream():
            yield "Hello, "
            yield "**World!**"

        res = ui.render_stream(sample_stream())
        assert res == "Hello, **World!**"
        output = test_console.export_text()
        assert "AI:" in output
        assert "Hello, World!" in output
    finally:
        ui.console = orig_console
