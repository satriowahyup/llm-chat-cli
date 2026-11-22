from llm_chat_cli.metrics import (
    SessionMetrics,
    TurnMetrics,
    calculate_cost,
)


def test_calculate_cost_flash():
    # 1,000,000 prompt tokens = $0.075, 1,000,000 candidate tokens = $0.30
    cost = calculate_cost("gemini-2.5-flash", 1_000_000, 1_000_000)
    assert round(cost, 3) == 0.375


def test_calculate_cost_pro():
    # 1,000,000 prompt tokens = $1.25, 1,000,000 candidate tokens = $5.00
    cost = calculate_cost("gemini-1.5-pro", 1_000_000, 1_000_000)
    assert round(cost, 2) == 6.25


def test_turn_metrics_properties():
    turn = TurnMetrics(
        prompt_tokens=100,
        candidate_tokens=50,
        total_tokens=150,
        time_to_first_token=0.25,
        total_duration=1.0,
        tokens_per_second=50.0,
        estimated_cost_usd=0.0001,
    )
    assert turn.ttft_ms == 250.0
    assert turn.prompt_tokens == 100
    assert turn.candidate_tokens == 50
    assert turn.total_tokens == 150


def test_session_metrics_aggregation():
    session_metrics = SessionMetrics(model="gemini-2.5-flash")
    assert session_metrics.turn_count == 0
    assert session_metrics.average_ttft_ms == 0.0
    assert session_metrics.average_tokens_per_second == 0.0

    t1 = TurnMetrics(
        prompt_tokens=100,
        candidate_tokens=50,
        total_tokens=150,
        time_to_first_token=0.2,
        total_duration=1.0,
        tokens_per_second=50.0,
        estimated_cost_usd=0.00005,
    )
    t2 = TurnMetrics(
        prompt_tokens=150,
        candidate_tokens=100,
        total_tokens=250,
        time_to_first_token=0.4,
        total_duration=2.0,
        tokens_per_second=50.0,
        estimated_cost_usd=0.00010,
    )

    session_metrics.record_turn(t1)
    session_metrics.record_turn(t2)

    assert session_metrics.turn_count == 2
    assert session_metrics.total_prompt_tokens == 250
    assert session_metrics.total_candidate_tokens == 150
    assert session_metrics.total_tokens == 400
    assert round(session_metrics.total_cost_usd, 5) == 0.00015
    assert session_metrics.average_ttft_ms == 300.0  # (200 + 400) / 2
    assert session_metrics.average_tokens_per_second == 50.0

    session_metrics.reset()
    assert session_metrics.turn_count == 0
    assert session_metrics.total_tokens == 0
