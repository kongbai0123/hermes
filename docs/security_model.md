# Hermes Security Model

## Security Goal

Hermes should become more capable without becoming uncontrolled.

The security model is based on separation:

```text
Decision != Execution
Planning != Permission
Tool availability != Tool approval
Trace != Trust unless verified
```

## Core Principles

```text
Management-first, Tool-second.
Safety-first, Autonomy-second.
Trace-first, Magic-second.
Patch-first, Shell-last.
Memory-first, Prompt-second.
Workbench-first, Dashboard-second.
```

## Risk Levels

| Risk | Examples | Default Action |
| --- | --- | --- |
| low | general answer, read-only file lookup, trace display | allow |
| medium | run tests, create isolated project workspace, read MCP | allow with trace |
| high | modify core files, propose code change, dependency change | proposal only |
| approval required | apply patch, execute shell, push git, external mutation | require approval |
| blocked | delete, unknown MCP, unrestricted shell, secret exfiltration | block |

## Risk Gate

Risk Gate is deterministic first. The LLM can explain context, but it must not be the final authority for permission.

Example:

```text
User asks to modify hermes/core/runtime.py
→ risk = high
→ direct write blocked
→ propose_patch only
```

## Approval Model

Actions that can mutate code, environment, external systems, or local machine state require proposal and approval.

Approval-required actions:

- apply patch
- run governed shell command
- install dependencies
- clone external code
- push or merge git branches
- create external issues or pull requests
- send email or messages
- publish, upload, or deploy

Approvals should include:

- proposal id
- target tool
- arguments
- risk level
- reason
- expected result
- expiration
- hash or freshness check when applicable

## Patch Governance

Patch flow:

```text
propose_patch
  ↓
diff preview
  ↓
approval token
  ↓
before_hash stale check
  ↓
apply_approved_patch
  ↓
run tests
  ↓
auditor verification
```

Patch rules:

- Do not apply unapproved patches.
- Do not silently rewrite unrelated files.
- Check source freshness before applying.
- Record all patch actions in Trace.
- Provide rollback where possible.

## Governed Shell

Shell should exist because practical engineering tasks require it:

- clone examples
- install packages
- run build/test/lint
- start dev servers
- inspect tooling

But shell must be governed:

```text
User request
  ↓
Executive risk decision
  ↓
ShellCommandProposal
  ↓
Approval
  ↓
Restricted execution
  ↓
Trace + Auditor
```

Shell is not allowed as raw model output. The model may request a shell action, but Hermes must convert it into a proposal and run it only through approved tools.

## MCP Governance

MCP tools are untrusted by default.

Rules:

1. Unknown MCP tools default blocked.
2. Read-only MCP tools may be enabled after classification.
3. Write, delete, shell, publish, upload, merge, or push tools require proposal or approval.
4. MCP tools must be registered as Hermes `ToolSpec`.
5. MCP calls must produce Hermes `ToolResult`.
6. MCP events must enter Trace.
7. MCP cannot bypass Management Layer.

## Trace and Audit

Trace should capture:

- user command
- decision packet
- planned steps
- tool calls
- tool results
- MCP events
- approval decisions
- auditor results
- final status

Auditor should verify:

- all required steps have results
- no tool exceeded permission
- high-risk actions used approval
- final reply is grounded in actual results
- tests or verification ran when required

## Memory Safety

Memory must remain reviewable and editable.

Recommended memory rules:

- Store stable preferences, conventions, and decisions.
- Avoid storing secrets.
- Avoid storing transient runtime state as long-term memory.
- Allow user review and correction.
- Version important memory changes.

