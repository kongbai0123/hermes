import { useChat } from "@/contexts/ChatContext";
import { useTheme } from "@/contexts/ThemeContext";
import { useLanguage } from "@/contexts/LanguageContext";
import { Button } from "@/components/ui/button";
import { Languages, MessageSquare, PanelRight, Settings, Moon, Sun, ChevronDown } from "lucide-react";
import { createDefaultChat } from "@/lib/workAgent";
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

export default function TopBar({ agentFlowOpen, onToggleAgentFlow }: TopBarProps) {
  const { state, dispatch } = useChat();
  const { theme, toggleTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const currentChat = state.chats.find((c) => c.id === state.currentChatId);
  const currentModel = state.models.find((m) => m.id === currentChat?.model);

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

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-4 gap-4">
      <div className="flex items-center gap-2 min-w-0">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center flex-shrink-0">
          <MessageSquare className="w-5 h-5 text-white" />
        </div>
        <h1 className="font-semibold text-lg hidden sm:block">Work Agent</h1>
      </div>

      <div className="flex-1 flex justify-center">
        {currentChat && currentModel ? (
          <div className="flex items-center gap-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 max-w-xs truncate">
                  <span className="text-sm truncate">{currentModel.name}</span>
                  <ChevronDown className="w-4 h-4 flex-shrink-0" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="center" className="w-56">
                {state.models.map((model) => (
                  <DropdownMenuItem
                    key={model.id}
                    onClick={() => {
                      dispatch({
                        type: "UPDATE_CHAT_SETTINGS",
                        payload: {
                          chatId: currentChat.id,
                          settings: {
                            model: model.id,
                            provider: model.provider,
                          },
                        },
                      });
                    }}
                    className={model.id === currentChat.model ? "bg-primary/10" : ""}
                  >
                    <div className="flex flex-col gap-1">
                      <span className="font-medium">{model.name}</span>
                      <span className="text-xs text-muted-foreground">{model.provider}</span>
                    </div>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>

            <div className="hidden md:flex items-center gap-2 text-xs">
              <span className="rounded-full border border-border px-2 py-1 text-muted-foreground">
                {currentChat.workbench.safetyModeLabel ? t("top.safeMode") : t("top.safeMode")}
              </span>
              <span
                className={`rounded-full px-2 py-1 font-medium ${
                  currentChat.workbench.status === "error"
                    ? "bg-destructive/10 text-destructive"
                    : currentChat.workbench.status === "running"
                      ? "bg-amber-500/10 text-amber-600"
                      : "bg-primary/10 text-primary"
                }`}
              >
                {t(`status.${currentChat.workbench.status}`)}
              </span>
            </div>
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
          variant={agentFlowOpen ? "secondary" : "ghost"}
          size="icon"
          onClick={onToggleAgentFlow}
          title={agentFlowOpen ? t("flow.hide") : t("flow.show")}
        >
          <PanelRight className="w-5 h-5" />
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
