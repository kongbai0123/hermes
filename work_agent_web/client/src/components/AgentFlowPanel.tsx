import { useMemo, useState } from "react";
import { Bot, CheckCircle2, HeartPulse, RotateCcw, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChat } from "@/contexts/ChatContext";
import type { AgentSlot, WorkbenchState } from "@/types/chat";

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
  isOpen: boolean;
  onClose: () => void;
}

const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 300;
const NODE_RADIUS = 38;

export function createAgentCanvasModel(
  agentTeam: AgentSlot[] = [],
  workbench?: WorkbenchState
): AgentCanvasModel {
  const enabledAgents = agentTeam.filter((slot) => slot.isEnabled);
  const agents = enabledAgents.length ? enabledAgents : agentTeam;
  const centerY = 150;
  const gap = agents.length > 1 ? 640 / Math.max(1, agents.length - 1) : 0;
  const startX = agents.length > 1 ? 130 : CANVAS_WIDTH / 2;

  const activeIndex = resolveActiveIndex(agents.length, workbench);

  const nodes = agents.map((slot, index) => ({
    id: slot.id,
    name: slot.name,
    role: slot.role,
    model: slot.model,
    x: startX + gap * index,
    y: centerY + Math.sin(index * 1.2) * 42,
    state: resolveNodeState(index, activeIndex, workbench?.status),
  }));

  const edges: CanvasEdge[] = [];
  for (let index = 0; index < nodes.length - 1; index += 1) {
    edges.push({
      id: `${nodes[index].id}-to-${nodes[index + 1].id}`,
      from: nodes[index].id,
      to: nodes[index + 1].id,
      kind: "handoff",
    });
  }

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

export default function AgentFlowPanel({ isOpen, onClose }: AgentFlowPanelProps) {
  const { currentChat } = useChat();
  const baseModel = useMemo(
    () => createAgentCanvasModel(currentChat?.agentTeam ?? [], currentChat?.workbench),
    [currentChat?.agentTeam, currentChat?.workbench]
  );
  const [overrides, setOverrides] = useState<Record<string, { x: number; y: number }>>({});
  const [draggingNode, setDraggingNode] = useState<string | null>(null);

  const model = useMemo(
    () => ({
      ...baseModel,
      nodes: baseModel.nodes.map((node) => ({
        ...node,
        ...(overrides[node.id] ?? {}),
      })),
    }),
    [baseModel, overrides]
  );

  if (!isOpen) return null;

  const updateNodePosition = (nodeId: string, clientX: number, clientY: number, svg: SVGSVGElement) => {
    const rect = svg.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * CANVAS_WIDTH;
    const y = ((clientY - rect.top) / rect.height) * CANVAS_HEIGHT;
    setOverrides((current) => ({
      ...current,
      [nodeId]: {
        x: Math.max(NODE_RADIUS + 12, Math.min(CANVAS_WIDTH - NODE_RADIUS - 12, x)),
        y: Math.max(NODE_RADIUS + 12, Math.min(CANVAS_HEIGHT - NODE_RADIUS - 12, y)),
      },
    }));
  };

  return (
    <section className="border-b border-border bg-background/95 shadow-sm">
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

      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-teal-500" />
              <h2 className="text-sm font-semibold">運行監控</h2>
              <span className="rounded-full bg-teal-500/10 px-2 py-0.5 text-xs text-teal-600">
                Agent Team Canvas
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {model.currentLabel}。拖曳圓形角色可以調整 2D 平面位置。
            </p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} title="關閉運行監控">
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="overflow-hidden rounded-lg border border-border bg-gradient-to-br from-sky-50 via-teal-50 to-rose-50 p-3 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
          <svg
            viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
            className="h-[300px] w-full touch-none"
            role="img"
            aria-label="Agent Team Canvas"
            onPointerMove={(event) => {
              if (!draggingNode) return;
              updateNodePosition(draggingNode, event.clientX, event.clientY, event.currentTarget);
            }}
            onPointerUp={() => setDraggingNode(null)}
            onPointerLeave={() => setDraggingNode(null)}
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
                  stroke={isReturn ? "#fb7185" : "#14b8a6"}
                  strokeLinecap="round"
                  strokeWidth="3"
                />
              );
            })}

            {model.nodes.map((node) => (
              <g
                key={node.id}
                aria-label={`${node.name} ${node.role}`}
                className={node.state === "active" ? "runtime-monitor-node-active" : ""}
                onPointerDown={(event) => {
                  event.preventDefault();
                  setDraggingNode(node.id);
                  updateNodePosition(node.id, event.clientX, event.clientY, event.currentTarget.ownerSVGElement!);
                }}
                style={{ cursor: "grab" }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={NODE_RADIUS}
                  fill={nodeFill(node.state)}
                  stroke={nodeStroke(node.state)}
                  strokeWidth="3"
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
        </div>
      </div>
    </section>
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
  status?: WorkbenchState["status"]
): CanvasNodeState {
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
