"""Safe tools for a local code and file assistant."""

from __future__ import annotations

import ast
import json
import operator
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def find_workspace_root() -> Path:
    env_root = os.environ.get("LOCAL_AGENT_TUTOR_ROOT")
    if env_root:
        return (Path(env_root) / "workspace").resolve()

    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parents[1],
    ]
    for candidate in candidates:
        workspace = (candidate / "workspace").resolve()
        if workspace.is_dir():
            return workspace
    return (Path(__file__).resolve().parents[1] / "workspace").resolve()


WORKSPACE_ROOT = find_workspace_root()


@dataclass
class ToolResult:
    ok: bool
    output: str

    def to_observation(self) -> str:
        status = "OK" if self.ok else "ERROR"
        return f"{status}: {self.output}"


class ToolError(ValueError):
    """Raised when a tool request is invalid or unsafe."""


def safe_path(relative_path: str) -> Path:
    candidate = (WORKSPACE_ROOT / relative_path).resolve()
    if candidate != WORKSPACE_ROOT and WORKSPACE_ROOT not in candidate.parents:
        raise ToolError("Path is outside the allowed workspace.")
    return candidate


def get_current_time(_: dict) -> ToolResult:
    return ToolResult(True, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def calculate(args: dict) -> ToolResult:
    expression = str(args.get("expression", ""))
    try:
        value = _safe_eval(expression)
    except Exception as exc:
        return ToolResult(False, f"Invalid expression: {exc}")
    return ToolResult(True, str(value))


def list_files(args: dict) -> ToolResult:
    relative_path = str(args.get("path", "."))
    try:
        root = safe_path(relative_path)
        if not root.exists():
            return ToolResult(False, f"Path not found: {relative_path}")
        if root.is_file():
            return ToolResult(True, root.relative_to(WORKSPACE_ROOT).as_posix())
        items = []
        for path in sorted(root.rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if path.is_file():
                items.append(path.relative_to(WORKSPACE_ROOT).as_posix())
        return ToolResult(True, "\n".join(items) if items else "(empty)")
    except ToolError as exc:
        return ToolResult(False, str(exc))


def read_file(args: dict) -> ToolResult:
    relative_path = str(args.get("path", ""))
    try:
        path = safe_path(relative_path)
        if not path.exists() or not path.is_file():
            return ToolResult(False, f"File not found: {relative_path}")
        if path.stat().st_size > 80_000:
            return ToolResult(False, "File is too large for this first version.")
        return ToolResult(True, path.read_text(encoding="utf-8", errors="replace"))
    except ToolError as exc:
        return ToolResult(False, str(exc))


def search_files(args: dict) -> ToolResult:
    pattern = str(args.get("pattern", ""))
    path_arg = str(args.get("path", "."))
    if not pattern:
        return ToolResult(False, "Missing search pattern.")
    try:
        root = safe_path(path_arg)
    except ToolError as exc:
        return ToolResult(False, str(exc))

    command = ["rg", "--line-number", "--no-heading", pattern, str(root)]
    try:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        return _fallback_search(pattern, root)
    except subprocess.TimeoutExpired:
        return ToolResult(False, "Search timed out.")

    output = completed.stdout.strip()
    if not output:
        return ToolResult(True, "No matches.")
    return ToolResult(True, _make_paths_relative(output))


def propose_patch(args: dict) -> ToolResult:
    path = str(args.get("path", ""))
    patch = str(args.get("patch", ""))
    try:
        safe_path(path)
    except ToolError as exc:
        return ToolResult(False, str(exc))
    if not patch.strip().startswith("---"):
        return ToolResult(False, "Patch must be a unified diff starting with '---'.")
    return ToolResult(
        True,
        "Patch proposal only. It was not applied.\n\n" + patch.strip(),
    )


def run_command(args: dict) -> ToolResult:
    command_text = str(args.get("command", "")).strip()
    if not command_text:
        return ToolResult(False, "Missing command.")
    allowed = [
        "python",
        "py",
        "pytest",
        "npm test",
        "npm run test",
        "rg",
    ]
    if not any(command_text == item or command_text.startswith(item + " ") for item in allowed):
        return ToolResult(False, f"Command is not allowed: {command_text}")
    if any(blocked in command_text.lower() for blocked in [" del ", "rm ", "remove-item", " rmdir "]):
        return ToolResult(False, "Destructive commands are blocked.")

    try:
        completed = subprocess.run(
            command_text,
            cwd=WORKSPACE_ROOT,
            shell=True,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(False, "Command timed out.")

    output = (completed.stdout + completed.stderr).strip()
    if not output:
        output = f"Command exited with code {completed.returncode}."
    return ToolResult(completed.returncode == 0, output[-6000:])


TOOLS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "list_files": list_files,
    "read_file": read_file,
    "search_files": search_files,
    "propose_patch": propose_patch,
    "run_command": run_command,
}


TOOL_GUIDE = """Available tools:
- get_current_time {}
- calculate {"expression": "2 + 2 * 3"}
- list_files {"path": "."}
- read_file {"path": "sample_project/calculator.py"}
- search_files {"pattern": "TODO", "path": "."}
- propose_patch {"path": "sample_project/calculator.py", "patch": "--- a/..."}
- run_command {"command": "python -m unittest discover -s sample_project"}
"""


def execute_tool(name: str, args: dict) -> ToolResult:
    tool = TOOLS.get(name)
    if tool is None:
        return ToolResult(False, f"Unknown tool: {name}")
    return tool(args)


def parse_action(text: str) -> dict | None:
    text_action = _parse_text_action(text)
    if text_action:
        return text_action

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if payload.get("type") != "action":
        return None
    return payload


def _parse_text_action(text: str) -> dict | None:
    match = re.search(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\{.*\})", text, re.DOTALL)
    if not match:
        return None
    tool_name = match.group(1)
    args_text = match.group(2).strip()
    try:
        args = json.loads(args_text)
    except json.JSONDecodeError:
        try:
            args = ast.literal_eval(args_text)
        except (SyntaxError, ValueError):
            return None
    if not isinstance(args, dict):
        return None
    return {"type": "action", "tool": tool_name, "args": args}


def _safe_eval(expression: str) -> int | float:
    allowed_binops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    allowed_unary = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def visit(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_binops:
            return allowed_binops[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_unary:
            return allowed_unary[type(node.op)](visit(node.operand))
        raise ToolError("Only numeric expressions are allowed.")

    return visit(ast.parse(expression, mode="eval"))


def _fallback_search(pattern: str, root: Path) -> ToolResult:
    matches = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            if pattern in line:
                rel = path.relative_to(WORKSPACE_ROOT).as_posix()
                matches.append(f"{rel}:{line_number}:{line}")
    return ToolResult(True, "\n".join(matches) if matches else "No matches.")


def _make_paths_relative(output: str) -> str:
    workspace = str(WORKSPACE_ROOT)
    return output.replace(workspace + os.sep, "").replace(workspace, ".")
