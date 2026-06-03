from pathlib import Path

from simple_agent.bounded_loop import BoundedLoopController, LoopLimits
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
) -> BoundedLoopController:
    tools = tools or ToolBox(str(workspace), ["python --version"])
    return BoundedLoopController(
        FakeManager(decisions),  # type: ignore[arg-type]
        FakeWorker(),  # type: ignore[arg-type]
        tools,
        LoopLimits(max_steps=3, max_replans=1, max_tool_failures=2, max_same_action_repeat=1),
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
