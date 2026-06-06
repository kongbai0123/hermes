from __future__ import annotations

import json
import os
import subprocess
import base64
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExternalChatResult:
    ok: bool
    target: str
    message: str
    reply: str
    status: str
    error: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "target": self.target,
                "message": self.message,
                "reply": self.reply,
                "status": self.status,
                "error": self.error,
            },
            ensure_ascii=False,
            indent=2,
        )


@dataclass(frozen=True)
class ExternalChatTurn:
    turn: int
    sent: str
    received: str
    status: str


@dataclass(frozen=True)
class ExternalChatLoopResult:
    ok: bool
    target: str
    initial_message: str
    turns: list[ExternalChatTurn]
    status: str
    stop_reason: str
    error: str | None = None

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def to_json(self) -> str:
        return json.dumps(
            {
                "ok": self.ok,
                "target": self.target,
                "initial_message": self.initial_message,
                "turn_count": self.turn_count,
                "status": self.status,
                "stop_reason": self.stop_reason,
                "error": self.error,
                "turns": [
                    {
                        "turn": turn.turn,
                        "sent": turn.sent,
                        "received": turn.received,
                        "status": turn.status,
                    }
                    for turn in self.turns
                ],
            },
            ensure_ascii=False,
            indent=2,
        )


class ExternalChatBridge(Protocol):
    def send_and_receive(self, message: str, *, target: str = "chatgpt_web") -> ExternalChatResult:
        ...


def run_external_chat_loop(
    bridge: ExternalChatBridge,
    initial_message: str,
    *,
    target: str = "chatgpt_web",
    max_turns: int = 3,
) -> ExternalChatLoopResult:
    safe_message = initial_message.strip()
    safe_target = target.strip() or "chatgpt_web"
    safe_max_turns = max(1, min(int(max_turns), 8))
    if not safe_message:
        return ExternalChatLoopResult(False, safe_target, safe_message, [], "failed", "empty_message", "message is required")

    turns: list[ExternalChatTurn] = []
    next_message = safe_message
    for turn_number in range(1, safe_max_turns + 1):
        result = bridge.send_and_receive(next_message, target=safe_target)
        turns.append(
            ExternalChatTurn(
                turn=turn_number,
                sent=next_message,
                received=result.reply,
                status=result.status,
            )
        )
        if not result.ok:
            return ExternalChatLoopResult(
                False,
                safe_target,
                safe_message,
                turns,
                "failed",
                "bridge_failed",
                result.error,
            )
        if not result.reply.strip():
            return ExternalChatLoopResult(True, safe_target, safe_message, turns, "completed", "empty_reply")
        next_message = _next_external_chat_message(result.reply)

    return ExternalChatLoopResult(True, safe_target, safe_message, turns, "completed", "max_turns_reached")


def _next_external_chat_message(previous_reply: str) -> str:
    clipped_reply = previous_reply.strip()[-1000:]
    return (
        "請根據上一輪回覆繼續，並給 Hermes 可執行的下一步。\n"
        f"上一輪回覆：{clipped_reply}"
    )


class FakeExternalChatBridge:
    def __init__(
        self,
        replies: dict[str, str] | None = None,
        *,
        default_reply: str = "收到外部 GPT 回覆。",
    ) -> None:
        self.replies = replies or {}
        self.default_reply = default_reply
        self.sent_messages: list[tuple[str, str]] = []

    def send_and_receive(self, message: str, *, target: str = "chatgpt_web") -> ExternalChatResult:
        safe_message = message.strip()
        safe_target = target.strip() or "chatgpt_web"
        self.sent_messages.append((safe_target, safe_message))
        return ExternalChatResult(
            ok=True,
            target=safe_target,
            message=safe_message,
            reply=self.replies.get(safe_message, self.default_reply),
            status="completed",
        )


class UnconfiguredExternalChatBridge:
    def send_and_receive(self, message: str, *, target: str = "chatgpt_web") -> ExternalChatResult:
        safe_message = message.strip()
        safe_target = target.strip() or "chatgpt_web"
        payload = {
            "status": "handoff_ready",
            "target": safe_target,
            "message": safe_message,
            "instruction": (
                "External chat bridge is not configured. Wire a browser or MCP adapter that can "
                "send message, wait for the external reply, extract text, and return it here."
            ),
        }
        return ExternalChatResult(
            ok=True,
            target=safe_target,
            message=safe_message,
            reply=json.dumps(payload, ensure_ascii=False, indent=2),
            status="handoff_ready",
        )


class WindowsClipboardExternalChatBridge:
    def __init__(
        self,
        *,
        window_title: str = "Google Chrome",
        wait_seconds: int = 20,
        powershell: str = "powershell",
    ) -> None:
        self.window_title = window_title
        self.wait_seconds = max(3, min(int(wait_seconds), 90))
        self.powershell = powershell

    def send_and_receive(self, message: str, *, target: str = "chatgpt_web") -> ExternalChatResult:
        safe_message = message.strip()
        safe_target = target.strip() or "chatgpt_web"
        if not safe_message:
            return ExternalChatResult(False, safe_target, safe_message, "", "failed", "message is required")

        completed = subprocess.run(
            [
                self.powershell,
                "-NoProfile",
                "-STA",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                self._powershell_script(),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.wait_seconds + 15,
            env={
                **os.environ,
                "LIB": "",
                "INCLUDE": "",
                "LIBPATH": "",
                "HERMES_EXTERNAL_CHAT_MESSAGE": safe_message,
                "HERMES_EXTERNAL_CHAT_WINDOW": self.window_title,
                "HERMES_EXTERNAL_CHAT_WAIT_MS": str(self.wait_seconds * 1000),
            },
        )
        if completed.returncode != 0:
            return ExternalChatResult(
                False,
                safe_target,
                safe_message,
                "",
                "failed",
                (completed.stderr or completed.stdout or "external chat bridge failed").strip(),
            )

        copied_text = self._decode_bridge_output(completed.stdout)
        if not copied_text.strip():
            return ExternalChatResult(False, safe_target, safe_message, "", "failed", "No text captured from external chat.")
        return ExternalChatResult(
            True,
            safe_target,
            safe_message,
            self._extract_reply(copied_text, safe_message),
            "completed",
        )

    def _decode_bridge_output(self, output: str) -> str:
        token = output.strip().splitlines()[-1] if output.strip() else ""
        try:
            return base64.b64decode(token).decode("utf-8", errors="replace")
        except Exception:
            return output

    def _extract_reply(self, copied_text: str, message: str) -> str:
        normalized = copied_text.replace("\r\n", "\n").strip()
        marker_index = normalized.lower().rfind(message.lower())
        if marker_index >= 0:
            reply = normalized[marker_index + len(message) :].strip()
            if reply:
                return reply[-4000:]
        return normalized[-4000:]

    def _powershell_script(self) -> str:
        return r'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class HermesExternalChatUi {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}
"@
$message = $env:HERMES_EXTERNAL_CHAT_MESSAGE
$title = $env:HERMES_EXTERNAL_CHAT_WINDOW
$waitMs = [int]$env:HERMES_EXTERNAL_CHAT_WAIT_MS
[System.Windows.Forms.Clipboard]::SetText($message)
$script:targetWindow = [IntPtr]::Zero
$callback = [HermesExternalChatUi+EnumWindowsProc]{
  param($hWnd, $lParam)
  if ([HermesExternalChatUi]::IsWindowVisible($hWnd)) {
    $sb = New-Object System.Text.StringBuilder 512
    [void][HermesExternalChatUi]::GetWindowText($hWnd, $sb, $sb.Capacity)
    $windowTitle = $sb.ToString()
    if (
      $windowTitle.IndexOf($title, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
      $windowTitle.IndexOf("Work Agent", [StringComparison]::OrdinalIgnoreCase) -lt 0
    ) {
      $script:targetWindow = $hWnd
      return $false
    }
  }
  return $true
}
[void][HermesExternalChatUi]::EnumWindows($callback, [IntPtr]::Zero)
if ($script:targetWindow -eq [IntPtr]::Zero) { throw "Cannot find external chat window title containing: $title" }
[HermesExternalChatUi]::ShowWindow($script:targetWindow, 5) | Out-Null
[HermesExternalChatUi]::SetForegroundWindow($script:targetWindow) | Out-Null
Start-Sleep -Milliseconds 800
$hWnd = $script:targetWindow
$rect = New-Object HermesExternalChatUi+RECT
[void][HermesExternalChatUi]::GetWindowRect($hWnd, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
$composeX = [int]($rect.Left + ($width * 0.55))
$composeY = [int]($rect.Bottom - 75)
[HermesExternalChatUi]::SetCursorPos($composeX, $composeY) | Out-Null
[HermesExternalChatUi]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
[HermesExternalChatUi]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds $waitMs
$pageX = [int]($rect.Left + ($width * 0.55))
$pageY = [int]($rect.Top + ($height * 0.35))
[HermesExternalChatUi]::SetCursorPos($pageX, $pageY) | Out-Null
[HermesExternalChatUi]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
[HermesExternalChatUi]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('^a')
Start-Sleep -Milliseconds 250
[System.Windows.Forms.SendKeys]::SendWait('^c')
Start-Sleep -Milliseconds 500
$copied = [System.Windows.Forms.Clipboard]::GetText()
$bytes = [System.Text.Encoding]::UTF8.GetBytes($copied)
[Convert]::ToBase64String($bytes)
'''
