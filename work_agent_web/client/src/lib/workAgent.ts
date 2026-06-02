import { nanoid } from "nanoid";
import type {
  Chat,
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
  },
  {
    id: "ollama-qwen-local",
    name: "Qwen Local",
    provider: "ollama",
    isActive: true,
    description: "Secondary local model for comparison",
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

export function createDefaultChat(models: Model[]): Chat {
  const activeModel = models[0] ?? WORK_AGENT_MODELS[0];
  return {
    id: nanoid(),
    title: "New Work Task",
    model: activeModel.id,
    provider: activeModel.provider,
    createdAt: new Date(),
    updatedAt: new Date(),
    messages: [],
    settings: {
      model: activeModel.id,
      provider: activeModel.provider,
      temperature: 0.2,
      maxTokens: 2000,
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
