import { describe, expect, it } from "vitest";
import {
  clampCanvasPosition,
  createAgentCanvasModel,
  resolveAgentFlowLayerPresentation,
  resolveMonitorViewport,
  resolveNodeDragPosition,
  resolveWheelZoom,
} from "./AgentFlowPanel";
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
    const model = createAgentCanvasModel(agentTeam, undefined, workbench);

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

  it("uses saved graph positions and user-created graph edges", () => {
    const model = createAgentCanvasModel(
      agentTeam,
      {
        edges: [{ id: "planner-to-reviewer", from: "planner", to: "reviewer" }],
        positions: {
          planner: { x: 210, y: 120 },
          reviewer: { x: 520, y: 190 },
        },
      },
      workbench
    );

    expect(model.nodes.find((node) => node.id === "planner")).toMatchObject({ x: 210, y: 120 });
    expect(model.nodes.find((node) => node.id === "reviewer")).toMatchObject({
      x: 520,
      y: 190,
    });
    expect(model.edges).toEqual([
      {
        id: "planner-to-reviewer",
        from: "planner",
        to: "reviewer",
        kind: "handoff",
      },
    ]);
  });

  it("adds a soft repair edge when the workbench reports an error", () => {
    const model = createAgentCanvasModel(agentTeam, undefined, { ...workbench, status: "error" });

    expect(model.edges).toContainEqual({
      id: "coder-to-planner-repair",
      from: "coder",
      to: "planner",
      kind: "return",
    });
    expect(model.nodes[1].state).toBe("error");
  });

  it("uses event-driven joint run state before inferred active index", () => {
    const model = createAgentCanvasModel(agentTeam, undefined, {
      ...workbench,
      status: "running",
      plan: [],
      toolLogs: [],
      agentRuns: {
        planner: {
          agentId: "planner",
          name: "Planner",
          status: "complete",
          updatedAt: 1000,
        },
        coder: {
          agentId: "coder",
          name: "Coder",
          status: "running",
          updatedAt: 1200,
          startedAt: 1200,
        },
      },
    });

    expect(model.nodes.find((node) => node.id === "planner")?.state).toBe("complete");
    expect(model.nodes.find((node) => node.id === "coder")?.state).toBe("active");
  });
});

describe("resolveAgentFlowLayerPresentation", () => {
  it("keeps monitor visible as a non-interactive chat background", () => {
    expect(resolveAgentFlowLayerPresentation("background")).toMatchObject({
      canInteract: false,
      containerClassName:
        "pointer-events-none absolute inset-0 z-0 border-0 bg-transparent opacity-35",
      canvasClassName: "h-full min-h-[420px] w-full touch-none",
    });
  });

  it("promotes monitor above chat when switched to interactive mode", () => {
    expect(resolveAgentFlowLayerPresentation("interactive")).toMatchObject({
      canInteract: true,
      containerClassName:
        "absolute inset-0 z-20 border-0 bg-background/92 shadow-none backdrop-blur-sm",
      canvasClassName: "h-full min-h-[420px] w-full touch-none",
      headerClassName: "pr-44",
    });
  });
});

describe("agent canvas interaction helpers", () => {
  it("clamps dragged joints inside the canvas bounds", () => {
    expect(clampCanvasPosition({ x: -40, y: 999 })).toEqual({ x: 50, y: 250 });
  });

  it("keeps the cursor offset stable while dragging a joint", () => {
    expect(
      resolveNodeDragPosition({
        pointer: { x: 320, y: 180 },
        offset: { x: 20, y: -10 },
      })
    ).toEqual({ x: 300, y: 190 });
  });

  it("zooms with wheel direction and clamps the monitor viewport", () => {
    expect(resolveWheelZoom(1, -120)).toBe(1.12);
    expect(resolveWheelZoom(1, 120)).toBe(0.88);
    expect(resolveWheelZoom(1.78, -120)).toBe(1.8);
    expect(resolveWheelZoom(0.72, 120)).toBe(0.7);
  });

  it("converts zoom into a centered svg viewBox", () => {
    expect(resolveMonitorViewport(1)).toEqual({ x: 0, y: 0, width: 900, height: 300 });
    expect(resolveMonitorViewport(1.5)).toEqual({ x: 150, y: 50, width: 600, height: 200 });
  });
});
