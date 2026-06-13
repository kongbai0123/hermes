import { useEffect, useRef } from 'react';
import { useChat } from '@/contexts/ChatContext';
import MessageList from './MessageList';
import MessageComposer from './MessageComposer';
import EmptyChatState from './EmptyChatState';
import AgentFlowPanel from './AgentFlowPanel';
import { Button } from "@/components/ui/button";
import { MessageSquare, Network } from "lucide-react";

/**
 * ChatWindow: Main chat area with messages and composer
 * 
 * Layout:
 * [Message List]
 * [Message Composer]
 */

interface ChatWindowProps {
  agentFlowOpen: boolean;
  onToggleAgentFlow: () => void;
}

export default function ChatWindow({ agentFlowOpen, onToggleAgentFlow }: ChatWindowProps) {
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
      <main className="relative flex-1 overflow-hidden bg-background">
        <AgentFlowPanel
          mode={agentFlowOpen ? "interactive" : "background"}
          onClose={onToggleAgentFlow}
        />
        <ChatMonitorSwitcher
          agentFlowOpen={agentFlowOpen}
          onToggleAgentFlow={onToggleAgentFlow}
        />
        <div className={agentFlowOpen ? "pointer-events-none relative z-10 h-full opacity-0" : "relative z-10 h-full"}>
          <EmptyChatState agentFlowOpen={agentFlowOpen} onToggleAgentFlow={onToggleAgentFlow} />
        </div>
      </main>
    );
  }

  return (
    <main className="relative flex-1 overflow-hidden bg-background">
      <AgentFlowPanel
        mode={agentFlowOpen ? "interactive" : "background"}
        onClose={onToggleAgentFlow}
      />
      <ChatMonitorSwitcher
        agentFlowOpen={agentFlowOpen}
        onToggleAgentFlow={onToggleAgentFlow}
      />

      <div
        className={`relative z-10 flex h-full flex-col transition-opacity duration-200 ${
          agentFlowOpen ? "pointer-events-none opacity-0" : "opacity-100"
        }`}
      >
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {currentChat.messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <EmptyChatState agentFlowOpen={agentFlowOpen} onToggleAgentFlow={onToggleAgentFlow} />
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
      </div>
    </main>
  );
}

function ChatMonitorSwitcher({
  agentFlowOpen,
  onToggleAgentFlow,
}: {
  agentFlowOpen: boolean;
  onToggleAgentFlow: () => void;
}) {
  return (
    <div className="absolute right-4 top-4 z-30 flex rounded-full border border-border bg-background/85 p-1 shadow-sm backdrop-blur">
      <Button
        type="button"
        variant={agentFlowOpen ? "ghost" : "default"}
        size="sm"
        onClick={() => agentFlowOpen && onToggleAgentFlow()}
        className="h-8 rounded-full px-3 text-xs"
        title="切換到聊天介面"
      >
        <MessageSquare className="mr-1 h-4 w-4" />
        聊天
      </Button>
      <Button
        type="button"
        variant={agentFlowOpen ? "default" : "ghost"}
        size="sm"
        onClick={() => !agentFlowOpen && onToggleAgentFlow()}
        className="h-8 rounded-full px-3 text-xs"
        title="切換到運行監控"
      >
        <Network className="mr-1 h-4 w-4" />
        監控
      </Button>
    </div>
  );
}
