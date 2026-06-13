import { describe, expect, it } from "vitest";
import {
  applyAgentRunEvent,
  createQueuedAgentRuns,
  createRunLogEntry,
} from "./agentRuns";
import type { AgentSlot } from "@/types/chat";

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
];

describe("agentRuns", () => {
  it("initializes enabled joints as queued for event-driven monitoring", () => {
    expect(createQueuedAgentRuns(team, 1000)).toEqual({
      planner: {
        agentId: "planner",
        name: "Planner",
        status: "queued",
        updatedAt: 1000,
      },
      generator: {
        agentId: "generator",
        name: "Generator",
        status: "queued",
        updatedAt: 1000,
      },
    });
  });

  it("marks a joint running with a minimum visible running window", () => {
    const runs = createQueuedAgentRuns(team, 1000);
    const next = applyAgentRunEvent(runs, {
      type: "joint-start",
      agentId: "planner",
      name: "Planner",
      at: 1200,
      minVisibleMs: 500,
    });

    expect(next.planner).toMatchObject({
      status: "running",
      startedAt: 1200,
      minVisibleUntil: 1700,
    });
  });

  it("records complete, error and skipped states by joint id", () => {
    const runs = createQueuedAgentRuns(team, 1000);
    const completed = applyAgentRunEvent(runs, {
      type: "joint-complete",
      agentId: "planner",
      name: "Planner",
      answer: "planned",
      at: 1300,
    });
    const failed = applyAgentRunEvent(completed, {
      type: "joint-error",
      agentId: "generator",
      name: "Generator",
      error: "failed",
      at: 1400,
    });
    const skipped = applyAgentRunEvent(failed, {
      type: "joint-skip",
      agentId: "reviewer",
      name: "Reviewer",
      reason: "upstream-failed",
      at: 1500,
    });

    expect(skipped.planner).toMatchObject({
      status: "complete",
      output: "planned",
      completedAt: 1300,
    });
    expect(skipped.generator).toMatchObject({
      status: "error",
      error: "failed",
      completedAt: 1400,
    });
    expect(skipped.reviewer).toMatchObject({
      status: "skipped",
      error: "upstream-failed",
      completedAt: 1500,
    });
  });

  it("creates compact run log entries for the monitor", () => {
    expect(
      createRunLogEntry({
        type: "joint-start",
        agentId: "planner",
        name: "Planner",
        at: 1200,
      })
    ).toEqual({
      id: "1200-planner-joint-start",
      agentId: "planner",
      name: "Planner",
      event: "joint-start",
      message: "Planner started",
      createdAt: 1200,
    });
  });
});
