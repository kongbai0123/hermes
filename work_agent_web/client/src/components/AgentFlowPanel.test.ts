import { describe, expect, it } from "vitest";
import { createAgentCanvasModel } from "./AgentFlowPanel";
import type { AgentSlot, WorkbenchState } from "@/types/chat";

const agentTeam: AgentSlot[] = [
  {
    id: "planner",
    name: "Planner",
    role: "規劃者",
    model: "gemma4",
    skill: "Plan the work.",
    permissions: ["plan"],
    outputFormat: "plan",
    isEnabled: true,
  },
  {
    id: "coder",
    name: "Coder",
    role: "執行者",
    model: "qwen-local",
    skill: "Implement the plan.",
    permissions: ["code"],
    outputFormat: "proposal",
    isEnabled: true,
  },
  {
    id: "reviewer",
    name: "Reviewer",
    role: "審核者",
    model: "gemma4",
    skill: "Review the output.",
    permissions: ["review", "verify"],
    outputFormat: "critique",
    isEnabled: false,
  },
];

const workbench: WorkbenchState = {
  status: "running",
  plan: [{ id: "1", title: "Plan", detail: "Prepare", status: "done" }],
  toolLogs: [],
  safetyRules: [],
  workspaceEntries: [],
};

describe("createAgentCanvasModel", () => {
  it("creates draggable circular role nodes from enabled agent slots", () => {
    const model = createAgentCanvasModel(agentTeam, workbench);

    expect(model.nodes).toHaveLength(2);
    expect(model.nodes[0]).toMatchObject({
      id: "planner",
      name: "Planner",
      role: "規劃者",
      model: "gemma4",
      state: "complete",
    });
    expect(model.nodes[1]).toMatchObject({
      id: "coder",
      name: "Coder",
      state: "active",
    });
    expect(model.edges).toEqual([
      {
        id: "planner-to-coder",
        from: "planner",
        to: "coder",
        kind: "handoff",
      },
    ]);
  });

  it("adds a soft repair edge when the workbench reports an error", () => {
    const model = createAgentCanvasModel(agentTeam, { ...workbench, status: "error" });

    expect(model.edges).toContainEqual({
      id: "coder-to-planner-repair",
      from: "coder",
      to: "planner",
      kind: "return",
    });
    expect(model.nodes[1].state).toBe("error");
  });
});
