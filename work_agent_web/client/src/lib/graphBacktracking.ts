export interface BacktrackingPolicy {
  maxRounds: number;
  maxRetryPerJoint: number;
  passingScore: number;
  minImprovement: number;
}

export interface VerifierScore {
  score: number;
  passed: boolean;
  retryTarget?: string;
  feedback?: string;
  failedReason?: string;
}

export interface BacktrackingDecisionInput {
  score: number;
  retryTarget?: string;
  feedback?: string;
  round: number;
  previousBestScore: number;
  retryCounts: Record<string, number>;
  policy?: BacktrackingPolicy;
}

export type BacktrackingAction =
  | { type: "accept"; reason: "score-passed"; bestScore: number }
  | {
      type: "retry";
      targetAgentId: string;
      feedback: string;
      nextRound: number;
      bestScore: number;
    }
  | {
      type: "stop";
      reason:
        | "max-rounds"
        | "retry-limit"
        | "insufficient-improvement"
        | "missing-retry-target";
      bestScore: number;
    };

export const DEFAULT_BACKTRACKING_POLICY: BacktrackingPolicy = {
  maxRounds: 2,
  maxRetryPerJoint: 1,
  passingScore: 0.75,
  minImprovement: 0.08,
};

export function chooseBacktrackingAction(input: BacktrackingDecisionInput): BacktrackingAction {
  const policy = input.policy ?? DEFAULT_BACKTRACKING_POLICY;
  const bestScore = Math.max(input.previousBestScore, input.score);

  if (input.score >= policy.passingScore) {
    return { type: "accept", reason: "score-passed", bestScore };
  }

  if (input.round >= policy.maxRounds) {
    return { type: "stop", reason: "max-rounds", bestScore };
  }

  if (!input.retryTarget) {
    return { type: "stop", reason: "missing-retry-target", bestScore };
  }

  if ((input.retryCounts[input.retryTarget] ?? 0) >= policy.maxRetryPerJoint) {
    return { type: "stop", reason: "retry-limit", bestScore };
  }

  if (input.round > 0 && input.score - input.previousBestScore < policy.minImprovement) {
    return { type: "stop", reason: "insufficient-improvement", bestScore };
  }

  return {
    type: "retry",
    targetAgentId: input.retryTarget,
    feedback: input.feedback ?? "請根據 Verifier 的評分補齊缺失，避免重複相同錯誤。",
    nextRound: input.round + 1,
    bestScore,
  };
}

export function parseVerifierScore(output: string): VerifierScore | null {
  const jsonText = extractJsonObject(output);
  if (!jsonText) return null;

  try {
    const parsed = JSON.parse(jsonText) as Partial<VerifierScore>;
    if (typeof parsed.score !== "number") return null;
    return {
      score: clampScore(parsed.score),
      passed: parsed.passed ?? parsed.score >= DEFAULT_BACKTRACKING_POLICY.passingScore,
      retryTarget: parsed.retryTarget,
      feedback: parsed.feedback,
      failedReason: parsed.failedReason,
    };
  } catch {
    return null;
  }
}

export function renderBacktrackingPolicyForPrompt(policy: BacktrackingPolicy): string {
  return [
    "Bounded Backtracking Policy:",
    `maxRounds: ${policy.maxRounds}`,
    `maxRetryPerJoint: ${policy.maxRetryPerJoint}`,
    `passingScore: ${policy.passingScore}`,
    `minImprovement: ${policy.minImprovement}`,
    "Verifier must output JSON with score, passed, failedReason, retryTarget, feedback.",
    "Do not continue debating indefinitely. If the answer does not improve enough, keep the best available result and stop.",
  ].join("\n");
}

function extractJsonObject(output: string) {
  const fenced = output.match(/```json\s*([\s\S]*?)```/i);
  if (fenced?.[1]) return fenced[1].trim();
  const firstBrace = output.indexOf("{");
  const lastBrace = output.lastIndexOf("}");
  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) return null;
  return output.slice(firstBrace, lastBrace + 1);
}

function clampScore(score: number) {
  return Math.max(0, Math.min(1, score));
}
