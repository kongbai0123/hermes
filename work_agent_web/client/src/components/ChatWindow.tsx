import { useEffect, useRef } from 'react';
import { useChat } from '@/contexts/ChatContext';
import MessageList from './MessageList';
import MessageComposer from './MessageComposer';
import EmptyChatState from './EmptyChatState';

/**
 * ChatWindow: Main chat area with messages and composer
 * 
 * Layout:
 * [Message List]
 * [Message Composer]
 */

export default function ChatWindow() {
  const { currentChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentChat?.messages]);

  if (!currentChat) {
    return (
      <main className="flex-1 flex items-center justify-center bg-background overflow-hidden">
        <EmptyChatState />
      </main>
    );
  }

  return (
    <main className="flex-1 flex flex-col bg-background overflow-hidden">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {currentChat.messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <EmptyChatState />
          </div>
        ) : (
          <div className="max-w-4xl mx-auto w-full px-4 py-8 space-y-4">
            <MessageList messages={currentChat.messages} />
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Composer */}
      <div className="border-t border-border bg-background p-4">
        <div className="max-w-4xl mx-auto">
          <MessageComposer />
        </div>
      </div>
    </main>
  );
}
