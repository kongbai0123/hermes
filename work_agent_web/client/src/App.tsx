import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ChatProvider } from "./contexts/ChatContext";
import { LanguageProvider } from "./contexts/LanguageContext";
import AppShell from "./components/AppShell";
import ErrorBoundary from "./components/ErrorBoundary";

/**
 * LLM Chat Application
 * 
 * A Chat-first LLM Workbench supporting:
 * - Multiple models (OpenAI, Ollama, etc.)
 * - Conversation history
 * - File attachments
 * - Streaming responses
 * - Future: Tool calling, MCP, Agent integration
 */

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <LanguageProvider>
          <ChatProvider>
            <TooltipProvider>
              <Toaster />
              <AppShell />
            </TooltipProvider>
          </ChatProvider>
        </LanguageProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
