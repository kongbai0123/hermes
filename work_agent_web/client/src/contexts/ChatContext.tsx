import { createContext, useContext, useEffect, useReducer, useRef, ReactNode } from "react";
import { AppState, ChatAction, Chat } from "@/types/chat";
import { WORK_AGENT_MODELS } from "@/lib/workAgent";
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
      chats: (parsed.chats || []).map((chat) => ({
        ...chat,
        createdAt: reviveDate(chat.createdAt),
        updatedAt: reviveDate(chat.updatedAt),
        messages: (chat.messages || []).map((message) => ({
          ...message,
          createdAt: reviveDate(message.createdAt),
        })),
      })) as Chat[],
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
