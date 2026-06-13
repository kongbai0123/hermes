import { describe, expect, it } from "vitest";
import {
  addAgentGraphEdge,
  buildAgentGraphLevels,
  createDefaultAgentGraph,
  getTerminalAgentIds,
  removeAgentFromGraph,
  updateAgentGraphPosition,
} from "./agentGraph";
import type { AgentGraph, AgentSlot } from "@/types/chat";

const team: AgentSlot[] = [
  {
    id: "planner",
    name: "Planner",
    role: "規劃者",
    model: "ollama-gemma4",
    skill: "Plan.",
    permissions: ["plan"],
    outputFormat: "plan",
    isEnabled: true,
  },
  {
    id: "generator",
    name: "Generator",
    role: "產生者",
    model: "ollama-qwen-local",
    skill: "Generate.",
    permissions: ["code"],
    outputFormat: "draft",
    isEnabled: true,
  },
  {
    id: "researcher",
    name: "Researcher",
    role: "研究者",
    model: "ollama-gemma4",
    skill: "Research.",
    permissions: ["plan"],
    outputFormat: "notes",
    isEnabled: true,
  },
  {
    id: "processor",
    name: "Processor",
    role: "處理者",
    model: "ollama-qwen-local",
    skill: "Process.",
    permissions: ["review"],
    outputFormat: "summary",
    isEnabled: true,
  },
];

describe("agentGraph", () => {
  it("creates an initial graph from the Planner root to the next enabled joint", () => {
    const graph = createDefaultAgentGraph(team);

    expect(graph.edges).toEqual([{ id: "planner-to-generator", from: "planner", to: "generator" }]);
    expect(graph.positions.planner).toEqual({ x: 130, y: 150 });
  });

  it("adds valid edges and ignores duplicate edges", () => {
    const initial: AgentGraph = { edges: [], positions: {} };

    const added = addAgentGraphEdge(initial, team, { from: "planner", to: "generator" });
    const duplicate = addAgentGraphEdge(added.graph, team, { from: "planner", to: "generator" });

    expect(added.ok).toBe(true);
    expect(added.graph.edges).toEqual([
      { id: "planner-to-generator", from: "planner", to: "generator" },
    ]);
    expect(duplicate.ok).toBe(true);
    expect(duplicate.graph.edges).toHaveLength(1);
  });

  it("blocks invalid edges into Planner, self edges, and cycle edges", () => {
    const graph: AgentGraph = {
      edges: [
        { id: "planner-to-generator", from: "planner", to: "generator" },
        { id: "generator-to-processor", from: "generator", to: "processor" },
      ],
      positions: {},
    };

    expect(addAgentGraphEdge({ edges: [], positions: {} }, team, { from: "generator", to: "planner" })).toMatchObject({
      ok: false,
      reason: "planner-incoming",
    });
    expect(addAgentGraphEdge({ edges: [], positions: {} }, team, { from: "planner", to: "planner" })).toMatchObject({
      ok: false,
      reason: "self-edge",
    });
    expect(addAgentGraphEdge(graph, team, { from: "processor", to: "planner" })).toMatchObject({
      ok: false,
      reason: "planner-incoming",
    });
    expect(addAgentGraphEdge(graph, team, { from: "processor", to: "generator" })).toMatchObject({
      ok: false,
      reason: "cycle",
    });
  });

  it("builds parallel execution levels and waits for multi-input joints", () => {
    const graph: AgentGraph = {
      edges: [
        { id: "planner-to-generator", from: "planner", to: "generator" },
        { id: "planner-to-researcher", from: "planner", to: "researcher" },
        { id: "generator-to-processor", from: "generator", to: "processor" },
        { id: "researcher-to-processor", from: "researcher", to: "processor" },
      ],
      positions: {},
    };

    expect(buildAgentGraphLevels(team, graph.edges)).toEqual([
      ["planner"],
      ["generator", "researcher"],
      ["processor"],
    ]);
    expect(getTerminalAgentIds(team, graph.edges)).toEqual(["processor"]);
  });

  it("removes graph edges with deleted joints and stores node positions", () => {
    const graph: AgentGraph = {
      edges: [
        { id: "planner-to-generator", from: "planner", to: "generator" },
        { id: "generator-to-processor", from: "generator", to: "processor" },
      ],
      positions: { planner: { x: 130, y: 150 }, generator: { x: 250, y: 140 } },
    };

    expect(removeAgentFromGraph(graph, "generator")).toEqual({
      edges: [],
      positions: { planner: { x: 130, y: 150 } },
    });
    expect(updateAgentGraphPosition(graph, "processor", { x: 420, y: 180 }).positions.processor).toEqual({
      x: 420,
      y: 180,
    });
  });
});
