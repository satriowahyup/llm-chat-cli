from unittest.mock import MagicMock, patch

from llm_chat_cli.cli import build_parser, run_one_shot


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.model is None
    assert args.temperature is None
    assert args.system is None
    assert args.prompt is None


def test_build_parser_custom_flags():
    parser = build_parser()
    args = parser.parse_args(
        [
            "-m",
            "gemini-1.5-pro",
            "-t",
            "0.2",
            "-s",
            "Custom system persona",
            "-p",
            "One shot prompt",
        ]
    )
    assert args.model == "gemini-1.5-pro"
    assert args.temperature == 0.2
    assert args.system == "Custom system persona"
    assert args.prompt == "One shot prompt"


def test_run_one_shot_success():
    fake_session = MagicMock()
    fake_session.send.return_value = ["Output chunk"]
    fake_session.last_turn_metrics = None

    with patch("llm_chat_cli.cli.render_stream", return_value="Output chunk"):
        code = run_one_shot(fake_session, "Halo")
        assert code == 0
        fake_session.send.assert_called_once_with("Halo")
