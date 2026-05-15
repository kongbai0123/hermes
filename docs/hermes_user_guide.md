# Hermes User Guide

## What Hermes Is

Hermes is a local-first managed AI Agent OS. Its goal is to help users move from conversation to execution.

Traditional chatbot:

```text
User asks -> model answers
```

Hermes Agent OS:

```text
User asks -> Hermes plans -> tools execute -> results are verified -> user receives deliverable
```

## Why Local-First Matters

Local-first design gives users:

- visibility into files and memory
- control over tools and approvals
- lower dependency on opaque cloud workflows
- easier auditing
- stronger privacy boundaries

## Key Concepts

### Workspace

The workspace is where Hermes reads project files, creates isolated outputs, records reports, and stores execution evidence.

### Memory

Memory should be transparent and reviewable. Prefer Markdown files for durable memory:

- `user.md` for user preferences and identity
- `project.md` for project context
- `conventions.md` for coding and workflow standards
- `decisions.md` for durable architectural decisions

### Skills

Skills are reusable procedures captured from successful work.

A good skill contains:

- when to use it
- required inputs
- allowed tools
- denied tools
- exact procedure
- verification
- failure handling

### Profiles

Profiles separate identities, providers, credentials, memory, and workflows. This prevents personal, work, and project contexts from contaminating each other.

### Dashboard

The Dashboard is not decoration. It is a control surface for:

- command entry
- model/provider selection
- risk and approval status
- management chain visibility
- trace inspection
- tool result review
- patch and shell approvals
- MCP server and tool status

## How Hermes Should Execute a Task

1. Understand the command.
2. Decide intent, risk, and permission.
3. Plan execution steps.
4. Use tools through ToolRegistry.
5. Record trace events.
6. Verify output.
7. Reply with grounded results.
8. Optionally capture reusable skill or memory.

## Common Misunderstandings

| Misunderstanding | Correct View |
| --- | --- |
| Agent means fully autonomous | Good agents are governed and auditable |
| UI is only visual polish | UI is the intervention and monitoring loop |
| Memory can be hidden | Useful memory should be inspectable |
| Local model is always best | Local models trade privacy for speed and capability limits |
| More tools means better agent | Better governance makes tools useful |

## Seven-Day Adoption Path

| Day | Focus | Output |
| --- | --- | --- |
| D1 | Run Hermes locally | Start dashboard and send first command |
| D2 | Define memory | Create user/project memory files |
| D3 | Profile separation | Separate personal and project profiles |
| D4 | Tool execution | Run read-only workspace task |
| D5 | Patch governance | Review a patch proposal before applying |
| D6 | MCP exploration | Connect local read-only MCP tools |
| D7 | Audit workflow | Review trace, tool results, and reports |

## Recommended First Workflow

Ask Hermes:

```text
請讀取 README.md，整理目前專案定位、已完成能力、缺口，並列出下一步測試計畫。
```

Expected result:

- Hermes classifies the task as low or medium risk.
- Hermes reads files through governed tools.
- Hermes records Trace.
- Hermes replies with evidence.
- Hermes does not modify production code without approval.

