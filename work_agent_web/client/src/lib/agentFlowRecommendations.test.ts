import { describe, expect, it } from "vitest";
import {
  buildRecommendedAgentFlow,
  getAgentFlowRecommendation,
} from "./agentFlowRecommendations";

describe("agentFlowRecommendations", () => {
  it("includes a neural collaboration recommendation with layered multi-input wiring", () => {
    const recommendation = getAgentFlowRecommendation("neural-collaboration");

    expect(recommendation?.name).toBe("神經元協作流程");
    expect(recommendation?.slots.map((slot) => slot.id)).toEqual([
      "planner",
      "signal-analyzer",
      "generator",
      "critic",
      "hidden-integrator-a",
      "hidden-integrator-b",
      "output-synthesizer",
      "verifier",
    ]);
    expect(recommendation?.edges).toContainEqual({
      from: "generator",
      to: "hidden-integrator-a",
    });
    expect(recommendation?.edges).toContainEqual({
      from: "critic",
      to: "hidden-integrator-b",
    });
    expect(recommendation?.edges).toContainEqual({
      from: "hidden-integrator-b",
      to: "output-synthesizer",
    });
  });

  it("builds a recommendation with the selected model and graph positions", () => {
    const flow = buildRecommendedAgentFlow("neural-collaboration", "ollama-qwen-local");

    expect(flow.agentTeam.every((slot) => slot.model === "ollama-qwen-local")).toBe(true);
    expect(flow.agentGraph.edges).toContainEqual({
      id: "planner-to-generator",
      from: "planner",
      to: "generator",
    });
    expect(flow.agentGraph.positions.planner).toEqual({ x: 110, y: 150 });
    expect(flow.agentGraph.positions["output-synthesizer"]).toEqual({ x: 720, y: 150 });
  });
});
