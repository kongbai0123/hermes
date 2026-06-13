import { useMemo, useRef, useState } from "react";
import type { PointerEvent } from "react";
import {
  Bot,
  CheckCircle2,
  GitBranch,
  HeartPulse,
  LayoutGrid,
  Link2,
  ListChecks,
  Plus,
  RotateCcw,
  Save,
  Sparkles,
  Trash2,
  X,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChat } from "@/contexts/ChatContext";
import { cn } from "@/lib/utils";
import { AGENT_FLOW_RECOMMENDATIONS } from "@/lib/agentFlowRecommendations";
import {
  createDefaultAgentGraph,
  createAgentGraphEdgeId,
} from "@/lib/agentGraph";
import type { AgentGraph, AgentPermission, AgentRunStatus, AgentSlot, WorkbenchState } from "@/types/chat";

export type AgentFlowLayerMode = "background" | "interactive";
type CanvasNodeState = "idle" | "active" | "complete" | "error";
type CanvasEdgeKind = "handoff" | "return";

interface CanvasNode {
  id: string;
  name: string;
  role: string;
  model: string;
  x: number;
  y: number;
  state: CanvasNodeState;
  isEnabled: boolean;
}

interface CanvasEdge {
  id: string;
  from: string;
  to: string;
  kind: CanvasEdgeKind;
}

interface AgentCanvasModel {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  currentLabel: string;
}

interface AgentFlowPanelProps {
  isOpen?: boolean;
  mode?: AgentFlowLayerMode;
  onClose: () => void;
}

const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 300;
const NODE_RADIUS = 38;
const CANVAS_PADDING = NODE_RADIUS + 12;
const MIN_ZOOM = 0.7;
const MAX_ZOOM = 1.8;
const ZOOM_STEP = 0.12;
const DRAG_CLICK_THRESHOLD = 4;

interface CanvasPoint {
  x: number;
  y: number;
}

interface DragState {
  nodeId: string;
  pointerId: number;
  offset: CanvasPoint;
  start: CanvasPoint;
  moved: boolean;
}

export function resolveAgentFlowLayerPresentation(mode: AgentFlowLayerMode) {
  if (mode === "background") {
    return {
      canInteract: false,
      containerClassName:
        "pointer-events-none absolute inset-0 z-0 border-0 bg-transparent opacity-35",
      canvasClassName: "h-full min-h-[420px] w-full touch-none",
      headerClassName: "",
    };
  }

  return {
    canInteract: true,
    containerClassName:
      "absolute inset-0 z-20 border-0 bg-background/92 shadow-none backdrop-blur-sm",
    canvasClassName: "h-full min-h-[420px] w-full touch-none",
    headerClassName: "pr-44",
  };
}

export function clampCanvasPosition(position: CanvasPoint): CanvasPoint {
  return {
    x: Math.max(CANVAS_PADDING, Math.min(CANVAS_WIDTH - CANVAS_PADDING, position.x)),
    y: Math.max(CANVAS_PADDING, Math.min(CANVAS_HEIGHT - CANVAS_PADDING, position.y)),
  };
}

export function resolveNodeDragPosition({
  pointer,
  offset,
}: {
  pointer: CanvasPoint;
  offset: CanvasPoint;
}): CanvasPoint {
  return clampCanvasPosition({
    x: pointer.x - offset.x,
    y: pointer.y - offset.y,
  });
}

export function resolveWheelZoom(currentZoom: number, deltaY: number): number {
  const nextZoom = currentZoom + (deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP);
  return Number(Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, nextZoom)).toFixed(2));
}

export function resolveMonitorViewport(zoom: number) {
  const safeZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom));
  const width = Number((CANVAS_WIDTH / safeZoom).toFixed(2));
  const height = Number((CANVAS_HEIGHT / safeZoom).toFixed(2));
  return {
    x: Number(((CANVAS_WIDTH - width) / 2).toFixed(2)),
    y: Number(((CANVAS_HEIGHT - height) / 2).toFixed(2)),
    width,
    height,
  };
}

export function createAgentCanvasModel(
  agentTeam: AgentSlot[] = [],
  agentGraph?: AgentGraph,
  workbench?: WorkbenchState
): AgentCanvasModel {
  const enabledAgents = agentTeam.filter((slot) => slot.isEnabled);
  const graphAgentIds = new Set((agentGraph?.edges ?? []).flatMap((edge) => [edge.from, edge.to]));
  const agents = agentTeam.filter((slot) => slot.isEnabled || graphAgentIds.has(slot.id));
  const visibleAgents = agents.length ? agents : enabledAgents.length ? enabledAgents : agentTeam;
  const centerY = 150;
  const gap = visibleAgents.length > 1 ? 640 / Math.max(1, visibleAgents.length - 1) : 0;
  const startX = visibleAgents.length > 1 ? 130 : CANVAS_WIDTH / 2;

  const activeIndex = resolveActiveIndex(visibleAgents.length, workbench);

  const nodes = visibleAgents.map((slot, index) => ({
    id: slot.id,
    name: slot.name,
    role: slot.role,
    model: slot.model,
    x: agentGraph?.positions[slot.id]?.x ?? startX + gap * index,
    y: agentGraph?.positions[slot.id]?.y ?? centerY + Math.sin(index * 1.2) * 42,
    state: resolveNodeState(index, activeIndex, workbench?.status, workbench?.agentRuns?.[slot.id]?.status),
    isEnabled: slot.isEnabled,
  }));

  const visibleNodeIds = new Set(nodes.map((node) => node.id));
  const graphEdges = agentGraph?.edges.length ? agentGraph.edges : createDefaultAgentGraph(visibleAgents).edges;
  const edges: CanvasEdge[] = graphEdges
    .filter((edge) => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to))
    .map((edge) => ({ ...edge, kind: "handoff" }));

  if (workbench?.status === "error" && nodes.length > 1) {
    const from = nodes[Math.min(activeIndex, nodes.length - 1)];
    const to = nodes[Math.max(0, Math.min(activeIndex - 1, nodes.length - 2))];
    edges.push({
      id: `${from.id}-to-${to.id}-repair`,
      from: from.id,
      to: to.id,
      kind: "return",
    });
  }

  return {
    nodes,
    edges,
    currentLabel: resolveCurrentLabel(workbench),
  };
}

export default function AgentFlowPanel({ isOpen, mode, onClose }: AgentFlowPanelProps) {
  const { state, currentChat, dispatch } = useChat();
  const layerMode = mode ?? (isOpen ? "interactive" : "background");
  const presentation = resolveAgentFlowLayerPresentation(layerMode);
  const baseModel = useMemo(
    () =>
      createAgentCanvasModel(
        currentChat?.agentTeam ?? [],
        currentChat?.agentGraph,
        currentChat?.workbench
      ),
    [currentChat?.agentTeam, currentChat?.agentGraph, currentChat?.workbench]
  );
  const [zoom, setZoom] = useState(1);
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [connectMode, setConnectMode] = useState(false);
  const [connectSourceId, setConnectSourceId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [editingSlot, setEditingSlot] = useState<AgentSlot | null>(null);
  const [recommendationsOpen, setRecommendationsOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const dragStateRef = useRef<DragState | null>(null);
  const suppressClickNodeRef = useRef<string | null>(null);
  const model = baseModel;
  const viewport = resolveMonitorViewport(zoom);

  if (!mode && !isOpen) return null;

  const getCanvasPoint = (clientX: number, clientY: number, svg: SVGSVGElement): CanvasPoint => {
    const rect = svg.getBoundingClientRect();
    return {
      x: viewport.x + ((clientX - rect.left) / rect.width) * viewport.width,
      y: viewport.y + ((clientY - rect.top) / rect.height) * viewport.height,
    };
  };

  const updateNodePosition = (nodeId: string, position: CanvasPoint) => {
    if (!currentChat) return;
    const clamped = clampCanvasPosition(position);
    dispatch({
      type: "UPDATE_AGENT_GRAPH_POSITION",
      payload: {
        chatId: currentChat.id,
        agentId: nodeId,
        position: clamped,
      },
    });
  };

  const startNodeDrag = (
    node: CanvasNode,
    event: PointerEvent<SVGGElement>
  ) => {
    if (!presentation.canInteract || connectMode) return;
    const svg = event.currentTarget.ownerSVGElement;
    if (!svg) return;
    event.preventDefault();
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    const pointer = getCanvasPoint(event.clientX, event.clientY, svg);
    dragStateRef.current = {
      nodeId: node.id,
      pointerId: event.pointerId,
      offset: { x: pointer.x - node.x, y: pointer.y - node.y },
      start: pointer,
      moved: false,
    };
    setDraggingNode(node.id);
  };

  const moveNodeDrag = (event: PointerEvent<SVGSVGElement>) => {
    const drag = dragStateRef.current;
    if (!presentation.canInteract || !drag) return;
    const pointer = getCanvasPoint(event.clientX, event.clientY, event.currentTarget);
    const hasMoved =
      Math.abs(pointer.x - drag.start.x) > DRAG_CLICK_THRESHOLD ||
      Math.abs(pointer.y - drag.start.y) > DRAG_CLICK_THRESHOLD;
    dragStateRef.current = { ...drag, moved: drag.moved || hasMoved };
    updateNodePosition(
      drag.nodeId,
      resolveNodeDragPosition({
        pointer,
        offset: drag.offset,
      })
    );
  };

  const endNodeDrag = () => {
    const drag = dragStateRef.current;
    if (drag?.moved) suppressClickNodeRef.current = drag.nodeId;
    dragStateRef.current = null;
    setDraggingNode(null);
  };

  const openNewJointDialog = () => {
    if (!currentChat) return;
    setEditingSlot({
      id: `agent-${Date.now()}`,
      name: `Agent ${(currentChat.agentTeam?.length ?? 0) + 1}`,
      role: "自訂角色",
      model: currentChat.settings.model,
      skill: "描述這個 joint 的任務、責任範圍、禁止事項與完成條件。",
      permissions: ["plan"],
      outputFormat: "summary",
      isEnabled: true,
    });
  };

  const saveEditingSlot = () => {
    if (!currentChat || !editingSlot) return;
    const exists = currentChat.agentTeam.some((slot) => slot.id === editingSlot.id);
    dispatch(
      exists
        ? {
            type: "UPDATE_AGENT_SLOT",
            payload: { chatId: currentChat.id, slotId: editingSlot.id, updates: editingSlot },
          }
        : {
            type: "ADD_AGENT_SLOT",
            payload: { chatId: currentChat.id, slot: editingSlot },
          }
    );
    setEditingSlot(null);
  };

  const deleteSelection = () => {
    if (!currentChat) return;
    if (selectedEdgeId) {
      dispatch({
        type: "DELETE_AGENT_GRAPH_EDGE",
        payload: { chatId: currentChat.id, edgeId: selectedEdgeId },
      });
      setSelectedEdgeId(null);
      return;
    }
    if (selectedNodeId && selectedNodeId !== "planner") {
      dispatch({
        type: "DELETE_AGENT_SLOT",
        payload: { chatId: currentChat.id, slotId: selectedNodeId },
      });
      setSelectedNodeId(null);
    }
  };

  const handleNodeClick = (nodeId: string) => {
    if (!currentChat) return;
    if (suppressClickNodeRef.current === nodeId) {
      suppressClickNodeRef.current = null;
      return;
    }
    setSelectedNodeId(nodeId);
    setSelectedEdgeId(null);

    if (connectMode) {
      if (!connectSourceId) {
        setConnectSourceId(nodeId);
        setStatusMessage("已選擇來源 joint，請點擊目標 joint。");
        return;
      }

      const beforeCount = currentChat.agentGraph?.edges.length ?? 0;
      dispatch({
        type: "ADD_AGENT_GRAPH_EDGE",
        payload: { chatId: currentChat.id, from: connectSourceId, to: nodeId },
      });
      const edgeId = createAgentGraphEdgeId(connectSourceId, nodeId);
      setSelectedEdgeId(edgeId);
      setConnectSourceId(null);
      setStatusMessage(beforeCount === currentChat.agentGraph?.edges.length ? "已送出連線要求。" : "連線已建立。");
      return;
    }

    const slot = currentChat.agentTeam.find((agent) => agent.id === nodeId);
    if (slot) setEditingSlot({ ...slot, permissions: [...slot.permissions] });
  };

  const autoLayout = () => {
    if (!currentChat) return;
    const graph = createDefaultAgentGraph(currentChat.agentTeam);
    Object.entries(graph.positions).forEach(([agentId, position]) => {
      dispatch({
        type: "UPDATE_AGENT_GRAPH_POSITION",
        payload: { chatId: currentChat.id, agentId, position },
      });
    });
  };

  const applyRecommendation = (recommendationId: string) => {
    if (!currentChat) return;
    dispatch({
      type: "APPLY_AGENT_FLOW_RECOMMENDATION",
      payload: { chatId: currentChat.id, recommendationId },
    });
    setRecommendationsOpen(false);
    setSelectedEdgeId(null);
    setSelectedNodeId(null);
    setStatusMessage("已套用推薦流程，節點與串接已重新佈置。");
  };

  return (
    <section className={presentation.containerClassName}>
      <style>{`
        @keyframes monitor-breathe {
          0%, 100% { filter: drop-shadow(0 0 8px rgba(45, 212, 191, 0.18)); }
          50% { filter: drop-shadow(0 0 22px rgba(96, 165, 250, 0.48)); }
        }

        @keyframes monitor-flow {
          0% { stroke-dashoffset: 28; opacity: 0.45; }
          50% { opacity: 1; }
          100% { stroke-dashoffset: 0; opacity: 0.45; }
        }

        .runtime-monitor-node-active {
          animation: monitor-breathe 2.4s ease-in-out infinite;
        }

        .runtime-monitor-edge-active {
          stroke-dasharray: 7 7;
          animation: monitor-flow 1.8s linear infinite;
        }

        @media (prefers-reduced-motion: reduce) {
          .runtime-monitor-node-active,
          .runtime-monitor-edge-active {
            animation: none;
          }
        }
      `}</style>

      <div
        className={cn(
          "flex h-full w-full flex-col",
          presentation.canInteract ? "gap-3 px-4 py-3" : "justify-center px-4 py-8"
        )}
      >
        <div
          className={cn(
            "flex items-start justify-between gap-3",
            presentation.headerClassName,
            !presentation.canInteract && "sr-only"
          )}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-teal-500" />
              <h2 className="text-sm font-semibold">運行監控</h2>
              <span className="rounded-full bg-teal-500/10 px-2 py-0.5 text-xs text-teal-600">
                Agent Team Canvas
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {model.currentLabel}。拖曳 joint 調整位置，連線模式可串接任務輸入。
            </p>
            {statusMessage ? <p className="mt-1 text-xs text-teal-600">{statusMessage}</p> : null}
          </div>
          <div className="flex shrink-0 flex-wrap items-center justify-end gap-1">
            <div className="relative">
              <Button
                variant={recommendationsOpen ? "default" : "outline"}
                size="sm"
                onClick={() => setRecommendationsOpen((current) => !current)}
                title="推薦流程"
              >
                <ListChecks className="mr-1 h-4 w-4" />
                推薦流程
              </Button>
              {recommendationsOpen ? (
                <div className="absolute right-0 top-10 z-40 w-80 rounded-lg border border-border bg-background p-2 shadow-xl">
                  <div className="mb-2 px-2 text-xs font-medium text-muted-foreground">
                    選擇後會重新佈置 Joint 與串接
                  </div>
                  <div className="grid gap-1">
                    {AGENT_FLOW_RECOMMENDATIONS.map((recommendation) => (
                      <button
                        key={recommendation.id}
                        type="button"
                        className="rounded-md px-2 py-2 text-left hover:bg-accent"
                        onClick={() => applyRecommendation(recommendation.id)}
                      >
                        <div className="text-sm font-medium">{recommendation.name}</div>
                        <div className="mt-0.5 text-xs text-muted-foreground">
                          {recommendation.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
            <div className="mr-1 flex items-center rounded-md border border-border bg-background/80 p-0.5">
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setZoom((current) => resolveWheelZoom(current, 120))}
                title="縮小監控畫布"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <button
                type="button"
                className="h-8 min-w-12 rounded px-2 text-xs font-medium text-muted-foreground"
                onClick={() => setZoom(1)}
                title="重設縮放"
              >
                {Math.round(zoom * 100)}%
              </button>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => setZoom((current) => resolveWheelZoom(current, -120))}
                title="放大監控畫布"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={openNewJointDialog} title="新增 joint">
              <Plus className="mr-1 h-4 w-4" />
              Joint
            </Button>
            <Button
              variant={connectMode ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setConnectMode((current) => !current);
                setConnectSourceId(null);
              }}
              title="連線模式"
            >
              <Link2 className="mr-1 h-4 w-4" />
              Connect
            </Button>
            <Button variant="outline" size="icon" onClick={autoLayout} title="自動排列">
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={deleteSelection}
              disabled={!selectedEdgeId && (!selectedNodeId || selectedNodeId === "planner")}
              title="刪除選取項目"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose} title="關閉運行監控">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div
          className={cn(
            "overflow-hidden rounded-lg border border-border bg-gradient-to-br from-sky-50 via-teal-50 to-rose-50 p-3 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950",
            presentation.canInteract
              ? "flex-1"
              : "mx-auto h-full max-h-[620px] w-full max-w-6xl border-teal-500/20 bg-gradient-to-br from-sky-50/40 via-teal-50/40 to-rose-50/30 p-0 blur-[0.2px] dark:from-slate-950/50 dark:via-slate-900/50 dark:to-slate-950/50"
          )}
        >
          <svg
            viewBox={`${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`}
            className={presentation.canvasClassName}
            role="img"
            aria-label="Agent Team Canvas"
            onWheel={(event) => {
              if (!presentation.canInteract) return;
              event.preventDefault();
              setZoom((current) => resolveWheelZoom(current, event.deltaY));
            }}
            onPointerMove={moveNodeDrag}
            onPointerUp={endNodeDrag}
            onPointerCancel={endNodeDrag}
            onPointerLeave={endNodeDrag}
          >
            <defs>
              <marker
                id="monitor-arrow"
                markerHeight="8"
                markerWidth="8"
                orient="auto"
                refX="6"
                refY="4"
              >
                <path d="M0,0 L8,4 L0,8 Z" fill="#14b8a6" />
              </marker>
              <marker
                id="monitor-return-arrow"
                markerHeight="8"
                markerWidth="8"
                orient="auto"
                refX="6"
                refY="4"
              >
                <path d="M0,0 L8,4 L0,8 Z" fill="#fb7185" />
              </marker>
            </defs>

            {model.edges.map((edge) => {
              const from = model.nodes.find((node) => node.id === edge.from);
              const to = model.nodes.find((node) => node.id === edge.to);
              if (!from || !to) return null;
              const isReturn = edge.kind === "return";
              const midY = isReturn ? Math.min(from.y, to.y) - 44 : (from.y + to.y) / 2;
              const path = `M ${from.x} ${from.y} C ${(from.x + to.x) / 2} ${midY}, ${(from.x + to.x) / 2} ${midY}, ${to.x} ${to.y}`;

              return (
                <path
                  key={edge.id}
                  d={path}
                  fill="none"
                  markerEnd={`url(#${isReturn ? "monitor-return-arrow" : "monitor-arrow"})`}
                  className={isReturn ? "runtime-monitor-edge-active" : ""}
                  stroke={edge.id === selectedEdgeId ? "#2563eb" : isReturn ? "#fb7185" : "#14b8a6"}
                  strokeLinecap="round"
                  strokeWidth={edge.id === selectedEdgeId ? "5" : "3"}
                  onPointerDown={(event) => {
                    if (!presentation.canInteract) return;
                    event.stopPropagation();
                    setSelectedEdgeId(edge.id);
                    setSelectedNodeId(null);
                  }}
                  style={{ cursor: presentation.canInteract ? "pointer" : "default" }}
                />
              );
            })}

            {model.nodes.map((node) => (
              <g
                key={node.id}
                aria-label={`${node.name} ${node.role}`}
                className={node.state === "active" ? "runtime-monitor-node-active" : ""}
                onPointerDown={(event) => startNodeDrag(node, event)}
                onClick={() => presentation.canInteract && handleNodeClick(node.id)}
                style={{
                  cursor: presentation.canInteract
                    ? draggingNode === node.id
                      ? "grabbing"
                      : connectMode
                        ? "crosshair"
                        : "grab"
                    : "default",
                }}
              >
                <circle
                  cx={node.x - NODE_RADIUS - 7}
                  cy={node.y}
                  r="6"
                  fill={connectSourceId === node.id ? "#2563eb" : "#ffffff"}
                  stroke="#14b8a6"
                  strokeWidth="2"
                />
                <circle
                  cx={node.x + NODE_RADIUS + 7}
                  cy={node.y}
                  r="6"
                  fill={connectSourceId === node.id ? "#2563eb" : "#ffffff"}
                  stroke="#14b8a6"
                  strokeWidth="2"
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={NODE_RADIUS}
                  fill={nodeFill(node.state)}
                  opacity={node.isEnabled ? "1" : "0.45"}
                  stroke={selectedNodeId === node.id ? "#2563eb" : nodeStroke(node.state)}
                  strokeWidth={selectedNodeId === node.id ? "5" : "3"}
                />
                <circle cx={node.x - 19} cy={node.y - 15} r="9" fill="rgba(255,255,255,0.28)" />
                <foreignObject x={node.x - 14} y={node.y - 21} width="28" height="28">
                  <div className="flex h-7 w-7 items-center justify-center text-white">
                    {node.state === "complete" ? (
                      <CheckCircle2 className="h-4 w-4" />
                    ) : node.state === "error" ? (
                      <RotateCcw className="h-4 w-4" />
                    ) : node.state === "active" ? (
                      <Sparkles className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                </foreignObject>
                <text
                  x={node.x}
                  y={node.y + 8}
                  textAnchor="middle"
                  className="fill-white text-[13px] font-semibold"
                >
                  {node.name.slice(0, 14)}
                </text>
                <text
                  x={node.x}
                  y={node.y + 25}
                  textAnchor="middle"
                  className="fill-white/80 text-[10px]"
                >
                  {node.role.slice(0, 12)}
                </text>
                <text
                  x={node.x}
                  y={node.y + 55}
                  textAnchor="middle"
                  className="fill-slate-600 text-[10px] dark:fill-slate-300"
                >
                  {node.model.slice(0, 18)}
                </text>
              </g>
            ))}
          </svg>
          {presentation.canInteract && currentChat?.workbench.agentRunLog?.length ? (
            <div className="mt-2 max-h-24 overflow-y-auto rounded-md border border-border/70 bg-background/75 px-3 py-2">
              <div className="mb-1 text-xs font-medium text-muted-foreground">執行紀錄</div>
              <div className="grid gap-1">
                {currentChat.workbench.agentRunLog.slice(-6).map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center justify-between gap-2 text-xs text-muted-foreground"
                  >
                    <span className="truncate">{entry.message}</span>
                    <span className="shrink-0 tabular-nums">
                      {new Date(entry.createdAt).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {presentation.canInteract && editingSlot ? (
        <AgentJointDialog
          slot={editingSlot}
          models={state.models}
          isPlanner={editingSlot.id === "planner"}
          onChange={setEditingSlot}
          onCancel={() => setEditingSlot(null)}
          onSave={saveEditingSlot}
          onDelete={() => {
            if (!currentChat || editingSlot.id === "planner") return;
            dispatch({
              type: "DELETE_AGENT_SLOT",
              payload: { chatId: currentChat.id, slotId: editingSlot.id },
            });
            setEditingSlot(null);
          }}
        />
      ) : null}
    </section>
  );
}

function AgentJointDialog({
  slot,
  models,
  isPlanner,
  onChange,
  onCancel,
  onSave,
  onDelete,
}: {
  slot: AgentSlot;
  models: { id: string; name: string }[];
  isPlanner: boolean;
  onChange: (slot: AgentSlot) => void;
  onCancel: () => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  const togglePermission = (permission: AgentPermission) => {
    onChange({
      ...slot,
      permissions: slot.permissions.includes(permission)
        ? slot.permissions.filter((item) => item !== permission)
        : [...slot.permissions, permission],
    });
  };

  const permissions: AgentPermission[] = ["plan", "code", "review", "verify", "tools", "gui", "external"];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="編輯 joint"
        className="w-full max-w-xl rounded-lg border border-border bg-background p-4 shadow-xl"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-teal-500" />
            <h3 className="text-sm font-semibold">Joint 設定</h3>
          </div>
          <Button variant="ghost" size="icon" onClick={onCancel} title="關閉">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="mt-4 grid gap-3">
          <label className="grid gap-1 text-xs font-medium">
            名稱
            <input
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={slot.name}
              onChange={(event) => onChange({ ...slot, name: event.target.value })}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium">
            角色
            <input
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={slot.role}
              onChange={(event) => onChange({ ...slot, role: event.target.value })}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium">
            Model
            <select
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={slot.model}
              onChange={(event) => onChange({ ...slot, model: event.target.value })}
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-xs font-medium">
            Skill Prompt
            <textarea
              className="min-h-20 rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={slot.skill}
              onChange={(event) => onChange({ ...slot, skill: event.target.value })}
            />
          </label>
          <label className="grid gap-1 text-xs font-medium">
            Output Format
            <input
              className="rounded-md border border-border bg-background px-3 py-2 text-sm"
              value={slot.outputFormat}
              onChange={(event) => onChange({ ...slot, outputFormat: event.target.value })}
            />
          </label>
          <div className="grid gap-2">
            <span className="text-xs font-medium">權限</span>
            <div className="flex flex-wrap gap-2">
              {permissions.map((permission) => (
                <label
                  key={permission}
                  className="flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs"
                >
                  <input
                    type="checkbox"
                    checked={slot.permissions.includes(permission)}
                    onChange={() => togglePermission(permission)}
                  />
                  {permission}
                </label>
              ))}
            </div>
          </div>
          <label className="flex items-center gap-2 text-xs font-medium">
            <input
              type="checkbox"
              checked={slot.isEnabled}
              onChange={(event) => onChange({ ...slot, isEnabled: event.target.checked })}
            />
            啟用此 joint
          </label>
        </div>

        <div className="mt-4 flex justify-between gap-2">
          <Button variant="outline" onClick={onDelete} disabled={isPlanner}>
            <Trash2 className="mr-1 h-4 w-4" />
            Delete
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button onClick={onSave}>
              <Save className="mr-1 h-4 w-4" />
              Save
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function resolveActiveIndex(agentCount: number, workbench?: WorkbenchState) {
  if (agentCount <= 0) return 0;
  if (workbench?.status === "done") return agentCount - 1;
  if (workbench?.status === "error") return Math.min(1, agentCount - 1);
  if (workbench?.toolLogs.length) return Math.min(2, agentCount - 1);
  if (workbench?.plan.length) return Math.min(1, agentCount - 1);
  return 0;
}

function resolveNodeState(
  index: number,
  activeIndex: number,
  status?: WorkbenchState["status"],
  runStatus?: AgentRunStatus
): CanvasNodeState {
  if (runStatus === "complete") return "complete";
  if (runStatus === "running") return "active";
  if (runStatus === "error") return "error";
  if (runStatus === "skipped") return "error";
  if (runStatus === "queued") return "idle";
  if (status === "error" && index === activeIndex) return "error";
  if (index < activeIndex) return "complete";
  if (index === activeIndex) return status === "done" ? "complete" : "active";
  return "idle";
}

function resolveCurrentLabel(workbench?: WorkbenchState) {
  if (!workbench) return "等待建立工作項";
  if (workbench.status === "error") return "偵測到退回修復路徑";
  if (workbench.status === "done") return "任務已完成，流程穩定";
  if (workbench.status === "running") return "Agent 正在拋接任務";
  return "等待使用者下達指令";
}

function nodeFill(state: CanvasNodeState) {
  const colors: Record<CanvasNodeState, string> = {
    idle: "#64748b",
    active: "#38bdf8",
    complete: "#14b8a6",
    error: "#fb7185",
  };
  return colors[state];
}

function nodeStroke(state: CanvasNodeState) {
  const colors: Record<CanvasNodeState, string> = {
    idle: "#cbd5e1",
    active: "#e0f2fe",
    complete: "#ccfbf1",
    error: "#ffe4e6",
  };
  return colors[state];
}
