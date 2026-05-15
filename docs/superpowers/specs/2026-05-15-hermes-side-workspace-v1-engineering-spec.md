# Hermes Side Workspace v1 Engineering Spec

## 1. Product Positioning

Hermes Side Workspace v1 is the engineering realization of a chat-first AI execution workbench.

Its purpose is not to replace Hermes chat, nor to become a full work-management platform. Its purpose is to turn chat-driven work into structured runtime objects that can be tracked, inspected, saved, and reused.

Core chain:

```text
Conversation -> Task -> Trace -> Memory / Skill
```

## 2. Goals and Non-Goals

### Goals

- Support task creation from chat.
- Stream execution evidence into a structured trace timeline.
- Allow trace-derived records to be saved as memory.
- Allow successful task traces to be promoted into a skill draft.
- Keep package boundaries clear so the workspace can be embedded into Hermes dashboard without becoming dashboard-only code.
- Keep lightweight governance visible and actionable.

### Non-Goals

- Full project-management surface
- Full document platform
- Full approval orchestration engine
- Multi-user permissions model
- Team chat or collaboration platform
- MCP marketplace UX

## 3. Packaging Strategy

Packaging model:

```text
independent package first
+ dashboard embeddable later
```

Implementation consequences:

1. Core workspace models and events live in reusable packages.
2. Dashboard integration happens through a host bridge layer.
3. UI panels consume shared state and events rather than calling each other directly.
4. The existing HTML/JS dashboard is treated as a host shell, not as the owner of workspace logic.

## 4. UX Model

### Layout

```text
┌───────────────────────────────┬────────────────────────────┐
│                               │ Task Summary               │
│        Hermes Chat            │ -------------------------  │
│                               │ [Trace] [Memory]           │
│                               │ selected panel content     │
└───────────────────────────────┴────────────────────────────┘
```

### Interaction Mode

v1 uses a hybrid side workspace:

- task summary always visible
- `Trace` and `Memory` rendered as tabs below

Rationale:

- users keep current task context visible
- trace and memory do not compete for vertical space
- host integration stays simple for the current dashboard

## 5. Core Panels

### Task Panel

Responsibilities:

- display current task summary
- show steps and per-step status
- show completion conditions
- show risk tags
- show approval state

### Trace Panel

Responsibilities:

- render execution timeline
- show event source and event outcome
- show tool calls and verification steps
- group events by task and optionally by step

### Memory Panel

Responsibilities:

- display saved memory records
- preview Markdown content
- save project, user, decision, and skill memory

## 6. Data Lifecycle

The v1 lifecycle is:

```text
Conversation Event
-> Task Candidate
-> Confirmed Task
-> Trace Stream
-> Verified Result
-> Memory Record
-> Skill Draft
-> Archived Artifact
```

### Lifecycle States

#### Task Lifecycle

- `draft`
- `confirmed`
- `running`
- `waiting_approval`
- `blocked`
- `done`
- `failed`
- `archived`

#### Trace Lifecycle

- `open`
- `recording`
- `verified`
- `saved`
- `archived`

#### Memory Lifecycle

- `draft`
- `saved`
- `promoted`
- `archived`

### Lifecycle Rules

1. A chat message may create zero or one task candidate.
2. A task candidate must be confirmed before it becomes a tracked task.
3. Trace recording starts only after a task enters `confirmed` or `running`.
4. Memory records can only be saved from verified or explicitly user-selected trace segments.
5. Skill drafts can only be promoted from a trace that has at least one successful execution path.

## 7. Data Model

### Task

```ts
type Task = {
  id: string;
  title: string;
  goal: string;
  lifecycle: "draft" | "confirmed" | "running" | "waiting_approval" | "blocked" | "done" | "failed" | "archived";
  status:
    | "TODO"
    | "IN_PROGRESS"
    | "WAITING_APPROVAL"
    | "BLOCKED"
    | "DONE"
    | "FAILED";
  steps: TaskStep[];
  doneWhen: string[];
  riskTags: RiskTag[];
  doNotTouch?: string[];
  currentStepId?: string;
  nextStepId?: string;
  approvalDecisionId?: string;
  createdAt: string;
  updatedAt: string;
};
```

### TaskStep

```ts
type TaskStep = {
  id: string;
  title: string;
  status: "TODO" | "IN_PROGRESS" | "DONE" | "FAILED" | "SKIPPED";
  order: number;
  evidenceTraceIds?: string[];
};
```

### TraceEvent

```ts
type TraceEvent = {
  id: string;
  taskId: string;
  stepId?: string;
  type: "PLAN" | "ACTION" | "RESULT" | "ERROR" | "VERIFY" | "RECOVER";
  content: string;
  source: "USER" | "ASSISTANT" | "TOOL" | "SYSTEM";
  toolName?: string;
  success?: boolean;
  timestamp: string;
  metadata?: Record<string, unknown>;
};
```

### Memory

```ts
type Memory = {
  id: string;
  lifecycle: "draft" | "saved" | "promoted" | "archived";
  type: "PROJECT" | "USER" | "DECISION" | "SKILL";
  title: string;
  content: string;
  contentPath?: string;
  sourceTaskId?: string;
  sourceTraceIds?: string[];
  createdAt: string;
  updatedAt: string;
};
```

### SkillDraft

```ts
type SkillDraft = {
  id: string;
  taskId: string;
  traceIds: string[];
  title: string;
  markdown: string;
  status: "DRAFT" | "READY_FOR_REVIEW" | "PROMOTED";
  createdAt: string;
};
```

### RiskTag

```ts
type RiskTag =
  | "FILE_WRITE"
  | "PRODUCTION_CHANGE"
  | "SECRET_ACCESS"
  | "DEPENDENCY_CHANGE"
  | "GIT_PUSH"
  | "DESTRUCTIVE_ACTION";
```

### ApprovalDecision

```ts
type ApprovalDecision = {
  id: string;
  taskId: string;
  requestedAction: string;
  riskTags: RiskTag[];
  decision: "APPROVED" | "REJECTED" | "REVISED";
  decidedBy: "USER";
  reason?: string;
  timestamp: string;
};
```

## 8. Command Model

Commands represent desired actions. They are not historical facts.

```ts
type WorkspaceCommand =
  | { type: "CREATE_TASK_FROM_CHAT"; messageId: string }
  | { type: "CONFIRM_TASK"; taskId: string }
  | { type: "START_TRACE"; taskId: string }
  | { type: "SAVE_TRACE"; taskId: string }
  | { type: "SAVE_MEMORY"; traceIds: string[]; memoryType: "PROJECT" | "USER" | "DECISION" | "SKILL" }
  | { type: "PROMOTE_TRACE_TO_SKILL"; taskId: string }
  | { type: "REQUEST_APPROVAL"; taskId: string }
  | { type: "APPLY_APPROVAL_DECISION"; taskId: string; decision: "APPROVED" | "REJECTED" | "REVISED"; reason?: string };
```

Command routing rules:

1. UI panels emit commands through the workspace host or event bus.
2. Commands are interpreted by workspace controllers or reducers.
3. Commands may yield zero or more events.
4. Panels never mutate sibling panel state directly.

## 9. Event Model

Events represent facts that already happened.

```ts
type WorkspaceEvent =
  | TaskCreatedEvent
  | TaskConfirmedEvent
  | TaskUpdatedEvent
  | TraceRecordedEvent
  | TraceVerifiedEvent
  | MemorySavedEvent
  | ApprovalRequestedEvent
  | ApprovalDecidedEvent
  | SkillDraftCreatedEvent;
```

Event handling rules:

1. Events must be append-only within a trace stream.
2. Event consumers may derive view state, but must not rewrite event history.
3. `TracePanel` is the primary UI consumer for runtime events.
4. `TaskPanel` consumes derived task state, not raw runtime logs.

## 10. Storage Strategy

v1 storage is file-backed and human-inspectable.

### Storage Targets

- Tasks: JSON
- Trace events: JSONL
- Memory records: Markdown plus sidecar metadata if needed
- Skill drafts: Markdown
- Approval decisions: JSON

### Proposed Layout

```text
.hermes/
├── tasks/
│   └── task_001.json
├── traces/
│   └── task_001.trace.jsonl
├── approvals/
│   └── approval_001.json
├── memory/
│   ├── project/
│   ├── user/
│   ├── decision/
│   └── skill/
└── skills/
    └── repo-test-diagnosis.skill.md
```

### Storage Notes

1. JSONL is preferred for trace because it is append-friendly.
2. Markdown is preferred for memory and skill drafts because users may want to read and edit them directly.
3. v1 should keep storage local-first and avoid requiring a database.
4. A future storage adapter may move tasks and traces into SQLite, but that is not a v1 requirement.

## 11. Host Bridge Layer

The current dashboard is HTML/JS based. A dedicated bridge layer is required to prevent direct coupling between legacy dashboard code and workspace packages.

### Proposed Bridge

```text
Current Dashboard
-> hermes-dashboard-bridge
-> workspace-core event bus
-> task / trace / memory panels
```

### Bridge Responsibilities

- convert current dashboard events into `WorkspaceCommand` or `WorkspaceEvent`
- expose a workspace mount point in the existing dashboard
- adapt current chat/tool/runtime signals into trace events
- prevent direct dependency from workspace packages onto `renderers.js` or `workspace.js`
- preserve the option to replace the host implementation later

### Initial Integration Reality

Current Hermes host files include:

- `hermes/api/dashboard.html`
- `hermes/api/static/renderers.js`
- `hermes/api/static/workspace.js`

v1 implementation should add a thin host bridge around this surface rather than expanding these files into the long-term workspace architecture.

## 12. API Contract

Minimum API surface:

```text
POST  /workspace/tasks
GET   /workspace/tasks
PATCH /workspace/tasks/:id

POST  /workspace/traces
GET   /workspace/traces?taskId=

POST  /workspace/memories
GET   /workspace/memories

POST  /workspace/skills/draft

POST  /workspace/approvals
POST  /workspace/approvals/:id/decision
```

### Response Conventions

All endpoints should return stable machine-readable envelopes:

```json
{
  "ok": true,
  "data": {}
}
```

Error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "STRING_CODE",
    "message": "Human-readable message"
  }
}
```

## 13. Lightweight Governance

v1 governance is intentionally narrow.

### Required Behaviors

- risky tasks may enter `WAITING_APPROVAL`
- risky tasks surface risk tags
- protected scope is visible to the user
- patch-plan-required flows are visible before execution

### Protected Action Examples

- delete file
- modify `.env`
- push to GitHub
- install package
- change production code

### Governance Persistence

When an approval request occurs, an `ApprovalDecision` record must be stored even if the decision is rejection.

## 14. Skill Promotion Rules

Trace promotion must not generate an underspecified skill draft.

### Minimum Required Sections

A promoted skill draft must include:

- `Purpose`
- `When to Use`
- `Inputs`
- `Steps`
- `Outputs`
- `Validation`
- `Failure Handling`

### Promotion Eligibility

Skill promotion is allowed only when:

1. the task has a successful path
2. the trace contains enough procedural detail
3. the user or system selects the relevant trace slice

## 15. Error and Recovery Policy

v1 must explicitly represent recovery behavior.

### Error Rules

1. Failed task execution must emit `ERROR` trace events.
2. Recovery attempts must emit `RECOVER` trace events.
3. Verification after recovery must emit `VERIFY` trace events.
4. UI must distinguish failed tasks from blocked tasks and approval-waiting tasks.

### Recovery Principles

- preserve trace history
- do not overwrite failed evidence
- show the latest task state separately from historical trace

## 16. Test Strategy

Testing must cover both package logic and host integration seams.

### Unit Tests

Required for:

- task lifecycle transitions
- command-to-event transformation
- trace event formatting
- skill promotion rules
- risk tag helpers
- approval decision logic

### Integration Tests

Required for:

- host bridge command/event translation
- chat-to-task creation flow
- trace persistence flow
- trace-to-memory save flow
- trace-to-skill draft flow

### UI Tests

Required for:

- task summary rendering
- tab switching between Trace and Memory
- empty states
- approval state display
- risk tag display

### File-System Tests

Required for:

- task JSON persistence
- trace JSONL append behavior
- Markdown memory save behavior
- skill draft save behavior

### Acceptance Tests

Required for:

1. user creates task from chat
2. Hermes executes and emits trace
3. trace is visible in workspace
4. trace can be saved as memory
5. successful trace can be promoted to skill draft
6. risky task enters approval flow without executing immediately

## 17. MVP Phases

### Phase A: Workspace Shell

- right-side shell
- task summary region
- tabs for `Trace` and `Memory`
- mock data
- local event viewer

### Phase B: Chat -> Task

- create task candidate from chat
- confirm task
- edit generated title / steps / doneWhen

### Phase C: Execution -> Trace

- emit and render `PLAN`, `ACTION`, `RESULT`, `ERROR`, `VERIFY`, `RECOVER`
- attach trace evidence to task steps

### Phase D: Trace -> Memory

- save decision
- save project memory
- save user rule
- save trace selection as markdown-backed record

### Phase E: Trace -> Skill

- promote verified trace into skill draft
- validate required sections
- persist markdown draft

## 18. Acceptance Criteria

This engineering spec is satisfied when:

1. `TaskStep` and approval records are first-class model elements.
2. commands and events are explicitly separated.
3. trace source and tool evidence are modeled.
4. storage layout is file-backed and defined.
5. host bridge responsibilities are isolated.
6. governance persistence exists for approval decisions.
7. testing covers lifecycle, host bridge, persistence, and promotion.

## 19. Initial Package Map

```text
packages/
├── workspace-core/
│   ├── src/types.ts
│   ├── src/commands.ts
│   ├── src/events.ts
│   ├── src/lifecycle.ts
│   └── src/index.ts
├── task-panel/
├── trace-panel/
├── memory-panel/
├── governance-core/
├── skill-promoter/
└── hermes-dashboard-bridge/
```

This package map is the intended implementation target for v1 package decomposition.
