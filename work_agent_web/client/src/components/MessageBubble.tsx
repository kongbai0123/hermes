import { Message } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Copy, RotateCcw, ThumbsUp, ThumbsDown, Trash2 } from 'lucide-react';
import { Streamdown } from 'streamdown';
import { toast } from 'sonner';
import { useLanguage } from '@/contexts/LanguageContext';

/**
 * MessageBubble: Individual message display
 * 
 * Features:
 * - User messages (right-aligned)
 * - Assistant messages (left-aligned)
 * - Markdown rendering
 * - Copy button
 * - Regenerate button (assistant only)
 */

interface MessageBubbleProps {
  message: Message;
  onDelete: () => void;
}

export default function MessageBubble({ message, onDelete }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const { t } = useLanguage();

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    toast.success(t("toast.messageCopied"));
  };

  const handlePlaceholderAction = (label: string) => {
    toast.info(t("toast.placeholderNoted", { label }));
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} message-enter`}>
      <div
        className={`max-w-2xl rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-none'
            : 'bg-secondary text-foreground rounded-bl-none'
        }`}
      >
        {/* Message Content */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {message.isStreaming ? (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-current typing-dot" />
                <div className="w-2 h-2 rounded-full bg-current typing-dot" />
                <div className="w-2 h-2 rounded-full bg-current typing-dot" />
              </div>
            </div>
          ) : (
            <Streamdown>{message.content}</Streamdown>
          )}
        </div>

        {message.attachments?.length ? (
          <div className="mt-3 grid grid-cols-2 gap-2">
            {message.attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="overflow-hidden rounded border border-current/20 bg-background/20"
              >
                {attachment.dataUrl && attachment.type?.startsWith("image/") ? (
                  <img
                    src={attachment.dataUrl}
                    alt={attachment.name}
                    className="h-32 w-full object-cover"
                  />
                ) : (
                  <div className="p-2 text-xs">{attachment.name}</div>
                )}
              </div>
            ))}
          </div>
        ) : null}

        {/* Message Actions */}
        {!message.isStreaming && (
          <div className="flex items-center gap-1 mt-2 pt-2 border-t border-current/20">
            {!isUser && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-6 px-2 text-xs"
                  title={t("bubble.copy")}
                >
                  <Copy className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePlaceholderAction(t("bubble.regenerateLabel"))}
                  className="h-6 px-2 text-xs"
                  title={t("bubble.regenerate")}
                >
                  <RotateCcw className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePlaceholderAction(t("bubble.positiveLabel"))}
                  className="h-6 px-2 text-xs"
                  title={t("bubble.good")}
                >
                  <ThumbsUp className="w-3 h-3" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePlaceholderAction(t("bubble.negativeLabel"))}
                  className="h-6 px-2 text-xs"
                  title={t("bubble.bad")}
                >
                  <ThumbsDown className="w-3 h-3" />
                </Button>
              </>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onDelete}
              className="h-6 px-2 text-xs hover:text-destructive"
              title={t("bubble.delete")}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
