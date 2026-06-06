import { useRef, useState } from "react";
import { useChat } from "@/contexts/ChatContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Paperclip, Square } from "lucide-react";
import { nanoid } from "nanoid";
import { toast } from "sonner";
import { Attachment, Message } from "@/types/chat";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  attachmentsToPromptNote,
  clipboardItemsToImageAttachments,
  imageFileToAttachment,
} from "@/lib/attachments";

/**
 * MessageComposer: Input area for sending messages
 * 
 * Features:
 * - Multi-line textarea
 * - File attachment
 * - Send / Stop button
 * - Keyboard shortcuts (Enter to send, Shift+Enter for newline)
 */

export default function MessageComposer() {
  const { state, dispatch, currentChat } = useChat();
  const { t } = useLanguage();
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

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

      {/* Input Area */}
      <div className="flex gap-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          placeholder={t("composer.placeholder")}
          className="flex-1 resize-none max-h-32"
          disabled={isLoading}
        />

        <div className="flex flex-col gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <Button
            variant="outline"
            size="icon"
            title={t("composer.attach")}
            disabled={isLoading}
            onClick={handleAttachClick}
          >
            <Paperclip className="w-4 h-4" />
          </Button>

          {isLoading ? (
            <Button
              variant="destructive"
              size="icon"
              onClick={handleStop}
              title={t("composer.stop")}
            >
              <Square className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSendMessage}
              disabled={(!input.trim() && attachments.length === 0) || isLoading}
              size="icon"
              className="bg-primary hover:bg-primary/90"
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
