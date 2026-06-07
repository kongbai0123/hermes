from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol


CommandRunner = Callable[[str, int], subprocess.CompletedProcess[str]]


class GuiRunner(Protocol):
    def observe(self) -> str:
        """Return a compact JSON description of the current GUI state."""

    def verify(self, condition: str) -> str:
        """Return a compact JSON verification result for a GUI condition."""

    def click(self, target: str) -> str:
        """Click a governed GUI target."""

    def type_text(self, target: str, text: str) -> str:
        """Type text into a governed GUI target."""

    def hotkey(self, keys: str) -> str:
        """Send a governed hotkey chord."""


class MockGuiRunner:
    """Deterministic GUI runner used for policy, trace, and integration tests."""

    def observe(self) -> str:
        payload = {
            "status": "observed",
            "runner": "mock",
            "screen_id": "mock_screen_001",
            "visible_elements": [
                {
                    "id": "chat_prompt",
                    "label": "ChatGPT prompt",
                    "role": "textbox",
                    "bounds": {"x": 370, "y": 600, "width": 720, "height": 52},
                },
                {
                    "id": "send_button",
                    "label": "Send",
                    "role": "button",
                    "bounds": {"x": 1088, "y": 606, "width": 44, "height": 44},
                },
            ],
        }
        return json.dumps(payload, ensure_ascii=False)

    def verify(self, condition: str) -> str:
        safe_condition = (condition or "").strip()
        known_conditions = {
            "chat_prompt_visible": True,
            "send_button_visible": True,
            "external_reply_visible": False,
        }
        payload = {
            "status": "verified",
            "runner": "mock",
            "condition": safe_condition,
            "matched": known_conditions.get(safe_condition, False),
        }
        return json.dumps(payload, ensure_ascii=False)

    def click(self, target: str) -> str:
        payload = {
            "status": "clicked",
            "runner": "mock",
            "target": (target or "").strip(),
        }
        return json.dumps(payload, ensure_ascii=False)

    def type_text(self, target: str, text: str) -> str:
        safe_text = text or ""
        payload = {
            "status": "typed",
            "runner": "mock",
            "target": (target or "").strip(),
            "text_length": len(safe_text),
        }
        return json.dumps(payload, ensure_ascii=False)

    def hotkey(self, keys: str) -> str:
        payload = {
            "status": "hotkey_sent",
            "runner": "mock",
            "keys": _split_hotkey(keys),
        }
        return json.dumps(payload, ensure_ascii=False)


class WindowsGuiRunner:
    """Best-effort Windows desktop runner for governed Hermes GUI work."""

    def __init__(
        self,
        *,
        system_probe: Callable[[], dict] | None = None,
        ocr_reader: Callable[[Path], str] | None = None,
        command_runner: CommandRunner | None = None,
        screenshot_dir: str | Path | None = None,
    ) -> None:
        self.system_probe = system_probe or self._default_system_probe
        self.ocr_reader = ocr_reader or self._default_ocr_reader
        self.command_runner = command_runner or (lambda script, timeout: self._run_powershell(script, timeout=timeout))
        self.screenshot_dir = Path(screenshot_dir or Path(tempfile.gettempdir()) / "hermes_gui")

    def observe(self) -> str:
        payload = {
            "status": "observed",
            "runner": "windows",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            **self._safe_probe(),
        }
        return json.dumps(payload, ensure_ascii=False)

    def verify(self, condition: str) -> str:
        safe_condition = (condition or "").strip()
        probe = self._safe_probe()
        matched = self._match_condition(safe_condition, probe)
        payload = {
            "status": "verified",
            "runner": "windows",
            "condition": safe_condition,
            "matched": matched,
            "active_window": probe.get("active_window", {}),
            "evidence": self._condition_evidence(safe_condition, probe),
        }
        return json.dumps(payload, ensure_ascii=False)

    def click(self, target: str) -> str:
        x, y = self._parse_coordinates(target)
        if x is None or y is None:
            return self._unsupported_action("gui_click", target, "target must be x,y coordinates for WindowsGuiRunner.")
        script = f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class HermesMouse {{
  [DllImport("user32.dll")]
  public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}}
"@
[HermesMouse]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
[HermesMouse]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
"""
        self.command_runner(script, 5)
        return json.dumps({"status": "clicked", "runner": "windows", "target": target, "x": x, "y": y}, ensure_ascii=False)

    def type_text(self, target: str, text: str) -> str:
        safe_text = text or ""
        focused_window = self._focus_window_target(target)
        x, y = self._parse_coordinates(target)
        if x is not None and y is not None:
            self.click(target)
        escaped = safe_text.replace("'", "''")
        script = f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{escaped}')
"""
        self.command_runner(script, 10)
        return json.dumps(
            {
                "status": "typed",
                "runner": "windows",
                "target": target,
                "focused_window": focused_window,
                "text_length": len(safe_text),
            },
            ensure_ascii=False,
        )

    def hotkey(self, keys: str) -> str:
        parsed = _split_hotkey(keys)
        send_keys = self._to_sendkeys(parsed)
        script = f"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait('{send_keys}')
"""
        self.command_runner(script, 5)
        return json.dumps({"status": "hotkey_sent", "runner": "windows", "keys": parsed}, ensure_ascii=False)

    def _focus_window_target(self, target: str) -> str | None:
        prefix = "window:"
        if not (target or "").lower().startswith(prefix):
            return None
        title = target[len(prefix) :].strip()
        if not title:
            raise RuntimeError("window target requires a title fragment.")
        escaped_title = title.replace("'", "''")
        script = f"""
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class HermesWindowFocus {{
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")]
  public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")]
  public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")]
  public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
  [DllImport("user32.dll")]
  public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")]
  public static extern bool SetForegroundWindow(IntPtr hWnd);
}}
"@
$needle = '{escaped_title}'.ToLowerInvariant()
$script:targetWindow = [IntPtr]::Zero
$callback = [HermesWindowFocus+EnumWindowsProc]{{
  param([IntPtr]$hWnd, [IntPtr]$lParam)
  if ([HermesWindowFocus]::IsWindowVisible($hWnd)) {{
    $sb = New-Object System.Text.StringBuilder 512
    [void][HermesWindowFocus]::GetWindowText($hWnd, $sb, $sb.Capacity)
    if ($sb.ToString().ToLowerInvariant().Contains($needle)) {{
      $script:targetWindow = $hWnd
      return $false
    }}
  }}
  return $true
}}
[void][HermesWindowFocus]::EnumWindows($callback, [IntPtr]::Zero)
if ($script:targetWindow -eq [IntPtr]::Zero) {{
  throw "No visible window matched title fragment: {escaped_title}"
}}
[void][HermesWindowFocus]::ShowWindow($script:targetWindow, 5)
[void][HermesWindowFocus]::SetForegroundWindow($script:targetWindow)
Start-Sleep -Milliseconds 250
"""
        self.command_runner(script, 8)
        return title

    def _safe_probe(self) -> dict:
        try:
            probe = self.system_probe()
            return self._normalize_probe(probe)
        except Exception as exc:
            return {
                "active_window": {"title": "", "handle": ""},
                "screenshot": {"status": "failed", "reason": str(exc)},
                "clipboard": {"status": "failed", "text_preview": "", "text_length": 0, "reason": str(exc)},
                "ocr": {"status": "unavailable", "text_preview": "", "text_length": 0},
            }

    def _normalize_probe(self, probe: dict) -> dict:
        screenshot = probe.get("screenshot", {"status": "skipped"})
        return {
            "active_window": probe.get("active_window", {"title": "", "handle": ""}),
            "screenshot": screenshot,
            "clipboard": probe.get("clipboard", {"status": "skipped", "text_preview": "", "text_length": 0}),
            "ocr": probe.get("ocr") or self._ocr_from_screenshot(screenshot),
        }

    def _default_system_probe(self) -> dict:
        if os.name != "nt":
            return {
                "active_window": {"title": "", "handle": ""},
                "screenshot": {"status": "unavailable", "reason": "WindowsGuiRunner requires Windows."},
                "clipboard": {"status": "unavailable", "text_preview": "", "text_length": 0},
                "ocr": {"status": "unavailable", "text_preview": "", "text_length": 0},
            }
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = self.screenshot_dir / f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
        script = rf"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class HermesWindow {{
  [DllImport("user32.dll")]
  public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")]
  public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
}}
"@
$handle = [HermesWindow]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder 512
[void][HermesWindow]::GetWindowText($handle, $sb, $sb.Capacity)
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save('{str(screenshot_path).replace("'", "''")}', [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()
$clip = ""
try {{ $clip = Get-Clipboard -Raw -ErrorAction Stop }} catch {{ $clip = "" }}
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
@{{
  active_window = @{{ title = $sb.ToString(); handle = $handle.ToInt64().ToString() }}
  screenshot = @{{ status = "captured"; path = "{screenshot_path.as_posix()}" }}
  clipboard = @{{ status = "captured"; text_preview = if ($clip.Length -gt 500) {{ $clip.Substring(0,500) }} else {{ $clip }}; text_length = $clip.Length }}
}} | ConvertTo-Json -Compress -Depth 5
"""
        completed = self._run_powershell(script, timeout=15)
        return json.loads(completed.stdout)

    def _ocr_from_screenshot(self, screenshot: dict) -> dict:
        if screenshot.get("status") != "captured" or not screenshot.get("path"):
            return {
                "status": "unavailable",
                "text_preview": "",
                "text_length": 0,
                "reason": "No captured screenshot is available for OCR.",
            }
        try:
            text = self.ocr_reader(Path(str(screenshot["path"])))
            preview = text[:1000]
            return {
                "status": "captured",
                "text_preview": preview,
                "text_length": len(text),
            }
        except Exception as exc:
            return {
                "status": "unavailable",
                "text_preview": "",
                "text_length": 0,
                "reason": str(exc),
            }

    def _default_ocr_reader(self, path: Path) -> str:
        try:
            from PIL import Image  # type: ignore[import-not-found]
            import pytesseract  # type: ignore[import-not-found]
        except Exception as exc:
            raise RuntimeError("OCR dependencies are not installed: Pillow and pytesseract are required.") from exc
        tesseract_path = self._resolve_tesseract_path()
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = str(tesseract_path)
        try:
            return str(pytesseract.image_to_string(Image.open(path))).strip()
        except Exception as exc:
            raise RuntimeError(f"OCR failed: {exc}") from exc

    def _resolve_tesseract_path(self) -> Path | None:
        path = shutil.which("tesseract")
        if path:
            return Path(path)
        candidates = [
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Tesseract-OCR" / "tesseract.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _run_powershell(self, script: str, *, timeout: int) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in ("LIB", "INCLUDE", "LIBPATH"):
            env.pop(key, None)
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or "PowerShell GUI operation failed.")
        return completed

    def _match_condition(self, condition: str, probe: dict) -> bool:
        if not condition:
            return False
        scope, _, needle = condition.partition(":")
        if not needle:
            needle = condition
            haystacks = [
                str(probe.get("active_window", {}).get("title", "")),
                str(probe.get("clipboard", {}).get("text_preview", "")),
                str(probe.get("ocr", {}).get("text_preview", "")),
            ]
        else:
            scope = scope.lower()
            haystacks = {
                "active_window": [str(probe.get("active_window", {}).get("title", ""))],
                "window": [str(probe.get("active_window", {}).get("title", ""))],
                "clipboard": [str(probe.get("clipboard", {}).get("text_preview", ""))],
                "ocr": [str(probe.get("ocr", {}).get("text_preview", ""))],
            }.get(scope, [])
        return any(needle.lower() in haystack.lower() for haystack in haystacks)

    def _condition_evidence(self, condition: str, probe: dict) -> dict:
        return {
            "active_window_title": str(probe.get("active_window", {}).get("title", ""))[:200],
            "clipboard_preview": str(probe.get("clipboard", {}).get("text_preview", ""))[:200],
            "ocr_preview": str(probe.get("ocr", {}).get("text_preview", ""))[:200],
            "condition": condition,
        }

    def _parse_coordinates(self, target: str) -> tuple[int | None, int | None]:
        parts = [part.strip() for part in (target or "").replace(";", ",").split(",")]
        if len(parts) != 2:
            return None, None
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None, None

    def _unsupported_action(self, tool: str, target: str, reason: str) -> str:
        return json.dumps(
            {"ok": False, "status": "unsupported_target", "runner": "windows", "tool": tool, "target": target, "reason": reason},
            ensure_ascii=False,
        )

    def _to_sendkeys(self, keys: list[str]) -> str:
        modifiers = {"ctrl": "^", "control": "^", "shift": "+", "alt": "%"}
        prefix = ""
        normal: list[str] = []
        for key in keys:
            lowered = key.lower()
            if lowered in modifiers:
                prefix += modifiers[lowered]
            else:
                normal.append(key)
        body = "".join(f"{{{key.upper()}}}" if len(key) > 1 else key for key in normal)
        return f"{prefix}{body}"


def _split_hotkey(keys: str) -> list[str]:
    return [part.strip() for part in (keys or "").replace(",", "+").split("+") if part.strip()]
