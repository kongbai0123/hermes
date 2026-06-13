import type { AgentGraph, AgentGraphEdge, AgentGraphPosition, AgentSlot } from "@/types/chat";

export type AgentGraphValidationReason =
  | "unknown-node"
  | "self-edge"
  | "planner-incoming"
  | "cycle";

export type AddAgentGraphEdgeResult =
  | { ok: true; graph: AgentGraph }
  | { ok: false; graph: AgentGraph; reason: AgentGraphValidationReason };

const PLANNER_ID = "planner";
const CANVAS_WIDTH = 900;
const CANVAS_CENTER_Y = 150;

export function createDefaultAgentGraph(team: AgentSlot[]): AgentGraph {
  const enabledTeam = getEnabledTeam(team);
  const positions = createDefaultPositions(enabledTeam);
  const [planner, next] = enabledTeam;

  return {
    positions,
    edges:
      planner?.id === PLANNER_ID && next
        ? [{ id: createAgentGraphEdgeId(planner.id, next.id), from: planner.id, to: next.id }]
        : [],
  };
}

export function addAgentGraphEdge(
  graph: AgentGraph,
  team: AgentSlot[],
  edge: Pick<AgentGraphEdge, "from" | "to">
): AddAgentGraphEdgeResult {
  const nodes = new Set(team.map((slot) => slot.id));
  if (!nodes.has(edge.from) || !nodes.has(edge.to)) {
    return { ok: false, graph, reason: "unknown-node" };
  }
  if (edge.from === edge.to) {
    return { ok: false, graph, reason: "self-edge" };
  }
  if (edge.to === PLANNER_ID) {
    return { ok: false, graph, reason: "planner-incoming" };
  }

  const id = createAgentGraphEdgeId(edge.from, edge.to);
  if (graph.edges.some((existing) => existing.id === id)) {
    return { ok: true, graph };
  }

  const nextGraph = {
    ...graph,
    edges: [...graph.edges, { id, from: edge.from, to: edge.to }],
  };

  if (hasCycle(nextGraph.edges, team.map((slot) => slot.id))) {
    return { ok: false, graph, reason: "cycle" };
  }

  return { ok: true, graph: nextGraph };
}

export function removeAgentGraphEdge(graph: AgentGraph, edgeId: string): AgentGraph {
  return {
    ...graph,
    edges: graph.edges.filter((edge) => edge.id !== edgeId),
  };
}

export function removeAgentFromGraph(graph: AgentGraph, agentId: string): AgentGraph {
  const { [agentId]: _removed, ...positions } = graph.positions;
  return {
    positions,
    edges: graph.edges.filter((edge) => edge.from !== agentId && edge.to !== agentId),
  };
}

export function updateAgentGraphPosition(
  graph: AgentGraph,
  agentId: string,
  position: AgentGraphPosition
): AgentGraph {
  return {
    ...graph,
    positions: {
      ...graph.positions,
      [agentId]: position,
    },
  };
}

export function buildAgentGraphLevels(team: AgentSlot[], edges: AgentGraphEdge[]): string[][] {
  const enabledTeam = getEnabledTeam(team);
  const enabledIds = new Set(enabledTeam.map((slot) => slot.id));
  if (!enabledIds.has(PLANNER_ID)) return [];

  const reachable = findReachableIds(PLANNER_ID, edges, enabledIds);
  const relevantIds = enabledTeam.map((slot) => slot.id).filter((id) => reachable.has(id));
  const relevantEdges = edges.filter(
    (edge) => reachable.has(edge.from) && reachable.has(edge.to) && enabledIds.has(edge.from) && enabledIds.has(edge.to)
  );
  const indegree = new Map(relevantIds.map((id) => [id, 0]));
  const outgoing = new Map<string, string[]>();

  for (const edge of relevantEdges) {
    indegree.set(edge.to, (indegree.get(edge.to) ?? 0) + 1);
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge.to]);
  }

  let current = [PLANNER_ID].filter((id) => indegree.get(id) === 0);
  const levels: string[][] = [];
  const visited = new Set<string>();

  while (current.length) {
    const level = sortByTeamOrder(current, enabledTeam).filter((id) => !visited.has(id));
    if (!level.length) break;
    levels.push(level);
    level.forEach((id) => visited.add(id));

    const nextCandidates = new Set<string>();
    for (const id of level) {
      for (const target of outgoing.get(id) ?? []) {
        const nextIndegree = (indegree.get(target) ?? 0) - 1;
        indegree.set(target, nextIndegree);
        if (nextIndegree === 0) nextCandidates.add(target);
      }
    }
    current = Array.from(nextCandidates);
  }

  return levels;
}

export function getTerminalAgentIds(team: AgentSlot[], edges: AgentGraphEdge[]): string[] {
  const levels = buildAgentGraphLevels(team, edges);
  const runnableIds = new Set(levels.flat());
  const hasOutgoing = new Set(
    edges.filter((edge) => runnableIds.has(edge.from) && runnableIds.has(edge.to)).map((edge) => edge.from)
  );

  return team
    .filter((slot) => slot.isEnabled && runnableIds.has(slot.id) && !hasOutgoing.has(slot.id))
    .map((slot) => slot.id);
}

export function createAgentGraphEdgeId(from: string, to: string) {
  return `${from}-to-${to}`;
}

function getEnabledTeam(team: AgentSlot[]) {
  const enabled = team.filter((slot) => slot.isEnabled);
  return enabled.length ? enabled : team;
}

function createDefaultPositions(team: AgentSlot[]) {
  const gap = team.length > 1 ? 640 / Math.max(1, team.length - 1) : 0;
  const startX = team.length > 1 ? 130 : CANVAS_WIDTH / 2;

  return team.reduce<Record<string, AgentGraphPosition>>((positions, slot, index) => {
    positions[slot.id] = {
      x: Math.round(startX + gap * index),
      y: Math.round(CANVAS_CENTER_Y + Math.sin(index * 1.2) * 42),
    };
    return positions;
  }, {});
}

function hasCycle(edges: AgentGraphEdge[], nodeIds: string[]) {
  const visiting = new Set<string>();
  const visited = new Set<string>();
  const outgoing = new Map<string, string[]>();

  for (const edge of edges) {
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge.to]);
  }

  const visit = (id: string): boolean => {
    if (visiting.has(id)) return true;
    if (visited.has(id)) return false;

    visiting.add(id);
    for (const next of outgoing.get(id) ?? []) {
      if (visit(next)) return true;
    }
    visiting.delete(id);
    visited.add(id);
    return false;
  };

  return nodeIds.some((id) => visit(id));
}

function findReachableIds(rootId: string, edges: AgentGraphEdge[], enabledIds: Set<string>) {
  const reachable = new Set<string>();
  const outgoing = new Map<string, string[]>();

  for (const edge of edges) {
    if (!enabledIds.has(edge.from) || !enabledIds.has(edge.to)) continue;
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge.to]);
  }

  const queue = [rootId];
  while (queue.length) {
    const id = queue.shift()!;
    if (reachable.has(id)) continue;
    reachable.add(id);
    queue.push(...(outgoing.get(id) ?? []));
  }

  return reachable;
}

function sortByTeamOrder(ids: string[], team: AgentSlot[]) {
  const order = new Map(team.map((slot, index) => [slot.id, index]));
  return [...ids].sort((left, right) => (order.get(left) ?? 0) - (order.get(right) ?? 0));
}
