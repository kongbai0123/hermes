export type Provider = "ollama" | "openai" | "work-agent" | string;
export type MessageRole = "system" | "user" | "assistant";
export type WorkbenchStatus = "idle" | "running" | "done" | "error";
export type PlanStepStatus = "pending" | "running" | "done" | "error";
export type ReasoningLevel = "low" | "medium" | "high" | "ultra";
export type ResponseSpeed = "slow" | "standard" | "fast";
export type TaskMode = "single" | "multi" | "agent" | "orchestration";
export type AgentPermission = "plan" | "code" | "review" | "verify" | "tools" | "gui" | "external";

export interface Model {
  id: string;
  name: string;
  provider: Provider;
  isActive: boolean;
  description: string;
  availability?: "installed" | "downloadable" | "cloud";
  sizeGb?: number;
  minRamGb?: number;
  minVramGb?: number;
  downloadName?: string;
}

export interface Attachment {
  id: string;
  name: string;
  size: number;
  type?: string;
  dataUrl?: string;
}

export interface WorkbenchPlanStep {
  id: string;
  title: string;
  detail: string;
  status: PlanStepStatus;
}

export interface ToolObservation {
  id: string;
  tool: string;
  ok: boolean;
  summary: string;
  content: string;
  args?: Record<string, string>;
}

export interface SafetyRule {
  id: string;
  label: string;
  description: string;
}

export interface WorkspaceEntry {
  id: string;
  path: string;
  kind: "file" | "dir";
  summary: string;
  children?: WorkspaceEntry[];
}

export interface ProjectBucket {
  id: string;
  title: string;
  chatIds: string[];
  isExpanded: boolean;
}

export interface WorkspaceFilePreview {
  path: string;
  content: string;
}

export interface PatchProposal {
  path: string;
  summary: string;
  diff: string;
  revisedContent?: string;
}

export interface AgentSlot {
  id: string;
  name: string;
  role: string;
  model: string;
  skill: string;
  permissions: AgentPermission[];
  outputFormat: string;
  isEnabled: boolean;
}

export interface AgentGraphPosition {
  x: number;
  y: number;
}

export interface AgentGraphEdge {
  id: string;
  from: string;
  to: string;
}

export interface AgentGraph {
  edges: AgentGraphEdge[];
  positions: Record<string, AgentGraphPosition>;
}

export type AgentRunStatus = "queued" | "running" | "complete" | "error" | "skipped";

export interface AgentRunRecord {
  agentId: string;
  name: string;
  role?: string;
  model?: string;
  status: AgentRunStatus;
  startedAt?: number;
  completedAt?: number;
  updatedAt: number;
  minVisibleUntil?: number;
  output?: string;
  error?: string;
}

export interface AgentRunLogEntry {
  id: string;
  agentId: string;
  name: string;
  event: AgentRunEvent["type"];
  message: string;
  createdAt: number;
}

export type AgentRunEvent =
  | {
      type: "joint-start";
      agentId: string;
      name?: string;
      role?: string;
      model?: string;
      at: number;
      minVisibleMs?: number;
    }
  | {
      type: "joint-complete";
      agentId: string;
      name?: string;
      answer?: string;
      at: number;
    }
  | {
      type: "joint-error";
      agentId: string;
      name?: string;
      error?: string;
      at: number;
    }
  | {
      type: "joint-skip";
      agentId: string;
      name?: string;
      reason?: string;
      at: number;
    };

export interface WorkbenchState {
  status: WorkbenchStatus;
  plan: WorkbenchPlanStep[];
  toolLogs: ToolObservation[];
  safetyRules: SafetyRule[];
  workspaceEntries: WorkspaceEntry[];
  allowedCommands?: string[];
  safetyModeLabel?: string;
  selectedFile?: WorkspaceFilePreview | null;
  patch?: PatchProposal | null;
  agentRuns?: Record<string, AgentRunRecord>;
  agentRunLog?: AgentRunLogEntry[];
}

export interface ChatSettings {
  model: string;
  provider: Provider;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  reasoningLevel: ReasoningLevel;
  responseSpeed: ResponseSpeed;
}

export interface Message {
  id: string;
  chatId: string;
  role: MessageRole;
  content: string;
  createdAt: Date;
  isStreaming?: boolean;
  attachments?: Attachment[];
  plan?: WorkbenchPlanStep[];
  toolLogs?: ToolObservation[];
  patch?: PatchProposal | null;
}

export interface Chat {
  id: string;
  title: string;
  model: string;
  provider: Provider;
  taskMode: TaskMode;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
  settings: ChatSettings;
  agentTeam: AgentSlot[];
  agentGraph?: AgentGraph;
  isPinned?: boolean;
  workbench: WorkbenchState;
}

export interface AppState {
  currentChatId: string | null;
  chats: Chat[];
  projects: ProjectBucket[];
  models: Model[];
  isLoading: boolean;
  theme: "light" | "dark";
  rightPanelOpen: boolean;
  error?: string;
}

export type ChatAction =
  | { type: "HYDRATE_STATE"; payload: AppState }
  | { type: "CREATE_CHAT"; payload: Chat }
  | { type: "SELECT_CHAT"; payload: string }
  | { type: "DELETE_CHAT"; payload: string }
  | { type: "RENAME_CHAT"; payload: { id: string; title: string } }
  | { type: "PIN_CHAT"; payload: string }
  | { type: "CREATE_PROJECT"; payload: ProjectBucket }
  | { type: "TOGGLE_PROJECT"; payload: string }
  | { type: "ASSIGN_CHAT_TO_PROJECT"; payload: { projectId: string; chatId: string } }
  | { type: "ADD_MESSAGE"; payload: Message }
  | { type: "UPDATE_MESSAGE"; payload: Message }
  | { type: "DELETE_MESSAGE"; payload: { chatId: string; messageId: string } }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload?: string }
  | { type: "SET_THEME"; payload: "light" | "dark" }
  | { type: "TOGGLE_RIGHT_PANEL" }
  | { type: "SET_MODELS"; payload: Model[] }
  | {
      type: "UPDATE_CHAT_SETTINGS";
      payload: { chatId: string; settings: Partial<ChatSettings> };
    }
  | {
      type: "SET_TASK_MODE";
      payload: { chatId: string; mode: TaskMode };
    }
  | {
      type: "ADD_AGENT_SLOT";
      payload: { chatId: string; slot?: AgentSlot };
    }
  | {
      type: "UPDATE_AGENT_SLOT";
      payload: { chatId: string; slotId: string; updates: Partial<AgentSlot> };
    }
  | {
      type: "DELETE_AGENT_SLOT";
      payload: { chatId: string; slotId: string };
    }
  | {
      type: "ADD_AGENT_GRAPH_EDGE";
      payload: { chatId: string; from: string; to: string };
    }
  | {
      type: "DELETE_AGENT_GRAPH_EDGE";
      payload: { chatId: string; edgeId: string };
    }
  | {
      type: "UPDATE_AGENT_GRAPH_POSITION";
      payload: { chatId: string; agentId: string; position: AgentGraphPosition };
    }
  | {
      type: "APPLY_AGENT_FLOW_RECOMMENDATION";
      payload: { chatId: string; recommendationId: string };
    }
  | {
      type: "INITIALIZE_AGENT_RUNS";
      payload: { chatId: string; at?: number };
    }
  | {
      type: "UPDATE_AGENT_RUN_EVENT";
      payload: { chatId: string; event: AgentRunEvent };
    }
  | {
      type: "UPDATE_WORKBENCH";
      payload: { chatId: string; workbench: Partial<WorkbenchState> };
    };
