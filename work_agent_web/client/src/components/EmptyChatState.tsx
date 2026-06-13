import { useChat } from "@/contexts/ChatContext";
import { Activity } from "lucide-react";
import { toast } from "sonner";
import { createDefaultChat } from "@/lib/workAgent";
import { useLanguage } from "@/contexts/LanguageContext";
import { HERMES_HOME_COPY, HOME_MODE_TABS } from "./homeExperience";

interface EmptyChatStateProps {
  agentFlowOpen?: boolean;
  onToggleAgentFlow?: () => void;
}

export default function EmptyChatState({
  agentFlowOpen = false,
  onToggleAgentFlow,
}: EmptyChatStateProps) {
  const { currentChat, dispatch, state } = useChat();
  const { t } = useLanguage();

  const handleTaskModeClick = (mode: (typeof HOME_MODE_TABS)[number]) => {
    if (mode.kind === "monitor") {
      onToggleAgentFlow?.();
      return;
    }

    if (currentChat) {
      dispatch({
        type: "SET_TASK_MODE",
        payload: {
          chatId: currentChat.id,
          mode: mode.id,
        },
      });
      return;
    }

    const newChat = createDefaultChat(state.models);
    newChat.title = t("chat.newWorkTask");
    newChat.taskMode = mode.id;
    dispatch({ type: "CREATE_CHAT", payload: newChat });
    toast.success(t("toast.createdTask", { title: mode.label }));
  };

  return (
    <div className="relative flex h-full w-full items-center justify-center overflow-hidden px-4 py-10 text-center">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(115deg, transparent 0%, currentColor 48%, transparent 52%), linear-gradient(25deg, transparent 0%, currentColor 49%, transparent 53%)",
          backgroundSize: "180px 180px, 220px 220px",
        }}
        aria-hidden="true"
      />

      <div className="relative z-10 flex w-full max-w-4xl flex-col items-center gap-6">
        <div className="space-y-3">
          <h1 className="max-w-full break-words font-[Georgia,serif] text-2xl font-bold leading-none text-foreground sm:text-6xl md:text-7xl">
            {HERMES_HOME_COPY.title}
          </h1>
          <p className="mx-auto max-w-2xl text-sm text-muted-foreground sm:text-base">
            {HERMES_HOME_COPY.subtitle}
          </p>
        </div>

        <div
          data-testid="home-mode-switcher"
          className="flex max-w-full items-center overflow-x-auto rounded-full border border-border bg-background/85 p-1 shadow-sm backdrop-blur"
        >
          {HOME_MODE_TABS.map((mode) => {
            const isActive =
              mode.kind === "monitor"
                ? agentFlowOpen
                : (currentChat?.taskMode ?? "single") === mode.id;

            return (
              <button
                key={mode.id}
                type="button"
                title={mode.title}
                aria-pressed={isActive}
                onClick={() => handleTaskModeClick(mode)}
                className={`flex h-9 shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-4 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {mode.kind === "monitor" && <Activity className="h-4 w-4" />}
                {mode.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
