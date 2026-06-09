import { useChat } from "@/contexts/ChatContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { Button } from "@/components/ui/button";
import { Languages, MessageSquare, Settings, Moon, Sun } from "lucide-react";
import { createDefaultChat } from "@/lib/workAgent";
import type { TaskMode } from "@/types/chat";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface TopBarProps {
  agentFlowOpen: boolean;
  onToggleAgentFlow: () => void;
}

const taskModes: Array<{ id: TaskMode; label: string; title: string }> = [
  { id: "single", label: "單模型", title: "一個模型負責理解、規劃與回覆" },
  { id: "multi", label: "多模型", title: "Planner / Coder / Reviewer / External Model 分工" },
  { id: "agent", label: "代理操作", title: "允許 GUI、瀏覽器、桌面 app 與外部視窗操作" },
  { id: "orchestration", label: "任務編排", title: "分析任務後自動派工、審核、執行與彙整" },
];

export default function TopBar({ agentFlowOpen, onToggleAgentFlow }: TopBarProps) {
  const { state, dispatch } = useChat();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const currentChat = state.chats.find((c) => c.id === state.currentChatId);

  const handleThemeToggle = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    dispatch({ type: "SET_THEME", payload: newTheme });
    toggleTheme?.();
  };

  const handleWorkbenchToggle = () => {
    if (!currentChat) {
      const newChat = createDefaultChat(state.models);
      newChat.title = t("chat.newWorkTask");
      dispatch({ type: "CREATE_CHAT", payload: newChat });
    }
    dispatch({ type: "TOGGLE_RIGHT_PANEL" });
  };

  const handleTaskModeChange = (mode: TaskMode) => {
    if (!currentChat) return;
    dispatch({
      type: "SET_TASK_MODE",
      payload: {
        chatId: currentChat.id,
        mode,
      },
    });
  };

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-4 gap-4">
      <div className="flex items-center gap-2 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center flex-shrink-0">
          <MessageSquare className="w-5 h-5 text-white" />
        </div>
        <h1 className="font-semibold text-lg hidden sm:block">Work Agent</h1>
      </div>

      <div className="flex-1 flex justify-center">
        {currentChat ? (
          <div className="flex min-w-0 max-w-full items-center overflow-x-auto rounded-full border border-border bg-muted/40 p-1">
            {taskModes.map((mode) => {
              const isActive = (currentChat.taskMode ?? "single") === mode.id;

              return (
                <button
                  key={mode.id}
                  type="button"
                  title={mode.title}
                  aria-pressed={isActive}
                  onClick={() => handleTaskModeChange(mode.id)}
                  className={`h-8 whitespace-nowrap rounded-full px-3 text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:bg-background hover:text-foreground"
                  }`}
                >
                  {mode.label}
                </button>
              );
            })}
            <span className="mx-1 h-5 w-px bg-border" aria-hidden="true" />
            <button
              type="button"
              title={agentFlowOpen ? "隱藏運行監控" : "顯示運行監控"}
              aria-pressed={agentFlowOpen}
              onClick={onToggleAgentFlow}
              className={`h-8 whitespace-nowrap rounded-full px-3 text-xs font-medium transition-colors ${
                agentFlowOpen
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-background hover:text-foreground"
              }`}
            >
              運行監控
            </button>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">{t("top.createTask")}</div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2" title={t("top.language")}>
              <Languages className="w-5 h-5" />
              <span className="hidden sm:inline text-sm">{language === "zh-TW" ? "繁中" : "EN"}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem
              onClick={() => setLanguage("zh-TW")}
              className={language === "zh-TW" ? "bg-primary/10" : ""}
            >
              繁體中文
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => setLanguage("en")}
              className={language === "en" ? "bg-primary/10" : ""}
            >
              English
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="icon"
          onClick={handleThemeToggle}
          title={t("top.switchTheme", { mode: theme === "light" ? "dark" : "light" })}
        >
          {theme === "light" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={handleWorkbenchToggle}
          title={t("top.toggleWorkbench")}
        >
          <Settings className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}
