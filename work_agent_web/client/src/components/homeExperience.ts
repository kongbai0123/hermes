import type { TaskMode } from "@/types/chat";

export const HERMES_HOME_COPY = {
  title: "HERMES AGENT",
  subtitle: "tell me what you're making; i love refactors, tiny helpers, and big scary repos alike (>w<)",
} as const;

export type HomeModeTab =
  | {
      kind: "task-mode";
      id: TaskMode;
      label: string;
      title: string;
    }
  | {
      kind: "monitor";
      id: "monitor";
      label: string;
      title: string;
    };

export const HOME_MODE_TABS: HomeModeTab[] = [
  { kind: "task-mode", id: "single", label: "單模型", title: "一個模型負責理解、規劃與回覆" },
  { kind: "task-mode", id: "multi", label: "多模型", title: "Planner / Coder / Reviewer 分工" },
  { kind: "task-mode", id: "agent", label: "代理操作", title: "允許 GUI、瀏覽器、桌面 app 與外部視窗操作" },
  { kind: "task-mode", id: "orchestration", label: "任務編排", title: "分析任務後自動派工、審核、執行與彙整" },
  { kind: "monitor", id: "monitor", label: "運行監控", title: "查看任務執行階段與工作台狀態" },
];
