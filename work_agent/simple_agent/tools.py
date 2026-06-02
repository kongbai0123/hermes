from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Observation:
    ok: bool
    tool: str
    content: str

    def format(self) -> str:
        status = "OK" if self.ok else "ERROR"
        return f"[{status}] {self.tool}: {self.content}"


class ToolBox:
    def __init__(self, workspace_path: str, allowed_commands: list[str]) -> None:
        self.workspace = Path(workspace_path).resolve()
        self.allowed_commands = allowed_commands
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path: str) -> Path:
        candidate = (self.workspace / path).resolve()
        try:
            candidate.relative_to(self.workspace)
        except ValueError as exc:
            raise PermissionError("拒絕讀取 workspace 外的路徑。") from exc
        return candidate

    def list_files(self, path: str = ".") -> Observation:
        try:
            target = self._safe_path(path)
            if not target.exists():
                return Observation(False, "list_files", f"找不到路徑：{path}")
            if target.is_file():
                return Observation(True, "list_files", target.name)
            items = []
            for item in sorted(target.iterdir()):
                suffix = "/" if item.is_dir() else ""
                rel = item.relative_to(self.workspace).as_posix()
                items.append(f"{rel}{suffix}")
            return Observation(True, "list_files", "\n".join(items) or "(空資料夾)")
        except Exception as exc:
            return Observation(False, "list_files", str(exc))

    def read_file(self, path: str) -> Observation:
        try:
            target = self._safe_path(path)
            if not target.is_file():
                return Observation(False, "read_file", f"找不到檔案：{path}")
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > 8000:
                text = text[:8000] + "\n...(已截斷)"
            return Observation(True, "read_file", text)
        except Exception as exc:
            return Observation(False, "read_file", str(exc))

    def search_text(self, keyword: str, path: str = ".") -> Observation:
        try:
            target = self._safe_path(path)
            if not target.exists():
                return Observation(False, "search_text", f"找不到路徑：{path}")
            command = ["rg", "-n", "--hidden", "--glob", "!__pycache__", keyword, str(target)]
            try:
                completed = subprocess.run(
                    command,
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                output = completed.stdout.strip() or completed.stderr.strip()
            except FileNotFoundError:
                output = self._search_without_rg(keyword, target)
            return Observation(True, "search_text", output or "沒有找到結果。")
        except Exception as exc:
            return Observation(False, "search_text", str(exc))

    def _search_without_rg(self, keyword: str, target: Path) -> str:
        files = [target] if target.is_file() else target.rglob("*")
        matches = []
        for file_path in files:
            if not file_path.is_file():
                continue
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for number, line in enumerate(lines, start=1):
                if keyword in line:
                    rel = file_path.relative_to(self.workspace).as_posix()
                    matches.append(f"{rel}:{number}:{line}")
        return "\n".join(matches)

    def run_command(self, command: str) -> Observation:
        normalized = " ".join(shlex.split(command, posix=False))
        if not self._is_allowed(normalized):
            return Observation(False, "run_command", f"命令不在白名單內：{command}")
        try:
            completed = subprocess.run(
                command,
                cwd=self.workspace,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            output = "\n".join(
                part for part in [completed.stdout.strip(), completed.stderr.strip()] if part
            )
            if not output:
                output = f"命令完成，exit code = {completed.returncode}"
            return Observation(completed.returncode == 0, "run_command", output[:8000])
        except Exception as exc:
            return Observation(False, "run_command", str(exc))

    def _is_allowed(self, command: str) -> bool:
        for allowed in self.allowed_commands:
            if command == allowed or command.startswith(allowed + " "):
                return True
        return False

    def execute(self, name: str, **kwargs: str) -> Observation:
        if name == "list_files":
            return self.list_files(kwargs.get("path", "."))
        if name == "read_file":
            return self.read_file(kwargs.get("path", ""))
        if name == "search_text":
            return self.search_text(kwargs.get("keyword", ""), kwargs.get("path", "."))
        if name == "run_command":
            return self.run_command(kwargs.get("command", ""))
        return Observation(False, name, "未知工具。")

