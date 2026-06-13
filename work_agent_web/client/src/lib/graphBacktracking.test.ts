import { describe, expect, it } from "vitest";
import {
  DEFAULT_BACKTRACKING_POLICY,
  chooseBacktrackingAction,
  parseVerifierScore,
  renderBacktrackingPolicyForPrompt,
} from "./graphBacktracking";

describe("graphBacktracking", () => {
  it("accepts verifier output when the score passes the threshold", () => {
    const action = chooseBacktrackingAction({
      score: 0.82,
      retryTarget: "generator",
      round: 0,
      previousBestScore: 0.7,
      retryCounts: {},
    });

    expect(action).toEqual({
      type: "accept",
      reason: "score-passed",
      bestScore: 0.82,
    });
  });

  it("retries the target joint when score is low and policy budget remains", () => {
    const action = chooseBacktrackingAction({
      score: 0.62,
      retryTarget: "generator",
      feedback: "需要補上來源",
      round: 0,
      previousBestScore: 0.58,
      retryCounts: {},
    });

    expect(action).toEqual({
      type: "retry",
      targetAgentId: "generator",
      feedback: "需要補上來源",
      nextRound: 1,
      bestScore: 0.62,
    });
  });

  it("stops when retry rounds or per-joint retry limits are exhausted", () => {
    expect(
      chooseBacktrackingAction({
        score: 0.62,
        retryTarget: "generator",
        round: DEFAULT_BACKTRACKING_POLICY.maxRounds,
        previousBestScore: 0.7,
        retryCounts: {},
      })
    ).toMatchObject({ type: "stop", reason: "max-rounds" });

    expect(
      chooseBacktrackingAction({
        score: 0.62,
        retryTarget: "generator",
        round: 1,
        previousBestScore: 0.7,
        retryCounts: { generator: 1 },
      })
    ).toMatchObject({ type: "stop", reason: "retry-limit" });
  });

  it("stops when a retry does not improve enough", () => {
    const action = chooseBacktrackingAction({
      score: 0.63,
      retryTarget: "generator",
      round: 1,
      previousBestScore: 0.6,
      retryCounts: {},
    });

    expect(action).toEqual({
      type: "stop",
      reason: "insufficient-improvement",
      bestScore: 0.63,
    });
  });

  it("parses structured verifier JSON from model output", () => {
    expect(
      parseVerifierScore(
        '```json\n{"score":0.61,"passed":false,"retryTarget":"researcher","feedback":"缺少價格來源"}\n```'
      )
    ).toEqual({
      score: 0.61,
      passed: false,
      retryTarget: "researcher",
      feedback: "缺少價格來源",
    });
  });

  it("renders bounded retry rules for verifier prompts", () => {
    const rendered = renderBacktrackingPolicyForPrompt(DEFAULT_BACKTRACKING_POLICY);

    expect(rendered).toContain("maxRounds: 2");
    expect(rendered).toContain("passingScore: 0.75");
    expect(rendered).toContain("Do not continue debating indefinitely");
  });
});
