import json

from simple_agent.gui_agent import MockGuiRunner


def test_mock_gui_runner_observe_returns_visible_elements() -> None:
    runner = MockGuiRunner()

    result = runner.observe()

    payload = json.loads(result)
    assert payload["status"] == "observed"
    assert payload["screen_id"] == "mock_screen_001"
    assert payload["visible_elements"][0]["label"] == "ChatGPT prompt"


def test_mock_gui_runner_verify_returns_condition_result() -> None:
    runner = MockGuiRunner()

    result = runner.verify("chat_prompt_visible")

    payload = json.loads(result)
    assert payload["status"] == "verified"
    assert payload["condition"] == "chat_prompt_visible"
    assert payload["matched"] is True
