import json
import queue
import subprocess
import threading
import time
from typing import Any


class MCPStdioClient:
    def __init__(self, command: str, args: list[str], server_name: str, timeout_seconds: float = 5.0):
        self.command = command
        self.args = args
        self.server_name = server_name
        self.process = None
        self.next_id = 1
        self.timeout_seconds = timeout_seconds
        self._responses: queue.Queue[dict[str, Any]] = queue.Queue()
        self._reader_thread: threading.Thread | None = None

    def start(self) -> None:
        if self.process:
            return
        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._reader_thread = threading.Thread(target=self._read_stdout_loop, daemon=True)
        self._reader_thread.start()

    def initialize(self) -> dict:
        return self._request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hermes", "version": "0.1.0"},
            },
        )

    def list_tools(self) -> list[dict]:
        result = self._request("tools/list", {})
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: dict) -> dict:
        return self._request("tools/call", {"name": name, "arguments": arguments or {}})

    def stop(self) -> None:
        if not self.process:
            return
        try:
            if self.process.stdin:
                self.process.stdin.close()
        except Exception:
            pass
        if self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                self.process.kill()
        for stream_name in ("stdout", "stderr"):
            stream = getattr(self.process, stream_name, None)
            try:
                if stream:
                    stream.close()
            except Exception:
                pass
        self.process = None

    def _request(self, method: str, params: dict) -> dict:
        if not self.process or not self.process.stdin:
            raise RuntimeError(f"MCP server {self.server_name} is not started.")

        request_id = self.next_id
        self.next_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if self.process.poll() is not None and self._responses.empty():
                stderr = self._read_stderr_snapshot()
                detail = f": {stderr}" if stderr else ""
                raise RuntimeError(f"MCP server {self.server_name} exited before responding{detail}")
            timeout = min(0.1, max(0.01, deadline - time.monotonic()))
            try:
                response = self._responses.get(timeout=timeout)
            except queue.Empty:
                break
            if response.get("id") != request_id:
                continue
            if "error" in response:
                error = response["error"]
                if isinstance(error, dict):
                    raise RuntimeError(error.get("message") or str(error))
                raise RuntimeError(str(error))
            return response.get("result") or {}

        stderr = self._read_stderr_snapshot()
        detail = f" stderr: {stderr}" if stderr else ""
        raise TimeoutError(f"MCP request timed out: {method}{detail}")

    def _read_stdout_loop(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._responses.put(json.loads(line))
            except json.JSONDecodeError:
                self._responses.put({"error": {"message": f"Invalid JSON from MCP server: {line}"}})

    def _read_stderr_snapshot(self) -> str:
        if not self.process or not self.process.stderr:
            return ""
        if self.process.poll() is None:
            return ""
        try:
            return self.process.stderr.read().strip()
        except Exception:
            return ""
