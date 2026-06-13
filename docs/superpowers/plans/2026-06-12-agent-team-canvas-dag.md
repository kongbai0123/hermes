# Agent Team Canvas DAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an editable Agent Team Canvas where Planner is the fixed root, users connect joints into a DAG, and graph execution can run joints in graph order with parallel branches.

**Architecture:** Add a small graph domain module for validation and scheduling, persist `agentGraph` on each chat, keep the SVG canvas UI local to `AgentFlowPanel`, and add a server orchestration endpoint that emits NDJSON graph events while reusing the existing Work Agent runner. UI and reducer stay independent from backend execution so the canvas can be tested without live models.

**Tech Stack:** React 19, TypeScript, Vitest, Testing Library, Express, existing SVG canvas, existing Work Agent server runner.

---

## File Structure

- Create `work_agent_web/client/src/lib/agentGraph.ts`: pure graph helpers for edge validation, topological levels, terminal joints, and prompt context composition.
- Create `work_agent_web/client/src/lib/agentGraph.test.ts`: unit tests for graph rules and scheduling.
- Modify `work_agent_web/client/src/types/chat.ts`: add `AgentGraph`, `AgentGraphEdge`, `AgentGraphPosition`, execution event types, and reducer actions.
- Modify `work_agent_web/client/src/contexts/ChatContext.tsx`: restore graph state, add graph reducer actions, protect Planner deletion, clean edges on slot deletion.
- Modify `work_agent_web/client/src/contexts/ChatContext.test.ts`: reducer tests for graph persistence and graph actions.
- Modify `work_agent_web/client/src/components/AgentFlowPanel.tsx`: toolbar, connect mode, selected node/edge, edit dialog, persisted drag positions, graph edges.
- Modify `work_agent_web/client/src/components/AgentFlowPanel.test.ts`: component tests for dialog edit, add/delete joint, connect mode, and edge deletion.
- Modify `work_agent_web/server/index.ts`: add `/api/work-agent/run-graph-stream` and shared graph execution helpers.
- Create `work_agent_web/server/agentGraphRunner.test.ts` only if server test harness can import TS server helpers directly; otherwise keep graph scheduling tests in client pure module and verify server through build plus smoke request.

---

### Task 1: Graph Domain Model

**Files:**
- Create: `work_agent_web/client/src/lib/agentGraph.ts`
- Create: `work_agent_web/client/src/lib/agentGraph.test.ts`
- Modify: `work_agent_web/client/src/types/chat.ts`

- [ ] **Step 1: Write failing tests for graph validation and scheduling**

Add tests asserting:

```ts
expect(addAgentGraphEdge({ edges: [] }, { from: "planner", to: "coder" }).graph.edges).toHaveLength(1);
expect(addAgentGraphEdge({ edges: [] }, { from: "coder", to: "planner" }).reason).toBe("planner-incoming");
expect(buildAgentGraphLevels(team, edges)).toEqual([["planner"], ["generator", "researcher"], ["processor"]]);
```

Run: `npm exec vitest -- run client/src/lib/agentGraph.test.ts`
Expected: FAIL because `agentGraph.ts` does not exist.

- [ ] **Step 2: Implement minimal graph helpers**

Implement:

- `createDefaultAgentGraph(team)`
- `addAgentGraphEdge(graph, edge)`
- `removeAgentGraphEdge(graph, edgeId)`
- `removeAgentFromGraph(graph, agentId)`
- `updateAgentGraphPosition(graph, agentId, position)`
- `buildAgentGraphLevels(team, edges)`
- `getTerminalAgentIds(team, edges)`

- [ ] **Step 3: Run graph tests**

Run: `npm exec vitest -- run client/src/lib/agentGraph.test.ts`
Expected: PASS.

---

### Task 2: Chat State Persistence

**Files:**
- Modify: `work_agent_web/client/src/types/chat.ts`
- Modify: `work_agent_web/client/src/contexts/ChatContext.tsx`
- Modify: `work_agent_web/client/src/contexts/ChatContext.test.ts`

- [ ] **Step 1: Write failing reducer tests**

Add tests asserting:

```ts
DELETE_AGENT_SLOT with slotId "planner" leaves Planner in place.
ADD_AGENT_GRAPH_EDGE stores planner -> coder.
DELETE_AGENT_SLOT for "coder" removes coder and related edges.
UPDATE_AGENT_GRAPH_POSITION stores { x: 240, y: 120 }.
restoreChatState preserves saved agentGraph.
```

Run: `npm exec vitest -- run client/src/contexts/ChatContext.test.ts`
Expected: FAIL because graph actions/types do not exist.

- [ ] **Step 2: Implement reducer support**

Add `agentGraph` to `Chat`, graph action types, restore defaults for old chats, and reducer cases for edge add/delete and position update. Keep Planner protected from deletion.

- [ ] **Step 3: Run reducer tests**

Run: `npm exec vitest -- run client/src/contexts/ChatContext.test.ts`
Expected: PASS.

---

### Task 3: Editable Canvas UI

**Files:**
- Modify: `work_agent_web/client/src/components/AgentFlowPanel.tsx`
- Modify: `work_agent_web/client/src/components/AgentFlowPanel.test.ts`

- [ ] **Step 1: Write failing component tests**

Add tests asserting:

```ts
render panel -> Add joint button exists.
click Add joint -> dialog opens -> save creates new Agent slot.
click Planner node -> edit dialog opens.
connect mode -> click Planner then Coder -> dispatches ADD_AGENT_GRAPH_EDGE.
select edge -> click delete -> dispatches DELETE_AGENT_GRAPH_EDGE.
```

Run: `npm exec vitest -- run client/src/components/AgentFlowPanel.test.ts`
Expected: FAIL because controls/dialog are missing.

- [ ] **Step 2: Implement toolbar and dialog**

Add Add, Connect, Delete, Auto-layout buttons. Add a dialog implemented with existing component patterns or plain accessible markup. Use current `state.models` for model selection. Keep Planner delete disabled.

- [ ] **Step 3: Implement canvas interactions**

Render graph edges from `currentChat.agentGraph.edges`, preserve fallback sequential edge when no graph exists, persist node drag positions with `UPDATE_AGENT_GRAPH_POSITION`, and use connect mode source/target clicks to create edges.

- [ ] **Step 4: Run component tests**

Run: `npm exec vitest -- run client/src/components/AgentFlowPanel.test.ts`
Expected: PASS.

---

### Task 4: Graph Runner Stream

**Files:**
- Modify: `work_agent_web/server/index.ts`
- Modify: `work_agent_web/client/src/types/chat.ts`
- Add client helper only if needed: `work_agent_web/client/src/lib/agentGraphRun.ts`

- [ ] **Step 1: Write failing graph runner tests or smoke harness**

If direct server helper import is practical, extract pure runner helper and test:

```ts
planner completes before generator.
generator and researcher run in the same level after planner.
processor waits for generator and researcher.
```

If not practical, keep this behavior covered by `agentGraph.ts` scheduling tests and use build plus HTTP smoke verification after implementation.

- [ ] **Step 2: Implement endpoint**

Add `POST /api/work-agent/run-graph-stream` accepting:

```ts
{
  prompt: string;
  team: AgentSlot[];
  graph: AgentGraph;
}
```

Emit `graph-start`, `joint-start`, `joint-complete`, `joint-error`, and `graph-complete` NDJSON events. Reuse `runWorkAgent(composedPrompt, slot.model)` per joint.

- [ ] **Step 3: Verify endpoint**

Run: `npm run build`
Expected: PASS.

Start server and POST a two-node graph to `/api/work-agent/run-graph-stream`; expected response starts with `graph-start` and includes `joint-start`.

---

### Task 5: Full Verification

**Files:**
- All files above.

- [ ] **Step 1: Run focused tests**

Run:

```bash
npm exec vitest -- run client/src/lib/agentGraph.test.ts client/src/contexts/ChatContext.test.ts client/src/components/AgentFlowPanel.test.ts
```

Expected: PASS.

- [ ] **Step 2: Run project checks**

Run:

```bash
npm exec vitest -- run
npm run check
npm run build
```

Expected: PASS. Existing Vite chunk-size warnings are acceptable if no new errors are introduced.

- [ ] **Step 3: Browser verification**

Open the local app, switch to `運行監控`, verify:

- Add joint opens dialog and saves.
- Click joint opens edit dialog.
- Connect mode creates Planner to child edge.
- Invalid edge into Planner is rejected.
- Delete edge works.
- Node drag remains stable.

---

## Plan Self-Review

- Spec coverage: editable canvas, graph persistence, graph validation, Planner root, multi-output scheduling, multi-input waiting, and graph stream are covered.
- Placeholder scan: no incomplete markers are present.
- Type consistency: `AgentGraph`, `AgentGraphEdge`, and reducer action names are used consistently across tasks.
