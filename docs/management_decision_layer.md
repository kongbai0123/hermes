# Hermes Management Decision Layer

## Purpose

Management Decision Layer makes Hermes behave like a governed organization instead of a model directly calling tools.

It separates:

```text
decision -> planning -> operation -> verification
```

This is the core difference between a Tool Agent and a Managed Agent OS.

## Roles

| Layer | Role | Responsibility |
| --- | --- | --- |
| L1 | Executive Director | Define intent, risk, permissions, success criteria |
| L2 | Strategy Manager | Convert the decision into execution steps |
| L3 | Operator Worker | Execute tools through ToolRegistry |
| L4 | Auditor / Verifier | Validate evidence, permissions, and final reply |

## Data Structures

### DecisionPacket

```python
from dataclasses import dataclass, field

@dataclass
class DecisionPacket:
    task: str
    intent: str
    risk_level: str
    requires_tools: bool
    requires_write: bool
    requires_mcp: bool
    requires_user_approval: bool
    success_criteria: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    notes: dict = field(default_factory=dict)
```

### ExecutionStep

```python
from dataclasses import dataclass, field

@dataclass
class ExecutionStep:
    id: str
    type: str
    tool: str | None
    args: dict = field(default_factory=dict)
    reason: str = ""
    expected: str = ""
```

### ManagedTaskPlan

```python
from dataclasses import dataclass, field

@dataclass
class ManagedTaskPlan:
    decision: DecisionPacket
    steps: list[ExecutionStep] = field(default_factory=list)
    verification_steps: list[ExecutionStep] = field(default_factory=list)
```

## Risk Gate

Risk Gate should be deterministic before LLM interpretation.

Examples:

| User Intent | Risk | Route |
| --- | --- | --- |
| Ask a general question | low | answer directly |
| Read README | low | read-only tool |
| Run tests | medium | run_tests tool with trace |
| Create isolated project workspace | medium | workspace generator |
| Modify Hermes runtime | high | propose_patch only |
| Apply patch | approval required | approval flow |
| Shell install or git clone | approval required | shell proposal |
| Delete files | blocked | reject or require explicit approval |

## Execution Flow

```text
User Command
  ↓
Executive decision
  ↓
Strategy plan
  ↓
Operator executes each step
  ↓
Auditor verifies
  ↓
Final reply based on tool evidence
```

## Auditor Requirements

Auditor checks:

- each required step has a result
- tool permissions match risk level
- write/shell/MCP mutation used proposal or approval
- final answer cites actual result content
- tests or verification ran when required
- failures are not presented as success

## Dashboard Representation

Right-side Management Chain should show:

```text
Executive
Intent: create_project
Risk: medium
Approval: no

Strategy
Steps: 4
Fallback: enabled

Operator
Tool calls: 3/3
Status: done

Auditor
Verified: true
Failed criteria: 0
```

Management Chain is a trust mechanism. It should be visible, but the main reply remains the primary workspace.

