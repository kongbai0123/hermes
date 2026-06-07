import json
from pathlib import Path

from simple_agent.external_chat import FakeExternalChatBridge
from simple_agent.gui_agent import MockGuiRunner
from simple_agent.tools import ToolBox


def test_rejects_path_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.read_file("../secret.txt")

    assert result.ok is False
    assert "workspace 外" in result.content


def test_list_files_inside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "hello.txt").write_text("hello", encoding="utf-8")
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.list_files(".")

    assert result.ok is True
    assert "hello.txt" in result.content


def test_proxy_fetch_requires_allowed_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"])

    result = tools.proxy_fetch("https://example.com")

    assert result.ok is False
    assert "allowlist" in result.content


def test_proxy_fetch_rejects_localhost_even_when_allowlisted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_proxy_domains=["localhost"])

    result = tools.proxy_fetch("http://localhost:11434/api/tags")

    assert result.ok is False
    assert "內網" in result.content


def test_proxy_fetch_uses_registered_fetcher_for_allowlisted_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    def fake_fetcher(url: str, timeout: int, max_bytes: int) -> str:
        assert url == "https://example.com/status"
        assert timeout == 10
        assert max_bytes == 4096
        return "proxy ok"

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_proxy_domains=["example.com"],
        proxy_fetcher=fake_fetcher,
    )

    result = tools.proxy_fetch("https://example.com/status", timeout=10, max_bytes=4096)

    assert result.ok is True
    assert result.content == "proxy ok"


def test_proxy_fetch_execute_reports_invalid_numeric_args(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_proxy_domains=["example.com"])

    result = tools.execute("proxy_fetch", url="https://example.com", timeout="slow")

    assert result.ok is False
    assert "timeout" in result.content


def test_open_browser_uses_registered_opener_for_allowlisted_domain(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    opened: list[tuple[str, str]] = []

    def fake_opener(url: str, browser: str) -> None:
        opened.append((url, browser))

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_browser_domains=["youtube.com"],
        browser_opener=fake_opener,
    )

    result = tools.open_browser("https://www.youtube.com", browser="chrome")

    assert result.ok is True
    assert opened == [("https://www.youtube.com", "chrome")]
    assert "chrome" in result.content.lower()


def test_open_browser_rejects_localhost_even_when_allowlisted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tools = ToolBox(str(workspace), ["python --version"], allowed_browser_domains=["localhost"])

    result = tools.open_browser("http://localhost:3000", browser="chrome")

    assert result.ok is False
    assert "內網" in result.content


def test_external_chat_sends_message_and_receives_reply(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務"})
    tools = ToolBox(str(tmp_path), ["python --version"], external_chat_bridge=bridge)

    result = tools.external_chat("HI", target="chatgpt_web")

    assert result.ok is True
    assert result.tool == "external_chat"
    assert "HI，很高興為你服務" in result.content
    assert bridge.sent_messages == [("chatgpt_web", "HI")]


def test_external_chat_execute_uses_default_target(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務"})
    tools = ToolBox(str(tmp_path), ["python --version"], external_chat_bridge=bridge)

    result = tools.execute("external_chat", message="HI")

    assert result.ok is True
    assert bridge.sent_messages == [("chatgpt_web", "HI")]


def test_external_chat_loop_runs_multiple_turns(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge(
        {"HI": "第一輪回覆"},
        default_reply="第二輪回覆",
    )
    tools = ToolBox(str(tmp_path), ["python --version"], external_chat_bridge=bridge)

    result = tools.external_chat_loop("HI", target="chatgpt_web", max_turns="2")

    assert result.ok is True
    assert result.tool == "external_chat_loop"
    assert '"turn_count": 2' in result.content
    assert "第一輪回覆" in result.content
    assert "第二輪回覆" in result.content
    assert len(bridge.sent_messages) == 2


def test_external_chat_loop_execute_uses_default_target(tmp_path: Path) -> None:
    bridge = FakeExternalChatBridge({"HI": "收到"})
    tools = ToolBox(str(tmp_path), ["python --version"], external_chat_bridge=bridge)

    result = tools.execute("external_chat_loop", message="HI", max_turns="1")

    assert result.ok is True
    assert bridge.sent_messages == [("chatgpt_web", "HI")]


def test_self_improve_proposal_only_returns_patch_plan_without_writing(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"])

    result = tools.self_improve(
        goal="讓 Hermes 可以修改自己的工具能力",
        scope="simple_agent",
        mode="proposal_only",
    )
    payload = json.loads(result.content)

    assert result.ok is True
    assert result.tool == "self_improve"
    assert payload["status"] == "proposal_ready"
    assert payload["mode"] == "proposal_only"
    assert payload["requires_approval"] is True
    assert "tools.py" in " ".join(payload["candidate_files"])
    assert payload["tests_to_run"]


def test_self_improve_rejects_scope_outside_hermes_code(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"])

    result = tools.self_improve(
        goal="讀取 secrets",
        scope="../",
        mode="proposal_only",
    )

    assert result.ok is False
    assert "Hermes 程式範圍" in result.content


def test_self_improve_apply_mode_reports_approval_boundary(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"])

    result = tools.self_improve(
        goal="套用自我修改",
        scope="simple_agent",
        mode="apply_after_approval",
    )
    payload = json.loads(result.content)

    assert result.ok is False
    assert payload["status"] == "approval_required"
    assert payload["requires_approval"] is True


def test_gui_observe_uses_mock_runner(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"], gui_runner=MockGuiRunner())

    result = tools.gui_observe()
    payload = json.loads(result.content)

    assert result.ok is True
    assert result.tool == "gui_observe"
    assert payload["status"] == "observed"
    assert payload["screen_id"] == "mock_screen_001"


def test_gui_verify_uses_mock_runner(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"], gui_runner=MockGuiRunner())

    result = tools.execute("gui_verify", condition="chat_prompt_visible")
    payload = json.loads(result.content)

    assert result.ok is True
    assert result.tool == "gui_verify"
    assert payload["condition"] == "chat_prompt_visible"
    assert payload["matched"] is True


def test_gui_observe_reports_unavailable_runner(tmp_path: Path) -> None:
    class UnavailableRunner:
        def observe(self) -> str:
            raise RuntimeError("desktop bridge unavailable")

        def verify(self, condition: str) -> str:
            raise RuntimeError("desktop bridge unavailable")

    tools = ToolBox(str(tmp_path), ["python --version"], gui_runner=UnavailableRunner())

    result = tools.gui_observe()

    assert result.ok is False
    assert result.tool == "gui_observe"
    assert "tool_unavailable" in result.content


def test_gui_action_tools_call_runner_when_policy_allows_execution(tmp_path: Path) -> None:
    class RecordingRunner:
        def __init__(self) -> None:
            self.actions: list[tuple[str, tuple[str, ...]]] = []

        def observe(self) -> str:
            return "{}"

        def verify(self, condition: str) -> str:
            return "{}"

        def click(self, target: str) -> str:
            self.actions.append(("click", (target,)))
            return json.dumps({"status": "clicked", "target": target})

        def type_text(self, target: str, text: str) -> str:
            self.actions.append(("type_text", (target, text)))
            return json.dumps({"status": "typed", "target": target, "text_length": len(text)})

        def hotkey(self, keys: str) -> str:
            self.actions.append(("hotkey", (keys,)))
            return json.dumps({"status": "hotkey_sent", "keys": keys.split("+")})

    runner = RecordingRunner()
    tools = ToolBox(str(tmp_path), ["python --version"], gui_runner=runner)

    click_result = tools.execute("gui_click", target="send_button")
    type_result = tools.execute("gui_type_text", target="chat_prompt", text="HI")
    hotkey_result = tools.execute("gui_hotkey", keys="Ctrl+L")

    assert click_result.ok is True
    assert type_result.ok is True
    assert hotkey_result.ok is True
    assert runner.actions == [
        ("click", ("send_button",)),
        ("type_text", ("chat_prompt", "HI")),
        ("hotkey", ("Ctrl+L",)),
    ]


def test_app_launch_uses_registered_desktop_shortcut_launcher(tmp_path: Path) -> None:
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    shortcut = desktop / "原神.lnk"
    shortcut.write_text("shortcut", encoding="utf-8")
    launched: list[Path] = []

    def fake_launcher(path: Path) -> dict[str, str]:
        launched.append(path)
        return {"status": "launched", "target": "C:/Program Files/HoYoPlay/launcher.exe"}

    tools = ToolBox(
        str(tmp_path),
        ["python --version"],
        desktop_paths=[desktop],
        app_launcher=fake_launcher,
    )

    result = tools.app_launch("原神")
    payload = json.loads(result.content)

    assert result.ok is True
    assert result.tool == "app_launch"
    assert launched == [shortcut]
    assert payload["status"] == "launched"
    assert payload["shortcut"] == shortcut.as_posix()


def test_app_launch_rejects_path_like_shortcut_names(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"])

    result = tools.app_launch("../原神")

    assert result.ok is False
    assert "捷徑名稱" in result.content
