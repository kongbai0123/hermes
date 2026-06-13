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

  it("switches the task mode and records the change in the chat timeline", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Mode test",
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

    const nextState = chatReducer(state, {
      type: "SET_TASK_MODE",
      payload: {
        chatId: "chat-1",
        mode: "orchestration",
      },
    });

    expect(nextState.chats[0].taskMode).toBe("orchestration");
    expect(nextState.chats[0].messages).toHaveLength(1);
    expect(nextState.chats[0].messages[0].role).toBe("system");
    expect(nextState.chats[0].messages[0].content).toBe("系統：任務模式已切換為「任務編排」。");
  });

  it("manages agent team slots for multi-model work", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Agent team test",
          model: "ollama-gemma4",
          provider: "ollama",
          taskMode: "multi",
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
          agentTeam: [
            {
              id: "planner",
              name: "Planner",
              role: "規劃者",
              model: "ollama-gemma4",
              skill: "拆解任務並定義成功條件。",
              permissions: ["plan"],
              outputFormat: "plan",
              isEnabled: true,
            },
          ],
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

    const added = chatReducer(state, {
      type: "ADD_AGENT_SLOT",
      payload: { chatId: "chat-1" },
    });

    expect(added.chats[0].agentTeam).toHaveLength(2);
    expect(added.chats[0].agentTeam[1].name).toBe("Agent 2");

    const updated = chatReducer(added, {
      type: "UPDATE_AGENT_SLOT",
      payload: {
        chatId: "chat-1",
        slotId: added.chats[0].agentTeam[1].id,
        updates: {
          name: "Reviewer",
          role: "審核者",
          skill: "檢查輸出是否符合需求、安全規則與測試結果。",
          permissions: ["review", "verify"],
          outputFormat: "critique",
        },
      },
    });

    expect(updated.chats[0].agentTeam[1].name).toBe("Reviewer");
    expect(updated.chats[0].agentTeam[1].permissions).toEqual(["review", "verify"]);
    expect(updated.chats[0].agentTeam[1].outputFormat).toBe("critique");

    const plannerDeleteAttempt = chatReducer(updated, {
      type: "DELETE_AGENT_SLOT",
      payload: {
        chatId: "chat-1",
        slotId: "planner",
      },
    });

    expect(plannerDeleteAttempt.chats[0].agentTeam).toHaveLength(2);
    expect(plannerDeleteAttempt.chats[0].agentTeam[0].name).toBe("Planner");

    const removed = chatReducer(plannerDeleteAttempt, {
      type: "DELETE_AGENT_SLOT",
      payload: {
        chatId: "chat-1",
        slotId: updated.chats[0].agentTeam[1].id,
      },
    });

    expect(removed.chats[0].agentTeam).toHaveLength(1);
    expect(removed.chats[0].agentTeam[0].name).toBe("Planner");
  });

  it("persists agent graph edges and positions", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Graph test",
          model: "ollama-gemma4",
          provider: "ollama",
          taskMode: "orchestration",
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
          agentTeam: [
            {
              id: "planner",
              name: "Planner",
              role: "規劃者",
              model: "ollama-gemma4",
              skill: "拆解任務並定義成功條件。",
              permissions: ["plan"],
              outputFormat: "plan",
              isEnabled: true,
            },
            {
              id: "coder",
              name: "Coder",
              role: "執行者",
              model: "ollama-qwen-local",
              skill: "執行 Planner 的計畫。",
              permissions: ["code"],
              outputFormat: "proposal",
              isEnabled: true,
            },
          ],
          agentGraph: {
            edges: [],
            positions: {},
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

    const withEdge = chatReducer(state, {
      type: "ADD_AGENT_GRAPH_EDGE",
      payload: { chatId: "chat-1", from: "planner", to: "coder" },
    });

    expect(withEdge.chats[0].agentGraph?.edges).toEqual([
      { id: "planner-to-coder", from: "planner", to: "coder" },
    ]);

    const withPosition = chatReducer(withEdge, {
      type: "UPDATE_AGENT_GRAPH_POSITION",
      payload: { chatId: "chat-1", agentId: "coder", position: { x: 240, y: 120 } },
    });

    expect(withPosition.chats[0].agentGraph?.positions.coder).toEqual({ x: 240, y: 120 });

    const removedCoder = chatReducer(withPosition, {
      type: "DELETE_AGENT_SLOT",
      payload: { chatId: "chat-1", slotId: "coder" },
    });

    expect(removedCoder.chats[0].agentTeam.map((slot) => slot.id)).toEqual(["planner"]);
    expect(removedCoder.chats[0].agentGraph?.edges).toEqual([]);
    expect(removedCoder.chats[0].agentGraph?.positions.coder).toBeUndefined();
  });

  it("applies a recommended neural flow to the agent team and graph", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Recommendation test",
          model: "ollama-gemma4",
          provider: "ollama",
          taskMode: "orchestration",
          createdAt: new Date(),
          updatedAt: new Date(),
          messages: [],
          settings: {
            model: "ollama-qwen-local",
            provider: "ollama",
            temperature: 0.2,
            maxTokens: 2000,
            systemPrompt: "",
            reasoningLevel: "medium",
            responseSpeed: "standard",
          },
          agentTeam: [],
          agentGraph: { edges: [], positions: {} },
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

    const nextState = chatReducer(state, {
      type: "APPLY_AGENT_FLOW_RECOMMENDATION",
      payload: { chatId: "chat-1", recommendationId: "neural-collaboration" },
    });

    expect(nextState.chats[0].agentTeam.map((slot) => slot.id)).toEqual([
      "planner",
      "signal-analyzer",
      "generator",
      "critic",
      "hidden-integrator-a",
      "hidden-integrator-b",
      "output-synthesizer",
      "verifier",
    ]);
    expect(nextState.chats[0].agentTeam.every((slot) => slot.model === "ollama-qwen-local")).toBe(true);
    expect(nextState.chats[0].agentGraph?.edges).toContainEqual({
      id: "hidden-integrator-b-to-output-synthesizer",
      from: "hidden-integrator-b",
      to: "output-synthesizer",
    });
    expect(nextState.chats[0].workbench.agentRuns).toEqual({});
    expect(nextState.chats[0].workbench.agentRunLog).toEqual([]);
  });

  it("tracks graph stream events per joint instead of inferring active index", () => {
    const state: AppState = {
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Run state test",
          model: "ollama-gemma4",
          provider: "ollama",
          taskMode: "orchestration",
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
          agentTeam: [
            {
              id: "planner",
              name: "Planner",
              role: "規劃者",
              model: "ollama-gemma4",
              skill: "Plan.",
              permissions: ["plan"],
              outputFormat: "plan",
              isEnabled: true,
            },
            {
              id: "generator",
              name: "Generator",
              role: "產生者",
              model: "ollama-gemma4",
              skill: "Generate.",
              permissions: ["code"],
              outputFormat: "draft",
              isEnabled: true,
            },
          ],
          agentGraph: {
            edges: [{ id: "planner-to-generator", from: "planner", to: "generator" }],
            positions: {},
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

    const initialized = chatReducer(state, {
      type: "INITIALIZE_AGENT_RUNS",
      payload: { chatId: "chat-1", at: 1000 },
    });
    const running = chatReducer(initialized, {
      type: "UPDATE_AGENT_RUN_EVENT",
      payload: {
        chatId: "chat-1",
        event: { type: "joint-start", agentId: "generator", name: "Generator", at: 1200 },
      },
    });
    const completed = chatReducer(running, {
      type: "UPDATE_AGENT_RUN_EVENT",
      payload: {
        chatId: "chat-1",
        event: {
          type: "joint-complete",
          agentId: "generator",
          name: "Generator",
          answer: "done",
          at: 1600,
        },
      },
    });

    expect(initialized.chats[0].workbench.agentRuns?.planner.status).toBe("queued");
    expect(running.chats[0].workbench.agentRuns?.generator).toMatchObject({
      status: "running",
      minVisibleUntil: 1700,
    });
    expect(completed.chats[0].workbench.agentRuns?.generator).toMatchObject({
      status: "complete",
      output: "done",
    });
    expect(completed.chats[0].workbench.agentRunLog?.map((entry) => entry.message)).toEqual([
      "Generator started",
      "Generator completed",
    ]);
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
    expect(restored.chats[0].taskMode).toBe("single");
    expect(restored.chats[0].agentTeam).toHaveLength(2);
    expect(restored.chats[0].agentTeam[0].name).toBe("Planner");
    expect(restored.chats[0].agentGraph?.edges).toEqual([
      { id: "planner-to-coder", from: "planner", to: "coder" },
    ]);
  });

  it("preserves saved agent graph data", () => {
    const saved = JSON.stringify({
      ...baseState,
      chats: [
        {
          id: "chat-1",
          title: "Saved graph",
          model: "model",
          provider: "work-agent",
          taskMode: "orchestration",
          createdAt: "2026-06-05T00:00:00.000Z",
          updatedAt: "2026-06-05T00:01:00.000Z",
          messages: [],
          settings: {
            model: "model",
            provider: "work-agent",
            temperature: 0.2,
            maxTokens: 1000,
            systemPrompt: "",
          },
          agentTeam: [
            {
              id: "planner",
              name: "Planner",
              role: "規劃者",
              model: "model",
              skill: "Plan.",
              permissions: ["plan"],
              outputFormat: "plan",
              isEnabled: true,
            },
            {
              id: "coder",
              name: "Coder",
              role: "執行者",
              model: "model",
              skill: "Code.",
              permissions: ["code"],
              outputFormat: "proposal",
              isEnabled: true,
            },
          ],
          agentGraph: {
            edges: [{ id: "planner-to-coder", from: "planner", to: "coder" }],
            positions: { planner: { x: 130, y: 150 }, coder: { x: 320, y: 150 } },
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

    expect(restored.chats[0].agentGraph).toEqual({
      edges: [{ id: "planner-to-coder", from: "planner", to: "coder" }],
      positions: { planner: { x: 130, y: 150 }, coder: { x: 320, y: 150 } },
    });
  });
});
