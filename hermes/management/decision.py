from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from hermes.core.types import ToolResult


RiskLevel = Literal["low", "medium", "high", "requires_user_approval", "reject"]
StepType = Literal["read", "analyze", "generate", "write", "test", "verify", "reply"]


@dataclass
class DecisionPacket:
    task: str
    intent: str
    risk_level: RiskLevel
    requires_tools: bool
    requires_write: bool
    requires_user_approval: bool
    requires_mcp: bool = False
    external_tool_risk: str = "none"
    success_criteria: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)

    @property
    def rejected(self) -> bool:
        return self.risk_level == "reject"


@dataclass
class ExecutionStep:
    id: str
    type: StepType
    tool: str | None
    args: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    expected: str = ""


@dataclass
class ManagedTaskPlan:
    decision: DecisionPacket
    steps: List[ExecutionStep]
    verification_steps: List[ExecutionStep] = field(default_factory=list)


@dataclass
class AuditResult:
    verified: bool
    failed_criteria: List[str] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)
    final_status: str = "DONE"


@dataclass
class ExecutionResult:
    ok: bool
    plan: ManagedTaskPlan
    step_results: List[tuple[ExecutionStep, ToolResult]] = field(default_factory=list)
    audit: AuditResult | None = None
    error: str = ""

    def combined_tool_content(self) -> str:
        blocks = []
        for step, result in self.step_results:
            content = result.content or result.summary or result.error or ""
            blocks.append(f"[{step.id}] {step.tool}: {content}")
        return "\n\n".join(blocks)
