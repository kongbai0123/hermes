from __future__ import annotations

import contextlib
import difflib
import io
import json
import sys
from pathlib import Path

from .config import load_config
from .main import build_agent, build_external_chat_bridge
from .tools import ToolBox


def workspace_entries(workspace_root: Path) -> list[dict]:
    def build_entry(item: Path) -> dict:
        return {
            "id": item.relative_to(workspace_root).as_posix(),
            "path": f"workspace/{item.relative_to(workspace_root).as_posix()}",
            "kind": "dir" if item.is_dir() else "file",
            "summary": "Workspace directory" if item.is_dir() else "Workspace file",
            "children": [build_entry(child) for child in sorted(item.iterdir())] if item.is_dir() else [],
        }

    return [build_entry(item) for item in sorted(workspace_root.iterdir())]


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return stripped


def generate_patch(prompt: str, path: str, model_override: str | None = None) -> dict:
    config = load_config()
    tools = ToolBox(
        config["workspace_path"],
        config["allowed_commands"],
        allowed_proxy_domains=list(config.get("allowed_proxy_domains", [])),
        allowed_browser_domains=list(config.get("allowed_browser_domains", [])),
        external_chat_bridge=build_external_chat_bridge(config),
    )
    observation = tools.read_file(path)
    if not observation.ok:
        return {"ok": False, "error": observation.content}

    agent = build_agent(model_override=model_override)
    source = observation.content
    llm_prompt = (
        "你是程式碼修改助理。請根據使用者需求修改單一檔案內容。\n"
        "只輸出修改後的完整檔案內容，不要解釋，不要 markdown code fence。"
    )
    user_content = (
        f"檔案路徑：{path}\n"
        f"使用者需求：{prompt}\n"
        "原始檔案內容如下：\n"
        f"{source}"
    )
    revised = agent.worker.llm.chat(
        [{"role": "system", "content": llm_prompt}, {"role": "user", "content": user_content}]
    )
    revised = strip_code_fences(revised)
    diff = "\n".join(
        difflib.unified_diff(
            source.splitlines(),
            revised.splitlines(),
            fromfile=path,
            tofile=path,
            lineterm="",
        )
    )
    return {
        "ok": True,
        "path": path,
        "summary": f"為 {path} 產生 patch 建議。",
        "diff": diff or "(沒有產生差異)",
        "revisedContent": revised,
    }


def run_task(prompt: str, model_override: str | None = None) -> dict:
    config = load_config()
    agent = build_agent(model_override=model_override)
    captured_stdout = io.StringIO()
    with contextlib.redirect_stdout(captured_stdout):
        result = agent.run_once_structured(prompt)
    stop_reason = str(result.get("stop_reason", "DONE"))
    status = "done" if stop_reason == "DONE" else "blocked" if stop_reason in {
        "NEEDS_USER_APPROVAL",
        "NEEDS_USER_INPUT",
        "POLICY_REJECTED",
        "NO_PROGRESS_DETECTED",
    } else "error"

    trace = result.get("trace", [])
    latest_trace = trace[-1] if trace else {}
    routing = latest_trace.get("routing", {})
    policy = latest_trace.get("policy", {})

    return {
        "ok": True,
        "prompt": prompt,
        "answer": result["answer"],
        "status": status,
        "stopReason": stop_reason,
        "trace": trace,
        "loop": result.get("loop", {}),
        "plan": [
            {
                "id": "understand",
                "title": "Understand task",
                "detail": result["decision"]["plan"],
                "status": "done",
            },
            {
                "id": "use-tool",
                "title": "Use selected tool",
                "detail": f'{result["decision"]["tool"]} {result["decision"]["args"]}',
                "status": "done" if result["observation"]["ok"] else "error",
            },
            {
                "id": "summarize",
                "title": "Summarize findings",
                "detail": f"Return a concise explanation and next step. Stop reason: {stop_reason}",
                "status": "done" if status == "done" else "error",
            },
        ],
        "toolLogs": [
            {
                "id": "primary-observation",
                "tool": result["observation"]["tool"],
                "ok": result["observation"]["ok"],
                "summary": (
                    f'{routing.get("execution_mode", "PLAN_ONLY")} / '
                    f'{policy.get("decision", "unknown")} - {result["decision"]["plan"]}'
                ),
                "content": result["observation"]["content"],
                "args": {
                    **result["decision"]["args"],
                    "execution_mode": str(routing.get("execution_mode", "")),
                    "executor": str(routing.get("executor", "")),
                    "template_id": str(routing.get("template_id", "")),
                    "risk": str(policy.get("risk", "")),
                    "requires_approval": str(policy.get("requires_approval", "")),
                },
            }
        ],
        "safetyRules": [
            {
                "id": "workspace-only",
                "label": "Workspace Only",
                "description": "Only read files inside workspace/.",
            },
            {
                "id": "no-delete",
                "label": "No Delete",
                "description": "Do not delete files automatically.",
            },
            {
                "id": "command-whitelist",
                "label": "Whitelisted Commands",
                "description": "Only run approved commands from config.json.",
            },
        ],
        "workspaceEntries": workspace_entries(Path(config["workspace_path"])),
        "allowedCommands": list(config["allowed_commands"]),
    }


def main() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    raw = sys.stdin.read().strip()
    if not raw:
        print(json.dumps({"ok": False, "error": "No input payload provided."}, ensure_ascii=False))
        return

    payload = json.loads(raw)
    action = str(payload.get("action", "run")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    model_override = payload.get("model")
    if model_override is not None:
        model_override = str(model_override).strip() or None
    if action == "patch":
        path = str(payload.get("path", "")).strip()
        if not prompt or not path:
            print(json.dumps({"ok": False, "error": "Prompt and path are required."}, ensure_ascii=False))
            return
        try:
            result = generate_patch(prompt, path, model_override=model_override)
        except Exception as exc:  # pragma: no cover
            result = {"ok": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        return

    if not prompt:
        print(json.dumps({"ok": False, "error": "Prompt is required."}, ensure_ascii=False))
        return

    try:
        result = run_task(prompt, model_override=model_override)
    except Exception as exc:  # pragma: no cover - runtime safeguard for UI integration
        result = {"ok": False, "error": str(exc)}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
