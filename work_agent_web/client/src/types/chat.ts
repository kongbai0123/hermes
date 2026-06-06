export type Provider = "ollama" | "openai" | "work-agent" | string;
export type MessageRole = "system" | "user" | "assistant";
export type WorkbenchStatus = "idle" | "running" | "done" | "error";
export type PlanStepStatus = "pending" | "running" | "done" | "error";

export interface Model {
  id: string;
  name: string;
  provider: Provider;
  isActive: boolean;
  description: string;
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
}

export interface ChatSettings {
  model: string;
  provider: Provider;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
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
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
  settings: ChatSettings;
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
      type: "UPDATE_WORKBENCH";
      payload: { chatId: string; workbench: Partial<WorkbenchState> };
    };
