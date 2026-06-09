import express from "express";
import { createServer } from "http";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { spawn } from "child_process";

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

  app.post("/api/heartbeat", (_req, res) => {
    lastHeartbeat = Date.now();
    hasReceivedFirstHeartbeat = true;
    res.json({ ok: true });
  });

  const heartbeatInterval = setInterval(() => {
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
