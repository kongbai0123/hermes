from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from .tools import Observation, ToolBox


class ExecutionMode(StrEnum):
    PLAN_ONLY = "PLAN_ONLY"
    CLI_FAST = "CLI_FAST"
    CLI_SANDBOXED = "CLI_SANDBOXED"
    MCP_GOVERNED = "MCP_GOVERNED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    DENIED = "DENIED"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    APPROVAL_REQUIRED = "approval_required"


class CapabilityLevel(StrEnum):
    L0_PLAN_ONLY = "L0_PLAN_ONLY"
    L1_READ_ONLY = "L1_READ_ONLY"
    L2_LOCAL_VERIFY = "L2_LOCAL_VERIFY"
    L3_PATCH_PROPOSAL = "L3_PATCH_PROPOSAL"
    L4_APPROVED_WRITE = "L4_APPROVED_WRITE"
    L5_EXTERNAL_GOVERNED = "L5_EXTERNAL_GOVERNED"


@dataclass(frozen=True)
class WorkIntent:
    goal: str
    action_type: str
    tool_candidate: str
    params: dict[str, str] = field(default_factory=dict)
    read_only: bool = True
    network: bool = False
    writes_files: bool = False
    requires_credentials: bool = False
    reads_secrets: bool = False
    destructive: bool = False
    reversible: bool = True
    approved: bool = False
    expected_output: str = "summary"


@dataclass(frozen=True)
class RouteDecision:
    execution_mode: ExecutionMode
    risk: str
    policy_decision: PolicyDecision
    reason: str
    requires_approval: bool
    executor: str
    capability: CapabilityLevel
    template_id: str | None = None
    tool: str | None = None


@dataclass(frozen=True)
class CommandTemplate:
    template_id: str
    tool: str
    description: str
    risk: str
    execution_mode: ExecutionMode
    capability: CapabilityLevel
    writes_files: bool
    network: bool
    timeout_sec: int = 60
    max_output_chars: int = 4000
    required_params: tuple[str, ...] = ()
    command_pattern: str | None = None

    def matches(self, intent: WorkIntent) -> bool:
        if intent.tool_candidate != self.tool:
            return False
        if any(param not in intent.params for param in self.required_params):
            return False
        if self.command_pattern is None:
            return True
        command = intent.params.get("command", "")
        return re.fullmatch(self.command_pattern, command) is not None


class CommandTemplateRegistry:
    def __init__(self, templates: list[CommandTemplate]) -> None:
        self.templates = templates

    @classmethod
    def default(cls) -> CommandTemplateRegistry:
        return cls(
            [
                CommandTemplate(
                    template_id="read_file",
                    tool="read_file",
                    description="Read a file inside the workspace.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L1_READ_ONLY,
                    writes_files=False,
                    network=False,
                    required_params=("path",),
                ),
                CommandTemplate(
                    template_id="list_files",
                    tool="list_files",
                    description="List files inside the workspace.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L1_READ_ONLY,
                    writes_files=False,
                    network=False,
                ),
                CommandTemplate(
                    template_id="search_text",
                    tool="search_text",
                    description="Search workspace text.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L1_READ_ONLY,
                    writes_files=False,
                    network=False,
                    required_params=("keyword",),
                ),
                CommandTemplate(
                    template_id="python_version",
                    tool="run_command",
                    description="Read Python version.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    required_params=("command",),
                    command_pattern=r"python --version",
                ),
                CommandTemplate(
                    template_id="git_status",
                    tool="run_command",
                    description="Read git status.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    required_params=("command",),
                    command_pattern=r"git status --short",
                ),
                CommandTemplate(
                    template_id="git_diff_stat",
                    tool="run_command",
                    description="Read git diff stats.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    required_params=("command",),
                    command_pattern=r"git diff --stat",
                ),
                CommandTemplate(
                    template_id="pytest_quiet",
                    tool="run_command",
                    description="Run pytest in quiet mode.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    timeout_sec=90,
                    required_params=("command",),
                    command_pattern=r"(python -m pytest|pytest)( [\w./\\-]+)? -q",
                ),
                CommandTemplate(
                    template_id="npm_check",
                    tool="run_command",
                    description="Run npm check script.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    timeout_sec=90,
                    required_params=("command",),
                    command_pattern=r"npm run check",
                ),
                CommandTemplate(
                    template_id="npm_lint",
                    tool="run_command",
                    description="Run npm lint script.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    timeout_sec=90,
                    required_params=("command",),
                    command_pattern=r"npm run lint",
                ),
                CommandTemplate(
                    template_id="tsc_no_emit",
                    tool="run_command",
                    description="Run TypeScript no-emit check.",
                    risk="low",
                    execution_mode=ExecutionMode.CLI_FAST,
                    capability=CapabilityLevel.L2_LOCAL_VERIFY,
                    writes_files=False,
                    network=False,
                    timeout_sec=90,
                    required_params=("command",),
                    command_pattern=r"tsc --noEmit",
                ),
            ]
        )

    def find_for_intent(self, intent: WorkIntent) -> CommandTemplate | None:
        for template in self.templates:
            if template.matches(intent):
                return template
        return None


class WorkSkillRouter:
    GUI_OBSERVE_TOOLS = {"gui_observe", "gui_verify"}
    GUI_ACTION_TOOLS = {"gui_click", "gui_type_text", "gui_hotkey", "gui_wait"}
    APP_LAUNCH_TOOLS = {"app_launch"}
    EXTERNAL_TOOLS = {
        "proxy_fetch",
        "open_browser",
        "external_codex",
        "external_chat",
        "external_chat_loop",
        "github",
        "gmail",
        "calendar",
        "drive",
    }

    def __init__(self, registry: CommandTemplateRegistry) -> None:
        self.registry = registry

    def route(self, intent: WorkIntent) -> RouteDecision:
        if intent.tool_candidate == "none" or intent.action_type in {"agent_planning", "plan_only"}:
            return RouteDecision(
                ExecutionMode.PLAN_ONLY,
                "medium",
                PolicyDecision.APPROVAL_REQUIRED,
                "Broad agent work needs a plan before tool execution.",
                True,
                "planner",
                CapabilityLevel.L0_PLAN_ONLY,
                tool=intent.tool_candidate,
            )
        if intent.tool_candidate in self.GUI_OBSERVE_TOOLS:
            return RouteDecision(
                ExecutionMode.CLI_FAST,
                "gui_observe",
                PolicyDecision.ALLOW,
                "GUI observation uses a governed GUI runner and is read-only.",
                False,
                "gui_agent",
                CapabilityLevel.L1_READ_ONLY,
                tool=intent.tool_candidate,
            )
        if intent.tool_candidate in self.GUI_ACTION_TOOLS:
            approved = intent.approved
            return RouteDecision(
                ExecutionMode.APPROVAL_REQUIRED,
                "gui_action",
                PolicyDecision.ALLOW if approved else PolicyDecision.APPROVAL_REQUIRED,
                "GUI actions can affect external UI state and require explicit approval.",
                not approved,
                "gui_agent",
                CapabilityLevel.L4_APPROVED_WRITE,
                tool=intent.tool_candidate,
            )
        if intent.tool_candidate.startswith("gui_"):
            return self._denied("gui_unknown", "Unknown GUI tool is denied until registered.")
        if intent.tool_candidate in self.APP_LAUNCH_TOOLS:
            approved = intent.approved
            return RouteDecision(
                ExecutionMode.APPROVAL_REQUIRED,
                "external_state",
                PolicyDecision.ALLOW if approved else PolicyDecision.APPROVAL_REQUIRED,
                "Launching a desktop application changes external UI state and requires approval.",
                not approved,
                "app_launcher",
                CapabilityLevel.L4_APPROVED_WRITE,
                tool=intent.tool_candidate,
            )
        if intent.tool_candidate == "self_improve":
            mode = intent.params.get("mode", "proposal_only")
            if mode == "proposal_only":
                return RouteDecision(
                    ExecutionMode.CLI_FAST,
                    "medium",
                    PolicyDecision.ALLOW,
                    "Hermes self-improvement proposal can inspect code but must not write files.",
                    False,
                    "self_development",
                    CapabilityLevel.L3_PATCH_PROPOSAL,
                    tool=intent.tool_candidate,
                )
            return RouteDecision(
                ExecutionMode.APPROVAL_REQUIRED,
                "medium",
                PolicyDecision.APPROVAL_REQUIRED if not intent.approved else PolicyDecision.ALLOW,
                "Hermes self-modification requires explicit approval before applying changes.",
                not intent.approved,
                "self_development",
                CapabilityLevel.L4_APPROVED_WRITE,
                tool=intent.tool_candidate,
            )
        if intent.destructive:
            return self._denied("destructive", "Destructive work is denied by default.")
        if intent.reads_secrets:
            return self._denied("credential", "Secret or credential reads are denied.")
        if intent.writes_files:
            return RouteDecision(
                ExecutionMode.APPROVAL_REQUIRED,
                "medium",
                PolicyDecision.APPROVAL_REQUIRED,
                "File writes require approval.",
                True,
                "approval",
                CapabilityLevel.L4_APPROVED_WRITE,
                tool=intent.tool_candidate,
            )
        if intent.network or intent.requires_credentials or intent.tool_candidate in self.EXTERNAL_TOOLS:
            requires_approval = not intent.approved
            if intent.tool_candidate == "open_browser":
                risk = "browser"
            elif intent.tool_candidate in {"external_codex", "external_chat", "external_chat_loop"}:
                risk = "external_state"
            else:
                risk = "network" if intent.network else "credential"
            return RouteDecision(
                ExecutionMode.MCP_GOVERNED,
                risk,
                PolicyDecision.APPROVAL_REQUIRED if requires_approval else PolicyDecision.ALLOW,
                "External or credential-boundary work uses MCP governed path.",
                requires_approval,
                "mcp_bridge",
                CapabilityLevel.L5_EXTERNAL_GOVERNED,
                tool=intent.tool_candidate,
            )
        template = self.registry.find_for_intent(intent)
        if template is None:
            if intent.tool_candidate == "run_command":
                return RouteDecision(
                    ExecutionMode.PLAN_ONLY,
                    "medium",
                    PolicyDecision.APPROVAL_REQUIRED,
                    "No CLI template matched this intent; create a plan or add a governed template before execution.",
                    True,
                    "planner",
                    CapabilityLevel.L0_PLAN_ONLY,
                    tool=intent.tool_candidate,
                )
            return self._denied("high", "No CLI template matched this intent; free shell is denied.")
        return RouteDecision(
            template.execution_mode,
            template.risk,
            PolicyDecision.ALLOW,
            "Matched governed CLI template.",
            False,
            "cli_template",
            template.capability,
            template_id=template.template_id,
            tool=template.tool,
        )

    def _denied(self, risk: str, reason: str) -> RouteDecision:
        return RouteDecision(
            ExecutionMode.DENIED,
            risk,
            PolicyDecision.DENY,
            reason,
            False,
            "none",
            CapabilityLevel.L0_PLAN_ONLY,
        )


@dataclass(frozen=True)
class WorkExecutionResult:
    ok: bool
    status: str
    execution_mode: ExecutionMode
    policy_decision: PolicyDecision
    summary: str
    raw_ref: str | None
    next_recommendation: str
    trace: dict[str, Any]


class ObservationSummarizer:
    def __init__(self, trace_root: Path, max_observation_chars: int = 2000) -> None:
        self.trace_root = trace_root
        self.max_observation_chars = max_observation_chars

    def summarize(self, observation: Observation, intent: WorkIntent) -> tuple[str, str | None, bool]:
        content = observation.content
        raw_ref = self._write_raw(content, intent)
        truncated = len(content) > self.max_observation_chars
        summary = content[: self.max_observation_chars]
        if truncated:
            summary += "\noutput truncated; see raw_ref"
        return summary, raw_ref, truncated

    def _write_raw(self, content: str, intent: WorkIntent) -> str:
        raw_dir = self.trace_root / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(
            f"{intent.tool_candidate}:{intent.params}:{content}".encode("utf-8", errors="replace")
        ).hexdigest()[:12]
        raw_path = raw_dir / f"{intent.tool_candidate}_{digest}.log"
        raw_path.write_text(content, encoding="utf-8", errors="replace")
        return raw_path.relative_to(self.trace_root).as_posix()


class SafeCommandExecutor:
    def __init__(self, tools: ToolBox) -> None:
        self.tools = tools

    def execute(self, intent: WorkIntent, decision: RouteDecision) -> Observation:
        if decision.executor in {"self_development", "gui_agent", "app_launcher"}:
            return self.tools.execute(intent.tool_candidate, **intent.params)
        if decision.template_id in {"read_file", "list_files", "search_text"}:
            return self.tools.execute(intent.tool_candidate, **intent.params)
        if intent.tool_candidate == "run_command":
            return self.tools.run_command(intent.params.get("command", ""))
        return Observation(False, intent.tool_candidate, "Unsupported CLI template.")


class McpGovernedAdapter:
    def __init__(self, tools: ToolBox) -> None:
        self.tools = tools

    def execute(self, intent: WorkIntent, decision: RouteDecision) -> Observation:
        if decision.requires_approval:
            payload = {
                "ok": False,
                "status": "approval_required",
                "tool": intent.tool_candidate,
                "reason": decision.reason,
            }
            return Observation(False, intent.tool_candidate, json.dumps(payload, ensure_ascii=False))
        if intent.tool_candidate in {"proxy_fetch", "open_browser", "external_codex", "external_chat", "external_chat_loop"}:
            return self.tools.execute(intent.tool_candidate, **intent.params)
        payload = {
            "ok": False,
            "status": "unsupported",
            "tool": intent.tool_candidate,
        }
        return Observation(False, intent.tool_candidate, json.dumps(payload, ensure_ascii=False))


def execute_work_intent(
    intent: WorkIntent,
    *,
    tools: ToolBox,
    trace_root: Path,
    registry: CommandTemplateRegistry | None = None,
) -> WorkExecutionResult:
    registry = registry or CommandTemplateRegistry.default()
    router = WorkSkillRouter(registry)
    decision = router.route(intent)
    summarizer = ObservationSummarizer(trace_root)

    if decision.policy_decision == PolicyDecision.DENY:
        observation = Observation(False, intent.tool_candidate, decision.reason)
    elif decision.execution_mode in {ExecutionMode.CLI_FAST, ExecutionMode.CLI_SANDBOXED}:
        observation = SafeCommandExecutor(tools).execute(intent, decision)
    elif decision.execution_mode == ExecutionMode.MCP_GOVERNED:
        observation = McpGovernedAdapter(tools).execute(intent, decision)
    elif decision.execution_mode == ExecutionMode.APPROVAL_REQUIRED:
        if decision.policy_decision == PolicyDecision.ALLOW and decision.executor in {"gui_agent", "app_launcher"}:
            observation = SafeCommandExecutor(tools).execute(intent, decision)
        else:
            observation = Observation(False, intent.tool_candidate, decision.reason)
    else:
        observation = Observation(False, intent.tool_candidate, "Plan only; no execution performed.")

    summary, raw_ref, truncated = summarizer.summarize(observation, intent)
    if decision.policy_decision == PolicyDecision.DENY:
        status = "denied"
    elif decision.requires_approval:
        status = "approval_required"
    elif observation.ok:
        status = "completed"
    else:
        status = "failed"

    audit = _build_audit_event(intent, decision, observation, status)
    trace = {
        "work_intent": asdict(intent),
        "routing": {
            "execution_mode": decision.execution_mode.value,
            "executor": decision.executor,
            "template_id": decision.template_id,
            "tool": decision.tool,
            "reason": decision.reason,
        },
        "policy": {
            "risk": decision.risk,
            "decision": decision.policy_decision.value,
            "requires_approval": decision.requires_approval,
            "capability": decision.capability.value,
        },
        "execution": {
            "status": status,
            "summary": summary,
            "raw_ref": raw_ref,
            "truncated": truncated,
        },
        "audit": audit,
    }
    return WorkExecutionResult(
        ok=observation.ok,
        status=status,
        execution_mode=decision.execution_mode,
        policy_decision=decision.policy_decision,
        summary=summary,
        raw_ref=raw_ref,
        next_recommendation="ask_user" if status == "approval_required" else "continue",
        trace=trace,
    )


def _build_audit_event(
    intent: WorkIntent,
    decision: RouteDecision,
    observation: Observation,
    status: str,
) -> dict[str, Any]:
    payload = {
        "goal": intent.goal,
        "tool_candidate": intent.tool_candidate,
        "params": intent.params,
        "approved": intent.approved,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {
        "tool_name": intent.tool_candidate,
        "executor": decision.executor,
        "risk_level": decision.risk,
        "policy_decision": decision.policy_decision.value,
        "status": status,
        "executed": observation.ok and not decision.requires_approval,
        "input_payload_hash": digest,
    }
