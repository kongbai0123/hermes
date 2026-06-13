import express from "express";
import { createServer } from "http";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";
import {
  classifyTaskIntent,
  renderTaskIntentForPrompt,
  type TaskIntent,
} from "../client/src/lib/taskIntent";
import {
  chooseBacktrackingAction,
  DEFAULT_BACKTRACKING_POLICY,
  parseVerifierScore,
  renderBacktrackingPolicyForPrompt,
} from "../client/src/lib/graphBacktracking";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const server = createServer(app);
  app.use(express.json({ limit: "15mb" }));
  const workspaceRoot = path.resolve(__dirname, "..", "..", "work_agent", "workspace");
  const chatStatePath = path.resolve(__dirname, "..", "data", "chat-state.json");

  let lastHeartbeat = Date.now();
  let hasReceivedFirstHeartbeat = false;
  let activeRequests = 0;

  app.use((req, res, next) => {
    if (req.path !== "/api/heartbeat") {
      activeRequests += 1;
      let released = false;
      const releaseRequest = () => {
        if (released) return;
        released = true;
        activeRequests = Math.max(0, activeRequests - 1);
      };
      res.on("finish", releaseRequest);
      res.on("close", releaseRequest);
    }
    next();
  });

  app.post("/api/heartbeat", (_req, res) => {
    lastHeartbeat = Date.now();
    hasReceivedFirstHeartbeat = true;
    res.json({ ok: true });
  });

  const heartbeatInterval = setInterval(() => {
    if (activeRequests > 0) return;
    if (hasReceivedFirstHeartbeat && Date.now() - lastHeartbeat > 7000) {
      console.log("[Heartbeat] No heartbeat detected for 7 seconds. Shutting down server...");
      clearInterval(heartbeatInterval);
      process.exit(0);
    }
  }, 3000);

  app.get("/api/chat-state", async (_req, res) => {
    try {
      const state = await readChatState(chatStatePath);
      res.json({ ok: true, state });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to read chat state.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.put("/api/chat-state", async (req, res) => {
    try {
      await writeChatState(chatStatePath, req.body?.state);
      res.json({ ok: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to write chat state.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.get("/api/workspace/tree", async (_req, res) => {
    try {
      res.json({ ok: true, entries: await listWorkspaceEntries(workspaceRoot, workspaceRoot) });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to list workspace.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.get("/api/workspace/file", async (req, res) => {
    try {
      const relativePath = String(req.query.path ?? "").trim();
      if (!relativePath) {
        res.status(400).json({ ok: false, error: "Path is required." });
        return;
      }
      const target = resolveWorkspacePath(workspaceRoot, relativePath);
      const content = await fs.readFile(target, "utf8");
      res.json({ ok: true, path: relativePath, content });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to read workspace file.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.post("/api/work-agent/run", async (req, res) => {
    const prompt = String(req.body?.prompt ?? "").trim();
    const model = typeof req.body?.model === "string" ? req.body.model.trim() : "";
    if (!prompt) {
      res.status(400).json({ ok: false, error: "Prompt is required." });
      return;
    }

    try {
      const result = await runWorkAgent(prompt, model);
      res.json(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown work_agent error.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.post("/api/work-agent/run-stream", async (req, res) => {
    const prompt = String(req.body?.prompt ?? "").trim();
    const model = typeof req.body?.model === "string" ? req.body.model.trim() : "";
    if (!prompt) {
      res.status(400).json({ ok: false, error: "Prompt is required." });
      return;
    }

    res.setHeader("Content-Type", "application/x-ndjson; charset=utf-8");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const writeEvent = (event: unknown) => {
      res.write(`${JSON.stringify(event)}\n`);
    };

    writeEvent({ type: "status", status: "running" });

    try {
      const result = await runWorkAgent(prompt, model);
      const typed = result as Record<string, unknown>;
      writeEvent({
        type: "workbench",
        status: typed.status ?? "done",
        plan: typed.plan ?? [],
        toolLogs: typed.toolLogs ?? [],
        safetyRules: typed.safetyRules ?? [],
        workspaceEntries: typed.workspaceEntries ?? [],
        allowedCommands: typed.allowedCommands ?? [],
      });

      const answer = String(typed.answer ?? "");
      const chunkSize = 80;
      for (let index = 0; index < answer.length; index += chunkSize) {
        writeEvent({
          type: "chunk",
          content: answer.slice(index, index + chunkSize),
        });
      }

      writeEvent({ type: "done" });
      res.end();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown work_agent error.";
      writeEvent({ type: "error", error: message });
      res.end();
    }
  });

  app.post("/api/work-agent/run-graph-stream", async (req, res) => {
    const prompt = String(req.body?.prompt ?? "").trim();
    const team = Array.isArray(req.body?.team) ? (req.body.team as AgentSlotPayload[]) : [];
    const graph = normalizeAgentGraph(req.body?.graph);
    if (!prompt) {
      res.status(400).json({ ok: false, error: "Prompt is required." });
      return;
    }
    if (!team.length) {
      res.status(400).json({ ok: false, error: "Agent team is required." });
      return;
    }

    res.setHeader("Content-Type", "application/x-ndjson; charset=utf-8");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const writeEvent = (event: unknown) => {
      res.write(`${JSON.stringify(event)}\n`);
    };

    const levels = buildAgentGraphLevels(team, graph.edges);
    const taskIntent = classifyTaskIntent(prompt);
    const outputs = new Map<string, string>();
    const failed = new Set<string>();
    const retryCounts: Record<string, number> = {};

    writeEvent({ type: "graph-start", levels, taskIntent, backtrackingPolicy: DEFAULT_BACKTRACKING_POLICY });

    try {
      for (const level of levels) {
        await Promise.all(
          level.map(async (agentId) => {
            const slot = team.find((agent) => agent.id === agentId);
            if (!slot || !slot.isEnabled) return;

            const upstream = graph.edges
              .filter((edge) => edge.to === agentId)
              .map((edge) => edge.from)
              .filter((id) => team.find((agent) => agent.id === id)?.isEnabled);

            if (upstream.some((id) => failed.has(id))) {
              writeEvent({ type: "joint-skip", agentId, reason: "upstream-failed" });
              failed.add(agentId);
              return;
            }

            writeEvent({
              type: "joint-start",
              agentId,
              name: slot.name,
              role: slot.role,
              model: slot.model,
            });

            try {
              const result = await runWorkAgent(composeJointPrompt(prompt, slot, upstream, outputs, taskIntent), slot.model);
              const typed = result as Record<string, unknown>;
              const answer = String(typed.answer ?? JSON.stringify(result));
              outputs.set(agentId, answer);
              writeEvent({
                type: "joint-complete",
                agentId,
                name: slot.name,
                answer,
                workbench: {
                  status: typed.status ?? "done",
                  plan: typed.plan ?? [],
                  toolLogs: typed.toolLogs ?? [],
                  safetyRules: typed.safetyRules ?? [],
                  workspaceEntries: typed.workspaceEntries ?? [],
                  allowedCommands: typed.allowedCommands ?? [],
                },
              });
            } catch (error) {
              const message = error instanceof Error ? error.message : "Unknown joint error.";
              failed.add(agentId);
              writeEvent({ type: "joint-error", agentId, name: slot.name, error: message });
            }
          })
        );
      }

      const verifierId = findVerifierAgentId(team, outputs);
      const verifierScore = verifierId ? parseVerifierScore(outputs.get(verifierId) ?? "") : null;
      if (verifierScore) {
        const action = chooseBacktrackingAction({
          score: verifierScore.score,
          retryTarget: verifierScore.retryTarget,
          feedback: verifierScore.feedback,
          round: 0,
          previousBestScore: 0,
          retryCounts,
        });
        writeEvent({ type: "backtracking-decision", verifierId, verifierScore, action });

        if (action.type === "retry") {
          const retrySlot = team.find((agent) => agent.id === action.targetAgentId && agent.isEnabled);
          if (retrySlot) {
            retryCounts[action.targetAgentId] = (retryCounts[action.targetAgentId] ?? 0) + 1;
            const upstream = graph.edges
              .filter((edge) => edge.to === action.targetAgentId)
              .map((edge) => edge.from)
              .filter((id) => team.find((agent) => agent.id === id)?.isEnabled);
            writeEvent({
              type: "backtracking-start",
              targetAgentId: action.targetAgentId,
              feedback: action.feedback,
              round: action.nextRound,
            });
            writeEvent({
              type: "joint-start",
              agentId: retrySlot.id,
              name: retrySlot.name,
              role: retrySlot.role,
              model: retrySlot.model,
              reason: "backtracking",
            });
            try {
              const retryPrompt = [
                composeJointPrompt(prompt, retrySlot, upstream, outputs, taskIntent),
                `Backtracking feedback:\n${action.feedback}`,
                "Revise only this joint's output. Do not restart an open-ended debate.",
              ].join("\n\n");
              const result = await runWorkAgent(retryPrompt, retrySlot.model);
              const typed = result as Record<string, unknown>;
              const answer = String(typed.answer ?? JSON.stringify(result));
              outputs.set(retrySlot.id, answer);
              writeEvent({
                type: "joint-complete",
                agentId: retrySlot.id,
                name: retrySlot.name,
                answer,
                reason: "backtracking",
              });
            } catch (error) {
              const message = error instanceof Error ? error.message : "Unknown backtracking retry error.";
              failed.add(retrySlot.id);
              writeEvent({ type: "joint-error", agentId: retrySlot.id, name: retrySlot.name, error: message });
            }
          }
        }
      } else {
        writeEvent({
          type: "backtracking-decision",
          action: { type: "stop", reason: "missing-verifier-score" },
        });
      }

      const terminalIds = getTerminalAgentIds(team, graph.edges).filter((id) => outputs.has(id));
      writeEvent({
        type: "graph-complete",
        terminalIds,
        answer: terminalIds.map((id) => outputs.get(id)).join("\n\n"),
      });
      res.end();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown graph runner error.";
      writeEvent({ type: "error", error: message });
      res.end();
    }
  });

  app.post("/api/work-agent/patch", async (req, res) => {
    const prompt = String(req.body?.prompt ?? "").trim();
    const filePath = String(req.body?.path ?? "").trim();
    const model = typeof req.body?.model === "string" ? req.body.model.trim() : "";
    if (!prompt || !filePath) {
      res.status(400).json({ ok: false, error: "Prompt and path are required." });
      return;
    }

    try {
      const result = await runWorkAgentPatch(prompt, filePath, model);
      res.json(result);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown patch generation error.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  app.post("/api/work-agent/apply-patch", async (req, res) => {
    try {
      const filePath = String(req.body?.path ?? "").trim();
      const content = typeof req.body?.content === "string" ? req.body.content : "";
      if (!filePath) {
        res.status(400).json({ ok: false, error: "Path is required." });
        return;
      }

      const target = resolveWorkspacePath(workspaceRoot, filePath);
      await fs.writeFile(target, content, "utf8");
      res.json({ ok: true, path: filePath });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to apply patch.";
      res.status(500).json({ ok: false, error: message });
    }
  });

  // Serve static files from dist/public in production
  const staticPath =
    process.env.NODE_ENV === "production"
      ? path.resolve(__dirname, "public")
      : path.resolve(__dirname, "..", "dist", "public");

  app.use(express.static(staticPath));

  // Handle client-side routing - serve index.html for all routes
  app.get("*", (_req, res) => {
    res.sendFile(path.join(staticPath, "index.html"));
  });

  const port = process.env.PORT || 3000;

  server.listen(port, () => {
    console.log(`Server running on http://localhost:${port}/`);
  });
}

async function readChatState(chatStatePath: string): Promise<unknown | null> {
  try {
    const raw = await fs.readFile(chatStatePath, "utf8");
    return JSON.parse(raw);
  } catch (error) {
    if (isNodeError(error) && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function writeChatState(chatStatePath: string, state: unknown): Promise<void> {
  if (!state || typeof state !== "object") {
    throw new Error("State payload is required.");
  }
  await fs.mkdir(path.dirname(chatStatePath), { recursive: true });
  const tempPath = `${chatStatePath}.${process.pid}.tmp`;
  await fs.writeFile(tempPath, JSON.stringify(state, null, 2), "utf8");
  await fs.rename(tempPath, chatStatePath);
}

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error;
}

function resolveBackendModel(modelId: string): string | null {
  const models: Record<string, string> = {
    "ollama-gemma4": "gemma4:latest",
    "ollama-qwen-local": "qwen-local:latest",
  };
  return models[modelId] ?? null;
}

function resolveWorkspacePath(workspaceRoot: string, relativePath: string): string {
  const normalized = relativePath.replace(/^workspace\//, "");
  const candidate = path.resolve(workspaceRoot, normalized);
  const relative = path.relative(workspaceRoot, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error("Workspace path is outside the allowed root.");
  }
  return candidate;
}

async function listWorkspaceEntries(root: string, current: string): Promise<unknown[]> {
  const items = await fs.readdir(current, { withFileTypes: true });
  return Promise.all(
    items
      .sort((left, right) => left.name.localeCompare(right.name))
      .map(async (item) => {
        const absolute = path.join(current, item.name);
        const relative = path.relative(root, absolute).split(path.sep).join("/");
        return {
          id: relative,
          path: `workspace/${relative}`,
          kind: item.isDirectory() ? "dir" : "file",
          summary: item.isDirectory() ? "Workspace directory" : "Workspace file",
          children: item.isDirectory() ? await listWorkspaceEntries(root, absolute) : [],
        };
      })
  );
}

function runWorkAgent(prompt: string, modelId: string): Promise<unknown> {
  const workAgentRoot = path.resolve(__dirname, "..", "..", "work_agent");
  const pythonExec = process.env.WORK_AGENT_PYTHON || "python";
  const model = resolveBackendModel(modelId);

  return new Promise((resolve, reject) => {
    const child = spawn(pythonExec, ["-m", "simple_agent.web_api"], {
      cwd: workAgentRoot,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("Work Agent timed out."));
    }, 120000);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });

    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Work Agent exited with code ${code}.`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(
          new Error(
            `Work Agent returned invalid JSON: ${error instanceof Error ? error.message : "unknown error"}`
          )
        );
      }
    });

    child.stdin.write(JSON.stringify({ prompt, model }));
    child.stdin.end();
  });
}

interface AgentSlotPayload {
  id: string;
  name: string;
  role: string;
  model: string;
  skill: string;
  outputFormat: string;
  isEnabled: boolean;
}

interface AgentGraphEdgePayload {
  id: string;
  from: string;
  to: string;
}

interface AgentGraphPayload {
  edges: AgentGraphEdgePayload[];
}

function normalizeAgentGraph(value: unknown): AgentGraphPayload {
  const maybeGraph = value as { edges?: unknown };
  const edges = Array.isArray(maybeGraph?.edges)
    ? maybeGraph.edges
        .map((edge) => edge as Partial<AgentGraphEdgePayload>)
        .filter(
          (edge): edge is AgentGraphEdgePayload =>
            typeof edge.id === "string" &&
            typeof edge.from === "string" &&
            typeof edge.to === "string"
        )
    : [];
  return { edges };
}

function buildAgentGraphLevels(team: AgentSlotPayload[], edges: AgentGraphEdgePayload[]): string[][] {
  const enabledTeam = team.filter((slot) => slot.isEnabled);
  const enabledIds = new Set(enabledTeam.map((slot) => slot.id));
  if (!enabledIds.has("planner")) return [];

  const reachable = findReachableIds("planner", edges, enabledIds);
  const relevantIds = enabledTeam.map((slot) => slot.id).filter((id) => reachable.has(id));
  const relevantEdges = edges.filter((edge) => reachable.has(edge.from) && reachable.has(edge.to));
  const indegree = new Map(relevantIds.map((id) => [id, 0]));
  const outgoing = new Map<string, string[]>();

  for (const edge of relevantEdges) {
    indegree.set(edge.to, (indegree.get(edge.to) ?? 0) + 1);
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge.to]);
  }

  const levels: string[][] = [];
  const visited = new Set<string>();
  let current = ["planner"].filter((id) => indegree.get(id) === 0);

  while (current.length) {
    const level = sortAgentIdsByTeam(current, enabledTeam).filter((id) => !visited.has(id));
    if (!level.length) break;
    levels.push(level);
    level.forEach((id) => visited.add(id));

    const next = new Set<string>();
    for (const id of level) {
      for (const target of outgoing.get(id) ?? []) {
        const nextIndegree = (indegree.get(target) ?? 0) - 1;
        indegree.set(target, nextIndegree);
        if (nextIndegree === 0) next.add(target);
      }
    }
    current = Array.from(next);
  }

  return levels;
}

function getTerminalAgentIds(team: AgentSlotPayload[], edges: AgentGraphEdgePayload[]): string[] {
  const runnableIds = new Set(buildAgentGraphLevels(team, edges).flat());
  const hasOutgoing = new Set(
    edges.filter((edge) => runnableIds.has(edge.from) && runnableIds.has(edge.to)).map((edge) => edge.from)
  );
  return team.filter((slot) => slot.isEnabled && runnableIds.has(slot.id) && !hasOutgoing.has(slot.id)).map((slot) => slot.id);
}

function findReachableIds(rootId: string, edges: AgentGraphEdgePayload[], enabledIds: Set<string>) {
  const reachable = new Set<string>();
  const outgoing = new Map<string, string[]>();

  for (const edge of edges) {
    if (!enabledIds.has(edge.from) || !enabledIds.has(edge.to)) continue;
    outgoing.set(edge.from, [...(outgoing.get(edge.from) ?? []), edge.to]);
  }

  const queue = [rootId];
  while (queue.length) {
    const id = queue.shift()!;
    if (reachable.has(id)) continue;
    reachable.add(id);
    queue.push(...(outgoing.get(id) ?? []));
  }

  return reachable;
}

function sortAgentIdsByTeam(ids: string[], team: AgentSlotPayload[]) {
  const order = new Map(team.map((slot, index) => [slot.id, index]));
  return [...ids].sort((left, right) => (order.get(left) ?? 0) - (order.get(right) ?? 0));
}

function composeJointPrompt(
  originalTask: string,
  slot: AgentSlotPayload,
  upstreamIds: string[],
  outputs: Map<string, string>,
  taskIntent: TaskIntent
) {
  const upstreamContext = upstreamIds
    .map((id) => `## Upstream joint: ${id}\n${outputs.get(id) ?? ""}`)
    .join("\n\n");

  return [
    `You are the "${slot.name}" joint in an agent DAG.`,
    `Role: ${slot.role}`,
    `Skill prompt: ${slot.skill}`,
    `Required output format: ${slot.outputFormat}`,
    `Original user task:\n${originalTask}`,
    renderTaskIntentForPrompt(taskIntent),
    renderBacktrackingPolicyForPrompt(DEFAULT_BACKTRACKING_POLICY),
    slot.id === "verifier" || /verifier|驗證/i.test(`${slot.id} ${slot.name} ${slot.role}`)
      ? [
          "Verifier scoring requirement:",
          "Return a concise answer plus a JSON block containing score, passed, failedReason, retryTarget, feedback.",
          "Score must be 0 to 1. If required evidence is missing, passed must be false.",
        ].join("\n")
      : "",
    upstreamContext ? `Upstream context:\n${upstreamContext}` : "Upstream context: none. You are receiving the original task directly.",
  ].join("\n\n");
}

function findVerifierAgentId(team: AgentSlotPayload[], outputs: Map<string, string>) {
  return team.find(
    (slot) =>
      outputs.has(slot.id) &&
      (slot.id === "verifier" || /verifier|驗證/i.test(`${slot.name} ${slot.role}`))
  )?.id;
}

function runWorkAgentPatch(prompt: string, filePath: string, modelId: string): Promise<unknown> {
  const workAgentRoot = path.resolve(__dirname, "..", "..", "work_agent");
  const pythonExec = process.env.WORK_AGENT_PYTHON || "python";
  const model = resolveBackendModel(modelId);

  return new Promise((resolve, reject) => {
    const child = spawn(pythonExec, ["-m", "simple_agent.web_api"], {
      cwd: workAgentRoot,
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("Patch generation timed out."));
    }, 120000);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });

    child.on("error", (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Patch generator exited with code ${code}.`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(
          new Error(
            `Patch generator returned invalid JSON: ${error instanceof Error ? error.message : "unknown error"}`
          )
        );
      }
    });

    child.stdin.write(JSON.stringify({ action: "patch", prompt, path: filePath, model }));
    child.stdin.end();
  });
}

startServer().catch(console.error);
