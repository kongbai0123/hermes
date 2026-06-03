from __future__ import annotations

import os
import shlex
import subprocess
import ipaddress
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass
class Observation:
    ok: bool
    tool: str
    content: str

    def format(self) -> str:
        status = "OK" if self.ok else "ERROR"
        return f"[{status}] {self.tool}: {self.content}"


class ToolBox:
    def __init__(
        self,
        workspace_path: str,
        allowed_commands: list[str],
        *,
        allowed_proxy_domains: list[str] | None = None,
        proxy_fetcher: Callable[[str, int, int], str] | None = None,
    ) -> None:
        self.workspace = Path(workspace_path).resolve()
        self.allowed_commands = allowed_commands
        self.allowed_proxy_domains = [domain.lower() for domain in (allowed_proxy_domains or [])]
        self.proxy_fetcher = proxy_fetcher or self._default_proxy_fetcher
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

    def proxy_fetch(self, url: str, timeout: int | str = 10, max_bytes: int | str = 65536) -> Observation:
        validation_error = self._validate_proxy_url(url)
        if validation_error:
            return Observation(False, "proxy_fetch", validation_error)

        try:
            safe_timeout = max(1, min(int(timeout), 30))
            safe_max_bytes = max(1024, min(int(max_bytes), 200000))
            content = self.proxy_fetcher(url, safe_timeout, safe_max_bytes)
            if len(content) > safe_max_bytes:
                content = content[:safe_max_bytes] + "\n...(已截斷)"
            return Observation(True, "proxy_fetch", content)
        except ValueError:
            return Observation(False, "proxy_fetch", "timeout 與 max_bytes 必須是整數。")
        except Exception as exc:
            return Observation(False, "proxy_fetch", str(exc))

    def _validate_proxy_url(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return "proxy_fetch 只允許 http 或 https URL。"
        if not parsed.hostname:
            return "proxy_fetch 需要有效的 hostname。"

        host = parsed.hostname.lower()
        if self._is_internal_host(host):
            return "拒絕透過 proxy_fetch 存取 localhost、內網或保留位址。"
        if not self._is_proxy_domain_allowed(host):
            return f"proxy_fetch domain 不在 allowlist 內：{host}"
        return None

    def _is_proxy_domain_allowed(self, host: str) -> bool:
        for domain in self.allowed_proxy_domains:
            if host == domain or host.endswith(f".{domain}"):
                return True
        return False

    def _is_internal_host(self, host: str) -> bool:
        if host in {"localhost", "localhost.localdomain"}:
            return True
        try:
            addresses = [host] if self._looks_like_ip(host) else socket.gethostbyname_ex(host)[2]
        except OSError:
            return True
        return any(self._is_blocked_ip(address) for address in addresses)

    def _looks_like_ip(self, host: str) -> bool:
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            return False

    def _is_blocked_ip(self, address: str) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return True
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )

    def _default_proxy_fetcher(self, url: str, timeout: int, max_bytes: int) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": "Hermes-Work-Agent/0.5",
                "Accept": "text/plain,text/html,application/json;q=0.9,*/*;q=0.1",
            },
            method="GET",
        )
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(max_bytes + 1)
            charset = response.headers.get_content_charset() or "utf-8"
        text = payload[:max_bytes].decode(charset, errors="replace")
        if len(payload) > max_bytes:
            text += "\n...(已截斷)"
        return text

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
        if name == "proxy_fetch":
            return self.proxy_fetch(
                kwargs.get("url", ""),
                kwargs.get("timeout", "10"),
                kwargs.get("max_bytes", "65536"),
            )
        return Observation(False, name, "未知工具。")
