"""MCP stdio server for LocalAgentTutor.

This implementation intentionally avoids third-party MCP packages so the
packaged folder can run on a plain Python installation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Any


SERVER_NAME = "local-agent-tutor-mcp"
PROTOCOL_VERSION = "2024-11-05"


def find_project_root() -> Path:
    env_root = os.environ.get("LOCAL_AGENT_TUTOR_ROOT")
    if env_root:
        candidate = Path(env_root).resolve()
        if (candidate / "LocalAgentTutor.py").exists():
            return candidate

    here = Path(__file__).resolve()
    candidates = [
        here.parents[1],
        Path.cwd(),
        Path(sys.executable).resolve().parent,
        Path(sys.executable).resolve().parent.parent,
    ]
    for candidate in candidates:
        if (candidate / "LocalAgentTutor.py").exists() and (candidate / "agent").is_dir():
            return candidate.resolve()
    return here.parents[1].resolve()


ROOT = find_project_root()
os.environ["LOCAL_AGENT_TUTOR_ROOT"] = str(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def text_result(text: str, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "isError": is_error,
    }


def tool_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS = [
    {
        "name": "package_info",
        "description": "Show where the packaged LocalAgentTutor folder is and which launchers are available.",
        "inputSchema": tool_schema({}),
    },
    {
        "name": "list_lessons",
        "description": "List all LocalAgentTutor lessons with their numbers, codes, titles, and summaries.",
        "inputSchema": tool_schema({}),
    },
    {
        "name": "run_lesson",
        "description": "Run one tutorial lesson by number, code, or script path and return its output.",
        "inputSchema": tool_schema(
            {
                "lesson": {
                    "type": "string",
                    "description": "Lesson number such as 1 or 18, lesson code such as 1-2, or a lesson script path.",
                }
            },
            ["lesson"],
        ),
    },
    {
        "name": "ask_agent",
        "description": "Ask the local Codex-like ReAct agent a question about the bundled workspace.",
        "inputSchema": tool_schema(
            {
                "prompt": {
                    "type": "string",
                    "description": "Question or task to send to the local agent.",
                }
            },
            ["prompt"],
        ),
    },
    {
        "name": "run_tests",
        "description": "Run the bundled sample_project tests and return the output.",
        "inputSchema": tool_schema({}),
    },
    {
        "name": "open_tutor_ui",
        "description": "Open the packaged LocalAgentTutor teaching UI.",
        "inputSchema": tool_schema({}),
    },
]


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "package_info":
        ui_exe = ROOT / "dist" / "LocalAgentTutorUI.exe"
        cli_exe = ROOT / "dist" / "LocalAgentTutor.exe"
        info = [
            f"Package root: {ROOT}",
            f"Teaching UI exe: {ui_exe} ({'exists' if ui_exe.exists() else 'missing'})",
            f"CLI launcher exe: {cli_exe} ({'exists' if cli_exe.exists() else 'missing'})",
            f"Workspace: {ROOT / 'workspace'} ({'exists' if (ROOT / 'workspace').is_dir() else 'missing'})",
        ]
        return text_result("\n".join(info))

    if name == "list_lessons":
        from LocalAgentTutor import LESSONS

        lines = []
        for index, (lesson_id, title, script, summary) in enumerate(LESSONS, start=1):
            lines.append(f"{index}. [{lesson_id}] {title}\n   {summary}\n   {script}")
        return text_result("\n".join(lines))

    if name == "run_lesson":
        lesson = str(args.get("lesson", "")).strip()
        script = resolve_lesson_script(lesson)
        if script is None:
            return text_result(f"找不到課程：{lesson}", True)
        from tutor_ui import run_script

        result = run_script(script)
        return text_result(result.get("output", ""), not bool(result.get("ok")))

    if name == "ask_agent":
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            return text_result("prompt 不可為空。", True)
        from tutor_ui import run_agent

        result = run_agent(prompt)
        return text_result(result.get("output", ""), not bool(result.get("ok")))

    if name == "run_tests":
        from tutor_ui import run_tests

        result = run_tests()
        return text_result(result.get("output", ""), not bool(result.get("ok")))

    if name == "open_tutor_ui":
        ui_exe = ROOT / "dist" / "LocalAgentTutorUI.exe"
        if ui_exe.exists():
            subprocess.Popen([str(ui_exe)], cwd=ROOT)
            return text_result(f"已啟動教學 UI：{ui_exe}")
        tutor_ui = ROOT / "tutor_ui.py"
        subprocess.Popen([sys.executable, str(tutor_ui)], cwd=ROOT)
        return text_result("找不到 UI exe，已改用 Python 原始碼模式啟動 tutor_ui.py。")

    return text_result(f"Unknown tool: {name}", True)


def resolve_lesson_script(value: str) -> str | None:
    from LocalAgentTutor import LESSONS, find_lesson

    found = find_lesson(value)
    if found is not None:
        return found[2]
    for _, lesson_id, title, script, _summary in [
        (index, *lesson) for index, lesson in enumerate(LESSONS, start=1)
    ]:
        if value == lesson_id or value == title or value == script:
            return script
    candidate = (ROOT / value).resolve()
    lessons_root = (ROOT / "lessons").resolve()
    if candidate.is_file() and (candidate == lessons_root or lessons_root in candidate.parents):
        return candidate.relative_to(ROOT).as_posix()
    return None


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    message_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if message_id is None:
        return None

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": SERVER_NAME, "version": "1.0.0"},
                },
            }

        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": message_id, "result": {"tools": TOOLS}}

        if method == "tools/call":
            name = str(params.get("name", ""))
            args = params.get("arguments") or {}
            if not isinstance(args, dict):
                args = {}
            return {"jsonrpc": "2.0", "id": message_id, "result": call_tool(name, args)}

        return error_response(message_id, -32601, f"Method not found: {method}")
    except Exception as exc:
        print(traceback.format_exc(), file=sys.stderr)
        return error_response(message_id, -32603, str(exc))


def error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {"code": code, "message": message},
    }


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_request(message)
        if response is None:
            continue
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

