from pathlib import Path

from simple_agent.tools import ToolBox
from simple_agent.work_execution import (
    CapabilityLevel,
    CommandTemplateRegistry,
    ExecutionMode,
    PolicyDecision,
    WorkIntent,
    WorkSkillRouter,
    execute_work_intent,
)


def test_router_sends_read_only_file_work_to_cli_fast() -> None:
    intent = WorkIntent(
        goal="inspect README",
        action_type="read_only",
        tool_candidate="read_file",
        params={"path": "README.md"},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.CLI_FAST
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.capability == CapabilityLevel.L1_READ_ONLY
    assert decision.executor == "cli_template"
    assert decision.template_id == "read_file"


def test_router_denies_free_shell_command() -> None:
    intent = WorkIntent(
        goal="run arbitrary shell",
        action_type="local_verify",
        tool_candidate="run_command",
        params={"command": "whoami"},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.PLAN_ONLY
    assert decision.policy_decision == PolicyDecision.APPROVAL_REQUIRED
    assert "template" in decision.reason


def test_router_keeps_broad_agent_work_as_plan_only() -> None:
    intent = WorkIntent(
        goal="ask Codex to evaluate Hermes features and propose improvements",
        action_type="agent_planning",
        tool_candidate="none",
        params={},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.PLAN_ONLY
    assert decision.policy_decision == PolicyDecision.APPROVAL_REQUIRED
    assert decision.executor == "planner"


def test_router_routes_external_codex_to_mcp_governed_path() -> None:
    intent = WorkIntent(
        goal="ask external Codex to discuss Hermes self optimization",
        action_type="external",
        tool_candidate="external_codex",
        params={"topic": "Hermes self optimization", "mode": "self_optimization_discussion"},
        read_only=True,
        network=True,
        writes_files=False,
        requires_credentials=False,
        approved=True,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.MCP_GOVERNED
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.capability == CapabilityLevel.L5_EXTERNAL_GOVERNED
    assert decision.executor == "mcp_bridge"


def test_router_routes_external_chat_to_mcp_governed_path() -> None:
    intent = WorkIntent(
        goal="send HI to web GPT and receive reply",
        action_type="external",
        tool_candidate="external_chat",
        params={"message": "HI", "target": "chatgpt_web"},
        read_only=True,
        network=True,
        writes_files=False,
        requires_credentials=True,
        approved=True,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.MCP_GOVERNED
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.capability == CapabilityLevel.L5_EXTERNAL_GOVERNED
    assert decision.executor == "mcp_bridge"


def test_router_routes_external_chat_loop_to_mcp_governed_path() -> None:
    intent = WorkIntent(
        goal="keep chatting with web GPT for multiple turns",
        action_type="external",
        tool_candidate="external_chat_loop",
        params={"message": "HI", "target": "chatgpt_web", "max_turns": "2"},
        read_only=True,
        network=True,
        writes_files=False,
        requires_credentials=True,
        approved=True,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.MCP_GOVERNED
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.capability == CapabilityLevel.L5_EXTERNAL_GOVERNED
    assert decision.executor == "mcp_bridge"


def test_router_allows_self_improve_proposal_only_as_patch_proposal() -> None:
    intent = WorkIntent(
        goal="let Hermes improve its own tool code",
        action_type="self_improve",
        tool_candidate="self_improve",
        params={"goal": "改善 Hermes 工具能力", "scope": "simple_agent", "mode": "proposal_only"},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
        approved=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.CLI_FAST
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.capability == CapabilityLevel.L3_PATCH_PROPOSAL
    assert decision.executor == "self_development"


def test_router_requires_approval_for_self_improve_apply_mode() -> None:
    intent = WorkIntent(
        goal="apply Hermes self improvement patch",
        action_type="self_improve",
        tool_candidate="self_improve",
        params={"goal": "套用 Hermes 自我修改", "scope": "simple_agent", "mode": "apply_after_approval"},
        read_only=False,
        network=False,
        writes_files=True,
        requires_credentials=False,
        approved=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.APPROVAL_REQUIRED
    assert decision.policy_decision == PolicyDecision.APPROVAL_REQUIRED
    assert decision.capability == CapabilityLevel.L4_APPROVED_WRITE


def test_router_allows_gui_observe_as_read_only_gui_agent() -> None:
    intent = WorkIntent(
        goal="observe external chat UI",
        action_type="gui",
        tool_candidate="gui_observe",
        params={},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.CLI_FAST
    assert decision.policy_decision == PolicyDecision.ALLOW
    assert decision.risk == "gui_observe"
    assert decision.executor == "gui_agent"
    assert decision.capability == CapabilityLevel.L1_READ_ONLY


def test_router_requires_approval_for_gui_click_action() -> None:
    intent = WorkIntent(
        goal="click send button in external UI",
        action_type="gui",
        tool_candidate="gui_click",
        params={"target": "send_button"},
        read_only=False,
        network=False,
        writes_files=False,
        requires_credentials=False,
        reversible=True,
        approved=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.APPROVAL_REQUIRED
    assert decision.policy_decision == PolicyDecision.APPROVAL_REQUIRED
    assert decision.risk == "gui_action"
    assert decision.executor == "gui_agent"


def test_router_denies_unknown_gui_tool() -> None:
    intent = WorkIntent(
        goal="drag something without a governed template",
        action_type="gui",
        tool_candidate="gui_drag",
        params={"target": "message"},
        read_only=False,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    decision = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)

    assert decision.execution_mode == ExecutionMode.DENIED
    assert decision.policy_decision == PolicyDecision.DENY
    assert decision.risk == "gui_unknown"


def test_execute_work_intent_runs_cli_template_and_records_raw_ref(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    trace_root = tmp_path / "trace"
    workspace.mkdir()
    (workspace / "README.md").write_text("Hermes gateway", encoding="utf-8")
    tools = ToolBox(str(workspace), ["python --version"])
    intent = WorkIntent(
        goal="read README",
        action_type="read_only",
        tool_candidate="read_file",
        params={"path": "README.md"},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    result = execute_work_intent(intent, tools=tools, trace_root=trace_root)

    assert result.ok is True
    assert result.status == "completed"
    assert result.execution_mode == ExecutionMode.CLI_FAST
    assert result.summary == "Hermes gateway"
    assert result.raw_ref is not None
    assert (trace_root / result.raw_ref).read_text(encoding="utf-8") == "Hermes gateway"


def test_execute_work_intent_requires_approval_for_proxy_fetch(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    tools = ToolBox(str(workspace), ["python --version"], allowed_proxy_domains=["example.com"])
    intent = WorkIntent(
        goal="fetch external status",
        action_type="external_fetch",
        tool_candidate="proxy_fetch",
        params={"url": "https://example.com/status"},
        read_only=True,
        network=True,
        writes_files=False,
        requires_credentials=False,
        approved=False,
    )

    result = execute_work_intent(intent, tools=tools, trace_root=tmp_path / "trace")

    assert result.ok is False
    assert result.status == "approval_required"
    assert result.execution_mode == ExecutionMode.MCP_GOVERNED
    assert result.policy_decision == PolicyDecision.APPROVAL_REQUIRED
    assert result.next_recommendation == "ask_user"


def test_execute_work_intent_uses_mcp_governed_path_after_approval(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    def fake_fetcher(url: str, timeout: int, max_bytes: int) -> str:
        assert url == "https://example.com/status"
        return "external ok"

    tools = ToolBox(
        str(workspace),
        ["python --version"],
        allowed_proxy_domains=["example.com"],
        proxy_fetcher=fake_fetcher,
    )
    intent = WorkIntent(
        goal="fetch external status",
        action_type="external_fetch",
        tool_candidate="proxy_fetch",
        params={"url": "https://example.com/status"},
        read_only=True,
        network=True,
        writes_files=False,
        requires_credentials=False,
        approved=True,
    )

    result = execute_work_intent(intent, tools=tools, trace_root=tmp_path / "trace")

    assert result.ok is True
    assert result.status == "completed"
    assert result.execution_mode == ExecutionMode.MCP_GOVERNED
    assert result.summary == "external ok"


def test_execute_work_intent_records_gui_audit_trace(tmp_path: Path) -> None:
    tools = ToolBox(str(tmp_path), ["python --version"])
    intent = WorkIntent(
        goal="observe desktop UI before acting",
        action_type="gui",
        tool_candidate="gui_observe",
        params={},
        read_only=True,
        network=False,
        writes_files=False,
        requires_credentials=False,
    )

    result = execute_work_intent(intent, tools=tools, trace_root=tmp_path / "trace")

    assert result.ok is True
    assert result.status == "completed"
    assert result.execution_mode == ExecutionMode.CLI_FAST
    assert result.trace["audit"]["tool_name"] == "gui_observe"
    assert result.trace["audit"]["input_payload_hash"]
    assert result.trace["audit"]["executed"] is True
