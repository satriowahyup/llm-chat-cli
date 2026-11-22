from unittest.mock import MagicMock, patch

from google.genai import errors

from llm_chat_cli.client import ChatSession
from llm_chat_cli.config import Settings


def make_chunk(text, usage=None):
    chunk = MagicMock()
    chunk.text = text
    chunk.usage_metadata = usage
    return chunk


def make_session(chunks=None):
    fake_client = MagicMock()
    stream = fake_client.chats.create.return_value.send_message_stream
    if chunks is None:
        chunks = [make_chunk("Ha"), make_chunk("lo")]
    stream.return_value = chunks
    session = ChatSession(
        Settings(api_key="test", model="gemini-2.5-flash"), "system", client=fake_client
    )
    return session, fake_client


def test_send_streams_text_and_records_history():
    session, _ = make_session()
    result = "".join(session.send("hai"))
    assert result == "Halo"
    assert len(session.history) == 2
    assert session.history[0] == {"role": "user", "content": "hai"}
    assert session.history[1] == {"role": "assistant", "content": "Halo"}


def test_send_captures_telemetry_and_tokens():
    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 5
    mock_usage.total_token_count = 15

    chunks = [make_chunk("Ha"), make_chunk("lo", usage=mock_usage)]
    session, _ = make_session(chunks=chunks)

    _ = list(session.send("hai"))

    assert session.last_turn_metrics is not None
    assert session.last_turn_metrics.prompt_tokens == 10
    assert session.last_turn_metrics.candidate_tokens == 5
    assert session.last_turn_metrics.total_tokens == 15
    assert (
        session.last_turn_metrics.time_to_first_token > 0
        or session.last_turn_metrics.total_duration > 0
    )
    assert session.total_tokens == 15
    assert session.metrics.turn_count == 1


def test_send_retries_on_429():
    fake_client = MagicMock()
    stream = fake_client.chats.create.return_value.send_message_stream

    rate_limit_err = errors.APIError(429, {"message": "Resource exhausted"})
    # First attempt raises 429, second attempt succeeds
    stream.side_effect = [
        rate_limit_err,
        [make_chunk("Halo ", usage=None), make_chunk("dunia", usage=None)],
    ]

    session = ChatSession(
        Settings(api_key="test", model="gemini-2.5-flash"), "system", client=fake_client
    )

    with patch("time.sleep") as mock_sleep:
        res = "".join(session.send("test"))
        assert res == "Halo dunia"
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args[0][0] == 1  # 2^0 = 1s backoff


def test_reset_creates_new_chat_and_resets_metrics():
    session, fake_client = make_session()
    session.total_tokens = 50
    session.history.append({"role": "user", "content": "dummy"})
    session.reset()
    assert fake_client.chats.create.call_count == 2
    assert session.total_tokens == 0
    assert session.metrics.turn_count == 0
    assert session.last_turn_metrics is None
    assert len(session.history) == 0


def test_set_system_prompt_updates_and_resets():
    session, fake_client = make_session()
    session.set_system_prompt("persona baru")
    assert session.system_prompt == "persona baru"
    assert fake_client.chats.create.call_count == 2
