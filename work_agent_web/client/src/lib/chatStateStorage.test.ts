import { afterEach, describe, expect, it, vi } from "vitest";
import {
  CHAT_STORAGE_KEY,
  fetchServerChatState,
  readLocalChatState,
  writeLocalChatState,
} from "./chatStateStorage";
import type { AppState } from "@/types/chat";

const state = {
  currentChatId: "chat-1",
  chats: [],
  projects: [],
  models: [],
  isLoading: false,
  theme: "dark",
  rightPanelOpen: false,
} satisfies AppState;

describe("chatStateStorage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("reads and writes local chat state", () => {
    const store = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => store.set(key, value),
    });

    writeLocalChatState(state);

    expect(readLocalChatState()).toBe(store.get(CHAT_STORAGE_KEY));
  });

  it("serializes server chat state payloads for restoreChatState", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({ ok: true, state }),
      })),
    );

    await expect(fetchServerChatState()).resolves.toBe(JSON.stringify(state));
  });
});
