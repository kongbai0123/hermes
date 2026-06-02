import { Message } from '@/types/chat';
import MessageBubble from './MessageBubble';

/**
 * MessageList: Display all messages in a conversation
 */

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </div>
  );
}
