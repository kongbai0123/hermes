import json
import subprocess

from simple_agent.gui_agent import MockGuiRunner, WindowsGuiRunner


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


def test_mock_gui_runner_records_click_type_and_hotkey_actions() -> None:
    runner = MockGuiRunner()

    click_payload = json.loads(runner.click("send_button"))
    type_payload = json.loads(runner.type_text("chat_prompt", "HI"))
    hotkey_payload = json.loads(runner.hotkey("Ctrl+L"))

    assert click_payload["status"] == "clicked"
    assert click_payload["target"] == "send_button"
    assert type_payload["status"] == "typed"
    assert type_payload["target"] == "chat_prompt"
    assert type_payload["text_length"] == 2
    assert hotkey_payload["status"] == "hotkey_sent"
    assert hotkey_payload["keys"] == ["Ctrl", "L"]


def test_windows_gui_runner_observe_includes_active_window_screenshot_clipboard_and_ocr_contract() -> None:
    runner = WindowsGuiRunner(
        system_probe=lambda: {
            "active_window": {"title": "Antigravity", "handle": "123"},
            "screenshot": {"status": "captured", "path": "trace/gui/screen.png"},
            "clipboard": {"status": "captured", "text_preview": "hello", "text_length": 5},
            "ocr": {"status": "unavailable", "text_preview": "", "text_length": 0},
        }
    )

    payload = json.loads(runner.observe())

    assert payload["status"] == "observed"
    assert payload["runner"] == "windows"
    assert payload["active_window"]["title"] == "Antigravity"
    assert payload["screenshot"]["status"] == "captured"
    assert payload["clipboard"]["text_preview"] == "hello"
    assert payload["ocr"]["status"] == "unavailable"


def test_windows_gui_runner_verify_matches_active_window_clipboard_or_ocr_text() -> None:
    runner = WindowsGuiRunner(
        system_probe=lambda: {
            "active_window": {"title": "Antigravity", "handle": "123"},
            "screenshot": {"status": "skipped"},
            "clipboard": {"status": "captured", "text_preview": "ChatGPT prompt ready", "text_length": 20},
            "ocr": {"status": "captured", "text_preview": "send_button", "text_length": 11},
        }
    )

    title_payload = json.loads(runner.verify("active_window:Antigravity"))
    clipboard_payload = json.loads(runner.verify("clipboard:prompt"))
    ocr_payload = json.loads(runner.verify("ocr:send_button"))

    assert title_payload["matched"] is True
    assert clipboard_payload["matched"] is True
    assert ocr_payload["matched"] is True


def test_windows_gui_runner_uses_injected_ocr_reader_for_captured_screenshot(tmp_path) -> None:
    screenshot_path = tmp_path / "screen.png"
    screenshot_path.write_bytes(b"fake-image")
    runner = WindowsGuiRunner(
        system_probe=lambda: {
            "active_window": {"title": "Antigravity", "handle": "123"},
            "screenshot": {"status": "captured", "path": screenshot_path.as_posix()},
            "clipboard": {"status": "captured", "text_preview": "", "text_length": 0},
        },
        ocr_reader=lambda path: "Launch Antigravity",
    )

    payload = json.loads(runner.observe())

    assert payload["ocr"]["status"] == "captured"
    assert payload["ocr"]["text_preview"] == "Launch Antigravity"
    assert payload["ocr"]["text_length"] == len("Launch Antigravity")


def test_windows_gui_runner_reports_ocr_unavailable_when_reader_fails(tmp_path) -> None:
    screenshot_path = tmp_path / "screen.png"
    screenshot_path.write_bytes(b"fake-image")

    def failing_reader(_path):
        raise RuntimeError("tesseract is not installed")

    runner = WindowsGuiRunner(
        system_probe=lambda: {
            "active_window": {"title": "Antigravity", "handle": "123"},
            "screenshot": {"status": "captured", "path": screenshot_path.as_posix()},
            "clipboard": {"status": "captured", "text_preview": "", "text_length": 0},
        },
        ocr_reader=failing_reader,
    )

    payload = json.loads(runner.observe())

    assert payload["ocr"]["status"] == "unavailable"
    assert "tesseract is not installed" in payload["ocr"]["reason"]


def test_windows_gui_runner_types_text_after_focusing_named_window() -> None:
    scripts: list[str] = []

    def command_runner(script: str, timeout: int) -> subprocess.CompletedProcess[str]:
        scripts.append(script)
        return subprocess.CompletedProcess(["powershell"], 0, stdout="", stderr="")

    runner = WindowsGuiRunner(command_runner=command_runner)

    payload = json.loads(runner.type_text("window:antigravity", "HI"))

    assert payload["status"] == "typed"
    assert payload["target"] == "window:antigravity"
    assert payload["focused_window"] == "antigravity"
    assert any("SetForegroundWindow" in script for script in scripts)
    assert any("antigravity" in script for script in scripts)
    assert any("SendKeys" in script and "HI" in script for script in scripts)
