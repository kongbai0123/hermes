import { useChat } from "@/contexts/ChatContext";
import { MessageSquare, FileText, Code, Lightbulb } from "lucide-react";
import { toast } from "sonner";
import { createDefaultChat } from "@/lib/workAgent";
import { useLanguage } from "@/contexts/LanguageContext";

export default function EmptyChatState() {
  const { dispatch, state } = useChat();
  const { t } = useLanguage();

  const prompts = [
    {
      icon: FileText,
      title: t("empty.analyze.title"),
      description: t("empty.analyze.desc"),
    },
    {
      icon: Code,
      title: t("empty.debug.title"),
      description: t("empty.debug.desc"),
    },
    {
      icon: Lightbulb,
      title: t("empty.safety.title"),
      description: t("empty.safety.desc"),
    },
    {
      icon: MessageSquare,
      title: t("empty.start.title"),
      description: t("empty.start.desc"),
    },
  ];

  const handlePromptClick = (title: string) => {
    const newChat = createDefaultChat(state.models);
    newChat.title = title;
    dispatch({ type: "CREATE_CHAT", payload: newChat });
    toast.success(t("toast.createdTask", { title }));
  };

  return (
    <div className="text-center space-y-8 px-4">
      <div className="space-y-2">
        <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center mx-auto">
          <MessageSquare className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold">{t("empty.heading")}</h1>
        <p className="text-muted-foreground">
          {t("empty.subtitle")}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
        {prompts.map((prompt) => {
          const Icon = prompt.icon;
          return (
            <button
              key={prompt.title}
              onClick={() => handlePromptClick(prompt.title)}
              className="p-4 rounded-lg border border-border hover:border-primary hover:bg-primary/5 transition-all text-left space-y-2 group"
            >
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
                <span className="font-medium">{prompt.title}</span>
              </div>
              <p className="text-sm text-muted-foreground">{prompt.description}</p>
            </button>
          );
        })}
      </div>

      <div className="text-xs text-muted-foreground space-y-1">
        <p>{t("empty.powered")}</p>
        <p>{t("empty.safeWorkflow")}</p>
      </div>
    </div>
  );
}
