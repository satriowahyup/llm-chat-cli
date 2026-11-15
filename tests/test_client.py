from unittest.mock import MagicMock

from llm_chat_cli.client import ChatSession
from llm_chat_cli.config import Settings


def make_chunk(text):
    chunk = MagicMock()
    chunk.text = text
    chunk.usage_metadata = None
    return chunk


def make_session():
    fake_client = MagicMock()
    stream = fake_client.chats.create.return_value.send_message_stream
    stream.return_value = [make_chunk("Ha"), make_chunk("lo")]
    session = ChatSession(Settings(api_key="test"), "system", client=fake_client)
    return session, fake_client


def test_send_streams_text():
    session, _ = make_session()
    assert "".join(session.send("hai")) == "Halo"


def test_reset_creates_new_chat():
    session, fake_client = make_session()
    session.reset()
    assert fake_client.chats.create.call_count == 2


def test_set_system_prompt_updates_and_resets():
    session, fake_client = make_session()
    session.set_system_prompt("persona baru")
    assert session.system_prompt == "persona baru"
    assert fake_client.chats.create.call_count == 2