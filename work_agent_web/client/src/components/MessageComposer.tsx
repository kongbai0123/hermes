import { useRef, useState } from "react";
import { useChat } from "@/contexts/ChatContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Check,
  ChevronDown,
  Mic,
  Paperclip,
  Send,
  ShieldCheck,
  Square,
} from "lucide-react";
import { nanoid } from "nanoid";
import { toast } from "sonner";
import { Attachment, ChatSettings, Message, ReasoningLevel, ResponseSpeed } from "@/types/chat";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  attachmentsToPromptNote,
  clipboardItemsToImageAttachments,
  imageFileToAttachment,
} from "@/lib/attachments";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * MessageComposer: Input area for sending messages
 * 
 * Features:
 * - Multi-line textarea
 * - File attachment
 * - Send / Stop button
 * - Keyboard shortcuts (Enter to send, Shift+Enter for newline)
 */

const REASONING_OPTIONS: Array<{ value: ReasoningLevel; label: string }> = [
  { value: "low", label: "低" },
  { value: "medium", label: "中" },
  { value: "high", label: "高" },
  { value: "ultra", label: "超高" },
];

const SPEED_OPTIONS: Array<{ value: ResponseSpeed; label: string }> = [
  { value: "slow", label: "慢" },
  { value: "standard", label: "標準" },
  { value: "fast", label: "快" },
];

export default function MessageComposer() {
  const { state, dispatch, currentChat } = useChat();
  const { t } = useLanguage();
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const currentModel = state.models.find((model) => model.id === currentChat?.settings.model);
  const currentReasoning =
    REASONING_OPTIONS.find((option) => option.value === currentChat?.settings.reasoningLevel) ??
    REASONING_OPTIONS[1];
  const currentSpeed =
    SPEED_OPTIONS.find((option) => option.value === currentChat?.settings.responseSpeed) ??
    SPEED_OPTIONS[1];

  const addSettingTimelineMessage = (content: string) => {
    if (!currentChat) return;
    dispatch({
      type: "ADD_MESSAGE",
      payload: {
        id: nanoid(),
        chatId: currentChat.id,
        role: "system",
        content,
        createdAt: new Date(),
      },
    });
  };

  const updateSettingsWithTimeline = (
    settings: Partial<ChatSettings>,
    timelineMessage: string
  ) => {
    if (!currentChat) return;
    dispatch({
      type: "UPDATE_CHAT_SETTINGS",
      payload: {
        chatId: currentChat.id,
        settings,
      },
    });
    addSettingTimelineMessage(timelineMessage);
  };

  const handleModelChange = (modelId: string) => {
    const model = state.models.find((item) => item.id === modelId);
    if (!model || !currentChat || model.id === currentChat.settings.model) return;
    updateSettingsWithTimeline(
      {
        model: model.id,
        provider: model.provider,
      },
      `模型已切換至 ${model.name}`
    );
  };

  const handleReasoningChange = (reasoningLevel: ReasoningLevel) => {
    const option = REASONING_OPTIONS.find((item) => item.value === reasoningLevel);
    if (!option || !currentChat || reasoningLevel === currentChat.settings.reasoningLevel) return;
    updateSettingsWithTimeline({ reasoningLevel }, `推理已切換至 ${option.label}`);
  };

  const handleSpeedChange = (responseSpeed: ResponseSpeed) => {
    const option = SPEED_OPTIONS.find((item) => item.value === responseSpeed);
    if (!option || !currentChat || responseSpeed === currentChat.settings.responseSpeed) return;
    updateSettingsWithTimeline({ responseSpeed }, `速度已切換至 ${option.label}`);
  };

  const handleSendMessage = async () => {
    if ((!input.trim() && attachments.length === 0) || !currentChat || isLoading) return;
    const prompt = input.trim();
    const messageAttachments = attachments;

    // Add user message
    const userMessage: Message = {
      id: nanoid(),
      chatId: currentChat.id,
      role: 'user',
      content: prompt,
      createdAt: new Date(),
      attachments: messageAttachments,
    };

    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    const assistantMessageId = nanoid();
    dispatch({
      type: "ADD_MESSAGE",
      payload: {
        id: assistantMessageId,
        chatId: currentChat.id,
        role: "assistant",
        content: "",
        createdAt: new Date(),
        isStreaming: true,
      },
    });
    dispatch({
      type: "UPDATE_WORKBENCH",
      payload: {
        chatId: currentChat.id,
        workbench: {
          status: "running",
          plan: [],
          toolLogs: [],
        },
      },
    });
    setInput('');
    setAttachments([]);
    setIsLoading(true);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/work-agent/run-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: `${prompt}${attachmentsToPromptNote(messageAttachments)}`,
          model: currentChat.settings.model,
          reasoningLevel: currentChat.settings.reasoningLevel,
          responseSpeed: currentChat.settings.responseSpeed,
        }),
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(t("error.streamFailed"));
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.trim()) continue;
          const event = JSON.parse(line);

          if (event.type === "workbench") {
            dispatch({
              type: "UPDATE_WORKBENCH",
              payload: {
                chatId: currentChat.id,
                workbench: {
                  status: event.status === "error" ? "error" : "running",
                  plan: Array.isArray(event.plan) ? event.plan : [],
                  toolLogs: Array.isArray(event.toolLogs) ? event.toolLogs : [],
                  safetyRules: Array.isArray(event.safetyRules)
                    ? event.safetyRules
                    : currentChat.workbench.safetyRules,
                  workspaceEntries: Array.isArray(event.workspaceEntries)
                    ? event.workspaceEntries
                    : currentChat.workbench.workspaceEntries,
                  allowedCommands: Array.isArray(event.allowedCommands)
                    ? event.allowedCommands
                    : currentChat.workbench.allowedCommands,
                },
              },
            });
          }

          if (event.type === "chunk") {
            assistantContent += String(event.content ?? "");
            dispatch({
              type: "UPDATE_MESSAGE",
              payload: {
                id: assistantMessageId,
                chatId: currentChat.id,
                role: "assistant",
                content: assistantContent,
                createdAt: new Date(),
                isStreaming: true,
              },
            });
          }

          if (event.type === "done") {
            dispatch({
              type: "UPDATE_MESSAGE",
              payload: {
                id: assistantMessageId,
                chatId: currentChat.id,
                role: "assistant",
                content: assistantContent,
                createdAt: new Date(),
                isStreaming: false,
              },
            });
            dispatch({
              type: "UPDATE_WORKBENCH",
              payload: {
                chatId: currentChat.id,
                workbench: {
                  status: "done",
                },
              },
            });
          }

          if (event.type === "error") {
            throw new Error(String(event.error ?? t("error.requestFailed")));
          }
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        toast.info(t("toast.requestStopped"));
        dispatch({
          type: "UPDATE_WORKBENCH",
          payload: {
            chatId: currentChat.id,
            workbench: {
              status: "idle",
            },
          },
        });
        dispatch({
          type: "UPDATE_MESSAGE",
          payload: {
            id: assistantMessageId,
            chatId: currentChat.id,
            role: "assistant",
            content: t("toast.requestStopped"),
            createdAt: new Date(),
            isStreaming: false,
          },
        });
        return;
      }

      const message = error instanceof Error ? error.message : t("error.requestFailed");
      toast.error(message);
      dispatch({
        type: "UPDATE_WORKBENCH",
        payload: {
          chatId: currentChat.id,
          workbench: {
            status: "error",
          },
        },
      });
      dispatch({
        type: "UPDATE_MESSAGE",
        payload: {
          id: assistantMessageId,
          chatId: currentChat.id,
          role: "assistant",
          content: t("error.agentError", { message }),
          createdAt: new Date(),
          isStreaming: false,
        },
      });
    } finally {
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handlePaste = async (event: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const pastedImages = await clipboardItemsToImageAttachments(event.clipboardData.items);
    if (!pastedImages.length) return;

    event.preventDefault();
    setAttachments((current) => [...current, ...pastedImages]);
    toast.success(`${pastedImages.length} image attached`);
  };

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []).filter((file) => file.type.startsWith("image/"));
    if (!files.length) return;

    const nextAttachments = await Promise.all(files.map((file) => imageFileToAttachment(file)));
    setAttachments((current) => [...current, ...nextAttachments]);
    event.target.value = "";
  };

  const removeAttachment = (id: string) => {
    setAttachments((current) => current.filter((attachment) => attachment.id !== id));
  };

  return (
    <div className="space-y-3">
      {attachments.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {attachments.map((file) => (
            <div
              key={file.id}
              className="relative h-20 w-24 shrink-0 overflow-hidden rounded border border-border bg-secondary"
            >
              {file.dataUrl ? (
                <img src={file.dataUrl} alt={file.name} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center px-2 text-xs text-muted-foreground">
                  {file.name}
                </div>
              )}
              <button
                type="button"
                onClick={() => removeAttachment(file.id)}
                className="absolute right-1 top-1 grid h-5 w-5 place-items-center rounded bg-background/90 text-xs text-foreground shadow"
                aria-label={`Remove ${file.name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="rounded-2xl border border-border bg-card shadow-sm">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={t("composer.placeholder")}
          className="max-h-40 min-h-24 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
          disabled={isLoading}
        />

        <div className="flex items-center gap-2 border-t border-border/70 px-3 py-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            variant="ghost"
            size="icon-sm"
            title={t("composer.attach")}
            disabled={isLoading}
            onClick={handleAttachClick}
          >
            <Paperclip className="w-4 h-4" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1 text-amber-600">
                <ShieldCheck className="w-4 h-4" />
                <span className="hidden sm:inline">{currentChat?.workbench.safetyModeLabel ?? "完整存取權"}</span>
                <ChevronDown className="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-48">
              <DropdownMenuLabel>授權</DropdownMenuLabel>
              <DropdownMenuItem disabled>
                {currentChat?.workbench.safetyModeLabel ?? "完整存取權"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="flex-1" />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1">
                <span>{currentModel?.name ?? currentChat?.settings.model ?? "模型"}</span>
                <ChevronDown className="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>模型</DropdownMenuLabel>
              {state.models.map((model) => (
                <DropdownMenuItem key={model.id} onClick={() => handleModelChange(model.id)}>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium">{model.name}</div>
                    <div className="truncate text-xs text-muted-foreground">{model.provider}</div>
                  </div>
                  {model.id === currentChat?.settings.model ? <Check className="w-4 h-4" /> : null}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1">
                <span>推理 {currentReasoning.label}</span>
                <ChevronDown className="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36">
              <DropdownMenuLabel>推理</DropdownMenuLabel>
              {REASONING_OPTIONS.map((option) => (
                <DropdownMenuItem key={option.value} onClick={() => handleReasoningChange(option.value)}>
                  <span className="flex-1">{option.label}</span>
                  {option.value === currentChat?.settings.reasoningLevel ? <Check className="w-4 h-4" /> : null}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="gap-1">
                <span>速度 {currentSpeed.label}</span>
                <ChevronDown className="w-3 h-3" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36">
              <DropdownMenuLabel>速度</DropdownMenuLabel>
              {SPEED_OPTIONS.map((option) => (
                <DropdownMenuItem key={option.value} onClick={() => handleSpeedChange(option.value)}>
                  <span className="flex-1">{option.label}</span>
                  {option.value === currentChat?.settings.responseSpeed ? <Check className="w-4 h-4" /> : null}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            variant="ghost"
            size="icon-sm"
            title="語音輸入"
            disabled={isLoading}
            onClick={() => toast.info("語音輸入尚未啟用")}
          >
            <Mic className="w-4 h-4" />
          </Button>

          {isLoading ? (
            <Button
              variant="destructive"
              size="icon"
              onClick={handleStop}
              title={t("composer.stop")}
              className="rounded-full"
            >
              <Square className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSendMessage}
              disabled={(!input.trim() && attachments.length === 0) || isLoading}
              size="icon"
              className="rounded-full bg-primary hover:bg-primary/90"
              title={t("composer.send")}
            >
              <Send className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Helper Text */}
      <p className="text-xs text-muted-foreground text-center">
        {t("composer.helper")}
      </p>
    </div>
  );
}
