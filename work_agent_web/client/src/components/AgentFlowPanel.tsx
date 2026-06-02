import { useMemo } from "react";
import {
  Bot,
  CheckCircle2,
  ChevronRight,
  Code2,
  FilePenLine,
  GitMerge,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useChat } from "@/contexts/ChatContext";
import { useLanguage } from "@/contexts/LanguageContext";

type FlowNodeId = "user" | "manager" | "workerA" | "workerB" | "integration" | "final";
type FlowNodeState = "idle" | "active" | "complete" | "error";

interface FlowNode {
  id: FlowNodeId;
  icon: typeof UserRound;
  titleKey: string;
  subtitleKey: string;
  x: number;
  y: number;
}

const nodes: FlowNode[] = [
  {
    id: "user",
    icon: UserRound,
    titleKey: "flow.user.title",
    subtitleKey: "flow.user.subtitle",
    x: 50,
    y: 10,
  },
  {
    id: "manager",
    icon: Bot,
    titleKey: "flow.manager.title",
    subtitleKey: "flow.manager.subtitle",
    x: 50,
    y: 26,
  },
  {
    id: "workerA",
    icon: Code2,
    titleKey: "flow.workerA.title",
    subtitleKey: "flow.workerA.subtitle",
    x: 23,
    y: 47,
  },
  {
    id: "workerB",
    icon: FilePenLine,
    titleKey: "flow.workerB.title",
    subtitleKey: "flow.workerB.subtitle",
    x: 77,
    y: 47,
  },
  {
    id: "integration",
    icon: GitMerge,
    titleKey: "flow.integration.title",
    subtitleKey: "flow.integration.subtitle",
    x: 50,
    y: 67,
  },
  {
    id: "final",
    icon: CheckCircle2,
    titleKey: "flow.final.title",
    subtitleKey: "flow.final.subtitle",
    x: 50,
    y: 86,
  },
];

const paths = [
  { from: "50,15", to: "50,21" },
  { from: "44,31", to: "28,42" },
  { from: "56,31", to: "72,42" },
  { from: "28,52", to: "44,62" },
  { from: "72,52", to: "56,62" },
  { from: "50,72", to: "50,81" },
];

interface AgentFlowPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AgentFlowPanel({ isOpen, onClose }: AgentFlowPanelProps) {
  const { currentChat } = useChat();
  const { t } = useLanguage();

  const nodeStates = useMemo(() => getNodeStates(currentChat?.workbench), [currentChat]);
  const currentStage = useMemo(() => getCurrentStage(currentChat?.workbench), [currentChat]);

  return (
    <div className="pointer-events-none fixed right-0 top-16 z-40">
      <aside
        className={`pointer-events-auto h-[calc(100vh-6rem)] w-[390px] border-l border-border bg-background/98 shadow-2xl transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold">{t("flow.title")}</h2>
              <p className="text-xs text-muted-foreground">{t(currentStage)}</p>
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
            <div className="relative h-[560px] rounded-md border border-border bg-card">
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
                <Sparkles className="h-4 w-4 text-primary" />
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
      className={`agent-flow-node absolute w-40 rounded-md border bg-background p-3 shadow-sm ${
        active ? "agent-flow-node-active border-primary text-foreground" : ""
      } ${complete ? "border-emerald-500/40 text-foreground" : ""} ${
        error ? "agent-flow-node-error border-destructive text-foreground" : ""
      } ${state === "idle" ? "opacity-35 grayscale" : ""}`}
      style={{ left: `${node.x}%`, top: `${node.y}%` }}
    >
      <div className="flex items-center gap-2">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-md ${
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
    manager: "idle",
    workerA: "idle",
    workerB: "idle",
    integration: "idle",
    final: "idle",
  };

  if (!workbench) return states;

  if (workbench.status === "error") {
    states.user = "complete";
    states.manager = "complete";
    states.workerA = workbench.toolLogs.length > 0 ? "error" : "idle";
    states.workerB = workbench.toolLogs.length > 0 ? "error" : "idle";
    states.integration = "error";
    return states;
  }

  if (workbench.status === "running") {
    states.user = "complete";
    if (workbench.toolLogs.length > 0) {
      states.manager = "complete";
      states.workerA = "active";
      states.workerB = "active";
    } else if (workbench.plan.length > 0) {
      states.manager = "active";
    } else {
      states.manager = "active";
    }
    return states;
  }

  if (workbench.status === "done") {
    states.user = "complete";
    states.manager = "complete";
    states.workerA = "complete";
    states.workerB = "complete";
    states.integration = "complete";
    states.final = "active";
    return states;
  }

  return states;
}

function getCurrentStage(workbench?: { status: string; plan: unknown[]; toolLogs: unknown[] }) {
  if (!workbench) return "flow.stage.waiting";
  if (workbench.status === "error") return "flow.stage.error";
  if (workbench.status === "done") return "flow.stage.final";
  if (workbench.status === "running" && workbench.toolLogs.length > 0) return "flow.stage.workers";
  if (workbench.status === "running") return "flow.stage.manager";
  return "flow.stage.waiting";
}
