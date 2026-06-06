import { describe, expect, it } from "vitest";
import { chatReducer, restoreChatState } from "./ChatContext";
import type { AppState } from "@/types/chat";

const baseState: AppState = {
  currentChatId: "chat-1",
  chats: [],
  models: [],
  isLoading: false,
  theme: "dark",
  rightPanelOpen: false,
  projects: [
    {
      id: "project-a",
      title: "Project A",
      chatIds: ["chat-1"],
      isExpanded: true,
    },
    {
      id: "project-b",
      title: "Project B",
      chatIds: [],
      isExpanded: true,
    },
  ],
};

describe("chatReducer project item filing", () => {
  it("hydrates state from persistent storage", () => {
    const restored = {
      ...baseState,
      currentChatId: "chat-restored",
      chats: [],
      projects: [],
    };

    const nextState = chatReducer(baseState, {
      type: "HYDRATE_STATE",
      payload: restored,
    });

    expect(nextState.currentChatId).toBe("chat-restored");
    expect(nextState.projects).toEqual([]);
  });

  it("moves a left-sidebar chat item into the target project", () => {
    const nextState = chatReducer(baseState, {
      type: "ASSIGN_CHAT_TO_PROJECT",
      payload: { projectId: "project-b", chatId: "chat-1" },
    });

    expect(nextState.projects[0].chatIds).toEqual([]);
    expect(nextState.projects[1].chatIds).toEqual(["chat-1"]);
  });

  it("updates model controls and records the switch in the chat timeline", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Control test",
          model: "ollama-gemma4",
          provider: "ollama",
          createdAt: new Date(),
          updatedAt: new Date(),
          messages: [],
          settings: {
            model: "ollama-gemma4",
            provider: "ollama",
            temperature: 0.2,
            maxTokens: 2000,
            systemPrompt: "",
            reasoningLevel: "medium",
            responseSpeed: "standard",
          },
          workbench: {
            status: "idle",
            plan: [],
            toolLogs: [],
            safetyRules: [],
            workspaceEntries: [],
            selectedFile: null,
            patch: null,
          },
        },
      ],
    };

    const updated = chatReducer(state, {
      type: "UPDATE_CHAT_SETTINGS",
      payload: {
        chatId: "chat-1",
        settings: {
          reasoningLevel: "high",
          responseSpeed: "fast",
        },
      },
    });
    const nextState = chatReducer(updated, {
      type: "ADD_MESSAGE",
      payload: {
        id: "setting-message",
        chatId: "chat-1",
        role: "system",
        content: "推理已切換至 高",
        createdAt: new Date(),
      },
    });

    expect(nextState.chats[0].settings.reasoningLevel).toBe("high");
    expect(nextState.chats[0].settings.responseSpeed).toBe("fast");
    expect(nextState.chats[0].messages[0].role).toBe("system");
    expect(nextState.chats[0].messages[0].content).toBe("推理已切換至 高");
  });
});

describe("restoreChatState", () => {
  it("rehydrates saved workspace items and dates", () => {
    const saved = JSON.stringify({
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Saved work",
          model: "model",
          provider: "work-agent",
          createdAt: "2026-06-05T00:00:00.000Z",
          updatedAt: "2026-06-05T00:01:00.000Z",
          messages: [
            {
              id: "message-1",
              chatId: "chat-1",
              role: "user",
              content: "persist me",
              createdAt: "2026-06-05T00:02:00.000Z",
            },
          ],
          settings: {
            model: "model",
            provider: "work-agent",
            temperature: 0.2,
            maxTokens: 1000,
            systemPrompt: "",
          },
          workbench: {
            status: "idle",
            plan: [],
            toolLogs: [],
            safetyRules: [],
            workspaceEntries: [],
            selectedFile: null,
            patch: null,
          },
        },
      ],
    });

    const restored = restoreChatState(saved);

    expect(restored.chats).toHaveLength(1);
    expect(restored.projects[0].chatIds).toEqual(["chat-1"]);
    expect(restored.chats[0].createdAt).toBeInstanceOf(Date);
    expect(restored.chats[0].messages[0].createdAt).toBeInstanceOf(Date);
    expect(restored.chats[0].settings.reasoningLevel).toBe("medium");
    expect(restored.chats[0].settings.responseSpeed).toBe("standard");
  });
});
