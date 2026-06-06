import type { AppState } from "@/types/chat";

export const CHAT_STORAGE_KEY = "work-agent-chat-state";

export function readLocalChatState(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(CHAT_STORAGE_KEY);
}

export function writeLocalChatState(state: AppState): void {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(state));
}

export async function fetchServerChatState(): Promise<string | null> {
  const response = await fetch("/api/chat-state");
  if (!response.ok) return null;

  const payload = await response.json();
  if (!payload?.ok || !payload.state) return null;
  return JSON.stringify(payload.state);
}

export async function persistServerChatState(state: AppState): Promise<void> {
  await fetch("/api/chat-state", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });
}
