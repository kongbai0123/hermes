from pathlib import Path

from simple_agent.bounded_loop import BoundedLoopController, LoopLimits
from simple_agent.external_chat import FakeExternalChatBridge
from simple_agent.roles import ManagerDecision
from simple_agent.tools import ToolBox


class FakeManager:
    def __init__(self, decisions: list[ManagerDecision]) -> None:
        self.decisions = decisions
        self.index = 0

    def decide(self, _user_text: str) -> ManagerDecision:
        decision = self.decisions[min(self.index, len(self.decisions) - 1)]
        self.index += 1
        return decision


class FakeWorker:
    def respond(self, _user_text: str, decision: ManagerDecision, observation) -> str:
        return f"{decision.tool}: {observation.format()}"


def make_controller(
    workspace: Path,
    decisions: list[ManagerDecision],
    *,
    tools: ToolBox | None = None,
    default_capability: str = "read_only",
) -> BoundedLoopController:
    tools = tools or ToolBox(str(workspace), ["python --version"])
    return BoundedLoopController(
        FakeManager(decisions),  # type: ignore[arg-type]
        FakeWorker(),  # type: ignore[arg-type]
        tools,
        LoopLimits(
            max_steps=3,
            max_replans=1,
            max_tool_failures=2,
            max_same_action_repeat=1,
            default_capability=default_capability,
        ),
    )


def test_bounded_loop_allows_read_only_tool(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "README.md").write_text("hello", encoding="utf-8")
    controller = make_controller(
        workspace,
        [ManagerDecision("Read the workspace README.", "file", "read_file", {"path": "README.md"})],
    )

    result = controller.run("read README")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["trace"][0]["policy"]["decision"] == "allow"
    assert result["trace"][0]["energy"]["value"] >= 0


def test_bounded_loop_requires_approval_for_shell_by_default(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("Check Python version.", "test", "run_command", {"command": "python --version"})],
    )

    result = controller.run("run python version")

    assert result["stop_reason"] == "NEEDS_USER_APPROVAL"
    assert result["observation"]["ok"] is False
    assert result["trace"][0]["policy"]["decision"] == "approval_required"


def test_bounded_loop_allows_whitelisted_shell_in_controlled_autonomous(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("Check Python version.", "test", "run_command", {"command": "python --version"})],
        default_capability="controlled_autonomous",
    )

    result = controller.run("run python version")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["trace"][0]["policy"]["decision"] == "allow"


def test_bounded_loop_still_blocks_non_whitelisted_shell_in_controlled_autonomous(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("Run a non-whitelisted command.", "test", "run_command", {"command": "whoami"})],
        default_capability="controlled_autonomous",
    )

    result = controller.run("run whoami")

    assert result["stop_reason"] == "NEEDS_USER_INPUT"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "plan"
    assert "template" in result["observation"]["content"]
    assert result["trace"][0]["routing"]["execution_mode"] == "PLAN_ONLY"
    assert result["trace"][0]["policy"]["decision"] == "approval_required"


def test_bounded_loop_requires_approval_for_proxy_fetch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "Fetch external data through the proxy tool.",
                "network",
                "proxy_fetch",
                {"url": "https://example.com/status"},
            )
        ],
    )

    result = controller.run("use proxy to fetch example.com")

    assert result["stop_reason"] == "NEEDS_USER_APPROVAL"
    assert result["trace"][0]["policy"]["risk"] == "network"
    assert result["trace"][0]["policy"]["decision"] == "approval_required"


def test_bounded_loop_allows_open_browser_tool(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    opened: list[tuple[str, str]] = []

    def fake_opener(url: str, browser: str) -> None:
        opened.append((url, browser))

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_browser_domains=["youtube.com"],
        browser_opener=fake_opener,
    )
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "Open YouTube in Chrome.",
                "browser",
                "open_browser",
                {"url": "https://www.youtube.com", "browser": "chrome"},
            )
        ],
        tools=tools,
    )

    result = controller.run("open youtube in chrome")

    assert result["stop_reason"] == "DONE"
    assert result["trace"][0]["policy"]["risk"] == "browser"
    assert result["trace"][0]["policy"]["decision"] == "allow"
    assert opened == [("https://www.youtube.com", "chrome")]


def test_bounded_loop_rejects_destructive_request(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("Delete the workspace files.", "file", "read_file", {"path": "."})],
    )

    result = controller.run("delete files")

    assert result["stop_reason"] == "POLICY_REJECTED"
    assert result["trace"][0]["policy"]["risk"] == "destructive"


def test_bounded_loop_returns_plan_only_without_tool_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "先產生代理工作規劃，不直接執行未 template 化命令。",
                "explain",
                "none",
                {},
            )
        ],
    )

    result = controller.run("請 Codex 評估 Hermes 並提出優化")

    assert result["stop_reason"] == "NEEDS_USER_INPUT"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "plan"
    assert "工具 `none` 未完成" not in result["answer"]
    assert result["trace"][0]["routing"]["execution_mode"] == "PLAN_ONLY"


def test_bounded_loop_executes_external_codex_runner(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    dispatched: list[tuple[str, str]] = []

    def fake_external_codex_runner(topic: str, mode: str) -> str:
        dispatched.append((topic, mode))
        return "external codex accepted self optimization discussion"

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        external_codex_runner=fake_external_codex_runner,
    )
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "要求外部 Codex 與 Hermes 進行自我優化討論。",
                "external",
                "external_codex",
                {
                    "topic": "Codex 與 Hermes 自我優化討論",
                    "mode": "self_optimization_discussion",
                },
            )
        ],
        tools=tools,
        default_capability="controlled_autonomous",
    )

    result = controller.run("請外部 codex 與 hermes 討論自我優化")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "external_codex"
    assert result["trace"][0]["routing"]["execution_mode"] == "MCP_GOVERNED"
    assert result["trace"][0]["policy"]["decision"] == "allow"
    assert dispatched == [("Codex 與 Hermes 自我優化討論", "self_optimization_discussion")]


def test_bounded_loop_uses_external_chat_reply_as_observation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    bridge = FakeExternalChatBridge({"HI": "HI，很高興為你服務，請問有甚麼可以幫忙的嗎?"})
    tools = ToolBox(str(workspace), ["python --version"], external_chat_bridge=bridge)
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "到網頁版 GPT 下達 HI 並讀回回答。",
                "external",
                "external_chat",
                {"message": "HI", "target": "chatgpt_web"},
            )
        ],
        tools=tools,
        default_capability="controlled_autonomous",
    )

    result = controller.run("請 Hermes 到 GPT 下達 HI 並讀回回答")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "external_chat"
    assert "HI，很高興為你服務" in result["answer"]
    assert result["trace"][0]["routing"]["execution_mode"] == "MCP_GOVERNED"
    assert result["trace"][0]["policy"]["decision"] == "allow"
    assert bridge.sent_messages == [("chatgpt_web", "HI")]


def test_bounded_loop_uses_external_chat_loop_turns_as_observation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    bridge = FakeExternalChatBridge({"HI": "第一輪外部回覆"}, default_reply="第二輪外部回覆")
    tools = ToolBox(str(workspace), ["python --version"], external_chat_bridge=bridge)
    controller = make_controller(
        workspace,
        [
            ManagerDecision(
                "到網頁版 GPT 下達 HI 並維持多輪對話。",
                "external",
                "external_chat_loop",
                {"message": "HI", "target": "chatgpt_web", "max_turns": "2"},
            )
        ],
        tools=tools,
        default_capability="controlled_autonomous",
    )

    result = controller.run("請 Hermes 到 GPT 下達 HI 並跟外部 model 來回聊天")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "external_chat_loop"
    assert "第一輪外部回覆" in result["answer"]
    assert "第二輪外部回覆" in result["answer"]
    assert result["trace"][0]["routing"]["execution_mode"] == "MCP_GOVERNED"
    assert result["trace"][0]["policy"]["decision"] == "allow"
    assert len(bridge.sent_messages) == 2


def test_bounded_loop_denies_gui_observe_in_plan_only_capability(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("觀察外部桌面 UI。", "gui", "gui_observe", {})],
        default_capability="plan_only",
    )

    result = controller.run("觀察外部 GPT 畫面")

    assert result["stop_reason"] == "POLICY_REJECTED"
    assert result["trace"][0]["policy"]["risk"] == "gui_observe"
    assert result["trace"][0]["policy"]["decision"] == "deny"


def test_bounded_loop_allows_gui_observe_in_read_only_capability(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("觀察外部桌面 UI。", "gui", "gui_observe", {})],
        default_capability="read_only",
    )

    result = controller.run("觀察外部 GPT 畫面")

    assert result["stop_reason"] == "DONE"
    assert result["observation"]["ok"] is True
    assert result["observation"]["tool"] == "gui_observe"
    assert result["trace"][0]["policy"]["risk"] == "gui_observe"
    assert result["trace"][0]["policy"]["decision"] == "allow"


def test_bounded_loop_requires_approval_for_gui_click_in_controlled_autonomous(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    controller = make_controller(
        workspace,
        [ManagerDecision("點擊外部 GPT 送出按鈕。", "gui", "gui_click", {"target": "send_button"})],
        default_capability="controlled_autonomous",
    )

    result = controller.run("點擊外部 GPT 送出按鈕")

    assert result["stop_reason"] == "NEEDS_USER_APPROVAL"
    assert result["trace"][0]["policy"]["risk"] == "gui_action"
    assert result["trace"][0]["policy"]["decision"] == "approval_required"
