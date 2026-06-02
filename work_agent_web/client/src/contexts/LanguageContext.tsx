import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

export type AppLanguage = "zh-TW" | "en";

type TranslationKey =
  | "top.createTask"
  | "top.safeMode"
  | "top.switchTheme"
  | "top.toggleWorkbench"
  | "top.language"
  | "status.idle"
  | "status.running"
  | "status.done"
  | "status.error"
  | "status.pending"
  | "sidebar.newChat"
  | "sidebar.search"
  | "sidebar.pinned"
  | "sidebar.recent"
  | "sidebar.noChats"
  | "sidebar.noChatsYet"
  | "sidebar.workspace"
  | "sidebar.refreshWorkspace"
  | "sidebar.rename"
  | "sidebar.pin"
  | "sidebar.unpin"
  | "sidebar.delete"
  | "empty.heading"
  | "empty.subtitle"
  | "empty.powered"
  | "empty.safeWorkflow"
  | "empty.analyze.title"
  | "empty.analyze.desc"
  | "empty.debug.title"
  | "empty.debug.desc"
  | "empty.safety.title"
  | "empty.safety.desc"
  | "empty.start.title"
  | "empty.start.desc"
  | "toast.createdTask"
  | "toast.messageCopied"
  | "toast.placeholderNoted"
  | "toast.requestStopped"
  | "toast.attachmentDisabled"
  | "toast.opened"
  | "toast.selectFileFirst"
  | "toast.writePatchInstruction"
  | "toast.patchGenerated"
  | "toast.generatePatchFirst"
  | "toast.patchApplied"
  | "error.loadWorkspace"
  | "error.readFile"
  | "error.streamFailed"
  | "error.requestFailed"
  | "error.agentError"
  | "error.generatePatch"
  | "error.applyPatch"
  | "composer.placeholder"
  | "composer.attach"
  | "composer.stop"
  | "composer.send"
  | "composer.helper"
  | "bubble.copy"
  | "bubble.regenerate"
  | "bubble.good"
  | "bubble.bad"
  | "bubble.regenerateLabel"
  | "bubble.positiveLabel"
  | "bubble.negativeLabel"
  | "panel.workbench"
  | "panel.settings"
  | "panel.context"
  | "panel.patch"
  | "panel.executionStatus"
  | "panel.liveWorkbench"
  | "panel.plan"
  | "panel.noPlan"
  | "panel.toolLog"
  | "panel.step"
  | "panel.noToolObservations"
  | "panel.safetyRules"
  | "panel.allowedCommands"
  | "panel.workspace"
  | "panel.selectedFile"
  | "panel.selectFilePreview"
  | "panel.temperature"
  | "panel.temperatureHint"
  | "panel.maxTokens"
  | "panel.systemPrompt"
  | "panel.systemPromptPlaceholder"
  | "panel.attachedFiles"
  | "panel.noFiles"
  | "panel.contextWindow"
  | "panel.messages"
  | "panel.model"
  | "panel.patchInstruction"
  | "panel.patchPlaceholder"
  | "panel.generating"
  | "panel.generatePatch"
  | "panel.latestPatch"
  | "panel.applying"
  | "panel.applyAfterConfirm"
  | "panel.noPatch"
  | "confirm.applyPatch"
  | "chat.newWorkTask"
  | "safety.workspaceOnly.label"
  | "safety.workspaceOnly.desc"
  | "safety.noDelete.label"
  | "safety.noDelete.desc"
  | "safety.commandWhitelist.label"
  | "safety.commandWhitelist.desc"
  | "errorBoundary.title"
  | "errorBoundary.reload"
  | "notFound.title"
  | "notFound.body"
  | "notFound.home"
  | "flow.title"
  | "flow.show"
  | "flow.hide"
  | "flow.user.title"
  | "flow.user.subtitle"
  | "flow.manager.title"
  | "flow.manager.subtitle"
  | "flow.workerA.title"
  | "flow.workerA.subtitle"
  | "flow.workerB.title"
  | "flow.workerB.subtitle"
  | "flow.integration.title"
  | "flow.integration.subtitle"
  | "flow.final.title"
  | "flow.final.subtitle"
  | "flow.stage.waiting"
  | "flow.stage.manager"
  | "flow.stage.workers"
  | "flow.stage.final"
  | "flow.stage.error"
  | "flow.legend.title"
  | "flow.legend.dim"
  | "flow.legend.active"
  | "flow.legend.done";

const translations: Record<AppLanguage, Record<string, string>> = {
  "zh-TW": {
    "top.createTask": "建立工作任務後開始",
    "top.safeMode": "安全模式",
    "top.switchTheme": "切換到 {mode} 模式",
    "top.toggleWorkbench": "開關工作台面板",
    "top.language": "語言",
    "status.idle": "待命",
    "status.running": "執行中",
    "status.done": "完成",
    "status.error": "錯誤",
    "status.pending": "等待中",
    "sidebar.newChat": "新工作",
    "sidebar.search": "搜尋對話...",
    "sidebar.pinned": "釘選",
    "sidebar.recent": "最近",
    "sidebar.noChats": "找不到對話",
    "sidebar.noChatsYet": "尚無對話，先建立一個工作。",
    "sidebar.workspace": "工作區",
    "sidebar.refreshWorkspace": "重新整理工作區",
    "sidebar.rename": "重新命名",
    "sidebar.pin": "釘選",
    "sidebar.unpin": "取消釘選",
    "sidebar.delete": "刪除",
    "empty.heading": "要讓 Work Agent 檢查什麼？",
    "empty.subtitle": "從任務模板開始，或建立一個安全工作階段",
    "empty.powered": "由 Work Agent 驅動",
    "empty.safeWorkflow": "設計給安全的本機檔案與命令工作流",
    "empty.analyze.title": "分析工作區",
    "empty.analyze.desc": "檢查檔案並摘要專案結構",
    "empty.debug.title": "除錯範例程式",
    "empty.debug.desc": "檢查 workspace/calculator.py 並建議下一步",
    "empty.safety.title": "檢視安全規則",
    "empty.safety.desc": "了解工作區限制、命令白名單與工具安全",
    "empty.start.title": "開始 Work Agent 任務",
    "empty.start.desc": "開啟安全工作階段並送出第一個請求",
    "toast.createdTask": "已建立任務：{title}",
    "toast.messageCopied": "已複製訊息。",
    "toast.placeholderNoted": "{label} 已記錄在目前 Work Agent 工作階段。",
    "toast.requestStopped": "已停止 Work Agent 請求。",
    "toast.attachmentDisabled": "尚未啟用檔案附件。目前 Work Agent 流程專注於文字任務、工作區工具與觀察結果。",
    "toast.opened": "已開啟 {path}",
    "toast.selectFileFirst": "請先選擇工作區檔案。",
    "toast.writePatchInstruction": "請寫入 patch 指令，或先送出一個任務。",
    "toast.patchGenerated": "Patch 已產生。",
    "toast.generatePatchFirst": "請先產生 patch 再套用。",
    "toast.patchApplied": "確認後已套用 patch。",
    "error.loadWorkspace": "無法載入工作區。",
    "error.readFile": "無法讀取工作區檔案。",
    "error.streamFailed": "Work Agent 串流請求失敗。",
    "error.requestFailed": "Work Agent 請求失敗。",
    "error.agentError": "Work Agent 錯誤：{message}",
    "error.generatePatch": "無法產生 patch。",
    "error.applyPatch": "無法套用 patch。",
    "composer.placeholder": "描述一個工作任務...（Shift+Enter 換行）",
    "composer.attach": "附加檔案",
    "composer.stop": "停止產生",
    "composer.send": "送出訊息（Enter）",
    "composer.helper": "按 Enter 送出，Shift+Enter 換行",
    "bubble.copy": "複製訊息",
    "bubble.regenerate": "重新產生",
    "bubble.good": "回覆良好",
    "bubble.bad": "回覆不佳",
    "bubble.regenerateLabel": "重新產生",
    "bubble.positiveLabel": "正向回饋",
    "bubble.negativeLabel": "負向回饋",
    "panel.workbench": "工作台",
    "panel.settings": "設定",
    "panel.context": "上下文",
    "panel.patch": "Patch",
    "panel.executionStatus": "執行狀態",
    "panel.liveWorkbench": "即時工作台：顯示計畫、工具觀察與工作區指引。",
    "panel.plan": "計畫",
    "panel.noPlan": "尚無計畫。送出任務後會產生。",
    "panel.toolLog": "工具紀錄",
    "panel.step": "步驟 {number}",
    "panel.noToolObservations": "尚無工具觀察結果。",
    "panel.safetyRules": "安全規則",
    "panel.allowedCommands": "允許命令",
    "panel.workspace": "工作區",
    "panel.selectedFile": "已選檔案",
    "panel.selectFilePreview": "從左側工作區檔案樹選擇檔案即可預覽。",
    "panel.temperature": "Temperature",
    "panel.temperatureHint": "較低 = 更專注，較高 = 更有創造性",
    "panel.maxTokens": "最大 Tokens",
    "panel.systemPrompt": "System Prompt",
    "panel.systemPromptPlaceholder": "定義助理的行為...",
    "panel.attachedFiles": "附加檔案",
    "panel.noFiles": "尚未附加檔案",
    "panel.contextWindow": "上下文視窗",
    "panel.messages": "訊息數：",
    "panel.model": "模型：",
    "panel.patchInstruction": "Patch 指令",
    "panel.patchPlaceholder": "描述已選檔案應如何修改...",
    "panel.generating": "產生中...",
    "panel.generatePatch": "產生 Patch",
    "panel.latestPatch": "最新 Patch",
    "panel.applying": "套用中...",
    "panel.applyAfterConfirm": "確認後套用",
    "panel.noPatch": "選擇檔案並產生 patch 後，這裡會顯示 unified diff。",
    "confirm.applyPatch": "要將這個 patch 套用到 workspace/{path} 嗎？這會覆寫該檔案。",
    "chat.newWorkTask": "新工作任務",
    "safety.workspaceOnly.label": "僅限工作區",
    "safety.workspaceOnly.desc": "只讀取 workspace/ 內的檔案。",
    "safety.noDelete.label": "禁止刪除",
    "safety.noDelete.desc": "不自動刪除檔案。",
    "safety.commandWhitelist.label": "命令白名單",
    "safety.commandWhitelist.desc": "只執行 config.json 核准的命令。",
    "errorBoundary.title": "發生未預期錯誤。",
    "errorBoundary.reload": "重新載入頁面",
    "notFound.title": "找不到頁面",
    "notFound.body": "你要找的頁面不存在，可能已移動或刪除。",
    "notFound.home": "回首頁",
    "flow.title": "Agent 分工流程",
    "flow.show": "展開 Agent 分工流程",
    "flow.hide": "隱藏 Agent 分工流程",
    "flow.user.title": "User",
    "flow.user.subtitle": "提交任務",
    "flow.manager.title": "Manager Model",
    "flow.manager.subtitle": "管理者 / 決策角色",
    "flow.workerA.title": "Worker A",
    "flow.workerA.subtitle": "程式專家",
    "flow.workerB.title": "Worker B",
    "flow.workerB.subtitle": "整理 / 文案專家",
    "flow.integration.title": "Integration",
    "flow.integration.subtitle": "檢視與整合",
    "flow.final.title": "Final Output",
    "flow.final.subtitle": "輸出結果",
    "flow.stage.waiting": "目前：等待使用者提交任務",
    "flow.stage.manager": "目前：Manager 正在拆解任務與規劃",
    "flow.stage.workers": "目前：Worker Models 正在執行子任務",
    "flow.stage.final": "目前：整合完成，準備輸出最終結果",
    "flow.stage.error": "目前：流程遇到錯誤，需要檢查工具觀察",
    "flow.legend.title": "狀態說明",
    "flow.legend.dim": "未到此階段",
    "flow.legend.active": "目前階段",
    "flow.legend.done": "已完成",
  },
  en: {
    "top.createTask": "Create a work task to begin",
    "top.safeMode": "Safe Mode",
    "top.switchTheme": "Switch to {mode} mode",
    "top.toggleWorkbench": "Toggle workbench panel",
    "top.language": "Language",
    "status.idle": "IDLE",
    "status.running": "RUNNING",
    "status.done": "DONE",
    "status.error": "ERROR",
    "status.pending": "PENDING",
    "sidebar.newChat": "New Chat",
    "sidebar.search": "Search chats...",
    "sidebar.pinned": "Pinned",
    "sidebar.recent": "Recent",
    "sidebar.noChats": "No chats found",
    "sidebar.noChatsYet": "No chats yet. Start a new one!",
    "sidebar.workspace": "Workspace",
    "sidebar.refreshWorkspace": "Refresh workspace",
    "sidebar.rename": "Rename",
    "sidebar.pin": "Pin",
    "sidebar.unpin": "Unpin",
    "sidebar.delete": "Delete",
    "empty.heading": "What should Work Agent inspect?",
    "empty.subtitle": "Start with a task template or create a safe work session",
    "empty.powered": "Powered by Work Agent",
    "empty.safeWorkflow": "Designed for safe local file and command workflows",
    "empty.analyze.title": "Analyze workspace",
    "empty.analyze.desc": "Inspect files and summarize the project structure",
    "empty.debug.title": "Debug sample code",
    "empty.debug.desc": "Review workspace/calculator.py and suggest next steps",
    "empty.safety.title": "Review safety rules",
    "empty.safety.desc": "See workspace limits, command whitelist, and tool safety",
    "empty.start.title": "Start Work Agent task",
    "empty.start.desc": "Open a safe work session and send your first request",
    "toast.createdTask": "Created task: {title}",
    "toast.messageCopied": "Message copied.",
    "toast.placeholderNoted": "{label} is noted for the current Work Agent session.",
    "toast.requestStopped": "Work Agent request stopped.",
    "toast.attachmentDisabled": "File attachment is not enabled yet. Current Work Agent flow focuses on text tasks, workspace tools, and observations.",
    "toast.opened": "Opened {path}",
    "toast.selectFileFirst": "Select a workspace file first.",
    "toast.writePatchInstruction": "Write a patch instruction or send a task first.",
    "toast.patchGenerated": "Patch generated.",
    "toast.generatePatchFirst": "Generate a patch before applying it.",
    "toast.patchApplied": "Patch applied after confirmation.",
    "error.loadWorkspace": "Unable to load workspace.",
    "error.readFile": "Unable to read workspace file.",
    "error.streamFailed": "Work Agent streaming request failed.",
    "error.requestFailed": "Work Agent request failed.",
    "error.agentError": "Work Agent error: {message}",
    "error.generatePatch": "Unable to generate patch.",
    "error.applyPatch": "Unable to apply patch.",
    "composer.placeholder": "Describe a work task... (Shift+Enter for newline)",
    "composer.attach": "Attach file",
    "composer.stop": "Stop generating",
    "composer.send": "Send message (Enter)",
    "composer.helper": "Press Enter to send, Shift+Enter for new line",
    "bubble.copy": "Copy message",
    "bubble.regenerate": "Regenerate",
    "bubble.good": "Good response",
    "bubble.bad": "Bad response",
    "bubble.regenerateLabel": "Regenerate",
    "bubble.positiveLabel": "Positive feedback",
    "bubble.negativeLabel": "Negative feedback",
    "panel.workbench": "Workbench",
    "panel.settings": "Settings",
    "panel.context": "Context",
    "panel.patch": "Patch",
    "panel.executionStatus": "Execution Status",
    "panel.liveWorkbench": "Live workbench for plan, tool observations, and workspace guidance.",
    "panel.plan": "Plan",
    "panel.noPlan": "No plan yet. Send a task to generate one.",
    "panel.toolLog": "Tool Log",
    "panel.step": "Step {number}",
    "panel.noToolObservations": "No tool observations yet.",
    "panel.safetyRules": "Safety Rules",
    "panel.allowedCommands": "Allowed Commands",
    "panel.workspace": "Workspace",
    "panel.selectedFile": "Selected File",
    "panel.selectFilePreview": "Select a file from the left workspace explorer to preview it.",
    "panel.temperature": "Temperature",
    "panel.temperatureHint": "Lower = more focused, Higher = more creative",
    "panel.maxTokens": "Max Tokens",
    "panel.systemPrompt": "System Prompt",
    "panel.systemPromptPlaceholder": "Define the assistant's behavior...",
    "panel.attachedFiles": "Attached Files",
    "panel.noFiles": "No files attached yet",
    "panel.contextWindow": "Context Window",
    "panel.messages": "Messages:",
    "panel.model": "Model:",
    "panel.patchInstruction": "Patch Instruction",
    "panel.patchPlaceholder": "Describe how the selected file should change...",
    "panel.generating": "Generating...",
    "panel.generatePatch": "Generate Patch",
    "panel.latestPatch": "Latest Patch",
    "panel.applying": "Applying...",
    "panel.applyAfterConfirm": "Apply After Confirm",
    "panel.noPatch": "Select a file and generate a patch to review a unified diff here.",
    "confirm.applyPatch": "Apply this patch to workspace/{path}? This will overwrite the file.",
    "chat.newWorkTask": "New Work Task",
    "safety.workspaceOnly.label": "Workspace Only",
    "safety.workspaceOnly.desc": "Only read files inside workspace/.",
    "safety.noDelete.label": "No Delete",
    "safety.noDelete.desc": "Do not delete files automatically.",
    "safety.commandWhitelist.label": "Whitelisted Commands",
    "safety.commandWhitelist.desc": "Only run approved commands from config.json.",
    "errorBoundary.title": "An unexpected error occurred.",
    "errorBoundary.reload": "Reload Page",
    "notFound.title": "Page Not Found",
    "notFound.body": "Sorry, the page you are looking for does not exist. It may have been moved or deleted.",
    "notFound.home": "Go Home",
    "flow.title": "Agent Work Split",
    "flow.show": "Show agent work split",
    "flow.hide": "Hide agent work split",
    "flow.user.title": "User",
    "flow.user.subtitle": "Submit task",
    "flow.manager.title": "Manager Model",
    "flow.manager.subtitle": "Coordinator / decision role",
    "flow.workerA.title": "Worker A",
    "flow.workerA.subtitle": "Code specialist",
    "flow.workerB.title": "Worker B",
    "flow.workerB.subtitle": "Writing / synthesis specialist",
    "flow.integration.title": "Integration",
    "flow.integration.subtitle": "Review and merge",
    "flow.final.title": "Final Output",
    "flow.final.subtitle": "Deliver result",
    "flow.stage.waiting": "Current: waiting for the user to submit a task",
    "flow.stage.manager": "Current: Manager is decomposing and planning",
    "flow.stage.workers": "Current: Worker Models are executing subtasks",
    "flow.stage.final": "Current: integration complete, final output ready",
    "flow.stage.error": "Current: the flow hit an error; inspect tool observations",
    "flow.legend.title": "State Legend",
    "flow.legend.dim": "Not reached",
    "flow.legend.active": "Current stage",
    "flow.legend.done": "Completed",
  },
};

interface LanguageContextType {
  language: AppLanguage;
  setLanguage: (language: AppLanguage) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<AppLanguage>(() => {
    const saved = localStorage.getItem("work-agent-language");
    return saved === "en" || saved === "zh-TW" ? saved : "zh-TW";
  });

  useEffect(() => {
    localStorage.setItem("work-agent-language", language);
    document.documentElement.lang = language;
  }, [language]);

  const value = useMemo<LanguageContextType>(
    () => ({
      language,
      setLanguage: setLanguageState,
      t: (key, values) => {
        let text = translations[language][key] ?? translations.en[key] ?? key;
        if (values) {
          for (const [name, value] of Object.entries(values)) {
            text = text.replaceAll(`{${name}}`, String(value));
          }
        }
        return text;
      },
    }),
    [language]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
