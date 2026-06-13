import type { AgentRunEvent, AgentRunLogEntry, AgentRunRecord, AgentSlot } from "@/types/chat";

export const MIN_JOINT_RUNNING_VISIBLE_MS = 500;

export function createQueuedAgentRuns(
  team: AgentSlot[],
  at = Date.now()
): Record<string, AgentRunRecord> {
  return team
    .filter((slot) => slot.isEnabled)
    .reduce<Record<string, AgentRunRecord>>((runs, slot) => {
      runs[slot.id] = {
        agentId: slot.id,
        name: slot.name,
        status: "queued",
        updatedAt: at,
      };
      return runs;
    }, {});
}

export function applyAgentRunEvent(
  runs: Record<string, AgentRunRecord> = {},
  event: AgentRunEvent
): Record<string, AgentRunRecord> {
  const previous = runs[event.agentId] ?? {
    agentId: event.agentId,
    name: event.name ?? event.agentId,
    status: "queued",
    updatedAt: event.at,
  };
  const name = event.name ?? previous.name ?? event.agentId;

  if (event.type === "joint-start") {
    return {
      ...runs,
      [event.agentId]: {
        ...previous,
        agentId: event.agentId,
        name,
        model: event.model ?? previous.model,
        role: event.role ?? previous.role,
        status: "running",
        startedAt: event.at,
        minVisibleUntil: event.at + (event.minVisibleMs ?? MIN_JOINT_RUNNING_VISIBLE_MS),
        updatedAt: event.at,
      },
    };
  }

  if (event.type === "joint-complete") {
    return {
      ...runs,
      [event.agentId]: {
        ...previous,
        agentId: event.agentId,
        name,
        status: "complete",
        output: event.answer,
        completedAt: event.at,
        updatedAt: event.at,
      },
    };
  }

  if (event.type === "joint-error") {
    return {
      ...runs,
      [event.agentId]: {
        ...previous,
        agentId: event.agentId,
        name,
        status: "error",
        error: event.error,
        completedAt: event.at,
        updatedAt: event.at,
      },
    };
  }

  return {
    ...runs,
    [event.agentId]: {
      ...previous,
      agentId: event.agentId,
      name,
      status: "skipped",
      error: event.reason,
      completedAt: event.at,
      updatedAt: event.at,
    },
  };
}

export function createRunLogEntry(event: AgentRunEvent): AgentRunLogEntry {
  return {
    id: `${event.at}-${event.agentId}-${event.type}`,
    agentId: event.agentId,
    name: event.name ?? event.agentId,
    event: event.type,
    message: `${event.name ?? event.agentId} ${eventLabel(event)}`,
    createdAt: event.at,
  };
}

function eventLabel(event: AgentRunEvent) {
  if (event.type === "joint-start") return "started";
  if (event.type === "joint-complete") return "completed";
  if (event.type === "joint-error") return "failed";
  return "skipped";
}
