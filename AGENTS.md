# Hermes Agent Operating Guide

This file is the fast-load operating guide for AI agents working inside the Hermes repo. For broader product and architecture context, read the files under `docs/`.

## Mission

Hermes is a local-first managed AI Agent OS. It should turn user requests into traceable, governed, testable deliverables rather than unverified chat output.

Core position:

```text
LLM = CPU
Hermes = OS
Dashboard = workbench and intervention console
Trace = execution evidence
```

## Non-Negotiable Rules

1. Do not pretend certainty. If information is missing, state the assumption.
2. Prefer structured execution: plan, execute, verify, report.
3. Preserve user work. Do not delete or revert unrelated files.
4. Keep production changes small and testable.
5. High-risk actions require approval or proposal flow.
6. No trace means no trustworthy execution.
7. Do not let MCP, shell, write, delete, or network mutation bypass ToolRegistry, Risk Gate, Management Layer, or Auditor.

## Runtime Model

Hermes tasks should follow this state flow:

```text
IDLE -> ASKING -> PLANNING -> EXECUTING -> VERIFYING -> RECOVERING -> DONE
```

Every meaningful task should produce:

- User intent and assumptions.
- Risk classification.
- Execution steps with reasons and expected outcomes.
- Tool results.
- Auditor verification.
- Final reply grounded in actual results.

## Management Chain

Hermes uses four management roles:

| Layer | Role | Responsibility |
| --- | --- | --- |
| L1 | Executive Director | Intent, risk, permission, success criteria |
| L2 | Strategy Manager | Decompose task into steps |
| L3 | Operator Worker | Execute ToolRegistry tools |
| L4 | Auditor / Verifier | Verify output, check policy, flag gaps |

## Tool Policy

Use this priority order:

```text
Management-first, Tool-second.
Safety-first, Autonomy-second.
Trace-first, Magic-second.
Patch-first, Shell-last.
Memory-first, Prompt-second.
Workbench-first, Dashboard-second.
```

Allowed by default:

- Read-only workspace inspection.
- Safe file listing/searching.
- Unit tests and compile checks when they do not mutate production state.
- MCP read-only tools after classification.

Requires proposal or approval:

- Writes to source files.
- Patch application.
- Shell execution.
- External network mutation.
- Package installation.
- Git push, merge, delete, or release actions.

Blocked unless explicitly approved and governed:

- Delete operations.
- Raw unrestricted shell.
- Unknown MCP tools.
- Secret or model-file mutation.

## Documentation Map

- `docs/architecture_overview.md`: system architecture and data flow.
- `docs/security_model.md`: risk gate, approval, sandbox, audit model.
- `docs/roadmap.md`: version roadmap and execution priorities.
- `docs/mcp_integration_plan.md`: governed MCP client plan.
- `docs/management_decision_layer.md`: decision layer specification.
- `docs/hermes_user_guide.md`: human-facing Hermes Agent OS guide.

## Testing Expectation

Before claiming completion, run the most relevant tests. For broad changes, use:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

If tests fail, report:

- Exact command.
- Pass/fail result.
- Error summary.
- Minimal repair plan.

