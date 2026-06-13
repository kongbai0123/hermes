import { createContext, useContext, useEffect, useReducer, useRef, ReactNode } from "react";
import { AgentGraph, AppState, ChatAction, Chat, TaskMode } from "@/types/chat";
import {
  addAgentGraphEdge,
  createDefaultAgentGraph,
  removeAgentFromGraph,
  removeAgentGraphEdge,
  updateAgentGraphPosition,
} from "@/lib/agentGraph";
import {
  buildRecommendedAgentFlow,
  getAgentFlowRecommendation,
} from "@/lib/agentFlowRecommendations";
import {
  applyAgentRunEvent,
  createQueuedAgentRuns,
  createRunLogEntry,
} from "@/lib/agentRuns";
import { DEFAULT_AGENT_TEAM, WORK_AGENT_MODELS } from "@/lib/workAgent";
import {
  fetchServerChatState,
  persistServerChatState,
  readLocalChatState,
  writeLocalChatState,
} from "@/lib/chatStateStorage";

/**
 * Chat Context: Global state management for LLM chat application
 */

const initialState: AppState = {
  currentChatId: null,
  chats: [],
  projects: [
    {
      id: "general-project",
      title: "一般專案",
      chatIds: [],
      isExpanded: true,
    },
  ],
  models: WORK_AGENT_MODELS,
  isLoading: false,
  theme: "light",
  rightPanelOpen: false,
};

const taskModeLabels: Record<TaskMode, string> = {
  single: "單模型",
  multi: "多模型",
  agent: "代理操作",
  orchestration: "任務編排",
};

function cloneDefaultAgentTeam() {
  return DEFAULT_AGENT_TEAM.map((slot) => ({ ...slot, permissions: [...slot.permissions] }));
}

function ensureAgentGraph(chat: Pick<Chat, "agentTeam" | "agentGraph">): AgentGraph {
  return chat.agentGraph ?? createDefaultAgentGraph(chat.agentTeam?.length ? chat.agentTeam : cloneDefaultAgentTeam());
}

function reviveDate(value: unknown): Date {
  if (value instanceof Date) return value;
  const date = new Date(String(value || Date.now()));
  return Number.isNaN(date.getTime()) ? new Date() : date;
}

export function restoreChatState(serialized: string | null): AppState {
  if (!serialized) return initialState;

  try {
    const parsed = JSON.parse(serialized) as Partial<AppState>;
    return {
      ...initialState,
      ...parsed,
      models: WORK_AGENT_MODELS,
      chats: (parsed.chats || []).map((chat) => {
        const agentTeam = chat.agentTeam?.length
          ? chat.agentTeam.map((slot) => ({
              ...slot,
              permissions: [...(slot.permissions || [])],
              isEnabled: slot.isEnabled ?? true,
            }))
          : cloneDefaultAgentTeam();

        return {
          ...chat,
          taskMode: chat.taskMode ?? "single",
          agentTeam,
          agentGraph: chat.agentGraph ?? createDefaultAgentGraph(agentTeam),
          createdAt: reviveDate(chat.createdAt),
          updatedAt: reviveDate(chat.updatedAt),
          settings: {
            ...chat.settings,
            reasoningLevel: chat.settings?.reasoningLevel ?? "medium",
            responseSpeed: chat.settings?.responseSpeed ?? "standard",
          },
          messages: (chat.messages || []).map((message) => ({
            ...message,
            createdAt: reviveDate(message.createdAt),
          })),
          workbench: {
            ...chat.workbench,
            agentRuns: chat.workbench?.agentRuns ?? {},
            agentRunLog: chat.workbench?.agentRunLog ?? [],
          },
        };
      }) as Chat[],
      projects: parsed.projects?.length ? parsed.projects : initialState.projects,
    };
  } catch {
    return initialState;
  }
}

export function chatReducer(state: AppState, action: ChatAction): AppState {
  switch (action.type) {
    case "HYDRATE_STATE":
      return action.payload;

    case 'CREATE_CHAT': {
      const newChats = [action.payload, ...state.chats];
      return {
        ...state,
        chats: newChats,
        currentChatId: action.payload.id,
      };
    }

    case 'SELECT_CHAT':
      return {
        ...state,
        currentChatId: action.payload,
      };

    case 'DELETE_CHAT': {
      const newChats = state.chats.filter((chat) => chat.id !== action.payload);
      const newCurrentId =
        state.currentChatId === action.payload ? newChats[0]?.id || null : state.currentChatId;
      return {
        ...state,
        chats: newChats,
        projects: state.projects.map((project) => ({
          ...project,
          chatIds: project.chatIds.filter((chatId) => chatId !== action.payload),
        })),
        currentChatId: newCurrentId,
      };
    }

    case 'RENAME_CHAT': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.id ? { ...chat, title: action.payload.title } : chat
        ),
      };
    }

    case 'PIN_CHAT': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload ? { ...chat, isPinned: !chat.isPinned } : chat
        ),
      };
    }

    case "CREATE_PROJECT": {
      return {
        ...state,
        projects: [action.payload, ...state.projects],
      };
    }

    case "TOGGLE_PROJECT": {
      return {
        ...state,
        projects: state.projects.map((project) =>
          project.id === action.payload
            ? { ...project, isExpanded: !project.isExpanded }
            : project
        ),
      };
    }

    case "ASSIGN_CHAT_TO_PROJECT": {
      return {
        ...state,
        projects: state.projects.map((project) => {
          const chatIds = project.chatIds.filter(
            (chatId) => chatId !== action.payload.chatId
          );

          if (project.id !== action.payload.projectId) {
            return { ...project, chatIds };
          }

          return {
            ...project,
            isExpanded: true,
            chatIds: [action.payload.chatId, ...chatIds],
          };
        }),
      };
    }

    case 'ADD_MESSAGE': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? { ...chat, messages: [...chat.messages, action.payload], updatedAt: new Date() }
            : chat
        ),
      };
    }

    case 'UPDATE_MESSAGE': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                messages: chat.messages.map((msg) =>
                  msg.id === action.payload.id ? action.payload : msg
                ),
              }
            : chat
        ),
      };
    }

    case 'DELETE_MESSAGE': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                messages: chat.messages.filter((msg) => msg.id !== action.payload.messageId),
              }
            : chat
        ),
      };
    }

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };

    case 'SET_THEME':
      return {
        ...state,
        theme: action.payload,
      };

    case 'TOGGLE_RIGHT_PANEL':
      return {
        ...state,
        rightPanelOpen: !state.rightPanelOpen,
      };

    case 'SET_MODELS':
      return {
        ...state,
        models: action.payload,
      };

    case 'UPDATE_CHAT_SETTINGS': {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                model: action.payload.settings.model ?? chat.model,
                provider: action.payload.settings.provider ?? chat.provider,
                settings: { ...chat.settings, ...action.payload.settings },
              }
            : chat
        ),
      };
    }

    case "SET_TASK_MODE": {
      return {
        ...state,
        chats: state.chats.map((chat) => {
          if (chat.id !== action.payload.chatId) return chat;
          if (chat.taskMode === action.payload.mode) return chat;

          return {
            ...chat,
            taskMode: action.payload.mode,
            updatedAt: new Date(),
            messages: [
              ...chat.messages,
              {
                id: `task-mode-${Date.now()}`,
                chatId: chat.id,
                role: "system",
                content: `系統：任務模式已切換為「${taskModeLabels[action.payload.mode]}」。`,
                createdAt: new Date(),
              },
            ],
          };
        }),
      };
    }

    case "ADD_AGENT_SLOT": {
      return {
        ...state,
        chats: state.chats.map((chat) => {
          if (chat.id !== action.payload.chatId) return chat;

          const currentTeam = chat.agentTeam?.length ? chat.agentTeam : cloneDefaultAgentTeam();
          const nextNumber = currentTeam.length + 1;
          const newSlot = action.payload.slot ?? {
            id: `agent-${Date.now()}`,
            name: `Agent ${nextNumber}`,
            role: "自訂角色",
            model: chat.settings.model,
            skill: "描述這個 Agent 的任務、責任範圍、禁止事項與完成條件。",
            permissions: ["plan"],
            outputFormat: "summary",
            isEnabled: true,
          };
          const nextTeam = [...currentTeam, newSlot];
          const graph = ensureAgentGraph({ agentTeam: currentTeam, agentGraph: chat.agentGraph });
          const defaultGraph = createDefaultAgentGraph(nextTeam);

          return {
            ...chat,
            updatedAt: new Date(),
            agentTeam: nextTeam,
            agentGraph: {
              ...graph,
              positions: {
                ...graph.positions,
                [newSlot.id]: defaultGraph.positions[newSlot.id],
              },
            },
          };
        }),
      };
    }

    case "UPDATE_AGENT_SLOT": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                updatedAt: new Date(),
                agentTeam: (chat.agentTeam || cloneDefaultAgentTeam()).map((slot) =>
                  slot.id === action.payload.slotId
                    ? {
                        ...slot,
                        ...action.payload.updates,
                        permissions:
                          action.payload.updates.permissions ?? slot.permissions,
                      }
                    : slot
                ),
              }
            : chat
        ),
      };
    }

    case "DELETE_AGENT_SLOT": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId && action.payload.slotId !== "planner"
            ? {
                ...chat,
                updatedAt: new Date(),
                agentTeam: (chat.agentTeam || []).filter((slot) => slot.id !== action.payload.slotId),
                agentGraph: removeAgentFromGraph(
                  ensureAgentGraph(chat),
                  action.payload.slotId
                ),
              }
            : chat
        ),
      };
    }

    case "ADD_AGENT_GRAPH_EDGE": {
      return {
        ...state,
        chats: state.chats.map((chat) => {
          if (chat.id !== action.payload.chatId) return chat;
          const result = addAgentGraphEdge(ensureAgentGraph(chat), chat.agentTeam, {
            from: action.payload.from,
            to: action.payload.to,
          });
          if (!result.ok) return chat;

          return {
            ...chat,
            updatedAt: new Date(),
            agentGraph: result.graph,
          };
        }),
      };
    }

    case "DELETE_AGENT_GRAPH_EDGE": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                updatedAt: new Date(),
                agentGraph: removeAgentGraphEdge(ensureAgentGraph(chat), action.payload.edgeId),
              }
            : chat
        ),
      };
    }

    case "UPDATE_AGENT_GRAPH_POSITION": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                updatedAt: new Date(),
                agentGraph: updateAgentGraphPosition(
                  ensureAgentGraph(chat),
                  action.payload.agentId,
                  action.payload.position
                ),
              }
            : chat
        ),
      };
    }

    case "APPLY_AGENT_FLOW_RECOMMENDATION": {
      return {
        ...state,
        chats: state.chats.map((chat) => {
          if (chat.id !== action.payload.chatId) return chat;
          if (!getAgentFlowRecommendation(action.payload.recommendationId)) return chat;
          const flow = buildRecommendedAgentFlow(
            action.payload.recommendationId,
            chat.settings.model
          );

          return {
            ...chat,
            updatedAt: new Date(),
            taskMode: "orchestration",
            agentTeam: flow.agentTeam,
            agentGraph: flow.agentGraph,
            workbench: {
              ...chat.workbench,
              agentRuns: {},
              agentRunLog: [],
            },
          };
        }),
      };
    }

    case "INITIALIZE_AGENT_RUNS": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                updatedAt: new Date(),
                workbench: {
                  ...chat.workbench,
                  agentRuns: createQueuedAgentRuns(chat.agentTeam, action.payload.at),
                  agentRunLog: [],
                },
              }
            : chat
        ),
      };
    }

    case "UPDATE_AGENT_RUN_EVENT": {
      return {
        ...state,
        chats: state.chats.map((chat) => {
          if (chat.id !== action.payload.chatId) return chat;
          const event = action.payload.event;

          return {
            ...chat,
            updatedAt: new Date(),
            workbench: {
              ...chat.workbench,
              agentRuns: applyAgentRunEvent(chat.workbench.agentRuns ?? {}, event),
              agentRunLog: [
                ...(chat.workbench.agentRunLog ?? []),
                createRunLogEntry(event),
              ].slice(-30),
            },
          };
        }),
      };
    }

    case "UPDATE_WORKBENCH": {
      return {
        ...state,
        chats: state.chats.map((chat) =>
          chat.id === action.payload.chatId
            ? {
                ...chat,
                updatedAt: new Date(),
                workbench: { ...chat.workbench, ...action.payload.workbench },
              }
            : chat
        ),
      };
    }

    default:
      return state;
  }
}

interface ChatContextType {
  state: AppState;
  dispatch: (action: ChatAction) => void;
  currentChat: Chat | null;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const hasLoadedServerState = useRef(false);
  const [state, dispatch] = useReducer(
    chatReducer,
    initialState,
    () => restoreChatState(readLocalChatState())
  );

  useEffect(() => {
    let cancelled = false;

    fetchServerChatState()
      .then((serialized) => {
        if (cancelled || !serialized) return;
        dispatch({ type: "HYDRATE_STATE", payload: restoreChatState(serialized) });
      })
      .catch(() => undefined)
      .finally(() => {
        hasLoadedServerState.current = true;
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    writeLocalChatState(state);
    if (!hasLoadedServerState.current) return;
    persistServerChatState(state).catch(() => undefined);
  }, [state]);

  const currentChat = state.currentChatId
    ? state.chats.find((chat) => chat.id === state.currentChatId) || null
    : null;

  return (
    <ChatContext.Provider value={{ state, dispatch, currentChat }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within ChatProvider');
  }
  return context;
}
