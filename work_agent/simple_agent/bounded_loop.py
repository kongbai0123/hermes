from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .roles import ManagerDecision, ManagerModel, WorkerModel
from .tools import Observation, ToolBox
from .work_execution import (
    CommandTemplateRegistry,
    ExecutionMode,
    PolicyDecision as WorkPolicyDecision,
    WorkIntent,
    WorkSkillRouter,
)


StopReason = Literal[
    "DONE",
    "NEEDS_USER_APPROVAL",
    "NEEDS_USER_INPUT",
    "POLICY_REJECTED",
    "TOOL_FAILURE_BACKOFF",
    "MAX_STEPS_REACHED",
    "MAX_REPLANS_REACHED",
    "VALIDATION_FAILED",
    "NO_PROGRESS_DETECTED",
    "PROVIDER_UNAVAILABLE",
]

PolicyDecision = Literal["allow", "deny", "approval_required"]


@dataclass
class LoopLimits:
    max_steps: int = 6
    max_replans: int = 2
    max_tool_failures: int = 2
    max_same_action_repeat: int = 1
    default_capability: str = "read_only"


@dataclass
class PolicyResult:
    risk: str
    decision: PolicyDecision
    reason: str
    execution_mode: str = "PLAN_ONLY"
    executor: str = "none"
    template_id: str | None = None
    capability: str = "L0_PLAN_ONLY"
    requires_approval: bool = False


@dataclass
class EnergyResult:
    value: float
    uncertainty: float
    repetition: float
    tool_failure: float
    no_progress: float
    trend: str
    suggestion: str


class PolicyGate:
    READ_ONLY_TOOLS = {"list_files", "read_file", "search_text", "none"}
    WRITE_TOOLS = {"write_file", "apply_patch", "generate_patch"}
    NETWORK_TOOLS = {"proxy_fetch"}
    BROWSER_TOOLS = {"open_browser"}
    EXTERNAL_AGENT_TOOLS = {"external_codex", "external_chat", "external_chat_loop"}
    GUI_OBSERVE_TOOLS = {"gui_observe", "gui_verify"}
    GUI_ACTION_TOOLS = {"gui_click", "gui_type_text", "gui_hotkey", "gui_wait"}

    def evaluate(self, decision: ManagerDecision, capability: str) -> PolicyResult:
        if decision.tool in self.GUI_OBSERVE_TOOLS or decision.tool in self.GUI_ACTION_TOOLS:
            return self._evaluate_gui(decision, capability)
        intent = self._intent_from_decision(decision, capability)
        route = WorkSkillRouter(CommandTemplateRegistry.default()).route(intent)
        if route.policy_decision == WorkPolicyDecision.DENY:
            return PolicyResult(
                route.risk,
                "deny",
                route.reason,
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                route.requires_approval,
            )
        if route.policy_decision == WorkPolicyDecision.APPROVAL_REQUIRED:
            return PolicyResult(
                route.risk,
                "approval_required",
                route.reason,
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                route.requires_approval,
            )
        if (
            route.capability.value == "L2_LOCAL_VERIFY"
            and capability not in {"controlled_autonomous", "approved_write", "full_dev"}
        ):
            return PolicyResult(
                route.risk,
                "approval_required",
                "Local verification commands require controlled autonomous capability or approval.",
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                True,
            )
        if route.execution_mode in {ExecutionMode.CLI_FAST, ExecutionMode.CLI_SANDBOXED}:
            return PolicyResult(
                route.risk,
                "allow",
                route.reason,
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                route.requires_approval,
            )
        if route.execution_mode == ExecutionMode.MCP_GOVERNED and not route.requires_approval:
            return PolicyResult(
                route.risk,
                "allow",
                route.reason,
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                route.requires_approval,
            )

        tool = decision.tool
        plan_text = f"{decision.plan} {decision.args}".lower()

        if any(word in plan_text for word in ["delete", "remove", "刪除", "清除"]):
            return PolicyResult("destructive", "deny", "Destructive requests are denied by default.")
        if any(word in plan_text for word in ["secret", "credential", "token", "密碼", "憑證"]):
            return PolicyResult("high", "deny", "Credential or secret access is denied.")
        if tool in self.READ_ONLY_TOOLS:
            return PolicyResult("low", "allow", "Read-only tool is allowed.")
        if tool == "run_command":
            if capability == "controlled_autonomous":
                return PolicyResult(
                    "medium",
                    "allow",
                    "Controlled autonomous mode may run commands after ToolBox whitelist validation.",
                )
            if capability in {"approved_write", "full_dev"}:
                return PolicyResult("medium", "approval_required", "Shell commands require approval.")
            return PolicyResult("medium", "approval_required", "Default read-only capability cannot run shell commands.")
        if tool in self.NETWORK_TOOLS:
            return PolicyResult("network", "approval_required", "Network or proxy tools require explicit approval.")
        if tool in self.BROWSER_TOOLS:
            return PolicyResult("browser", "allow", "Browser open action is allowed for configured allowlist domains.")
        if tool in self.EXTERNAL_AGENT_TOOLS:
            return PolicyResult("external_state", "allow", "External Codex agent handoff uses governed adapter path.")
        if tool.startswith("gui_"):
            return PolicyResult("gui_unknown", "deny", f"Unknown or unsupported GUI tool: {tool}")
        if tool in self.WRITE_TOOLS:
            return PolicyResult("medium", "approval_required", "Write or patch actions require approval.")
        return PolicyResult("high", "deny", f"Unknown or unsupported tool: {tool}")

    def _evaluate_gui(self, decision: ManagerDecision, capability: str) -> PolicyResult:
        route = WorkSkillRouter(CommandTemplateRegistry.default()).route(
            self._intent_from_decision(decision, capability)
        )
        if capability == "plan_only":
            return PolicyResult(
                route.risk,
                "deny",
                "Plan-only capability cannot execute GUI tools.",
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                False,
            )
        if decision.tool == "gui_observe":
            return PolicyResult(
                route.risk,
                "allow",
                "Read-only GUI observation is allowed through the governed mock runner.",
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                False,
            )
        if decision.tool == "gui_verify":
            if capability in {"controlled_autonomous", "approved_write", "full_dev", "external_governed"}:
                return PolicyResult(
                    route.risk,
                    "allow",
                    "GUI verification is allowed for controlled autonomous capability.",
                    route.execution_mode.value,
                    route.executor,
                    route.template_id,
                    route.capability.value,
                    False,
                )
            return PolicyResult(
                route.risk,
                "approval_required",
                "GUI verification requires controlled autonomous capability or approval.",
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                True,
            )
        if decision.tool in self.GUI_ACTION_TOOLS:
            if capability in {"approved_write", "full_dev"}:
                return PolicyResult(
                    route.risk,
                    "allow",
                    "Approved write capability may execute registered GUI actions.",
                    route.execution_mode.value,
                    route.executor,
                    route.template_id,
                    route.capability.value,
                    False,
                )
            return PolicyResult(
                route.risk,
                "approval_required",
                "GUI actions can affect external UI state and require explicit approval.",
                route.execution_mode.value,
                route.executor,
                route.template_id,
                route.capability.value,
                True,
            )
        return PolicyResult("gui_unknown", "deny", f"Unknown or unsupported GUI tool: {decision.tool}")

    def _intent_from_decision(self, decision: ManagerDecision, capability: str) -> WorkIntent:
        plan_text = f"{decision.plan} {decision.args}".lower()
        tool = decision.tool
        return WorkIntent(
            goal=decision.plan,
            action_type=self._action_type(tool),
            tool_candidate=tool,
            params=dict(decision.args),
            read_only=tool in self.READ_ONLY_TOOLS or tool in self.GUI_OBSERVE_TOOLS or tool == "run_command",
            network=tool in self.NETWORK_TOOLS or tool in self.BROWSER_TOOLS or tool in self.EXTERNAL_AGENT_TOOLS,
            writes_files=tool in self.WRITE_TOOLS,
            requires_credentials=tool in self.EXTERNAL_AGENT_TOOLS,
            reads_secrets=any(word in plan_text for word in ["secret", "credential", "token", "密碼", "憑證"]),
            destructive=any(word in plan_text for word in ["delete", "remove", "刪除", "清除"]),
            approved=(
                capability in {"approved_write", "full_dev", "external_governed"}
                or tool in self.BROWSER_TOOLS
                or (tool in self.EXTERNAL_AGENT_TOOLS and capability in {"controlled_autonomous", "external_governed"})
                or (tool in self.GUI_ACTION_TOOLS and capability in {"approved_write", "full_dev"})
            ),
        )

    def _action_type(self, tool: str) -> str:
        if tool in self.READ_ONLY_TOOLS:
            return "read_only"
        if tool == "run_command":
            return "local_verify"
        if tool in self.NETWORK_TOOLS or tool in self.BROWSER_TOOLS or tool in self.EXTERNAL_AGENT_TOOLS:
            return "external"
        if tool in self.GUI_OBSERVE_TOOLS or tool in self.GUI_ACTION_TOOLS:
            return "gui"
        if tool in self.WRITE_TOOLS:
            return "write"
        return "unknown"


class EnergyMonitor:
    def evaluate(
        self,
        *,
        decision: ManagerDecision,
        observation: Observation,
        repeated_action: bool,
        tool_failures: int,
        previous_energy: float | None,
    ) -> EnergyResult:
        uncertainty = 0.65 if decision.tool == "none" else 0.25
        repetition = 1.0 if repeated_action else 0.0
        tool_failure = min(tool_failures / 2, 1.0)
        no_progress = self._no_progress_score(decision, observation)
        value = round(
            0.35 * uncertainty
            + 0.25 * repetition
            + 0.20 * tool_failure
            + 0.20 * no_progress,
            3,
        )
        if previous_energy is None:
            trend = "flat"
        elif value > previous_energy:
            trend = "up"
        elif value < previous_energy:
            trend = "down"
        else:
            trend = "flat"

        suggestion = "continue"
        if value > 0.85 and no_progress > 0.7:
            suggestion = "stop"
        elif value > 0.75 or trend == "up":
            suggestion = "replan"
        elif decision.tool == "none" and no_progress > 0.5:
            suggestion = "ask_user"

        return EnergyResult(value, uncertainty, repetition, tool_failure, no_progress, trend, suggestion)

    def _no_progress_score(self, decision: ManagerDecision, observation: Observation) -> float:
        if not observation.ok:
            return 0.8
        if decision.tool == "none":
            return 0.7
        content = observation.content.strip()
        if not content or content in {"沒有找到結果。", "(空資料夾)"}:
            return 0.6
        return 0.15


class BoundedLoopController:
    def __init__(
        self,
        manager: ManagerModel,
        worker: WorkerModel,
        tools: ToolBox,
        limits: LoopLimits | None = None,
    ) -> None:
        self.manager = manager
        self.worker = worker
        self.tools = tools
        self.limits = limits or LoopLimits()
        self.policy_gate = PolicyGate()
        self.energy_monitor = EnergyMonitor()

    def run(self, user_text: str) -> dict:
        trace_id = f"trace_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        task_id = f"task_{abs(hash(user_text)) % 1000000:06d}"
        trace: list[dict] = []
        replan_count = 0
        tool_failures = 0
        previous_action: tuple[str, tuple[tuple[str, str], ...]] | None = None
        same_action_repeat = 0
        previous_energy: float | None = None
        last_decision: ManagerDecision | None = None
        last_observation: Observation | None = None
        stop_reason: StopReason = "MAX_STEPS_REACHED"

        for step in range(1, self.limits.max_steps + 1):
            decision = self.manager.decide(user_text)
            last_decision = decision
            action_key = (decision.tool, tuple(sorted(decision.args.items())))
            repeated_action = previous_action == action_key
            if repeated_action:
                same_action_repeat += 1
            else:
                same_action_repeat = 0
            previous_action = action_key

            policy = self.policy_gate.evaluate(decision, self.limits.default_capability)
            if policy.execution_mode == "PLAN_ONLY":
                observation = Observation(
                    True,
                    "plan",
                    (
                        "已建立執行前規劃，尚未呼叫工具。\n"
                        f"規劃：{decision.plan}\n"
                        f"治理狀態：{policy.reason}"
                    ),
                )
                stop_reason = "NEEDS_USER_INPUT"
            elif policy.decision == "deny":
                observation = Observation(False, decision.tool, policy.reason)
                stop_reason = "POLICY_REJECTED"
            elif policy.decision == "approval_required":
                observation = Observation(False, decision.tool, policy.reason)
                stop_reason = "NEEDS_USER_APPROVAL"
            elif decision.tool == "none":
                observation = Observation(
                    True,
                    "none",
                    "未使用工具。請補充更明確的目標，或改用目前支援的讀檔、列檔、搜尋任務。",
                )
                stop_reason = "NEEDS_USER_INPUT"
            else:
                observation = self.tools.execute(decision.tool, **decision.args)
                stop_reason = "DONE" if observation.ok else "TOOL_FAILURE_BACKOFF"

            last_observation = observation
            if not observation.ok:
                tool_failures += 1

            energy = self.energy_monitor.evaluate(
                decision=decision,
                observation=observation,
                repeated_action=repeated_action,
                tool_failures=tool_failures,
                previous_energy=previous_energy,
            )
            previous_energy = energy.value
            trace.append(
                self._trace_entry(
                    trace_id=trace_id,
                    task_id=task_id,
                    step=step,
                    phase="bounded_loop",
                    decision=decision,
                    policy=policy,
                    observation=observation,
                    energy=energy,
                    stop_reason=stop_reason,
                )
            )

            if same_action_repeat > self.limits.max_same_action_repeat:
                stop_reason = "NO_PROGRESS_DETECTED"
                trace[-1]["stop_reason"] = stop_reason
                break
            if tool_failures >= self.limits.max_tool_failures:
                stop_reason = "TOOL_FAILURE_BACKOFF"
                trace[-1]["stop_reason"] = stop_reason
                break
            if energy.suggestion == "replan" and stop_reason == "DONE":
                replan_count += 1
                if replan_count > self.limits.max_replans:
                    stop_reason = "MAX_REPLANS_REACHED"
                    trace[-1]["stop_reason"] = stop_reason
                    break
                continue
            if energy.suggestion == "stop":
                stop_reason = "NO_PROGRESS_DETECTED"
                trace[-1]["stop_reason"] = stop_reason
                break
            break

        if last_decision is None or last_observation is None:
            last_decision = ManagerDecision("無法建立計畫。", "explain", "none", {})
            last_observation = Observation(False, "none", "Provider unavailable or no decision produced.")
            stop_reason = "PROVIDER_UNAVAILABLE"

        answer = self.worker.respond(user_text, last_decision, last_observation)
        return {
            "answer": answer,
            "decision": {
                "plan": last_decision.plan,
                "worker": last_decision.worker,
                "tool": last_decision.tool,
                "args": dict(last_decision.args),
            },
            "observation": {
                "ok": last_observation.ok,
                "tool": last_observation.tool,
                "content": last_observation.content,
                "formatted": last_observation.format(),
            },
            "trace": trace,
            "stop_reason": stop_reason,
            "loop": {
                "max_steps": self.limits.max_steps,
                "max_replans": self.limits.max_replans,
                "max_tool_failures": self.limits.max_tool_failures,
                "max_same_action_repeat": self.limits.max_same_action_repeat,
                "steps": len(trace),
                "replans": replan_count,
                "tool_failures": tool_failures,
            },
        }

    def _trace_entry(
        self,
        *,
        trace_id: str,
        task_id: str,
        step: int,
        phase: str,
        decision: ManagerDecision,
        policy: PolicyResult,
        observation: Observation,
        energy: EnergyResult,
        stop_reason: StopReason,
    ) -> dict:
        return {
            "trace_id": trace_id,
            "task_id": task_id,
            "step": step,
            "phase": phase,
            "agent": decision.worker,
            "model": "configured-provider",
            "input_summary": decision.plan[:240],
            "decision": "use_tool" if decision.tool != "none" else "ask_user",
            "reason": decision.plan,
            "tool_call": {"name": decision.tool, "args": dict(decision.args)},
            "routing": {
                "execution_mode": policy.execution_mode,
                "executor": policy.executor,
                "template_id": policy.template_id,
                "reason": policy.reason,
            },
            "policy": {
                "risk": policy.risk,
                "decision": policy.decision,
                "reason": policy.reason,
                "requires_approval": policy.requires_approval,
                "capability": policy.capability,
            },
            "observation": {
                "status": "ok" if observation.ok else "failed",
                "summary": observation.content[:500],
                "raw_ref": None,
            },
            "energy": {
                "value": energy.value,
                "uncertainty": energy.uncertainty,
                "repetition": energy.repetition,
                "tool_failure": energy.tool_failure,
                "no_progress": energy.no_progress,
                "trend": energy.trend,
                "suggestion": energy.suggestion,
            },
            "stop_reason": stop_reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
