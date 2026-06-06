from __future__ import annotations

import os
import json
import shlex
import subprocess
import ipaddress
import socket
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .external_chat import ExternalChatBridge, UnconfiguredExternalChatBridge, run_external_chat_loop
from .gui_agent import GuiRunner, MockGuiRunner


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
        allowed_browser_domains: list[str] | None = None,
        browser_opener: Callable[[str, str], None] | None = None,
        external_codex_runner: Callable[[str, str], str] | None = None,
        external_chat_bridge: ExternalChatBridge | None = None,
        gui_runner: GuiRunner | None = None,
    ) -> None:
        self.workspace = Path(workspace_path).resolve()
        self.allowed_commands = allowed_commands
        self.allowed_proxy_domains = [domain.lower() for domain in (allowed_proxy_domains or [])]
        self.proxy_fetcher = proxy_fetcher or self._default_proxy_fetcher
        self.allowed_browser_domains = [domain.lower() for domain in (allowed_browser_domains or [])]
        self.browser_opener = browser_opener or self._default_browser_opener
        self.external_codex_runner = external_codex_runner
        self.external_chat_bridge = external_chat_bridge or UnconfiguredExternalChatBridge()
        self.gui_runner = gui_runner or MockGuiRunner()
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
        validation_error = self._validate_url(url, self.allowed_proxy_domains, "proxy_fetch")
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

    def open_browser(self, url: str, browser: str = "chrome") -> Observation:
        validation_error = self._validate_url(url, self.allowed_browser_domains, "open_browser")
        if validation_error:
            return Observation(False, "open_browser", validation_error)

        safe_browser = browser.strip().lower() or "chrome"
        if safe_browser not in {"chrome", "default"}:
            return Observation(False, "open_browser", "open_browser 目前只允許 chrome 或 default。")
        try:
            self.browser_opener(url, safe_browser)
            return Observation(True, "open_browser", f"已請 {safe_browser} 開啟：{url}")
        except Exception as exc:
            return Observation(False, "open_browser", str(exc))

    def external_codex(self, topic: str, mode: str = "self_optimization_discussion") -> Observation:
        safe_topic = (topic or "Codex 與 Hermes 自我優化討論").strip()[:2000]
        safe_mode = (mode or "self_optimization_discussion").strip()[:120]
        if safe_mode not in {"self_optimization_discussion", "architecture_review", "implementation_review"}:
            return Observation(False, "external_codex", f"不支援的 external_codex mode：{safe_mode}")

        try:
            if self.external_codex_runner is not None:
                result = self.external_codex_runner(safe_topic, safe_mode)
                return Observation(True, "external_codex", result[:8000])
            payload = {
                "status": "handoff_ready",
                "tool": "external_codex",
                "mode": safe_mode,
                "topic": safe_topic,
                "instruction": "請外部 Codex 針對 topic 執行自我優化討論，回傳可執行建議、風險與實作順序。",
            }
            return Observation(True, "external_codex", json.dumps(payload, ensure_ascii=False, indent=2))
        except Exception as exc:
            return Observation(False, "external_codex", str(exc))

    def external_chat(self, message: str, target: str = "chatgpt_web") -> Observation:
        safe_message = (message or "").strip()
        safe_target = (target or "chatgpt_web").strip()
        if not safe_message:
            return Observation(False, "external_chat", "external_chat 需要 message。")
        if safe_target not in {"chatgpt_web", "codex_web", "gpt_web"}:
            return Observation(False, "external_chat", f"不支援的 external_chat target：{safe_target}")

        try:
            result = self.external_chat_bridge.send_and_receive(safe_message, target=safe_target)
            return Observation(result.ok, "external_chat", result.to_json()[:8000])
        except Exception as exc:
            return Observation(False, "external_chat", str(exc))

    def external_chat_loop(
        self,
        message: str,
        target: str = "chatgpt_web",
        max_turns: int | str = 3,
    ) -> Observation:
        safe_message = (message or "").strip()
        safe_target = (target or "chatgpt_web").strip()
        if not safe_message:
            return Observation(False, "external_chat_loop", "external_chat_loop 需要 message。")
        if safe_target not in {"chatgpt_web", "codex_web", "gpt_web"}:
            return Observation(False, "external_chat_loop", f"不支援的 external_chat_loop target：{safe_target}")

        try:
            safe_max_turns = max(1, min(int(max_turns), 8))
        except ValueError:
            return Observation(False, "external_chat_loop", "max_turns 必須是整數。")

        try:
            result = run_external_chat_loop(
                self.external_chat_bridge,
                safe_message,
                target=safe_target,
                max_turns=safe_max_turns,
            )
            return Observation(result.ok, "external_chat_loop", result.to_json()[:8000])
        except Exception as exc:
            return Observation(False, "external_chat_loop", str(exc))

    def self_improve(
        self,
        goal: str,
        scope: str = "simple_agent",
        mode: str = "proposal_only",
        max_files: int | str = 8,
    ) -> Observation:
        safe_goal = (goal or "改善 Hermes 自身能力").strip()[:2000]
        safe_scope = (scope or "simple_agent").strip().replace("\\", "/")
        safe_mode = (mode or "proposal_only").strip()
        if safe_mode not in {"proposal_only", "apply_after_approval"}:
            return Observation(False, "self_improve", f"不支援的 self_improve mode：{safe_mode}")

        try:
            safe_max_files = max(1, min(int(max_files), 20))
        except ValueError:
            return Observation(False, "self_improve", "max_files 必須是整數。")

        if safe_mode == "apply_after_approval":
            payload = {
                "ok": False,
                "status": "approval_required",
                "mode": safe_mode,
                "goal": safe_goal,
                "scope": safe_scope,
                "requires_approval": True,
                "reason": "Hermes 自我修改會寫入自身程式，必須先取得使用者明確批准。",
            }
            return Observation(False, "self_improve", json.dumps(payload, ensure_ascii=False, indent=2))

        try:
            hermes_root = Path(__file__).resolve().parents[1]
            target = (hermes_root / safe_scope).resolve()
            try:
                target.relative_to(hermes_root)
            except ValueError as exc:
                raise PermissionError("self_improve 只允許檢查 Hermes 程式範圍內的檔案。") from exc
            if not target.exists():
                return Observation(False, "self_improve", f"找不到 Hermes 程式範圍：{safe_scope}")

            candidate_files = self._self_improve_candidate_files(target, hermes_root, safe_max_files)
            payload = {
                "ok": True,
                "status": "proposal_ready",
                "mode": safe_mode,
                "goal": safe_goal,
                "scope": safe_scope,
                "requires_approval": True,
                "candidate_files": candidate_files,
                "findings": self._self_improve_findings(safe_goal, candidate_files),
                "plan": [
                    "定位與 goal 相關的 Hermes 模組與測試。",
                    "先補失敗測試描述期望行為。",
                    "產生最小 patch，避免無關重構。",
                    "跑 focused tests，再跑完整 backend tests。",
                    "若測試通過，回報 touched files、風險與下一步。",
                ],
                "patch_summary": "proposal_only 不會寫入檔案；實際修改需使用者批准後才可套用。",
                "tests_to_run": [
                    "python -m pytest tests/test_tools.py tests/test_work_execution.py tests/test_roles.py -q",
                    "python -m pytest tests -q",
                ],
                "write_policy": "apply_after_approval requires explicit approval",
            }
            return Observation(True, "self_improve", json.dumps(payload, ensure_ascii=False, indent=2)[:8000])
        except Exception as exc:
            return Observation(False, "self_improve", str(exc))

    def gui_observe(self) -> Observation:
        try:
            return Observation(True, "gui_observe", self.gui_runner.observe()[:8000])
        except Exception as exc:
            payload = {
                "ok": False,
                "status": "tool_unavailable",
                "tool": "gui_observe",
                "reason": str(exc),
            }
            return Observation(False, "gui_observe", json.dumps(payload, ensure_ascii=False))

    def gui_verify(self, condition: str) -> Observation:
        safe_condition = (condition or "").strip()
        if not safe_condition:
            return Observation(False, "gui_verify", "gui_verify 需要 condition。")
        try:
            return Observation(True, "gui_verify", self.gui_runner.verify(safe_condition)[:8000])
        except Exception as exc:
            payload = {
                "ok": False,
                "status": "tool_unavailable",
                "tool": "gui_verify",
                "condition": safe_condition,
                "reason": str(exc),
            }
            return Observation(False, "gui_verify", json.dumps(payload, ensure_ascii=False))

    def gui_action_placeholder(self, tool_name: str, **kwargs: str) -> Observation:
        payload = {
            "ok": False,
            "status": "approval_required",
            "tool": tool_name,
            "args": dict(kwargs),
            "reason": "GUI action tools require explicit approval and a real governed runner before execution.",
        }
        return Observation(False, tool_name, json.dumps(payload, ensure_ascii=False))

    def _self_improve_candidate_files(self, target: Path, hermes_root: Path, max_files: int) -> list[str]:
        files = [target] if target.is_file() else target.rglob("*")
        candidates: list[str] = []
        file_paths: list[Path] = []
        for file_path in files:
            if not file_path.is_file():
                continue
            if any(part in {"__pycache__", ".pytest_cache", "dist"} for part in file_path.parts):
                continue
            if file_path.suffix not in {".py", ".md", ".json"}:
                continue
            file_paths.append(file_path)

        priority = {"simple_agent/tools.py": 0, "simple_agent/work_execution.py": 1, "simple_agent/bounded_loop.py": 2}
        for file_path in sorted(
            file_paths,
            key=lambda path: (priority.get(path.relative_to(hermes_root).as_posix(), 99), path.as_posix()),
        ):
            candidates.append(file_path.relative_to(hermes_root).as_posix())
            if len(candidates) >= max_files:
                break
        return candidates

    def _self_improve_findings(self, goal: str, candidate_files: list[str]) -> list[str]:
        findings = [
            "目前 Hermes 自我開發必須先產生 proposal，不能直接改寫自身程式。",
            "實際修改需要走 approval boundary，避免無限制 self-write。",
        ]
        if any("tools.py" in file for file in candidate_files):
            findings.append("ToolBox 是新增自我開發工具入口的主要候選位置。")
        if any("work_execution.py" in file for file in candidate_files):
            findings.append("WorkSkillRouter / PolicyGate 需要明確區分 proposal_only 與 apply_after_approval。")
        if "測試" in goal or "test" in goal.lower():
            findings.append("此 goal 涉及測試，應先新增 failing test 再實作。")
        return findings

    def _validate_url(self, url: str, allowed_domains: list[str], tool_name: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return f"{tool_name} 只允許 http 或 https URL。"
        if not parsed.hostname:
            return f"{tool_name} 需要有效的 hostname。"

        host = parsed.hostname.lower()
        if self._is_internal_host(host):
            return f"拒絕透過 {tool_name} 存取 localhost、內網或保留位址。"
        if not self._is_domain_allowed(host, allowed_domains):
            return f"{tool_name} domain 不在 allowlist 內：{host}"
        return None

    def _is_domain_allowed(self, host: str, allowed_domains: list[str]) -> bool:
        for domain in allowed_domains:
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

    def _default_browser_opener(self, url: str, browser: str) -> None:
        if browser == "chrome":
            if sys.platform.startswith("win"):
                completed = subprocess.run(
                    ["cmd", "/c", "start", "", "chrome", url],
                    cwd=self.workspace,
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if completed.returncode == 0:
                    return
            try:
                webbrowser.get("chrome").open(url, new=2)
                return
            except webbrowser.Error:
                pass
        webbrowser.open(url, new=2)

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
        if name == "open_browser":
            return self.open_browser(kwargs.get("url", ""), kwargs.get("browser", "chrome"))
        if name == "external_codex":
            return self.external_codex(
                kwargs.get("topic", ""),
                kwargs.get("mode", "self_optimization_discussion"),
            )
        if name == "external_chat":
            return self.external_chat(
                kwargs.get("message", ""),
                kwargs.get("target", "chatgpt_web"),
            )
        if name == "external_chat_loop":
            return self.external_chat_loop(
                kwargs.get("message", ""),
                kwargs.get("target", "chatgpt_web"),
                kwargs.get("max_turns", "3"),
            )
        if name == "self_improve":
            return self.self_improve(
                kwargs.get("goal", ""),
                kwargs.get("scope", "simple_agent"),
                kwargs.get("mode", "proposal_only"),
                kwargs.get("max_files", "8"),
            )
        if name == "gui_observe":
            return self.gui_observe()
        if name == "gui_verify":
            return self.gui_verify(kwargs.get("condition", ""))
        if name in {"gui_click", "gui_type_text", "gui_hotkey", "gui_wait"}:
            return self.gui_action_placeholder(name, **kwargs)
        return Observation(False, name, "未知工具。")
