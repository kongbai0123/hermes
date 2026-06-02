import { useChat } from "@/contexts/ChatContext";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import { Check, CheckCircle2, CircleAlert, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "sonner";
import { useLanguage } from "@/contexts/LanguageContext";

export default function RightPanel() {
  const { dispatch, currentChat } = useChat();
  const { t } = useLanguage();
  const [patchPrompt, setPatchPrompt] = useState("");
  const [isGeneratingPatch, setIsGeneratingPatch] = useState(false);
  const [isApplyingPatch, setIsApplyingPatch] = useState(false);

  if (!currentChat) return null;

  const settings = currentChat.settings;

  const handleTemperatureChange = (value: number[]) => {
    dispatch({
      type: "UPDATE_CHAT_SETTINGS",
      payload: {
        chatId: currentChat.id,
        settings: { temperature: value[0] },
      },
    });
  };

  const handleMaxTokensChange = (value: number[]) => {
    dispatch({
      type: "UPDATE_CHAT_SETTINGS",
      payload: {
        chatId: currentChat.id,
        settings: { maxTokens: value[0] },
      },
    });
  };

  const handleSystemPromptChange = (value: string) => {
    dispatch({
      type: "UPDATE_CHAT_SETTINGS",
      payload: {
        chatId: currentChat.id,
        settings: { systemPrompt: value },
      },
    });
  };

  const handleGeneratePatch = async () => {
    const selectedFile = currentChat.workbench.selectedFile;
    if (!selectedFile) {
      toast.info(t("toast.selectFileFirst"));
      return;
    }

    const prompt =
      patchPrompt.trim() ||
      currentChat.messages.filter((message) => message.role === "user").at(-1)?.content ||
      "";
    if (!prompt) {
      toast.info(t("toast.writePatchInstruction"));
      return;
    }

    setIsGeneratingPatch(true);
    try {
      const response = await fetch("/api/work-agent/patch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          path: selectedFile.path.replace(/^workspace\//, ""),
          model: currentChat.settings.model,
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || t("error.generatePatch"));
      }

      dispatch({
        type: "UPDATE_WORKBENCH",
        payload: {
          chatId: currentChat.id,
          workbench: {
            patch: {
              path: String(result.path),
              summary: String(result.summary ?? ""),
              diff: String(result.diff ?? ""),
              revisedContent: String(result.revisedContent ?? ""),
            },
          },
        },
      });
      toast.success(t("toast.patchGenerated"));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("error.generatePatch"));
    } finally {
      setIsGeneratingPatch(false);
    }
  };

  const handleApplyPatch = async () => {
    const patch = currentChat.workbench.patch;
    if (!patch?.revisedContent) {
      toast.info(t("toast.generatePatchFirst"));
      return;
    }

    const confirmed = window.confirm(t("confirm.applyPatch", { path: patch.path }));
    if (!confirmed) return;

    setIsApplyingPatch(true);
    try {
      const response = await fetch("/api/work-agent/apply-patch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: patch.path,
          content: patch.revisedContent,
        }),
      });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.error || t("error.applyPatch"));
      }

      const fileResponse = await fetch(`/api/workspace/file?path=${encodeURIComponent(patch.path)}`);
      const fileResult = await fileResponse.json();
      dispatch({
        type: "UPDATE_WORKBENCH",
        payload: {
          chatId: currentChat.id,
          workbench: {
            selectedFile: {
              path: String(fileResult.path ?? patch.path),
              content: String(fileResult.content ?? patch.revisedContent),
            },
          },
        },
      });
      toast.success(t("toast.patchApplied"));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("error.applyPatch"));
    } finally {
      setIsApplyingPatch(false);
    }
  };

  return (
    <aside className="w-80 border-l border-border bg-card flex flex-col overflow-hidden">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold">{t("panel.workbench")}</h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => dispatch({ type: "TOGGLE_RIGHT_PANEL" })}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      <Tabs defaultValue="workbench" className="flex-1 flex flex-col overflow-hidden">
        <TabsList className="w-full rounded-none border-b border-border">
          <TabsTrigger value="workbench" className="flex-1">
            {t("panel.workbench")}
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex-1">
            {t("panel.settings")}
          </TabsTrigger>
          <TabsTrigger value="context" className="flex-1">
            {t("panel.context")}
          </TabsTrigger>
          <TabsTrigger value="patch" className="flex-1">
            {t("panel.patch")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="workbench" className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="font-medium">{t("panel.executionStatus")}</h3>
              <span className="text-sm text-primary font-medium uppercase">
                {t(`status.${currentChat.workbench.status}`)}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {t("panel.liveWorkbench")}
            </p>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.plan")}</h3>
            {currentChat.workbench.plan.length > 0 ? (
              <div className="space-y-2">
                {currentChat.workbench.plan.map((step) => (
                  <div key={step.id} className="rounded-md bg-secondary p-3 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium">{step.title}</span>
                      <span className="text-xs uppercase text-muted-foreground">
                        {t(`status.${step.status}`)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">{step.detail}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("panel.noPlan")}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.toolLog")}</h3>
            {currentChat.workbench.toolLogs.length > 0 ? (
              <div className="relative pl-5 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-border">
                {currentChat.workbench.toolLogs.map((log, index) => (
                  <div key={log.id} className="relative pb-4 last:pb-0">
                    <span
                      className={`absolute -left-[18px] top-1 flex h-4 w-4 items-center justify-center rounded-full bg-card ${
                        log.ok ? "text-primary" : "text-destructive"
                      }`}
                    >
                      {log.ok ? <CheckCircle2 className="h-4 w-4" /> : <CircleAlert className="h-4 w-4" />}
                    </span>
                    <div className="rounded-md border border-border p-3 space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{log.tool}</span>
                        <span className="text-xs text-muted-foreground">{t("panel.step", { number: index + 1 })}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{log.summary}</p>
                      <p className="text-xs break-words">{log.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t("panel.noToolObservations")}</p>
            )}
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.safetyRules")}</h3>
            <div className="space-y-2">
              {currentChat.workbench.safetyRules.map((rule) => (
                <div key={rule.id} className="rounded-md bg-secondary p-3">
                  <p className="text-sm font-medium">{translateSafetyRule(rule.id, "label", rule.label, t)}</p>
                  <p className="text-xs text-muted-foreground">{translateSafetyRule(rule.id, "desc", rule.description, t)}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.allowedCommands")}</h3>
            <div className="space-y-2">
              {(currentChat.workbench.allowedCommands || []).map((command) => (
                <div key={command} className="rounded-md border border-border p-3">
                  <p className="text-sm font-medium">{command}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.workspace")}</h3>
            <div className="space-y-2">
              {currentChat.workbench.workspaceEntries.map((entry) => (
                <div key={entry.id} className="rounded-md border border-border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium">{entry.path}</span>
                    <span className="text-xs uppercase text-muted-foreground">{entry.kind}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{entry.summary}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.selectedFile")}</h3>
            {currentChat.workbench.selectedFile ? (
              <div className="rounded-md border border-border p-3 space-y-2">
                <p className="text-sm font-medium">{currentChat.workbench.selectedFile.path}</p>
                <pre className="max-h-64 overflow-auto rounded bg-secondary p-3 text-xs whitespace-pre-wrap break-words">
                  {currentChat.workbench.selectedFile.content}
                </pre>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("panel.selectFilePreview")}
              </p>
            )}
          </div>
        </TabsContent>

        <TabsContent value="settings" className="flex-1 overflow-y-auto p-4 space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t("panel.temperature")}</Label>
              <span className="text-sm text-muted-foreground">
                {settings.temperature.toFixed(2)}
              </span>
            </div>
            <Slider
              value={[settings.temperature]}
              onValueChange={handleTemperatureChange}
              min={0}
              max={2}
              step={0.1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              {t("panel.temperatureHint")}
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>{t("panel.maxTokens")}</Label>
              <span className="text-sm text-muted-foreground">{settings.maxTokens}</span>
            </div>
            <Slider
              value={[settings.maxTokens]}
              onValueChange={handleMaxTokensChange}
              min={100}
              max={4000}
              step={100}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label>{t("panel.systemPrompt")}</Label>
            <Textarea
              value={settings.systemPrompt}
              onChange={(e) => handleSystemPromptChange(e.target.value)}
              placeholder={t("panel.systemPromptPlaceholder")}
              className="min-h-24 resize-none"
            />
          </div>
        </TabsContent>

        <TabsContent value="context" className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.attachedFiles")}</h3>
            {currentChat.messages.some((m) => m.attachments?.length) ? (
              <div className="space-y-2">
                {currentChat.messages.flatMap((m) => m.attachments || []).map((file) => (
                  <div key={file.id} className="p-2 bg-secondary rounded text-sm">
                    <p className="font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{t("panel.noFiles")}</p>
            )}
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.contextWindow")}</h3>
            <div className="p-3 bg-secondary rounded space-y-1">
              <div className="flex justify-between text-sm">
                <span>{t("panel.messages")}</span>
                <span className="font-medium">{currentChat.messages.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>{t("panel.model")}</span>
                <span className="font-medium text-primary">{settings.model}</span>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="patch" className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="space-y-2">
            <Label>{t("panel.patchInstruction")}</Label>
            <Textarea
              value={patchPrompt}
              onChange={(e) => setPatchPrompt(e.target.value)}
              placeholder={t("panel.patchPlaceholder")}
              className="min-h-24 resize-none"
            />
            <Button onClick={handleGeneratePatch} disabled={isGeneratingPatch}>
              {isGeneratingPatch ? t("panel.generating") : t("panel.generatePatch")}
            </Button>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium">{t("panel.latestPatch")}</h3>
            {currentChat.workbench.patch ? (
              <div className="rounded-md border border-border p-3 space-y-2">
                <p className="text-sm font-medium">{currentChat.workbench.patch.path}</p>
                <p className="text-xs text-muted-foreground">{currentChat.workbench.patch.summary}</p>
                <pre className="max-h-[420px] overflow-auto rounded bg-secondary p-3 text-xs whitespace-pre-wrap break-words">
                  {currentChat.workbench.patch.diff}
                </pre>
                <Button
                  onClick={handleApplyPatch}
                  disabled={isApplyingPatch || !currentChat.workbench.patch.revisedContent}
                  className="gap-2"
                >
                  <Check className="h-4 w-4" />
                  {isApplyingPatch ? t("panel.applying") : t("panel.applyAfterConfirm")}
                </Button>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("panel.noPatch")}
              </p>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </aside>
  );
}

function translateSafetyRule(
  id: string,
  field: "label" | "desc",
  fallback: string,
  t: (key: string) => string
) {
  const keyById: Record<string, { label: string; desc: string }> = {
    "workspace-only": {
      label: "safety.workspaceOnly.label",
      desc: "safety.workspaceOnly.desc",
    },
    "no-delete": {
      label: "safety.noDelete.label",
      desc: "safety.noDelete.desc",
    },
    "command-whitelist": {
      label: "safety.commandWhitelist.label",
      desc: "safety.commandWhitelist.desc",
    },
  };
  const key = keyById[id]?.[field];
  return key ? t(key) : fallback;
}
