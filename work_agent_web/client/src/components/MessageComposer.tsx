import { useRef, useState } from "react";
import { useChat } from "@/contexts/ChatContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Paperclip, Square } from "lucide-react";
import { nanoid } from "nanoid";
import { toast } from "sonner";
import { Message } from "@/types/chat";
import { useLanguage } from "@/contexts/LanguageContext";

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
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSendMessage = async () => {
    if (!input.trim() || !currentChat || isLoading) return;
    const prompt = input.trim();

    // Add user message
    const userMessage: Message = {
      id: nanoid(),
      chatId: currentChat.id,
      role: 'user',
      content: prompt,
      createdAt: new Date(),
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
    setIsLoading(true);
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch("/api/work-agent/run-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
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

  const handleAttachClick = () => {
    toast.info(t("toast.attachmentDisabled"));
  };

  return (
    <div className="space-y-3">
      {/* Attached Files (placeholder) */}
      {/* <div className="flex gap-2 flex-wrap">
        {attachments.map((file) => (
          <div key={file.id} className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-full text-sm">
            <span>{file.name}</span>
            <button onClick={() => removeAttachment(file.id)}>×</button>
          </div>
        ))}
      </div> */}

      {/* Input Area */}
      <div className="flex gap-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t("composer.placeholder")}
          className="flex-1 resize-none max-h-32"
          disabled={isLoading}
        />

        <div className="flex flex-col gap-2">
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
              disabled={!input.trim() || isLoading}
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
