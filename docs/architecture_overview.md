# Hermes Architecture Overview

## Positioning

Hermes is a local-first managed AI Agent OS. Its purpose is to turn user intent into governed execution with observable evidence.

Hermes is not:

- a plain chatbot
- a simple Ollama frontend
- a prompt collection
- a decorative dashboard

Hermes is:

```text
User intent -> managed decision -> governed execution -> verified deliverable
```

## Top-Level Flow

```text
User Command
  ↓
Dashboard / API
  ↓
Hermes Runtime
  ↓
Management Decision Layer
  ├─ L1 Executive Director
  ├─ L2 Strategy Manager
  ├─ L3 Operator Worker
  └─ L4 Auditor / Verifier
  ↓
Risk Gate / Policy Engine
  ↓
ToolRegistry
  ├─ Built-in SafeExecutor tools
  ├─ Patch-Gated Runtime tools
  ├─ Governed Shell proposals
  └─ MCP Gateway tools
  ↓
ToolResult
  ↓
Trace Timeline
  ↓
Verification / Report
  ↓
Memory / Skill Candidate
```

## Runtime Core

`hermes/core/runtime.py` should remain a lifecycle coordinator. It should not contain protocol details, large prompt templates, UI formatting, or patch logic.

Runtime responsibilities:

- initialize dependencies
- manage state transitions
- call management orchestrator
- execute approved plans through ToolRegistry
- collect tool results
- expose status and trace

Runtime should delegate:

- risk classification to management policy
- MCP protocol to `hermes/mcp/`
- filesystem and patch execution to `hermes/harness/`
- audit decisions to `hermes/management/auditor.py`
- display rendering to dashboard assets

## Management Layer

The Management Layer separates authority from execution.

| Component | Purpose |
| --- | --- |
| `decision.py` | Defines `DecisionPacket`, `ExecutionStep`, `ManagedTaskPlan` |
| `policy.py` | Deterministic risk and permission classification |
| `orchestrator.py` | Converts decisions into executable steps |
| `auditor.py` | Verifies evidence and policy compliance |

This prevents the model from directly deciding and executing high-risk operations in one opaque step.

## Tool Layer

Hermes tools are accessed through `ToolRegistry`. Operators should not know whether a tool is built-in, patch-gated, shell-governed, or MCP-backed.

Tool classes:

1. Built-in safe tools:
   - read file
   - list files
   - grep/search
   - run tests

2. Patch-gated tools:
   - propose patch
   - approve patch
   - apply approved patch
   - rollback patch

3. Governed shell tools:
   - propose shell command
   - approve shell command
   - execute approved shell command

4. MCP tools:
   - `mcp.<server>.<tool>`
   - classified before registration
   - traced before and after execution

## MCP Layer

MCP is an external tool protocol, not a governance system.

Correct relationship:

```text
MCP extends ToolRegistry.
Hermes governs MCP.
MCP never governs Hermes.
```

MCP responsibilities:

- load `hermes_mcp.json`
- start enabled stdio servers
- initialize servers
- discover tools
- classify tool permissions
- register safe tools into ToolRegistry
- convert MCP responses into ToolResult
- emit MCP trace events

## Memory and Skill Evolution

Memory and skills should be explicit and reviewable.

Suggested structure:

```text
memory/
  user.md
  project.md
  conventions.md
  decisions.md
  execution_history.md

skills/
  test-audit.md
  mcp-integration.md
  patch-review.md
  project-generator.md
```

Memory is for stable context and preferences. Skills are reusable procedures derived from verified successful workflows.

## Dashboard as Workbench

The Dashboard should prioritize execution clarity:

1. Reply first.
2. Decision visible.
3. Evidence on demand.
4. Approval prominent.
5. Failure loud.

The UI should help the user answer:

- What did Hermes decide?
- What did Hermes execute?
- What evidence proves it?
- What failed?
- What needs my approval?

