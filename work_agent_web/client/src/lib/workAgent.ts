import { nanoid } from "nanoid";
import { createDefaultAgentGraph } from "@/lib/agentGraph";
import type {
  Chat,
  AgentSlot,
  Message,
  Model,
  SafetyRule,
  ToolObservation,
  WorkbenchPlanStep,
  WorkspaceEntry,
} from "@/types/chat";

export const WORK_AGENT_MODELS: Model[] = [
  {
    id: "ollama-gemma4",
    name: "Gemma 4",
    provider: "ollama",
    isActive: true,
    description: "Local Ollama model for Work Agent",
    availability: "installed",
  },
  {
    id: "ollama-qwen-local",
    name: "Qwen Local",
    provider: "ollama",
    isActive: true,
    description: "Secondary local model for comparison",
    availability: "installed",
  },
  {
    id: "download-qwen3.6",
    name: "qwen3.6",
    provider: "ollama",
    isActive: false,
    description: "Downloadable reasoning model for local multi-agent work.",
    availability: "downloadable",
    downloadName: "qwen3.6",
    sizeGb: 4.8,
    minRamGb: 8,
    minVramGb: 0,
  },
  {
    id: "download-gemma4",
    name: "gemma4",
    provider: "ollama",
    isActive: false,
    description: "Downloadable Gemma model from Ollama.",
    availability: "downloadable",
    downloadName: "gemma4",
    sizeGb: 5.1,
    minRamGb: 8,
    minVramGb: 0,
  },
  {
    id: "download-gemma4-31b",
    name: "gemma4:31b",
    provider: "ollama",
    isActive: false,
    description: "Large model candidate for stronger review and planning.",
    availability: "downloadable",
    downloadName: "gemma4:31b",
    sizeGb: 19.5,
    minRamGb: 32,
    minVramGb: 12,
  },
  {
    id: "download-nemotron-super",
    name: "nemotron-3-super",
    provider: "ollama",
    isActive: false,
    description: "Large cloud-style candidate listed for future local download flow.",
    availability: "downloadable",
    downloadName: "nemotron-3-super",
    sizeGb: 24,
    minRamGb: 48,
    minVramGb: 16,
  },
];

export const DEFAULT_SAFETY_RULES: SafetyRule[] = [
  {
    id: "workspace-only",
    label: "Workspace Only",
    description: "Only read files inside workspace/.",
  },
  {
    id: "no-delete",
    label: "No Delete",
    description: "Do not delete files automatically.",
  },
  {
    id: "command-whitelist",
    label: "Whitelisted Commands",
    description: "Only run approved commands from config.json.",
  },
];

export const DEFAULT_WORKSPACE_ENTRIES: WorkspaceEntry[] = [
  {
    id: "workspace-readme",
    path: "workspace/README.md",
    kind: "file",
    summary: "Explains the safe workspace boundary.",
  },
  {
    id: "workspace-calculator",
    path: "workspace/calculator.py",
    kind: "file",
    summary: "Simple sample file for analysis and debugging.",
  },
];

export const DEFAULT_AGENT_TEAM: AgentSlot[] = [
  {
    id: "planner",
    name: "Planner",
    role: "規劃者",
    model: "ollama-gemma4",
    skill: "分析任務、拆解步驟、定義成功條件，並決定後續交給哪個角色。",
    permissions: ["plan"],
    outputFormat: "plan",
    isEnabled: true,
  },
  {
    id: "coder",
    name: "Coder",
    role: "執行者",
    model: "ollama-qwen-local",
    skill: "根據 Planner 的計畫提出實作方案、程式修改建議與必要的驗證步驟。",
    permissions: ["code", "tools"],
    outputFormat: "proposal",
    isEnabled: true,
  },
];

export function createDefaultChat(models: Model[]): Chat {
  const activeModel = models[0] ?? WORK_AGENT_MODELS[0];
  return {
    id: nanoid(),
    title: "New Work Task",
    model: activeModel.id,
    provider: activeModel.provider,
    taskMode: "single",
    createdAt: new Date(),
    updatedAt: new Date(),
    messages: [],
    agentTeam: DEFAULT_AGENT_TEAM.map((slot) => ({ ...slot, permissions: [...slot.permissions] })),
    agentGraph: createDefaultAgentGraph(DEFAULT_AGENT_TEAM),
    settings: {
      model: activeModel.id,
      provider: activeModel.provider,
      temperature: 0.2,
      maxTokens: 2000,
      reasoningLevel: "medium",
      responseSpeed: "standard",
      systemPrompt:
        "You are Work Agent. Focus on safe file analysis, tool observations, and concise execution guidance.",
    },
    workbench: {
      status: "idle",
      plan: [],
      toolLogs: [],
      safetyRules: DEFAULT_SAFETY_RULES,
      workspaceEntries: DEFAULT_WORKSPACE_ENTRIES,
      allowedCommands: ["python --version", "python -m pytest", "pytest", "rg"],
      safetyModeLabel: "Safe Mode",
      selectedFile: null,
      patch: null,
    },
  };
}
