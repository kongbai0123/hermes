import { useCallback, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  CheckCircle2,
  ChevronRight,
  Eye,
  GitBranch,
  Route,
  ShieldCheck,
  UserRound,
  Wrench,
} from "lucide-react";
import { useChat } from "@/contexts/ChatContext";
import { useLanguage } from "@/contexts/LanguageContext";

const DESIGN_TOKENS = {
  colors: {
    canvasBg: "#0A0D14",
    nodeBgDefault: "#141923",
    nodeBgHover: "#1A2332",
    borderDefault: "#222A3A",
    borderIdle: "#3A4556",
    borderActive: "#3B82F6",
    borderSuccess: "#00E5A3",
    borderError: "#EF4444",
    textPrimary: "#FFFFFF",
    textSecondary: "#64748B",
    lineIdle: "#3A4556",
    lineActive: "#3B82F6",
    lineSuccess: "#00E5A3",
    lineError: "#EF4444",
    iconIdle: "#64748B",
    iconActive: "#3B82F6",
    iconSuccess: "#00E5A3",
    iconError: "#EF4444",
  },
  node: {
    width: 180,
    height: 72,
    borderRadius: 8,
  },
};

const MIN_PANEL_WIDTH = 420;
const MAX_PANEL_WIDTH = 1100;

type FlowNodeId =
  | "user"
  | "controller"
  | "planner"
  | "processor"
  | "policy"
  | "executor"
  | "observation"
  | "energy"
  | "final";
type FlowNodeState = "idle" | "active" | "complete" | "error";

interface NodeCoord {
  id: FlowNodeId;
  x: number;
  y: number;
  icon: typeof UserRound;
  titleKey: string;
  fallbackTitle: string;
  fallbackSubtitle: string;
}

interface Connection {
  from: FlowNodeId;
  to: FlowNodeId;
  type: "vertical" | "horizontal" | "diagonal";
}

const NODE_COORDINATES: NodeCoord[] = [
  {
    id: "user",
    x: 500,
    y: 80,
    icon: UserRound,
    titleKey: "flow.user.title",
    fallbackTitle: "User Input",
    fallbackSubtitle: "用戶輸入",
  },
  {
    id: "controller",
    x: 500,
    y: 200,
    icon: Route,
    titleKey: "flow.controller.title",
    fallbackTitle: "Controller",
    fallbackSubtitle: "流程控制",
  },
  {
    id: "planner",
    x: 280,
    y: 340,
    icon: GitBranch,
    titleKey: "flow.planner.title",
    fallbackTitle: "Planner",
    fallbackSubtitle: "計畫生成",
  },
  {
    id: "processor",
    x: 720,
    y: 340,
    icon: Bot,
    titleKey: "flow.processor.title",
    fallbackTitle: "Processor",
    fallbackSubtitle: "處理器",
  },
  {
    id: "policy",
    x: 400,
    y: 500,
    icon: ShieldCheck,
    titleKey: "flow.policy.title",
    fallbackTitle: "Policy",
    fallbackSubtitle: "策略驗證",
  },
  {
    id: "executor",
    x: 600,
    y: 500,
    icon: Wrench,
    titleKey: "flow.executor.title",
    fallbackTitle: "Executor",
    fallbackSubtitle: "執行器",
  },
  {
    id: "energy",
    x: 400,
    y: 680,
    icon: Activity,
    titleKey: "flow.energy.title",
    fallbackTitle: "Energy",
    fallbackSubtitle: "能量監控",
  },
  {
    id: "observation",
    x: 600,
    y: 680,
    icon: Eye,
    titleKey: "flow.observation.title",
    fallbackTitle: "Observation",
    fallbackSubtitle: "觀察反饋",
  },
  {
    id: "final",
    x: 500,
    y: 880,
    icon: CheckCircle2,
    titleKey: "flow.final.title",
    fallbackTitle: "Final Output",
    fallbackSubtitle: "最終輸出",
  },
];

const CONNECTIONS: Connection[] = [
  { from: "user", to: "controller", type: "vertical" },
  { from: "controller", to: "planner", type: "diagonal" },
  { from: "controller", to: "processor", type: "diagonal" },
  { from: "planner", to: "policy", type: "diagonal" },
  { from: "processor", to: "executor", type: "diagonal" },
  { from: "policy", to: "executor", type: "horizontal" },
  { from: "executor", to: "observation", type: "vertical" },
  { from: "observation", to: "energy", type: "horizontal" },
  { from: "energy", to: "policy", type: "vertical" },
  { from: "observation", to: "final", type: "diagonal" },
  { from: "energy", to: "final", type: "diagonal" },
];

interface AgentFlowPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AgentFlowPanel({ isOpen, onClose }: AgentFlowPanelProps) {
  const { currentChat } = useChat();
  const { t } = useLanguage();
  const [hoveredNode, setHoveredNode] = useState<FlowNodeId | null>(null);
  const [panelWidth, setPanelWidth] = useState(620);
  const [isResizing, setIsResizing] = useState(false);

  const nodeStates = useMemo(() => getNodeStates(currentChat?.workbench), [currentChat]);
  const currentStage = useMemo(() => getCurrentStage(currentChat?.workbench), [currentChat]);

  const handleResizeStart = useCallback((event: React.PointerEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = panelWidth;
    setIsResizing(true);

    const handleMove = (moveEvent: PointerEvent) => {
      const nextWidth = Math.min(
        MAX_PANEL_WIDTH,
        Math.max(MIN_PANEL_WIDTH, startWidth + startX - moveEvent.clientX)
      );
      setPanelWidth(nextWidth);
    };

    const handleUp = () => {
      setIsResizing(false);
      window.removeEventListener("pointermove", handleMove);
      window.removeEventListener("pointerup", handleUp);
    };

    window.addEventListener("pointermove", handleMove);
    window.addEventListener("pointerup", handleUp);
  }, [panelWidth]);

  return (
    <div className="pointer-events-none fixed right-0 top-16 z-40">
      <style>{`
        @keyframes flow-node-glow {
          0%, 100% {
            filter: drop-shadow(0 0 0 rgba(59, 130, 246, 0.25));
          }
          50% {
            filter: drop-shadow(0 0 14px rgba(59, 130, 246, 0.62));
          }
        }

        @keyframes flow-particle {
          0% { offset-distance: 0%; opacity: 0; }
          10% { opacity: 0.85; }
          90% { opacity: 0.85; }
          100% { offset-distance: 100%; opacity: 0; }
        }

        @keyframes icon-pulse {
          0%, 100% { opacity: 0.78; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.08); }
        }

        .agent-flow-redesign .node-active-rect {
          animation: flow-node-glow 2s ease-in-out infinite;
        }

        .agent-flow-redesign .node-active-icon {
          animation: icon-pulse 2s ease-in-out infinite;
          transform-origin: center;
        }

        .agent-flow-redesign .flow-particle {
          animation: flow-particle 3200ms linear infinite;
          offset-path: var(--path);
        }

        @media (prefers-reduced-motion: reduce) {
          .agent-flow-redesign .node-active-rect,
          .agent-flow-redesign .node-active-icon,
          .agent-flow-redesign .flow-particle {
            animation: none;
          }
        }
      `}</style>

      <aside
        className={`agent-flow-redesign pointer-events-auto relative h-[calc(100vh-6rem)] border-l border-slate-700/40 shadow-2xl transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        } ${isResizing ? "select-none" : ""}`}
        style={{
          width: `${panelWidth}px`,
          backgroundColor: DESIGN_TOKENS.colors.canvasBg,
        }}
      >
        <button
          type="button"
          aria-label={t("flow.resize")}
          title={t("flow.resize")}
          onPointerDown={handleResizeStart}
          className="absolute -left-2 top-0 z-10 h-full w-4 cursor-col-resize border-x border-transparent hover:border-blue-500/40"
        >
          <span className="mx-auto block h-full w-px bg-slate-700/70" />
        </button>

        <div className="flex h-full flex-col">
          <div
            className="border-b px-6 py-5 backdrop-blur-sm"
            style={{
              borderColor: DESIGN_TOKENS.colors.borderDefault,
              backgroundColor: `${DESIGN_TOKENS.colors.nodeBgDefault}cc`,
            }}
          >
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <h2
                  className="truncate text-lg font-bold tracking-wider"
                  style={{ color: DESIGN_TOKENS.colors.textPrimary }}
                >
                  AGENT FLOW
                </h2>
                <p
                  className="mt-2 truncate text-xs"
                  style={{ color: DESIGN_TOKENS.colors.textSecondary }}
                >
                  {t(currentStage)}
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded p-1.5 transition-all duration-200 hover:bg-slate-800"
                style={{ color: DESIGN_TOKENS.colors.textSecondary }}
                title={t("flow.hide")}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden p-4">
            <svg
              width="100%"
              height="100%"
              viewBox="205 55 670 900"
              preserveAspectRatio="xMidYMid meet"
              style={{
                display: "block",
                maxHeight: "100%",
                backgroundColor: DESIGN_TOKENS.colors.canvasBg,
                borderRadius: "8px",
              }}
              aria-label={t("flow.title")}
            >
              <defs>
                <marker
                  id="agent-flow-arrow-idle"
                  markerWidth="10"
                  markerHeight="10"
                  refX="8"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill={DESIGN_TOKENS.colors.lineIdle} />
                </marker>
                <marker
                  id="agent-flow-arrow-active"
                  markerWidth="10"
                  markerHeight="10"
                  refX="8"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill={DESIGN_TOKENS.colors.lineActive} />
                </marker>
                <marker
                  id="agent-flow-arrow-success"
                  markerWidth="10"
                  markerHeight="10"
                  refX="8"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill={DESIGN_TOKENS.colors.lineSuccess} />
                </marker>
                <marker
                  id="agent-flow-arrow-error"
                  markerWidth="10"
                  markerHeight="10"
                  refX="8"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill={DESIGN_TOKENS.colors.lineError} />
                </marker>
              </defs>

              {CONNECTIONS.map((connection) => (
                <FlowConnection
                  key={`${connection.from}-${connection.to}`}
                  connection={connection}
                  nodeStates={nodeStates}
                />
              ))}

              {NODE_COORDINATES.map((node) => (
                <g
                  key={node.id}
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{ cursor: "pointer" }}
                >
                  <FlowNodeSvg
                    node={node}
                    state={nodeStates[node.id]}
                    isHovered={hoveredNode === node.id}
                    title={t(node.titleKey)}
                    subtitle={node.fallbackSubtitle}
                  />
                </g>
              ))}
            </svg>
          </div>

          <div
            className="border-t px-6 py-4"
            style={{
              borderColor: DESIGN_TOKENS.colors.borderDefault,
              backgroundColor: `${DESIGN_TOKENS.colors.nodeBgDefault}cc`,
            }}
          >
            <div
              className="mb-3 text-xs font-semibold"
              style={{ color: DESIGN_TOKENS.colors.textSecondary }}
            >
              {t("flow.legend.title")}
            </div>
            <div className="grid grid-cols-4 gap-3 text-xs">
              <LegendItem color={DESIGN_TOKENS.colors.borderIdle} label={t("flow.legend.dim")} />
              <LegendItem color={DESIGN_TOKENS.colors.borderActive} label={t("flow.legend.active")} />
              <LegendItem color={DESIGN_TOKENS.colors.borderSuccess} label={t("flow.legend.done")} />
              <LegendItem color={DESIGN_TOKENS.colors.borderError} label="Error" />
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

function FlowConnection({
  connection,
  nodeStates,
}: {
  connection: Connection;
  nodeStates: Record<FlowNodeId, FlowNodeState>;
}) {
  const fromNode = NODE_COORDINATES.find((node) => node.id === connection.from);
  const toNode = NODE_COORDINATES.find((node) => node.id === connection.to);
  if (!fromNode || !toNode) return null;

  const fromState = nodeStates[connection.from];
  const toState = nodeStates[connection.to];
  const isActive = fromState === "active" || toState === "active";
  const isComplete = fromState === "complete" && toState === "complete";
  const isError = fromState === "error" || toState === "error";
  const pathD = calculateBezierPath(fromNode, toNode, connection.type);
  const lineColor = isError
    ? DESIGN_TOKENS.colors.lineError
    : isActive
      ? DESIGN_TOKENS.colors.lineActive
      : isComplete
        ? DESIGN_TOKENS.colors.lineSuccess
        : DESIGN_TOKENS.colors.lineIdle;
  const markerId = isError
    ? "agent-flow-arrow-error"
    : isActive
      ? "agent-flow-arrow-active"
      : isComplete
        ? "agent-flow-arrow-success"
        : "agent-flow-arrow-idle";

  return (
    <g>
      <path
        d={pathD}
        fill="none"
        stroke={lineColor}
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={isActive ? 2.2 : 1.5}
        markerEnd={`url(#${markerId})`}
        opacity={isActive || isComplete || isError ? 1 : 0.55}
        style={{ transition: "stroke 200ms cubic-bezier(0.4, 0, 0.2, 1)" }}
      />

      {isActive && (
        <circle
          r="3"
          fill={DESIGN_TOKENS.colors.lineActive}
          opacity="0.75"
          className="flow-particle"
          style={{ "--path": `path('${pathD}')` } as React.CSSProperties}
        />
      )}
    </g>
  );
}

function FlowNodeSvg({
  node,
  state,
  isHovered,
  title,
  subtitle,
}: {
  node: NodeCoord;
  state: FlowNodeState;
  isHovered: boolean;
  title: string;
  subtitle: string;
}) {
  const { width, height } = DESIGN_TOKENS.node;
  const Icon = node.icon;

  let borderColor = DESIGN_TOKENS.colors.borderIdle;
  let bgColor = DESIGN_TOKENS.colors.nodeBgDefault;
  let textColor = DESIGN_TOKENS.colors.textSecondary;
  let iconColor = DESIGN_TOKENS.colors.iconIdle;
  let opacity = 0.45;
  let shadowFilter = "none";

  if (state === "active") {
    borderColor = DESIGN_TOKENS.colors.borderActive;
    bgColor = DESIGN_TOKENS.colors.nodeBgHover;
    textColor = DESIGN_TOKENS.colors.textPrimary;
    iconColor = DESIGN_TOKENS.colors.iconActive;
    opacity = 1;
    shadowFilter = "drop-shadow(0 0 12px rgba(59, 130, 246, 0.4))";
  } else if (state === "complete") {
    borderColor = DESIGN_TOKENS.colors.borderSuccess;
    textColor = DESIGN_TOKENS.colors.textPrimary;
    iconColor = DESIGN_TOKENS.colors.iconSuccess;
    opacity = 1;
  } else if (state === "error") {
    borderColor = DESIGN_TOKENS.colors.borderError;
    bgColor = DESIGN_TOKENS.colors.nodeBgHover;
    textColor = DESIGN_TOKENS.colors.textPrimary;
    iconColor = DESIGN_TOKENS.colors.iconError;
    opacity = 1;
  }

  if (isHovered && state === "idle") {
    opacity = 0.78;
    bgColor = DESIGN_TOKENS.colors.nodeBgHover;
  }

  return (
    <g
      opacity={opacity}
      style={{
        filter: shadowFilter,
        transition: "filter 200ms cubic-bezier(0.4, 0, 0.2, 1), opacity 200ms",
      }}
    >
      <rect
        x={node.x}
        y={node.y}
        width={width}
        height={height}
        rx={DESIGN_TOKENS.node.borderRadius}
        fill={bgColor}
        stroke={borderColor}
        strokeWidth="1.5"
        className={state === "active" ? "node-active-rect" : ""}
      />

      <circle cx={node.x + 24} cy={node.y + height / 2} r="14" fill={`${iconColor}18`} />

      <foreignObject x={node.x + 10} y={node.y + height / 2 - 10} width="28" height="28">
        <div
          className={state === "active" ? "node-active-icon" : ""}
          style={{
            alignItems: "center",
            color: iconColor,
            display: "flex",
            height: "100%",
            justifyContent: "center",
            width: "100%",
          }}
        >
          <Icon size={16} strokeWidth={2} />
        </div>
      </foreignObject>

      <text
        x={node.x + 48}
        y={node.y + 30}
        fill={textColor}
        fontFamily="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
        fontSize="14"
        fontWeight="650"
      >
        {title || node.fallbackTitle}
      </text>
      <text
        x={node.x + 48}
        y={node.y + 49}
        fill={DESIGN_TOKENS.colors.textSecondary}
        fontFamily="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
        fontSize="12"
        fontWeight="400"
      >
        {subtitle}
      </text>
    </g>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex min-w-0 items-center gap-2">
      <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{ backgroundColor: color }} />
      <span className="truncate" style={{ color: DESIGN_TOKENS.colors.textSecondary }}>
        {label}
      </span>
    </div>
  );
}

function calculateBezierPath(
  fromNode: NodeCoord,
  toNode: NodeCoord,
  type: "vertical" | "horizontal" | "diagonal"
): string {
  const { width, height } = DESIGN_TOKENS.node;
  let x1: number;
  let y1: number;
  let x2: number;
  let y2: number;

  if (type === "horizontal") {
    x1 = fromNode.x + width;
    y1 = fromNode.y + height / 2;
    x2 = toNode.x;
    y2 = toNode.y + height / 2;
  } else {
    x1 = fromNode.x + width / 2;
    y1 = fromNode.y + height;
    x2 = toNode.x + width / 2;
    y2 = toNode.y;
  }

  if (type === "horizontal") {
    const dx = x2 - x1;
    return `M ${x1} ${y1} C ${x1 + dx * 0.4} ${y1} ${x2 - dx * 0.4} ${y2} ${x2} ${y2}`;
  }

  const dy = y2 - y1;
  return `M ${x1} ${y1} C ${x1} ${y1 + dy * 0.4} ${x2} ${y2 - dy * 0.4} ${x2} ${y2}`;
}

function getNodeStates(workbench?: { status: string; plan: unknown[]; toolLogs: unknown[] }) {
  const states: Record<FlowNodeId, FlowNodeState> = {
    user: "active",
    controller: "idle",
    planner: "idle",
    processor: "idle",
    policy: "idle",
    executor: "idle",
    observation: "idle",
    energy: "idle",
    final: "idle",
  };

  if (!workbench) return states;

  if (workbench.status === "error") {
    states.user = "complete";
    states.controller = "complete";
    states.planner = "complete";
    states.processor = "complete";
    states.policy = "error";
    states.executor = workbench.toolLogs.length > 0 ? "error" : "idle";
    states.observation = workbench.toolLogs.length > 0 ? "error" : "idle";
    states.energy = "error";
    return states;
  }

  if (workbench.status === "running") {
    states.user = "complete";
    states.controller = "active";
    if (workbench.plan.length > 0) {
      states.planner = "complete";
      states.processor = workbench.toolLogs.length > 0 ? "complete" : "active";
      states.policy = workbench.toolLogs.length > 0 ? "complete" : "idle";
    }
    if (workbench.toolLogs.length > 0) {
      states.executor = "active";
      states.observation = "active";
    }
    return states;
  }

  if (workbench.status === "done") {
    states.user = "complete";
    states.controller = "complete";
    states.planner = "complete";
    states.processor = "complete";
    states.policy = "complete";
    states.executor = "complete";
    states.observation = "complete";
    states.energy = "complete";
    states.final = "active";
    return states;
  }

  return states;
}

function getCurrentStage(workbench?: { status: string; plan: unknown[]; toolLogs: unknown[] }) {
  if (!workbench) return "flow.stage.waiting";
  if (workbench.status === "error") return "flow.stage.error";
  if (workbench.status === "done") return "flow.stage.final";
  if (workbench.status === "running" && workbench.toolLogs.length > 0) return "flow.stage.executor";
  if (workbench.status === "running") return "flow.stage.planner";
  return "flow.stage.waiting";
}
