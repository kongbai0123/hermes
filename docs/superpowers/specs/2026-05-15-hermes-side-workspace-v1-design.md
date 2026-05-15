# Hermes Side Workspace v1 Design

## Product Positioning

Hermes Side Workspace v1 is a chat-first AI execution workbench.

It keeps Hermes centered on question-and-answer interaction, then adds a side workspace that turns conversation into structured work artifacts:

- Conversation -> Task
- Task -> Trace
- Trace -> Memory / Skill

This is not a ClickUp clone, a full project-management suite, or a full governance console. It is a focused execution surface that makes AI work trackable, savable, and reusable.

## Goals

- Keep Hermes chat as the primary interaction surface.
- Add a side workspace that helps users inspect and manage task state.
- Persist execution traces in a structured, reusable form.
- Allow successful traces to be promoted into memory and skill drafts.
- Keep light governance guardrails visible without turning v1 into a heavy approval platform.
- Build the side workspace as an independent package first, then embed it into the dashboard.

## Non-Goals

The following are explicitly out of scope for v1:

- Full document management
- Full Kanban / sprint planning
- Full team collaboration / chat system
- Multi-tenant workspace administration
- Heavy approval workflow engine
- MCP marketplace management
- Full ClickUp-style project hierarchy

## Packaging Strategy

The packaging model for v1 is:

```text
independent package first
+ dashboard embeddable later
```

This means:

1. The side workspace is developed as a modular package set with clear internal boundaries.
2. Hermes dashboard acts as the host shell that mounts the workspace.
3. The same package boundaries can later support alternative shells, plugins, or embedded views without rewriting the feature as dashboard-only code.

## User Experience Model

### Primary Layout

```text
┌───────────────────────────────┬────────────────────────────┐
│                               │ Task Summary               │
│        Hermes Chat            │ -------------------------  │
│                               │ [Trace] [Memory]           │
│                               │ selected panel content     │
└───────────────────────────────┴────────────────────────────┘
```

The main chat remains the primary canvas. The right side workspace is secondary but persistent.

### Workspace Interaction Mode

v1 uses a hybrid interaction model:

- Task summary remains visible at the top of the side workspace.
- Trace and Memory are switched through tabs below.

This balances always-visible task context with constrained workspace width.

### Core Actions

The three most important user actions in v1 are:

1. `Save as Task`
2. `Save Trace`
3. `Promote to Skill`

These correspond directly to Hermes's core product chain:

```text
conversation -> task -> trace -> skill
```

## Core Panels

### Task Panel

Purpose: turn user intent from chat into a structured, trackable task.

Fields:

- title
- goal
- status
- steps
- doneWhen
- riskTags
- currentStep
- nextStep

Status model:

- `TODO`
- `IN_PROGRESS`
- `WAITING_APPROVAL`
- `BLOCKED`
- `DONE`
- `FAILED`

### Trace Panel

Purpose: show what Hermes did, why it did it, and what happened.

Event types:

- `PLAN`
- `ACTION`
- `RESULT`
- `ERROR`
- `VERIFY`
- `RECOVER`

The Trace panel is the runtime evidence surface for v1. It must be readable by humans and structured enough to be promoted into saved memory or skill drafts.

### Memory Panel

Purpose: preserve useful work outcomes in editable Markdown-backed records.

Memory types:

- `PROJECT`
- `USER`
- `DECISION`
- `SKILL`

Memory is not a passive archive. It is the bridge from one successful run to future reuse.

## Lightweight Governance Guard

v1 does not ship a full governance module. It includes four lightweight guardrails:

1. `WAITING_APPROVAL`
2. `riskTags`
3. `do-not-touch` scope display
4. `patch plan required`

These guardrails are embedded into task and trace state instead of presented as a separate heavy control plane.

### Risk Tags

Initial tag set:

- `FILE_WRITE`
- `PRODUCTION_CHANGE`
- `SECRET_ACCESS`
- `DEPENDENCY_CHANGE`
- `GIT_PUSH`
- `DESTRUCTIVE_ACTION`

### Protected Scope

The UI must support an explicit do-not-touch list such as:

- `.env`
- production config
- CI/CD config
- unrelated files

### Patch Plan Required

When a task requires modification, Hermes should prefer showing a patch-plan structure before final execution:

- problem
- root cause
- minimal patch
- affected files
- validation
- approval requirement

## Package Architecture

The package-first design for v1 is:

```text
packages/
├── workspace-core/
├── task-panel/
├── trace-panel/
├── memory-panel/
├── governance-core/
└── skill-promoter/
```

### `workspace-core`

Responsibilities:

- shared data types
- shared event types
- workspace state contract
- event bus interfaces

This package must not depend on UI rendering.

### `task-panel`

Responsibilities:

- task summary rendering
- task detail rendering
- task status controls
- step display
- completion criteria display

### `trace-panel`

Responsibilities:

- trace timeline rendering
- event grouping
- error / verify display
- event filtering by task

### `memory-panel`

Responsibilities:

- memory list
- memory detail view
- Markdown rendering / preview
- save actions from trace outputs

### `governance-core`

Responsibilities:

- risk tagging helpers
- approval-state helpers
- protected-scope helpers
- patch-plan contract

### `skill-promoter`

Responsibilities:

- trace-to-skill transformation
- draft markdown generation
- validation of minimum skill sections

## Dashboard Embedding Model

Hermes dashboard hosts the workspace rather than owning its internal logic.

Initial host responsibility:

- mount the side workspace shell
- pass chat-derived events into the workspace
- render workspace open/close state
- preserve visual consistency with existing dashboard theme

Target host file:

- `apps/hermes-dashboard/src/components/SideWorkspaceHost.tsx`

For the current codebase, this path is a future-state target rather than an existing file. The initial integration may need to bridge through the current `hermes/api/dashboard.html` surface before a React-based host exists.

## Event Model

Panels should not directly call one another. v1 uses a workspace event model.

### Workspace Event

```ts
type WorkspaceEvent =
  | TaskCreatedEvent
  | TaskUpdatedEvent
  | TraceRecordedEvent
  | MemorySavedEvent
  | ApprovalRequestedEvent
  | SkillDraftCreatedEvent;
```

### Trace Event

```ts
type TraceEvent = {
  id: string;
  taskId: string;
  type: "PLAN" | "ACTION" | "RESULT" | "ERROR" | "VERIFY" | "RECOVER";
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
};
```

## Data Model

### Task

```ts
type Task = {
  id: string;
  title: string;
  goal: string;
  status:
    | "TODO"
    | "IN_PROGRESS"
    | "WAITING_APPROVAL"
    | "BLOCKED"
    | "DONE"
    | "FAILED";
  steps: TaskStep[];
  doneWhen: string[];
  riskTags: string[];
};
```

### Memory

```ts
type Memory = {
  id: string;
  type: "PROJECT" | "USER" | "DECISION" | "SKILL";
  title: string;
  content: string;
  sourceTaskId?: string;
  sourceTraceIds?: string[];
  createdAt: string;
};
```

## API Contract

The minimum v1 API surface is:

```text
POST  /workspace/tasks
GET   /workspace/tasks
PATCH /workspace/tasks/:id

POST  /workspace/traces
GET   /workspace/traces?taskId=

POST  /workspace/memories
GET   /workspace/memories

POST  /workspace/skills/draft
```

These endpoints are intentionally narrow. They exist to support the side workspace flow rather than become a general project-management API.

## MVP Phases

### Phase A: Workspace Shell

Deliver:

- right-side workspace shell
- tab navigation
- empty states
- mock data
- local event viewer

Done when:

- Task / Trace / Memory UI can be shown without backend coupling

### Phase B: Chat -> Task

Deliver:

- `Save as Task`
- generated task title
- generated steps
- generated doneWhen
- manual editing

Done when:

- a user message can create an editable task candidate in the workspace

### Phase C: Execution -> Trace

Deliver:

- trace event recording
- event timeline rendering
- event grouping by task

Done when:

- each execution run produces a readable timeline

### Phase D: Trace -> Memory

Deliver:

- save trace as memory
- save decision
- save project memory
- save user rule

Done when:

- trace-derived Markdown records can be created and reviewed in the Memory panel

### Phase E: Trace -> Skill

Deliver:

- promote successful trace into skill draft
- generate markdown skill skeleton
- basic validation for required sections

Done when:

- a successful task flow can produce a reusable skill draft

## Technical Recommendations

### Frontend

- React
- TypeScript

Rationale:

- package boundaries are natural
- embeddable component model
- future SDK extraction is easier

### State Management

Use a lightweight solution in v1:

- Zustand, or
- reducer-based local state

Do not introduce a heavy state framework in the first iteration.

### Event Transport

Use an in-memory event bus first.

Potential future transports:

- WebSocket
- Server-Sent Events
- SQLite-backed event log

## Existing Codebase Fit

Current Hermes dashboard is still HTML/JS based:

- `hermes/api/dashboard.html`
- `hermes/api/static/renderers.js`
- `hermes/api/static/workspace.js`

This means the independent package boundary should be designed now, even if the first host integration requires a bridge layer before a React-native dashboard host exists.

v1 should avoid tightly coupling new workspace behavior to the current static renderer functions. If a bridge is needed, it should stay thin and host-oriented.

## Acceptance Criteria

The design is successful when:

1. Hermes remains chat-first.
2. Side Workspace exists as an independent modular surface.
3. Tasks can be created from chat.
4. Execution trace is visible and persisted as structured events.
5. Memory can be saved from trace outcomes.
6. Successful trace can be promoted into a skill draft.
7. Risky tasks can enter `WAITING_APPROVAL`.
8. The architecture stays package-first rather than becoming dashboard-only.

## Final Product Sentence

Hermes v1 is a chat-first AI execution workbench that lets users create tasks from conversation, inspect execution through trace, and preserve successful work as reusable memory and skill drafts.
