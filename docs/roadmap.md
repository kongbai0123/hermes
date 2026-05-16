# Hermes Agent OS Roadmap

## Product Direction

Hermes is not just a chatbot, Ollama frontend, or visual dashboard. It is a local-first managed Agent OS focused on governance, traceability, approval, memory, skills, and deliverable execution.

Reference direction:

- `nesquena/hermes-webui` demonstrates a lightweight Python + Vanilla JS web interface with no build step, a three-panel layout, workspace browsing, and persistent composer controls.
- `NousResearch/hermes-agent` positions Hermes as an agent that grows with persistent memory, self-improving skills, scheduled jobs, messaging integrations, provider flexibility, and MCP integration.

Hermes should absorb these ideas while keeping its own differentiator:

```text
Managed execution with Decision Layer + Risk Gate + Trace + Auditor + Patch Governance.
```

## Version Plan

| Version | Name | Goal |
| --- | --- | --- |
| V2.2 | Patch-Gated Runtime | Propose, review, approve, apply, and roll back controlled code changes |
| V2.3 | Management Decision Layer | Separate decision, planning, operation, and verification |
| V2.4 | Governed MCP Gateway | Connect external tools through ToolRegistry and policy gates |
| V2.5 | Workbench Dashboard | Make the UI a control console rather than a report wall |
| V3.0 | Local Agent OS | Persistent memory, skills, scheduling, MCP ecosystem, audited execution |

## V2.2: Patch-Gated Runtime

Goal:

```text
Hermes can propose modifications without silently changing source code.
```

Required capabilities:

- `propose_patch`
- diff preview
- approval token
- `apply_approved_patch`
- before-hash stale check
- rollback support
- patch governance tests

Completion criteria:

- Core file changes can be proposed but not directly applied.
- Unapproved patches cannot be applied.
- Apply flow validates source freshness before mutation.
- Rollback is available for approved patch flows.
- Tests cover proposal, approval, stale source, and rollback paths.

## V2.3: Management Decision Layer

Goal:

```text
Hermes becomes a managed multi-step agent instead of a one-shot tool caller.
```

Required capabilities:

- `DecisionPacket`
- `ExecutionStep`
- `ManagedTaskPlan`
- Executive Director
- Strategy Manager
- Operator Worker
- Auditor / Verifier
- deterministic Risk Gate

Completion criteria:

- Every task has intent, risk, permission, and success criteria.
- Every tool call has reason and expected outcome.
- Tool results are verified by Auditor.
- Dashboard displays the management chain.

## V2.4: Governed MCP Gateway

Goal:

```text
Hermes can use external MCP tools without letting MCP bypass governance.
```

Required capabilities:

- `hermes_mcp.json`
- `MCPStdioClient`
- `MCPGateway`
- MCP security classifier
- ToolRegistry bridge
- MCP trace events
- Dashboard MCP tab

Completion criteria:

- Hermes can discover MCP `tools/list`.
- Read-only MCP tools can be executed through Operator.
- Write, shell, delete, and unknown MCP tools are blocked or require approval.
- MCP calls enter Trace.
- Auditor checks MCP permission and execution evidence.

## V2.5: Workbench Dashboard

Goal:

```text
Hermes UI becomes a workbench for execution, oversight, and intervention.
```

Required layout:

```text
[ Command Input + Run / Mode / Risk ]

[ Hermes Reply / Console Output                  ][ Management Chain ]
[ Main output: scrollable, copyable, result-first ][ Executive        ]
[                                                   ][ Strategy         ]
[                                                   ][ Operator         ]
[                                                   ][ Auditor          ]
```

[ Trace ][ Tool Result ][ Patch Review ][ Files ][ MCP ][ Raw JSON ]
```

Completion criteria:

- Reply/result area is visually dominant.
- Management Chain is always visible but secondary.
- Trace and Tool Result are available on demand.
- Approval-required events become prominent.
- Failure states are loud and actionable.

## V3.0: Local Agent OS

Goal:

```text
Hermes becomes a full local-first managed agent operating system.
```

Required capabilities:

- persistent memory
- skill auto-capture
- scheduled tasks
- MCP ecosystem
- project workspaces
- profile isolation
- patch governance
- audited execution

Completion criteria:

- Hermes can accumulate usable memory across sessions.
- Successful workflows can become reusable skills.
- Scheduled jobs can run with traceable output.
- External tools are integrated through governed MCP.
- Project outputs are traceable, reviewable, and recoverable.

## Immediate Priority

1. Stabilize documentation: `AGENTS.md`, roadmap, architecture, security.
2. Keep Management Decision Layer as the central execution model.
3. Keep MCP governed through ToolRegistry, Risk Gate, and Auditor.
4. Expand Dashboard into a Workbench UI.
5. Add memory and skill evolution only after execution governance remains stable.

