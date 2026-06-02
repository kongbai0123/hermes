import { createContext, useContext, useReducer, ReactNode } from "react";
import { AppState, ChatAction, Chat } from "@/types/chat";
import { WORK_AGENT_MODELS } from "@/lib/workAgent";

/**
 * Chat Context: Global state management for LLM chat application
 */

const initialState: AppState = {
  currentChatId: null,
  chats: [],
  models: WORK_AGENT_MODELS,
  isLoading: false,
  theme: "light",
  rightPanelOpen: false,
};

function chatReducer(state: AppState, action: ChatAction): AppState {
  switch (action.type) {
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
  const [state, dispatch] = useReducer(chatReducer, initialState);

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
