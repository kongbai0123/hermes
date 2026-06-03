import { useCallback, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  CheckCircle2,
  ChevronRight,
  Eye,
  FileSearch,
  GitBranch,
  Route,
  ShieldCheck,
  UserRound,
  Wrench,
} from "lucide-react";
import { useChat } from "@/contexts/ChatContext";
import { useLanguage } from "@/contexts/LanguageContext";

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

interface FlowNode {
  id: FlowNodeId;
  icon: typeof UserRound;
  titleKey: string;
  subtitleKey: string;
  x: number;
  y: number;
  width?: string;
}

const MIN_PANEL_WIDTH = 340;
const MAX_PANEL_WIDTH = 680;

const nodes: FlowNode[] = [
  {
    id: "user",
    icon: UserRound,
    titleKey: "flow.user.title",
    subtitleKey: "flow.user.subtitle",
    x: 50,
    y: 8,
  },
  {
    id: "controller",
    icon: Route,
    titleKey: "flow.controller.title",
    subtitleKey: "flow.controller.subtitle",
    x: 50,
    y: 22,
    width: "w-48",
  },
  {
    id: "planner",
    icon: GitBranch,
    titleKey: "flow.planner.title",
    subtitleKey: "flow.planner.subtitle",
    x: 28,
    y: 38,
  },
  {
    id: "processor",
    icon: Bot,
    titleKey: "flow.processor.title",
    subtitleKey: "flow.processor.subtitle",
    x: 72,
    y: 38,
  },
  {
    id: "policy",
    icon: ShieldCheck,
    titleKey: "flow.policy.title",
    subtitleKey: "flow.policy.subtitle",
    x: 28,
    y: 56,
  },
  {
    id: "executor",
    icon: Wrench,
    titleKey: "flow.executor.title",
    subtitleKey: "flow.executor.subtitle",
    x: 72,
    y: 56,
  },
  {
    id: "observation",
    icon: Eye,
    titleKey: "flow.observation.title",
    subtitleKey: "flow.observation.subtitle",
    x: 72,
    y: 73,
  },
  {
    id: "energy",
    icon: Activity,
    titleKey: "flow.energy.title",
    subtitleKey: "flow.energy.subtitle",
    x: 28,
    y: 73,
  },
  {
    id: "final",
    icon: CheckCircle2,
    titleKey: "flow.final.title",
    subtitleKey: "flow.final.subtitle",
    x: 50,
    y: 90,
  },
];

const paths = [
  { from: "50,12", to: "50,18" },
  { from: "45,27", to: "32,34" },
  { from: "55,27", to: "68,34" },
  { from: "28,43", to: "28,51" },
  { from: "40,56", to: "60,56" },
  { from: "72,61", to: "72,68" },
  { from: "60,73", to: "40,73" },
  { from: "28,68", to: "28,61" },
  { from: "37,78", to: "47,86" },
  { from: "63,78", to: "53,86" },
  { from: "25,70", to: "22,42", dash: true },
  { from: "75,70", to: "78,42", dash: true },
];

interface AgentFlowPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AgentFlowPanel({ isOpen, onClose }: AgentFlowPanelProps) {
  const { currentChat } = useChat();
  const { t } = useLanguage();
  const [panelWidth, setPanelWidth] = useState(430);
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
      <aside
        className={`pointer-events-auto relative h-[calc(100vh-6rem)] border-l border-border bg-background/98 shadow-2xl transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        } ${isResizing ? "select-none" : ""}`}
        style={{ width: `${panelWidth}px` }}
      >
        <button
          type="button"
          aria-label={t("flow.resize")}
          title={t("flow.resize")}
          onPointerDown={handleResizeStart}
          className="absolute -left-2 top-0 z-10 h-full w-4 cursor-col-resize border-x border-transparent hover:border-primary/40"
        >
          <span className="mx-auto block h-full w-px bg-border" />
        </button>

        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <div className="min-w-0">
              <h2 className="truncate text-sm font-semibold">{t("flow.title")}</h2>
              <p className="truncate text-xs text-muted-foreground">{t(currentStage)}</p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-foreground"
              title={t("flow.hide")}
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="relative h-[640px] rounded-md border border-border bg-card">
              <svg
                className="absolute inset-0 h-full w-full"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
                aria-hidden="true"
              >
                <defs>
                  <marker
                    id="flow-arrow"
                    markerWidth="6"
                    markerHeight="6"
                    refX="5"
                    refY="3"
                    orient="auto"
                    markerUnits="strokeWidth"
                  >
                    <path d="M0,0 L6,3 L0,6 Z" className="fill-primary/60" />
                  </marker>
                </defs>
                {paths.map((path) => (
                  <line
                    key={`${path.from}-${path.to}`}
                    x1={path.from.split(",")[0]}
                    y1={path.from.split(",")[1]}
                    x2={path.to.split(",")[0]}
                    y2={path.to.split(",")[1]}
                    className="stroke-primary/45"
                    strokeDasharray={path.dash ? "3 3" : undefined}
                    strokeWidth="0.9"
                    markerEnd="url(#flow-arrow)"
                  />
                ))}
              </svg>

              {nodes.map((node) => (
                <FlowNodeCard
                  key={node.id}
                  node={node}
                  state={nodeStates[node.id]}
                  title={t(node.titleKey)}
                  subtitle={t(node.subtitleKey)}
                />
              ))}
            </div>

            <div className="mt-4 rounded-md border border-border bg-card p-3">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                <FileSearch className="h-4 w-4 text-primary" />
                {t("flow.legend.title")}
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                <span className="rounded bg-secondary px-2 py-1">{t("flow.legend.dim")}</span>
                <span className="rounded bg-primary/10 px-2 py-1 text-primary">{t("flow.legend.active")}</span>
                <span className="rounded bg-emerald-500/10 px-2 py-1 text-emerald-600">{t("flow.legend.done")}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

function FlowNodeCard({
  node,
  state,
  title,
  subtitle,
}: {
  node: FlowNode;
  state: FlowNodeState;
  title: string;
  subtitle: string;
}) {
  const Icon = node.icon;
  const active = state === "active";
  const complete = state === "complete";
  const error = state === "error";

  return (
    <div
      className={`agent-flow-node absolute ${node.width ?? "w-40"} rounded-md border bg-background p-3 shadow-sm ${
        active ? "agent-flow-node-active border-primary text-foreground" : ""
      } ${complete ? "border-emerald-500/40 text-foreground" : ""} ${
        error ? "agent-flow-node-error border-destructive text-foreground" : ""
      } ${state === "idle" ? "opacity-35 grayscale" : ""}`}
      style={{ left: `${node.x}%`, top: `${node.y}%` }}
    >
      <div className="flex items-center gap-2">
        <div
          className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md ${
            error
              ? "bg-destructive/10 text-destructive"
              : complete
                ? "bg-emerald-500/10 text-emerald-600"
                : "bg-primary/10 text-primary"
          }`}
        >
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{title}</p>
          <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
        </div>
      </div>
    </div>
  );
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
      states.energy = "idle";
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
