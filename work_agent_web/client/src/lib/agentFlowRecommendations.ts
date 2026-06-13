import { createAgentGraphEdgeId } from "@/lib/agentGraph";
import type { AgentGraph, AgentGraphEdge, AgentGraphPosition, AgentPermission, AgentSlot } from "@/types/chat";

export interface AgentFlowRecommendationSlot {
  id: string;
  name: string;
  role: string;
  skill: string;
  permissions: AgentPermission[];
  outputFormat: string;
  position: AgentGraphPosition;
}

export interface AgentFlowRecommendation {
  id: string;
  name: string;
  description: string;
  slots: AgentFlowRecommendationSlot[];
  edges: Array<Pick<AgentGraphEdge, "from" | "to">>;
}

export interface RecommendedAgentFlow {
  agentTeam: AgentSlot[];
  agentGraph: AgentGraph;
}

export const AGENT_FLOW_RECOMMENDATIONS: AgentFlowRecommendation[] = [
  {
    id: "standard-dev",
    name: "標準開發流程",
    description: "規劃、產生、處理、審核與驗證，適合一般功能開發。",
    slots: [
      slot("planner", "Planner", "規劃者", "拆解任務、定義成功條件與執行順序。", ["plan"], "plan", 110, 150),
      slot("generator", "Generator", "產生者", "依照計畫產出主要內容或程式變更。", ["code"], "draft", 270, 150),
      slot("processor", "Processor", "處理者", "整理 Generator 的輸出並補齊細節。", ["code", "tools"], "processed-output", 430, 150),
      slot("reviewer", "Reviewer", "審核者", "檢查邏輯、風險、遺漏與一致性。", ["review"], "critique", 590, 150),
      slot("verifier", "Verifier", "驗證者", "確認輸出符合需求並整理完成狀態。", ["verify"], "verification", 750, 150),
    ],
    edges: chain(["planner", "generator", "processor", "reviewer", "verifier"]),
  },
  {
    id: "fast-execution",
    name: "快速執行流程",
    description: "Planner 直接交給 Executor，適合簡短明確任務。",
    slots: [
      slot("planner", "Planner", "規劃者", "快速理解任務並定義輸出。", ["plan"], "plan", 250, 150),
      slot("executor", "Executor", "執行者", "直接完成使用者要求。", ["code", "tools"], "result", 560, 150),
    ],
    edges: chain(["planner", "executor"]),
  },
  {
    id: "research-synthesis",
    name: "研究整理流程",
    description: "先研究再彙整，適合資料整理、比較與報告。",
    slots: [
      slot("planner", "Planner", "規劃者", "拆解研究問題與判斷資料需求。", ["plan"], "plan", 140, 150),
      slot("researcher", "Researcher", "研究者", "蒐集與歸納可用資訊。", ["plan", "external"], "notes", 360, 110),
      slot("synthesizer", "Synthesizer", "彙整者", "整合研究筆記成清楚結論。", ["review"], "summary", 580, 150),
      slot("reviewer", "Reviewer", "審核者", "檢查結論是否完整可靠。", ["review", "verify"], "critique", 780, 150),
    ],
    edges: chain(["planner", "researcher", "synthesizer", "reviewer"]),
  },
  {
    id: "parallel-multi-model",
    name: "多模型並行流程",
    description: "Planner 分派給不同角色並行處理，再由 Integrator 合併。",
    slots: [
      slot("planner", "Planner", "規劃者", "分派任務與定義合併標準。", ["plan"], "plan", 110, 150),
      slot("researcher", "Researcher", "研究者", "從資訊面補充上下文。", ["plan", "external"], "notes", 320, 95),
      slot("generator", "Generator", "產生者", "產出主要方案。", ["code"], "draft", 320, 205),
      slot("integrator", "Integrator", "整合者", "合併並行輸出成單一方案。", ["review"], "integrated-output", 560, 150),
      slot("reviewer", "Reviewer", "審核者", "檢查整合結果。", ["review", "verify"], "critique", 780, 150),
    ],
    edges: [
      { from: "planner", to: "researcher" },
      { from: "planner", to: "generator" },
      { from: "researcher", to: "integrator" },
      { from: "generator", to: "integrator" },
      { from: "integrator", to: "reviewer" },
    ],
  },
  {
    id: "debug-repair",
    name: "修復除錯流程",
    description: "定位問題、修復、驗證，適合錯誤追蹤。",
    slots: [
      slot("planner", "Planner", "規劃者", "界定錯誤範圍與檢查順序。", ["plan"], "plan", 160, 150),
      slot("debugger", "Debugger", "除錯者", "找出根因並提出證據。", ["review", "tools"], "diagnosis", 380, 150),
      slot("fixer", "Fixer", "修復者", "根據診斷完成修復。", ["code", "tools"], "patch", 600, 150),
      slot("verifier", "Verifier", "驗證者", "執行驗證並確認修復有效。", ["verify"], "verification", 780, 150),
    ],
    edges: chain(["planner", "debugger", "fixer", "verifier"]),
  },
  {
    id: "neural-collaboration",
    name: "神經元協作流程",
    description: "分層、多輸入、多輸出，適合複雜任務與多角度融合。",
    slots: [
      slot("planner", "Planner", "任務編碼", "把使用者任務轉成可分派的子問題與輸入訊號。", ["plan"], "task-encoding", 110, 150),
      slot("signal-analyzer", "Signal Analyzer", "訊號分析", "分析需求、限制、風險與隱含條件。", ["plan", "review"], "signals", 300, 70),
      slot("generator", "Generator", "方案產生", "產生主要方案、內容或實作草稿。", ["code"], "draft", 300, 150),
      slot("critic", "Critic", "反例檢查", "尋找漏洞、反例、缺失與風險。", ["review"], "critique", 300, 230),
      slot("hidden-integrator-a", "Hidden Integrator A", "隱層整合 A", "融合分析與產生結果，形成第一組中間判斷。", ["review"], "hidden-state-a", 520, 110),
      slot("hidden-integrator-b", "Hidden Integrator B", "隱層整合 B", "融合產生結果與批判結果，形成第二組中間判斷。", ["review"], "hidden-state-b", 520, 205),
      slot("output-synthesizer", "Output Synthesizer", "輸出合成", "整合隱層結果成最終可交付輸出。", ["code", "review"], "final-output", 720, 150),
      slot("verifier", "Verifier", "驗證者", "檢查最終輸出是否符合任務與完成條件。", ["verify"], "verification", 850, 150),
    ],
    edges: [
      { from: "planner", to: "signal-analyzer" },
      { from: "planner", to: "generator" },
      { from: "planner", to: "critic" },
      { from: "signal-analyzer", to: "hidden-integrator-a" },
      { from: "generator", to: "hidden-integrator-a" },
      { from: "generator", to: "hidden-integrator-b" },
      { from: "critic", to: "hidden-integrator-b" },
      { from: "hidden-integrator-a", to: "output-synthesizer" },
      { from: "hidden-integrator-b", to: "output-synthesizer" },
      { from: "output-synthesizer", to: "verifier" },
    ],
  },
];

export function getAgentFlowRecommendation(id: string) {
  return AGENT_FLOW_RECOMMENDATIONS.find((recommendation) => recommendation.id === id);
}

export function buildRecommendedAgentFlow(
  recommendationId: string,
  model: string
): RecommendedAgentFlow {
  const recommendation = getAgentFlowRecommendation(recommendationId);
  if (!recommendation) {
    throw new Error(`Unknown agent flow recommendation: ${recommendationId}`);
  }

  return {
    agentTeam: recommendation.slots.map((item) => ({
      id: item.id,
      name: item.name,
      role: item.role,
      model,
      skill: item.skill,
      permissions: item.permissions,
      outputFormat: item.outputFormat,
      isEnabled: true,
    })),
    agentGraph: {
      positions: Object.fromEntries(recommendation.slots.map((item) => [item.id, item.position])),
      edges: recommendation.edges.map((edge) => ({
        ...edge,
        id: createAgentGraphEdgeId(edge.from, edge.to),
      })),
    },
  };
}

function slot(
  id: string,
  name: string,
  role: string,
  skill: string,
  permissions: AgentPermission[],
  outputFormat: string,
  x: number,
  y: number
): AgentFlowRecommendationSlot {
  return {
    id,
    name,
    role,
    skill,
    permissions,
    outputFormat,
    position: { x, y },
  };
}

function chain(ids: string[]) {
  return ids.slice(0, -1).map((from, index) => ({ from, to: ids[index + 1] }));
}
