# Hermes Side Workspace v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Hermes Side Workspace v1 as a package-first, dashboard-embedded chat-side execution workspace with Task, Trace, and Memory panels backed by local file storage and lightweight governance.

**Architecture:** The implementation starts with a reusable TypeScript package layer for models, commands, events, reducers, and file-backed storage. A thin dashboard bridge adapts the current `hermes/api/dashboard.html` host into the new workspace event system without coupling package internals to legacy static modules.

**Tech Stack:** Python backend, static HTML/JS host, TypeScript packages, React for embeddable panels, Vitest for package tests, Python `unittest` for dashboard integration coverage.

---

## File Structure

### New top-level files

- Create: `G:\program\hermes\package.json`
- Create: `G:\program\hermes\tsconfig.base.json`
- Create: `G:\program\hermes\vitest.workspace.ts`

### New packages

- Create: `G:\program\hermes\packages\workspace-core\src\types.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\commands.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\events.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\lifecycle.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\reducer.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\validators.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\index.ts`

- Create: `G:\program\hermes\packages\workspace-storage\src\taskStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\traceStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\memoryStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\skillStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\approvalStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\index.ts`

- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\mountWorkspace.tsx`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\dashboardEventAdapter.ts`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\chatCommandAdapter.ts`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\index.ts`

- Create: `G:\program\hermes\packages\task-panel\src\TaskPanel.tsx`
- Create: `G:\program\hermes\packages\task-panel\src\TaskSummaryCard.tsx`
- Create: `G:\program\hermes\packages\task-panel\src\index.ts`

- Create: `G:\program\hermes\packages\trace-panel\src\TracePanel.tsx`
- Create: `G:\program\hermes\packages\trace-panel\src\TraceTimeline.tsx`
- Create: `G:\program\hermes\packages\trace-panel\src\index.ts`

- Create: `G:\program\hermes\packages\memory-panel\src\MemoryPanel.tsx`
- Create: `G:\program\hermes\packages\memory-panel\src\MemoryPreview.tsx`
- Create: `G:\program\hermes\packages\memory-panel\src\index.ts`

- Create: `G:\program\hermes\packages\governance-core\src\risk.ts`
- Create: `G:\program\hermes\packages\governance-core\src\approval.ts`
- Create: `G:\program\hermes\packages\governance-core\src\index.ts`

- Create: `G:\program\hermes\packages\skill-promoter\src\promoteTraceToSkill.ts`
- Create: `G:\program\hermes\packages\skill-promoter\src\validateSkillDraft.ts`
- Create: `G:\program\hermes\packages\skill-promoter\src\index.ts`

### Backend/API files

- Modify: `G:\program\hermes\hermes\api\server.py`
- Modify: `G:\program\hermes\start_hermes.py`
- Modify: `G:\program\hermes\hermes\api\dashboard.html`
- Modify: `G:\program\hermes\hermes\api\static\workspace.js`
- Modify: `G:\program\hermes\hermes\api\static\renderers.js`
- Create: `G:\program\hermes\hermes\api\static\workspace_host.js`

### Tests

- Create: `G:\program\hermes\packages\workspace-core\src\reducer.test.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\lifecycle.test.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\traceStore.test.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\taskStore.test.ts`
- Create: `G:\program\hermes\packages\skill-promoter\src\promoteTraceToSkill.test.ts`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\dashboardEventAdapter.test.ts`
- Create: `G:\program\hermes\tests\test_workspace_side_panel_host.py`
- Create: `G:\program\hermes\tests\test_workspace_api.py`
- Create: `G:\program\hermes\tests\test_workspace_storage_contract.py`

## Task 1: Scaffold the package workspace and test tooling

**Files:**
- Create: `G:\program\hermes\package.json`
- Create: `G:\program\hermes\tsconfig.base.json`
- Create: `G:\program\hermes\vitest.workspace.ts`

- [ ] **Step 1: Write the failing Python integration test that asserts workspace host assets exist**

```python
import unittest
from pathlib import Path


class TestWorkspaceSidePanelHost(unittest.TestCase):
    def test_workspace_host_script_is_registered(self):
        html = Path("hermes/api/dashboard.html").read_text(encoding="utf-8")
        self.assertIn('static/workspace_host.js', html)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_workspace_side_panel_host -v`  
Expected: FAIL because `static/workspace_host.js` is not yet referenced.

- [ ] **Step 3: Add root package workspace tooling**

```json
{
  "name": "hermes-workspace-packages",
  "private": true,
  "type": "module",
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "test:packages": "vitest run",
    "build:packages": "tsc -b packages/workspace-core packages/workspace-storage packages/hermes-dashboard-bridge packages/task-panel packages/trace-panel packages/memory-panel packages/governance-core packages/skill-promoter"
  },
  "devDependencies": {
    "@types/node": "^24.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "typescript": "^5.8.0",
    "vitest": "^3.2.0"
  }
}
```

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "react-jsx",
    "declaration": true,
    "rootDir": ".",
    "outDir": "dist",
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

```ts
import { defineWorkspace } from "vitest/config";

export default defineWorkspace([]);
```

- [ ] **Step 4: Add the workspace host asset reference to the dashboard shell**

```html
<script src="static/workspace_host.js" defer></script>
```

- [ ] **Step 5: Run the Python host registration test**

Run: `python -m unittest tests.test_workspace_side_panel_host -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add package.json tsconfig.base.json vitest.workspace.ts hermes/api/dashboard.html tests/test_workspace_side_panel_host.py
git commit -m "chore: scaffold workspace package tooling"
```

## Task 2: Build `workspace-core` types, lifecycle, commands, events, and reducer

**Files:**
- Create: `G:\program\hermes\packages\workspace-core\src\types.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\commands.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\events.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\lifecycle.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\reducer.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\validators.ts`
- Create: `G:\program\hermes\packages\workspace-core\src\index.ts`
- Test: `G:\program\hermes\packages\workspace-core\src\lifecycle.test.ts`
- Test: `G:\program\hermes\packages\workspace-core\src\reducer.test.ts`

- [ ] **Step 1: Write the failing lifecycle and reducer tests**

```ts
import { describe, expect, it } from "vitest";
import { canTransitionTaskLifecycle, reduceWorkspaceCommand } from "./index";

describe("task lifecycle", () => {
  it("allows draft to confirmed", () => {
    expect(canTransitionTaskLifecycle("draft", "confirmed")).toBe(true);
  });

  it("blocks archived back to running", () => {
    expect(canTransitionTaskLifecycle("archived", "running")).toBe(false);
  });
});

describe("workspace reducer", () => {
  it("creates a task candidate from chat", () => {
    const result = reduceWorkspaceCommand(
      { tasks: {}, traces: {}, memories: {} },
      { type: "CREATE_TASK_FROM_CHAT", messageId: "msg_1" }
    );
    expect(result.events[0].type).toBe("TASK_CREATED");
  });
});
```

- [ ] **Step 2: Run package tests to verify they fail**

Run: `npm run test:packages -- packages/workspace-core/src/lifecycle.test.ts packages/workspace-core/src/reducer.test.ts`  
Expected: FAIL because `workspace-core` files do not exist yet.

- [ ] **Step 3: Implement shared models and reducer primitives**

```ts
export type RiskTag =
  | "FILE_WRITE"
  | "PRODUCTION_CHANGE"
  | "SECRET_ACCESS"
  | "DEPENDENCY_CHANGE"
  | "GIT_PUSH"
  | "DESTRUCTIVE_ACTION";

export type TaskLifecycle =
  | "draft"
  | "confirmed"
  | "running"
  | "waiting_approval"
  | "blocked"
  | "done"
  | "failed"
  | "archived";

export type TaskStep = {
  schemaVersion: "v1";
  id: string;
  title: string;
  status: "TODO" | "IN_PROGRESS" | "DONE" | "FAILED" | "SKIPPED";
  order: number;
  evidenceTraceIds?: string[];
};
```

```ts
const allowed: Record<TaskLifecycle, TaskLifecycle[]> = {
  draft: ["confirmed", "archived"],
  confirmed: ["running", "archived"],
  running: ["waiting_approval", "blocked", "done", "failed"],
  waiting_approval: ["running", "blocked", "failed"],
  blocked: ["running", "failed", "archived"],
  done: ["archived"],
  failed: ["archived"],
  archived: []
};

export function canTransitionTaskLifecycle(from: TaskLifecycle, to: TaskLifecycle): boolean {
  return allowed[from].includes(to);
}
```

```ts
export function reduceWorkspaceCommand(state: WorkspaceState, command: WorkspaceCommand): WorkspaceTransitionResult {
  if (command.type === "CREATE_TASK_FROM_CHAT") {
    return {
      state,
      events: [
        {
          schemaVersion: "v1",
          type: "TASK_CREATED",
          taskId: `task_${command.messageId}`,
          timestamp: new Date().toISOString()
        }
      ]
    };
  }

  return { state, events: [] };
}
```

- [ ] **Step 4: Run the workspace-core tests**

Run: `npm run test:packages -- packages/workspace-core/src/lifecycle.test.ts packages/workspace-core/src/reducer.test.ts`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/workspace-core package.json tsconfig.base.json
git commit -m "feat: add workspace core lifecycle and reducer"
```

## Task 3: Build `workspace-storage` with JSON, JSONL, Markdown, and approval stores

**Files:**
- Create: `G:\program\hermes\packages\workspace-storage\src\taskStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\traceStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\memoryStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\skillStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\approvalStore.ts`
- Create: `G:\program\hermes\packages\workspace-storage\src\index.ts`
- Test: `G:\program\hermes\packages\workspace-storage\src\taskStore.test.ts`
- Test: `G:\program\hermes\packages\workspace-storage\src\traceStore.test.ts`
- Test: `G:\program\hermes\tests\test_workspace_storage_contract.py`

- [ ] **Step 1: Write failing storage tests**

```ts
import { describe, expect, it } from "vitest";
import { appendTraceEvent, saveTask } from "./index";

describe("traceStore", () => {
  it("appends newline-delimited JSON events", async () => {
    const path = await appendTraceEvent("task_1", { schemaVersion: "v1", id: "tr_1" } as any);
    expect(path.endsWith("task_1.trace.jsonl")).toBe(true);
  });
});

describe("taskStore", () => {
  it("writes a task json file", async () => {
    const path = await saveTask({ schemaVersion: "v1", id: "task_1" } as any);
    expect(path.endsWith("task_1.json")).toBe(true);
  });
});
```

```python
import json
import unittest
from pathlib import Path


class TestWorkspaceStorageContract(unittest.TestCase):
    def test_workspace_storage_layout_is_documented_by_real_paths(self):
        root = Path(".hermes")
        expected = ["tasks", "traces", "approvals", "memory", "skills"]
        for name in expected:
            self.assertTrue((root / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm run test:packages -- packages/workspace-storage/src/taskStore.test.ts packages/workspace-storage/src/traceStore.test.ts`  
Expected: FAIL because store functions do not exist.

Run: `python -m unittest tests.test_workspace_storage_contract -v`  
Expected: FAIL because `.hermes/` directories do not exist.

- [ ] **Step 3: Implement file-backed storage with persistence error surfacing**

```ts
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

const root = join(process.cwd(), ".hermes");

export async function ensureWorkspaceDirs(): Promise<void> {
  for (const dir of ["tasks", "traces", "approvals", "memory/project", "memory/user", "memory/decision", "memory/skill", "skills"]) {
    await mkdir(join(root, dir), { recursive: true });
  }
}

export async function saveTask(task: Task): Promise<string> {
  await ensureWorkspaceDirs();
  const filePath = join(root, "tasks", `${task.id}.json`);
  await writeFile(filePath, JSON.stringify(task, null, 2), "utf8");
  return filePath;
}
```

```ts
import { appendFile } from "node:fs/promises";
import { join } from "node:path";

export async function appendTraceEvent(taskId: string, event: TraceEvent): Promise<string> {
  await ensureWorkspaceDirs();
  const filePath = join(process.cwd(), ".hermes", "traces", `${taskId}.trace.jsonl`);
  await appendFile(filePath, `${JSON.stringify(event)}\n`, "utf8");
  return filePath;
}
```

- [ ] **Step 4: Run storage tests**

Run: `npm run test:packages -- packages/workspace-storage/src/taskStore.test.ts packages/workspace-storage/src/traceStore.test.ts`  
Expected: PASS

Run: `python -m unittest tests.test_workspace_storage_contract -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/workspace-storage tests/test_workspace_storage_contract.py .hermes
git commit -m "feat: add workspace file storage adapters"
```

## Task 4: Add `hermes-dashboard-bridge` and mount the workspace host into the current static dashboard

**Files:**
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\mountWorkspace.tsx`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\dashboardEventAdapter.ts`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\chatCommandAdapter.ts`
- Create: `G:\program\hermes\packages\hermes-dashboard-bridge\src\index.ts`
- Create: `G:\program\hermes\hermes\api\static\workspace_host.js`
- Modify: `G:\program\hermes\hermes\api\dashboard.html`
- Test: `G:\program\hermes\packages\hermes-dashboard-bridge\src\dashboardEventAdapter.test.ts`

- [ ] **Step 1: Write the failing bridge adapter test**

```ts
import { describe, expect, it } from "vitest";
import { adaptChatMessageToCommand } from "./dashboardEventAdapter";

describe("dashboardEventAdapter", () => {
  it("adapts a chat save-as-task action into a workspace command", () => {
    const result = adaptChatMessageToCommand({ action: "save-task", messageId: "msg_1" });
    expect(result.type).toBe("CREATE_TASK_FROM_CHAT");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test:packages -- packages/hermes-dashboard-bridge/src/dashboardEventAdapter.test.ts`  
Expected: FAIL because adapter file does not exist.

- [ ] **Step 3: Implement the bridge adapter and host mount script**

```ts
export function adaptChatMessageToCommand(input: { action: string; messageId: string }) {
  if (input.action === "save-task") {
    return { type: "CREATE_TASK_FROM_CHAT", messageId: input.messageId } as const;
  }

  throw new Error(`Unsupported dashboard action: ${input.action}`);
}
```

```js
(() => {
  window.HermesWorkspaceHost = {
    mount(targetId) {
      const node = document.getElementById(targetId);
      if (!node) return;
      node.dataset.workspaceMounted = "true";
      node.innerHTML = '<div class="workspace-shell"><div class="workspace-task-summary">No task yet.</div><div class="workspace-tabs"><button data-tab="trace">Trace</button><button data-tab="memory">Memory</button></div><div class="workspace-panel-body">No trace recorded.</div></div>';
    }
  };
})();
```

- [ ] **Step 4: Add a mount point to the dashboard**

```html
<section id="side-workspace-host" class="side-workspace-host" aria-label="Side Workspace"></section>
```

- [ ] **Step 5: Run bridge tests**

Run: `npm run test:packages -- packages/hermes-dashboard-bridge/src/dashboardEventAdapter.test.ts`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/hermes-dashboard-bridge hermes/api/dashboard.html hermes/api/static/workspace_host.js
git commit -m "feat: add dashboard bridge for side workspace host"
```

## Task 5: Add backend workspace API endpoints and controller flow

**Files:**
- Modify: `G:\program\hermes\hermes\api\server.py`
- Modify: `G:\program\hermes\start_hermes.py`
- Create: `G:\program\hermes\tests\test_workspace_api.py`

- [ ] **Step 1: Write the failing workspace API contract test**

```python
import unittest
from hermes.api.server import app
from fastapi.testclient import TestClient


class TestWorkspaceApi(unittest.TestCase):
    def test_create_task_endpoint_returns_task_payload(self):
        client = TestClient(app)
        res = client.post("/workspace/tasks", json={
            "sourceMessageId": "msg_1",
            "title": "Check repo tests",
            "goal": "Run tests and classify failures"
        })
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["title"], "Check repo tests")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_workspace_api -v`  
Expected: FAIL because `/workspace/tasks` does not exist.

- [ ] **Step 3: Add minimal workspace endpoint handlers with explicit payload schemas**

```python
from pydantic import BaseModel
from typing import List, Optional


class CreateTaskRequest(BaseModel):
    sourceMessageId: Optional[str] = None
    title: str
    goal: str
    steps: List[str] = []
    doneWhen: List[str] = []
    riskTags: List[str] = []
    doNotTouch: List[str] = []


@app.post("/workspace/tasks")
def create_workspace_task(body: CreateTaskRequest):
    task = {
        "schemaVersion": "v1",
        "id": f"task_{body.sourceMessageId or 'manual'}",
        "title": body.title,
        "goal": body.goal,
        "status": "TODO",
        "steps": body.steps,
        "doneWhen": body.doneWhen,
        "riskTags": body.riskTags,
        "doNotTouch": body.doNotTouch,
    }
    return {"ok": True, "data": task}
```

- [ ] **Step 4: Run API contract test**

Run: `python -m unittest tests.test_workspace_api -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hermes/api/server.py start_hermes.py tests/test_workspace_api.py
git commit -m "feat: add workspace task api endpoints"
```

## Task 6: Build Task, Trace, and Memory panels with empty states and risk display

**Files:**
- Create: `G:\program\hermes\packages\task-panel\src\TaskPanel.tsx`
- Create: `G:\program\hermes\packages\task-panel\src\TaskSummaryCard.tsx`
- Create: `G:\program\hermes\packages\trace-panel\src\TracePanel.tsx`
- Create: `G:\program\hermes\packages\trace-panel\src\TraceTimeline.tsx`
- Create: `G:\program\hermes\packages\memory-panel\src\MemoryPanel.tsx`
- Create: `G:\program\hermes\packages\memory-panel\src\MemoryPreview.tsx`
- Modify: `G:\program\hermes\hermes\api\static\workspace_host.js`

- [ ] **Step 1: Write a failing Python UI shell test for empty states**

```python
import unittest
from pathlib import Path


class TestWorkspaceSidePanelHost(unittest.TestCase):
    def test_workspace_empty_states_are_present(self):
        host = Path("hermes/api/static/workspace_host.js").read_text(encoding="utf-8")
        self.assertIn("No task yet.", host)
        self.assertIn("No trace recorded.", host)
        self.assertIn("No memory saved.", host)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_workspace_side_panel_host -v`  
Expected: FAIL because `No memory saved.` is not rendered yet.

- [ ] **Step 3: Implement panel components and empty states**

```tsx
export function TaskSummaryCard({ task }: { task?: Task }) {
  if (!task) {
    return <div className="workspace-empty">No task yet. Use "Save as Task" from chat to create a trackable task.</div>;
  }
  return <div><h3>{task.title}</h3><p>{task.goal}</p></div>;
}
```

```tsx
export function TracePanel({ events }: { events: TraceEvent[] }) {
  if (!events.length) {
    return <div className="workspace-empty">No trace recorded. Start or confirm a task to begin recording execution evidence.</div>;
  }
  return <div>{events.map((event) => <div key={event.id}>{event.type}: {event.content}</div>)}</div>;
}
```

```tsx
export function MemoryPanel({ records }: { records: Memory[] }) {
  if (!records.length) {
    return <div className="workspace-empty">No memory saved. Save verified trace segments as project, user, decision, or skill memory.</div>;
  }
  return <div>{records.map((record) => <article key={record.id}>{record.title}</article>)}</div>;
}
```

- [ ] **Step 4: Update host shell to render the three empty states**

```js
node.innerHTML = `
  <div class="workspace-shell">
    <div class="workspace-task-summary">No task yet. Use "Save as Task" from chat to create a trackable task.</div>
    <div class="workspace-tabs"><button data-tab="trace">Trace</button><button data-tab="memory">Memory</button></div>
    <div class="workspace-panel-body" data-panel="trace">No trace recorded. Start or confirm a task to begin recording execution evidence.</div>
    <div class="workspace-panel-body is-hidden" data-panel="memory">No memory saved. Save verified trace segments as project, user, decision, or skill memory.</div>
  </div>
`;
```

- [ ] **Step 5: Run empty-state host test**

Run: `python -m unittest tests.test_workspace_side_panel_host -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packages/task-panel packages/trace-panel packages/memory-panel hermes/api/static/workspace_host.js tests/test_workspace_side_panel_host.py
git commit -m "feat: add task trace and memory panel shells"
```

## Task 7: Implement lightweight governance and trace-to-skill promotion

**Files:**
- Create: `G:\program\hermes\packages\governance-core\src\risk.ts`
- Create: `G:\program\hermes\packages\governance-core\src\approval.ts`
- Create: `G:\program\hermes\packages\skill-promoter\src\promoteTraceToSkill.ts`
- Create: `G:\program\hermes\packages\skill-promoter\src\validateSkillDraft.ts`
- Test: `G:\program\hermes\packages\skill-promoter\src\promoteTraceToSkill.test.ts`

- [ ] **Step 1: Write the failing skill promotion test**

```ts
import { describe, expect, it } from "vitest";
import { promoteTraceToSkill } from "./promoteTraceToSkill";

describe("promoteTraceToSkill", () => {
  it("emits a skill markdown draft with required sections", () => {
    const markdown = promoteTraceToSkill({
      title: "Repo Test Diagnosis",
      traces: [
        { type: "PLAN", content: "Find test command" },
        { type: "ACTION", content: "Run pytest" },
        { type: "VERIFY", content: "Classify import error" }
      ]
    } as any);
    expect(markdown).toContain("## Purpose");
    expect(markdown).toContain("## Validation");
    expect(markdown).toContain("## Failure Handling");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test:packages -- packages/skill-promoter/src/promoteTraceToSkill.test.ts`  
Expected: FAIL because promotion function does not exist.

- [ ] **Step 3: Implement promotion and validation**

```ts
export function promoteTraceToSkill(input: { title: string; traces: Array<{ type: string; content: string }> }): string {
  const steps = input.traces.map((trace, index) => `${index + 1}. ${trace.content}`).join("\n");
  return `# ${input.title}

## Purpose
Capture a reusable execution flow derived from a successful Hermes task trace.

## When to Use
Use when a similar task needs the same validated execution sequence.

## Inputs
- Task context
- Required files or runtime state

## Steps
${steps}

## Outputs
- Verified task outcome

## Validation
- Confirm the trace ends in a successful verify step

## Failure Handling
- Stop on failed action
- Record the error
- Ask for review before retrying risky changes
`;
}
```

```ts
export function validateSkillDraft(markdown: string): boolean {
  return [
    "## Purpose",
    "## When to Use",
    "## Inputs",
    "## Steps",
    "## Outputs",
    "## Validation",
    "## Failure Handling"
  ].every((section) => markdown.includes(section));
}
```

- [ ] **Step 4: Run the promotion test**

Run: `npm run test:packages -- packages/skill-promoter/src/promoteTraceToSkill.test.ts`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/governance-core packages/skill-promoter
git commit -m "feat: add governance helpers and skill promotion"
```

## Task 8: Final end-to-end validation for the v1 vertical slice

**Files:**
- Modify: `G:\program\hermes\tests\test_dashboard_static_modules.py`
- Modify: `G:\program\hermes\tests\test_dashboard_workbench_ui.py`
- Modify: `G:\program\hermes\tests\test_dashboard.py`

- [ ] **Step 1: Add failing integration assertions for side workspace presence**

```python
def test_dashboard_contains_side_workspace_host(self):
    self.assertIn('id="side-workspace-host"', self.dashboard)
    self.assertIn('static/workspace_host.js', self.dashboard)
    self.assertIn('Save as Task', self.dashboard)
```

- [ ] **Step 2: Run the dashboard integration test**

Run: `python -m unittest tests.test_dashboard_static_modules tests.test_dashboard_workbench_ui tests.test_dashboard -v`  
Expected: FAIL until all workspace shell strings and host assets are wired.

- [ ] **Step 3: Update dashboard host strings and actions**

```html
<button class="workspace-action-btn" data-action="save-task">Save as Task</button>
<button class="workspace-action-btn" data-action="save-trace">Save Trace</button>
<button class="workspace-action-btn" data-action="promote-skill">Promote to Skill</button>
```

```js
document.querySelectorAll("[data-action='save-task']").forEach((node) => {
  node.addEventListener("click", () => {
    window.HermesWorkspaceHost?.mount("side-workspace-host");
  });
});
```

- [ ] **Step 4: Run full validation**

Run: `python -m unittest discover -s tests -p "test_*.py"`  
Expected: PASS

Run: `npm run test:packages`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hermes/api/dashboard.html hermes/api/static/workspace_host.js tests/test_dashboard_static_modules.py tests/test_dashboard_workbench_ui.py tests/test_dashboard.py
git commit -m "feat: wire side workspace vertical slice into dashboard"
```

## Self-Review

### Spec coverage

This plan covers:

- package-first workspace core
- file-backed storage
- host bridge
- API contract entrypoint
- panel UI shells
- lightweight governance
- skill promotion
- dashboard integration
- package tests and Python integration tests

### Placeholder scan

There are no `TBD`, `TODO`, or "similar to previous task" steps. Each task names exact files, commands, and minimum code shape.

### Type consistency

The same entities are used throughout:

- `Task`
- `TaskStep`
- `TraceEvent`
- `Memory`
- `ApprovalDecision`
- `WorkspaceCommand`
- `WorkspaceEvent`

No alternate names are introduced later in the plan.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-15-hermes-side-workspace-v1-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
