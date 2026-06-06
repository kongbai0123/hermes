# Hermes Hybrid Execution Gateway Design

## 1. Purpose

This document defines the **Hermes Governed Hybrid Execution Gateway** for Agent Work Skill execution.

The goal is not to decide whether MCP or CLI is better. The goal is to give Hermes a governed execution layer that can automatically choose between local CLI execution, MCP tools, approval, plan-only handling, or denial based on risk, speed, token cost, side effects, and external authority boundaries.

```text
Hermes Agent Work Skill
= WorkIntent
+ WorkSkillRouter
+ PolicyGate
+ CLI Template Registry
+ MCP Governed Adapter
+ Observation Summarizer
+ Trace Recorder
```

Short definition:

```text
Hermes Agent Work Skill is a PolicyGate-governed hybrid execution layer:
CLI provides fast local agent work capability,
MCP provides external service and credential-boundary capability,
Hermes controls routing, approval, trace, stop reason, and bounded loop behavior.
```

## 2. Design Goals

The execution layer must support agent work across engineering tasks, file inspection, tests, network lookup, browser operation, and external service actions while preserving:

- speed
- low token cost
- safety
- auditability
- interruptibility
- replayability
- authorization

The core design is:

```text
CLI is the local executor.
MCP is the external service protocol boundary.
Hermes is the controller and safety authority.
```

## 3. Non-Goals

This document does not:

- implement runtime code
- replace the BoundedLoopController
- allow arbitrary shell execution
- make MCP wrap every local operation
- bypass PolicyGate
- bypass approval
- expose raw command output directly to the model by default
- reinterpret Hermes governance status inside MCP bridge tools
- implement commit, push, external service writes, or package installs

## 4. Architecture Overview

High-level flow:

```text
User Task
  ↓
BoundedLoopController
  ↓
Planner
  ↓
Processor
  ↓
Work Skill Router
  ↓
PolicyGate
  ├─ CLI Fast Path
  ├─ CLI Sandboxed Path
  ├─ MCP Governed Path
  ├─ Approval Required
  └─ Denied
  ↓
Executor / MCP Bridge
  ↓
Observation Summarizer
  ↓
Trace Recorder
  ↓
EnergyMonitor
  ↓
Stop / Replan / Continue / Ask User
```

The key component is the **Work Skill Router**. It converts a planned work action into an execution decision:

```text
cli_fast
cli_sandboxed
mcp_governed
approval_required
denied
plan_only
```

## 5. CLI Role

CLI must not be treated as a free shell. In Hermes it is a:

```text
Governed Local Command Executor
```

CLI execution is allowed only through registered, classified, parameter-limited command templates.

CLI is appropriate for:

- reading local files
- listing directories
- searching text
- running tests
- type checks
- lint checks
- git status
- git diff
- local build checks
- formatter checks

CLI is not appropriate for:

- arbitrary shell strings
- delete operations
- unbounded file modification
- unknown remote scripts
- reading secrets
- package installation
- external network requests
- automatic commit or push

## 6. MCP Role

MCP must not wrap every local task. In Hermes it is a:

```text
Governed External Tool Protocol
```

MCP is appropriate for:

- GitHub
- Gmail
- Google Calendar
- Google Drive
- browser automation
- proxy fetch
- external APIs
- credential-boundary tools
- cross-process or cross-service tools

MCP is not appropriate for:

- every local file read
- every grep/search
- every pytest run
- every npm check
- small local steps with high-volume observations

Using MCP for all local work would increase latency, token usage, trace noise, and schema exposure.

## 7. Execution Modes

Hermes should define the following execution modes:

```text
ExecutionMode:
  PLAN_ONLY
  CLI_FAST
  CLI_SANDBOXED
  MCP_GOVERNED
  APPROVAL_REQUIRED
  DENIED
```

### 7.1 PLAN_ONLY

Use when Hermes should plan but not execute.

Examples:

- refactor an entire project
- optimize all code
- remove unused files
- unclear or high-risk requests

PLAN_ONLY produces a plan and success criteria before any tool execution.

### 7.2 CLI_FAST

Use for local, low-risk, read-only, repeatable, low-token operations.

Examples:

- `read_file`
- `list_files`
- `search_text`
- `git status --short`
- `git diff --stat`
- `pytest -q`
- `npm run check`
- `tsc --noEmit`

Restrictions:

- no writes
- no deletes
- no network
- no secrets
- no arbitrary shell
- fixed timeout
- bounded output

### 7.3 CLI_SANDBOXED

Use for local execution that may create temporary files or build artifacts.

Examples:

- `npm run build`
- `python -m build`
- compile checks
- simulated patch in a temp workspace
- sandboxed artifact generation

Restrictions:

- explicit working directory
- fixed timeout
- bounded output
- restricted writable paths
- side effects declared in trace

### 7.4 MCP_GOVERNED

Use for external tools, credentials, network, browser, and service APIs.

Examples:

- GitHub issue / PR / repository work
- Gmail
- Calendar
- Drive
- browser automation
- proxy fetch
- external APIs

Restrictions:

- preserve Hermes governance payload
- preserve `trace_id`
- preserve status, risk, approval, and metadata
- MCP bridge must not reinterpret Hermes task status

### 7.5 APPROVAL_REQUIRED

Use for actions with side effects that may be reasonable after explicit user authorization.

Examples:

- write file
- apply patch
- git commit
- git push
- run command with write effects
- install package
- open non-allowlisted domain
- network fetch
- database migration

Approval prompt must state:

- what will be executed
- why it is needed
- impact scope
- rollback possibility
- risk level

### 7.6 DENIED

Use for clearly dangerous, unauthorized, or unacceptable actions.

Examples:

- read `.env`
- read private keys
- exfiltrate secrets
- `rm -rf`
- format disk
- `curl unknown.sh | sh`
- disable safety policy
- bypass PolicyGate

## 8. Work Skill Router

Planner or Processor must produce a `WorkIntent` before tool execution.

Example:

```json
{
  "intent_id": "intent_001",
  "task_goal": "verify current test status",
  "requested_action": "run tests",
  "tool_candidate": "run_command",
  "args": {
    "command": "python -m pytest tests -q"
  },
  "data_scope": "workspace",
  "side_effect": "none",
  "network": false,
  "writes_files": false,
  "reads_secrets": false,
  "external_account": false,
  "reversible": true,
  "expected_output": "test summary"
}
```

Router output is a decision, not execution:

```json
{
  "execution_mode": "CLI_FAST",
  "risk": "low",
  "decision": "allow",
  "reason": "read-only local verification command",
  "requires_approval": false,
  "executor": "cli_template",
  "template_id": "pytest_quiet"
}
```

Network example:

```json
{
  "execution_mode": "MCP_GOVERNED",
  "risk": "network",
  "decision": "approval_required",
  "reason": "proxy_fetch crosses network boundary",
  "requires_approval": true,
  "executor": "mcp_bridge",
  "tool": "proxy_fetch"
}
```

## 9. CLI Template Registry

The registry prevents unsafe free-shell execution.

Hermes must not allow:

```text
run_command("free shell string")
```

Hermes should allow:

```text
template_id + validated params
```

Template example:

```json
{
  "template_id": "pytest_quiet",
  "description": "Run pytest in quiet mode against a target path.",
  "command": ["python", "-m", "pytest", "{target}", "-q"],
  "allowed_params": {
    "target": {
      "type": "path",
      "default": "tests",
      "must_be_within_workspace": true
    }
  },
  "risk": "low",
  "execution_mode": "CLI_FAST",
  "writes_files": false,
  "network": false,
  "timeout_sec": 90,
  "max_output_chars": 4000
}
```

Recommended first templates:

- `read_file`
- `list_files`
- `search_text`
- `git_status`
- `git_diff`
- `pytest_quiet`
- `npm_check`
- `npm_lint`
- `tsc_no_emit`
- `python_module_readonly`

Allowed command examples:

```text
python -m pytest tests -q
npm run check
npm run lint
git status --short
git diff --stat
git diff -- src/
```

Do not include:

```text
rm
del
move
mv
cp
curl
wget
ssh
scp
powershell -Command unrestricted
cmd /c unrestricted
pip install
npm install
git push
git commit
```

## 10. MCP Tool Contract

MCP tools should pass through Hermes governance results. `isError` should describe MCP bridge failure, not the Hermes governance outcome.

Completed result:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"ok\":true,\"status\":\"completed\",\"trace_id\":\"trace_abc\",\"result\":{}}"
    }
  ],
  "isError": false
}
```

Approval-required result:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"ok\":false,\"status\":\"approval_required\",\"proposal_id\":\"proposal_001\",\"trace_id\":\"trace_abc\"}"
    }
  ],
  "isError": false
}
```

MCP is appropriate for:

- `github_search`
- `github_create_issue`
- `github_create_pr`
- `gmail_search`
- `calendar_create_event`
- `drive_fetch_doc`
- `proxy_fetch`
- `open_browser`
- `browser_click`
- `browser_extract`

Browser and proxy fetch paths must distinguish:

- allowlisted domain
- non-allowlisted domain
- credential boundary
- network risk

## 11. PolicyGate Model

Risk levels:

```text
none
low
medium
high
destructive
credential
network
external_state
```

Capability levels:

```text
L0_PLAN_ONLY
L1_READ_ONLY
L2_LOCAL_VERIFY
L3_PATCH_PROPOSAL
L4_APPROVED_WRITE
L5_EXTERNAL_GOVERNED
```

Capability mapping:

| Capability | Allows |
| --- | --- |
| `L0_PLAN_ONLY` | planning only, no tools |
| `L1_READ_ONLY` | read_file, list_files, search_text |
| `L2_LOCAL_VERIFY` | pytest, npm check, git status, git diff |
| `L3_PATCH_PROPOSAL` | generate diff or patch proposal without applying |
| `L4_APPROVED_WRITE` | write/apply_patch after approval |
| `L5_EXTERNAL_GOVERNED` | MCP/browser/network after approval or allowlist |

## 12. Routing Decision Table

| Task | Channel | Reason |
| --- | --- | --- |
| Read README | `CLI_FAST` | local read-only |
| Search `BoundedLoopController` | `CLI_FAST` | local read-only |
| Run `pytest -q` | `CLI_FAST` | local repeatable verification |
| Run `npm run check` | `CLI_FAST` | local repeatable verification |
| View `git diff` | `CLI_FAST` | read-only repository inspection |
| Generate patch | `PLAN_ONLY` / `PATCH_PROPOSAL` | do not directly modify |
| Apply patch | `APPROVAL_REQUIRED` | writes files |
| Commit | `APPROVAL_REQUIRED` | changes repository state |
| Push | `APPROVAL_REQUIRED` / `MCP_GOVERNED` | external state change |
| GitHub issue | `MCP_GOVERNED` | external service |
| Gmail | `MCP_GOVERNED` | credential boundary |
| Calendar | `MCP_GOVERNED` | credential boundary |
| Proxy fetch | `MCP_GOVERNED` / `APPROVAL_REQUIRED` | network boundary |
| Open allowlisted browser domain | `MCP_GOVERNED` | browser allowlist |
| Open unknown browser domain | `APPROVAL_REQUIRED` | browser/network risk |
| Read `.env` | `DENIED` | secrets |
| Delete folder | `DENIED` / `APPROVAL_REQUIRED` | destructive |
| `curl unknown.sh \| sh` | `DENIED` | remote code execution |

## 13. Observation Summarization

CLI and MCP outputs must be summarized before model consumption.

Executor result:

```json
{
  "status": "ok",
  "summary": "13 tests passed in 2.31s",
  "raw_ref": "trace/raw/pytest_001.log",
  "truncated": false,
  "metrics": {
    "exit_code": 0,
    "duration_ms": 2310,
    "output_chars": 420
  }
}
```

Failure result:

```json
{
  "status": "failed",
  "summary": "1 failed: tests/test_policy.py::test_proxy_fetch_requires_approval",
  "raw_ref": "trace/raw/pytest_002.log",
  "truncated": true,
  "top_errors": [
    "AssertionError: expected approval_required, got allow"
  ],
  "metrics": {
    "exit_code": 1,
    "duration_ms": 5100,
    "output_chars": 4000
  }
}
```

Recommended observation budget:

```text
max_observation_chars = 2000
max_error_lines = 50
max_file_preview_lines = 120
max_trace_raw_size = 1MB
```

When output exceeds budget:

```text
output truncated; see raw_ref
```

## 14. Trace Schema

Every routing, policy, execution, summary, energy, and stop decision should enter trace.

```json
{
  "trace_id": "trace_001",
  "task_id": "task_001",
  "step": 3,
  "phase": "execution",
  "work_intent": {
    "requested_action": "run tests",
    "tool_candidate": "run_command"
  },
  "routing": {
    "execution_mode": "CLI_FAST",
    "executor": "cli_template",
    "template_id": "pytest_quiet",
    "reason": "read-only local verification"
  },
  "policy": {
    "risk": "low",
    "decision": "allow",
    "requires_approval": false
  },
  "execution": {
    "status": "ok",
    "summary": "13 passed",
    "raw_ref": "trace/raw/pytest_001.log"
  },
  "energy": {
    "value": 0.22,
    "trend": "down",
    "repetition": 0.0,
    "tool_failure": 0.0,
    "no_progress": 0.1
  },
  "stop_reason": null
}
```

## 15. Unified API Shape

Future runtime implementation can expose one conceptual entry point:

```python
execute_work_intent(intent: WorkIntent) -> WorkExecutionResult
```

Flow:

```text
WorkIntent
  ↓
WorkSkillRouter
  ↓
PolicyGate
  ↓
ExecutorBackend
  ↓
ObservationSummarizer
  ↓
TraceRecorder
  ↓
WorkExecutionResult
```

WorkIntent:

```json
{
  "goal": "verify repository health",
  "action_type": "local_verify",
  "tool_candidate": "run_tests",
  "params": {
    "target": "tests"
  },
  "constraints": {
    "read_only": true,
    "network": false,
    "writes_files": false,
    "requires_credentials": false
  }
}
```

WorkExecutionResult:

```json
{
  "ok": true,
  "status": "completed",
  "execution_mode": "CLI_FAST",
  "policy_decision": "allow",
  "summary": "13 tests passed",
  "raw_ref": "trace/raw/pytest_001.log",
  "next_recommendation": "continue"
}
```

## 16. Implementation Phases

### Phase 1: Design and Documentation

Deliverable:

```text
docs/hybrid_execution_gateway.md
```

Scope:

- CLI / MCP responsibilities
- ExecutionMode
- PolicyGate routing
- CLI Template Registry
- MCP governed path
- Trace schema
- Observation budget
- Risk table
- Capability levels

### Phase 2: CLI Template Registry

Add or organize:

- `CommandTemplateRegistry`
- `SafeCommandExecutor`
- `ExecutionMode`
- `WorkIntent`
- `WorkExecutionResult`

Initial templates:

- pytest
- npm check
- git status
- git diff
- search_text
- read_file
- list_files

### Phase 3: MCP Governed Adapter

Add governed external paths:

- proxy_fetch
- open_browser
- GitHub
- external service adapters
- approval_required handling
- pass-through governance payload

## 17. Final Principles

Hermes Agent Work Skill should follow these rules:

1. Low-risk local tasks use `CLI_FAST`.
2. CLI must be template-based; no free shell.
3. External service and credential boundaries use `MCP_GOVERNED`.
4. Network, write, patch, and destructive actions require approval unless explicitly allowlisted.
5. Secrets and clearly dangerous actions are denied.
6. Every result enters trace.
7. Raw output is not sent directly to the model; use `summary + raw_ref`.
8. MCP must not reinterpret Hermes governance status.

