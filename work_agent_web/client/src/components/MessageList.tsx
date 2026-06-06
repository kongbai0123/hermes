import { Message } from '@/types/chat';
import MessageBubble from './MessageBubble';
import { useChat } from '@/contexts/ChatContext';
import { toast } from 'sonner';
import { useLanguage } from '@/contexts/LanguageContext';

/**
 * MessageList: Display all messages in a conversation
 */

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const { dispatch } = useChat();
  const { t } = useLanguage();

  const handleDeleteMessage = (message: Message) => {
    dispatch({
      type: "DELETE_MESSAGE",
      payload: { chatId: message.chatId, messageId: message.id },
    });
    toast.success(t("toast.messageDeleted"));
  };

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onDelete={() => handleDeleteMessage(message)}
        />
      ))}
    </div>
  );
}
