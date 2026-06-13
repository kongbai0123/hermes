import { useState } from 'react';
import { useChat } from '@/contexts/ChatContext';
import TopBar from './TopBar';
import ChatSidebar from './ChatSidebar';
import ChatWindow from './ChatWindow';
import RightPanel from './RightPanel';

/**
 * AppShell: Main layout container
 * 
 * Layout structure:
 * ┌─────────────────────────────────────────────┐
 * │ TopBar                                      │
 * ├──────────┬─────────────────────┬────────────┤
 * │ Sidebar  │ Chat Window         │ Right Panel│
 * │          │                     │ (Optional) │
 * └──────────┴─────────────────────┴────────────┘
 */

export default function AppShell() {
  const { state } = useChat();
  const [agentFlowOpen, setAgentFlowOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Top Bar */}
      <TopBar
        agentFlowOpen={agentFlowOpen}
        onToggleAgentFlow={() => setAgentFlowOpen((current) => !current)}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Chat History */}
        <ChatSidebar />

        {/* Center - Chat Window */}
        <ChatWindow
          agentFlowOpen={agentFlowOpen}
          onToggleAgentFlow={() => setAgentFlowOpen((current) => !current)}
        />

        {/* Right Panel - Optional Context/Settings */}
        {state.rightPanelOpen && <RightPanel />}
      </div>
    </div>
  );
}
