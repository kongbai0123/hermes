import { useEffect, useState, type DragEvent } from "react";
import { useChat } from "@/contexts/ChatContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ChevronDown,
  ChevronRight,
  FileCode2,
  Folder,
  FolderPlus,
  FolderTree,
  MessageSquare,
  Pin,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  Edit2,
} from "lucide-react";
import { Chat, WorkspaceEntry } from "@/types/chat";
import { createDefaultChat } from "@/lib/workAgent";
import { toast } from "sonner";
import { useLanguage } from "@/contexts/LanguageContext";

/**
 * ChatSidebar: Left sidebar with chat history
 * 
 * Features:
 * - New chat button
 * - Search chats
 * - Group by time (Today, Yesterday, etc.)
 * - Rename, delete, pin chats
 */

export default function ChatSidebar() {
  const { state, dispatch, currentChat } = useChat();
  const { language, t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [workspaceEntries, setWorkspaceEntries] = useState<WorkspaceEntry[]>([]);
  const [expandedDirs, setExpandedDirs] = useState<Record<string, boolean>>({});

  const loadWorkspace = async () => {
    try {
      const response = await fetch("/api/workspace/tree");
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || t("error.loadWorkspace"));
      }
      setWorkspaceEntries(result.entries || []);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("error.loadWorkspace"));
    }
  };

  const handleNewChat = () => {
    const newChat: Chat = createDefaultChat(state.models);
    newChat.title = t("chat.newWorkTask");
    dispatch({ type: 'CREATE_CHAT', payload: newChat });
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  const handleRenameChat = (id: string, currentTitle: string) => {
    setEditingId(id);
    setEditingTitle(currentTitle);
  };

  const handleSaveRename = (id: string) => {
    if (editingTitle.trim()) {
      dispatch({
        type: 'RENAME_CHAT',
        payload: { id, title: editingTitle.trim() },
      });
    }
    setEditingId(null);
  };

  const handleDeleteChat = (id: string) => {
    dispatch({ type: 'DELETE_CHAT', payload: id });
  };

  const handlePinChat = (id: string) => {
    dispatch({ type: 'PIN_CHAT', payload: id });
  };

  const handleCreateProject = () => {
    dispatch({
      type: "CREATE_PROJECT",
      payload: {
        id: crypto.randomUUID?.() ?? `project-${Date.now()}`,
        title: t("sidebar.newProject"),
        chatIds: [],
        isExpanded: true,
      },
    });
  };

  const handleDropChatToProject = (projectId: string, event: DragEvent) => {
    event.preventDefault();
    const chatId =
      event.dataTransfer.getData("application/x-work-agent-chat") ||
      event.dataTransfer.getData("text/plain");

    if (!chatId) return;

    dispatch({
      type: "ASSIGN_CHAT_TO_PROJECT",
      payload: { projectId, chatId },
    });
    toast.success(t("toast.chatFiled"));
  };

  const filteredChats = state.chats.filter((chat) =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filedChatIds = new Set(state.projects.flatMap((project) => project.chatIds));
  const unfiledChats = filteredChats.filter((chat) => !filedChatIds.has(chat.id));
  const pinnedChats = unfiledChats.filter((c) => c.isPinned);
  const unpinnedChats = unfiledChats.filter((c) => !c.isPinned);

  const ensureActiveChat = () => {
    if (currentChat) return currentChat;
    const newChat: Chat = createDefaultChat(state.models);
    dispatch({ type: "CREATE_CHAT", payload: newChat });
    return newChat;
  };

  const handleOpenWorkspaceFile = async (path: string) => {
    const chat = ensureActiveChat();
    try {
      const response = await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || t("error.readFile"));
      }
      dispatch({
        type: "UPDATE_WORKBENCH",
        payload: {
          chatId: chat.id,
          workbench: {
            selectedFile: {
              path: String(result.path),
              content: String(result.content ?? ""),
            },
            workspaceEntries,
          },
        },
      });
      toast.success(t("toast.opened", { path }));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("error.readFile"));
    }
  };

  const toggleDirectory = (path: string) => {
    setExpandedDirs((current) => ({ ...current, [path]: !current[path] }));
  };

  return (
    <aside className="w-64 border-r border-border bg-card flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-border space-y-3">
        <Button onClick={handleNewChat} className="w-full gap-2 bg-primary hover:bg-primary/90">
          <Plus className="w-4 h-4" />
          {t("sidebar.newChat")}
        </Button>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder={t("sidebar.search")}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto">
        {/* Unfiled work tasks */}
        {(pinnedChats.length > 0 || unpinnedChats.length > 0) && (
          <div className="px-2 py-3">
            <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase flex items-center gap-2">
              <FolderTree className="w-3.5 h-3.5" />
              {t("sidebar.workTasks")}
            </div>
            {pinnedChats.length > 0 && (
              <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">
                {t("sidebar.pinned")}
              </div>
            )}
            {[...pinnedChats, ...unpinnedChats].map((chat) => (
              <ChatHistoryItem
                key={chat.id}
                chat={chat}
                isActive={currentChat?.id === chat.id}
                isEditing={editingId === chat.id}
                editingTitle={editingTitle}
                onSelect={() => dispatch({ type: 'SELECT_CHAT', payload: chat.id })}
                onRename={() => handleRenameChat(chat.id, chat.title)}
                onSaveRename={() => handleSaveRename(chat.id)}
                onDelete={() => handleDeleteChat(chat.id)}
                onPin={() => handlePinChat(chat.id)}
                onEditChange={setEditingTitle}
                onDragStart={(event) => {
                  event.dataTransfer.setData("application/x-work-agent-chat", chat.id);
                  event.dataTransfer.setData("text/plain", chat.id);
                  event.dataTransfer.effectAllowed = "move";
                }}
                locale={language}
                labels={{
                  rename: t("sidebar.rename"),
                  pin: t("sidebar.pin"),
                  unpin: t("sidebar.unpin"),
                  delete: t("sidebar.delete"),
                }}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {unfiledChats.length === 0 && (
          <div className="p-4 text-center text-muted-foreground text-sm">
            {searchQuery ? t("sidebar.noChats") : t("sidebar.noChatsYet")}
          </div>
        )}

        <div className="px-4 py-3 border-t border-border space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase">
              <FolderTree className="w-4 h-4" />
              {t("sidebar.projects")}
            </div>
            <button
              onClick={handleCreateProject}
              className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
              title={t("sidebar.addProject")}
            >
              <FolderPlus className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-1">
            {state.projects.map((project) => (
              <ProjectExplorerItem
                key={project.id}
                project={project}
                chats={project.chatIds
                  .map((chatId) => state.chats.find((chat) => chat.id === chatId))
                  .filter(
                    (chat): chat is NonNullable<typeof chat> => Boolean(chat)
                  )}
                onToggle={() => dispatch({ type: "TOGGLE_PROJECT", payload: project.id })}
                onDrop={(event) => handleDropChatToProject(project.id, event)}
                onSelectMessage={(chatId) => dispatch({ type: "SELECT_CHAT", payload: chatId })}
                onDragChat={(chatId, event) => {
                  event.dataTransfer.setData("application/x-work-agent-chat", chatId);
                  event.dataTransfer.setData("text/plain", chatId);
                  event.dataTransfer.effectAllowed = "move";
                }}
                labels={{
                  dropMessage: t("sidebar.dropChat"),
                  emptyProject: t("sidebar.emptyProject"),
                }}
              />
            ))}
          </div>
        </div>

        <div className="px-4 py-3 border-t border-border space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase">
              <FolderTree className="w-4 h-4" />
              {t("sidebar.files")}
            </div>
            <button
              onClick={loadWorkspace}
              className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
              title={t("sidebar.refreshWorkspace")}
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-1">
            {workspaceEntries.map((entry) => (
              <WorkspaceExplorerItem
                key={entry.id}
                entry={entry}
                selectedPath={currentChat?.workbench.selectedFile?.path}
                expandedDirs={expandedDirs}
                onToggleDir={toggleDirectory}
                onOpenFile={handleOpenWorkspaceFile}
              />
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}

interface ProjectExplorerItemProps {
  project: {
    id: string;
    title: string;
    chatIds: string[];
    isExpanded: boolean;
  };
  chats: Array<{
    id: string;
    title: string;
    messages: Array<{ content: string }>;
  }>;
  onToggle: () => void;
  onDrop: (event: DragEvent<HTMLDivElement>) => void;
  onSelectMessage: (chatId: string) => void;
  onDragChat: (chatId: string, event: DragEvent<HTMLButtonElement>) => void;
  labels: {
    dropMessage: string;
    emptyProject: string;
  };
}

function ProjectExplorerItem({
  project,
  chats,
  onToggle,
  onDrop,
  onSelectMessage,
  onDragChat,
  labels,
}: ProjectExplorerItemProps) {
  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
      }}
      onDrop={onDrop}
      className="rounded-md border border-transparent hover:border-border"
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-1 rounded-md px-2 py-1.5 text-sm text-left hover:bg-secondary"
        title={labels.dropMessage}
      >
        {project.isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5" />
        )}
        <Folder className="w-4 h-4 flex-shrink-0" />
        <span className="min-w-0 flex-1 truncate">{project.title}</span>
        <span className="text-xs text-muted-foreground">{project.chatIds.length}</span>
      </button>

      {project.isExpanded && (
        <div className="space-y-1 pb-1 pl-6 pr-1">
          {chats.length === 0 ? (
            <div className="rounded border border-dashed border-border px-2 py-1.5 text-xs text-muted-foreground">
              {labels.emptyProject}
            </div>
          ) : (
            chats.map((chat) => (
              <button
                key={chat.id}
                draggable
                onDragStart={(event) => onDragChat(chat.id, event)}
                onClick={() => onSelectMessage(chat.id)}
                className="w-full flex items-start gap-1.5 rounded px-2 py-1.5 text-left text-xs hover:bg-secondary"
                title={chat.title}
              >
                <MessageSquare className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{chat.title}</span>
                  <span className="block truncate text-muted-foreground">
                    {chat.messages.at(-1)?.content || labels.dropMessage}
                  </span>
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

interface WorkspaceExplorerItemProps {
  entry: WorkspaceEntry;
  selectedPath?: string;
  expandedDirs: Record<string, boolean>;
  onToggleDir: (path: string) => void;
  onOpenFile: (path: string) => void;
  depth?: number;
}

function WorkspaceExplorerItem({
  entry,
  selectedPath,
  expandedDirs,
  onToggleDir,
  onOpenFile,
  depth = 0,
}: WorkspaceExplorerItemProps) {
  const isDir = entry.kind === "dir";
  const isExpanded = !!expandedDirs[entry.path];
  const isSelected = selectedPath === entry.path;

  return (
    <div>
      <button
        onClick={() => (isDir ? onToggleDir(entry.path) : onOpenFile(entry.path))}
        className={`w-full flex items-center gap-1 rounded-md px-2 py-1.5 text-sm text-left ${
          isSelected ? "bg-primary/10 text-primary" : "hover:bg-secondary"
        }`}
        style={{ paddingLeft: `${8 + depth * 14}px` }}
        title={entry.path}
      >
        {isDir ? (
          isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />
        ) : (
          <span className="w-3.5" />
        )}
        {isDir ? (
          <Folder className="w-4 h-4 flex-shrink-0" />
        ) : (
          <FileCode2 className="w-4 h-4 flex-shrink-0" />
        )}
        <span className="truncate">{entry.path.split("/").at(-1)}</span>
      </button>

      {isDir && isExpanded && entry.children?.length ? (
        <div className="space-y-1">
          {entry.children.map((child) => (
            <WorkspaceExplorerItem
              key={child.id}
              entry={child}
              selectedPath={selectedPath}
              expandedDirs={expandedDirs}
              onToggleDir={onToggleDir}
              onOpenFile={onOpenFile}
              depth={depth + 1}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

interface ChatHistoryItemProps {
  chat: Chat;
  isActive: boolean;
  isEditing: boolean;
  editingTitle: string;
  onSelect: () => void;
  onRename: () => void;
  onSaveRename: () => void;
  onDelete: () => void;
  onPin: () => void;
  onEditChange: (title: string) => void;
  onDragStart: (event: DragEvent<HTMLDivElement>) => void;
  locale: string;
  labels: {
    rename: string;
    pin: string;
    unpin: string;
    delete: string;
  };
}

function ChatHistoryItem({
  chat,
  isActive,
  isEditing,
  editingTitle,
  onSelect,
  onRename,
  onSaveRename,
  onDelete,
  onPin,
  onEditChange,
  onDragStart,
  locale,
  labels,
}: ChatHistoryItemProps) {
  return (
    <div
      draggable={!isEditing}
      onDragStart={onDragStart}
      className={`group px-2 py-2 rounded-lg cursor-pointer transition-colors ${
        isActive ? 'bg-primary/10 text-primary' : 'hover:bg-secondary text-foreground'
      }`}
      onClick={onSelect}
    >
      {isEditing ? (
        <input
          autoFocus
          value={editingTitle}
          onChange={(e) => onEditChange(e.target.value)}
          onBlur={onSaveRename}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSaveRename();
            if (e.key === 'Escape') onEditChange(chat.title);
          }}
          className="w-full px-2 py-1 bg-background border border-border rounded text-sm"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{chat.title}</p>
            <p className="text-xs text-muted-foreground truncate">
              {new Date(chat.updatedAt).toLocaleDateString(locale)}
            </p>
          </div>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRename();
              }}
              className="p-1 hover:bg-secondary rounded"
              title={labels.rename}
            >
              <Edit2 className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onPin();
              }}
              className="p-1 hover:bg-secondary rounded"
              title={chat.isPinned ? labels.unpin : labels.pin}
            >
              <Pin className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:bg-destructive/10 hover:text-destructive rounded"
              title={labels.delete}
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
