import json
import os
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from hermes.mcp.client import MCPStdioClient

class _MockHermesAPIProvider(BaseHTTPRequestHandler):
    def _send(self, status_code, body):
        encoded = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if self.path == "/api/task":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self.server.last_payload = body
            
            if body.get("task") == "trigger_approval":
                self._send(200, json.dumps({
                    "ok": False,
                    "status": "approval_required",
                    "proposal_id": "p_123",
                    "trace_id": "t_456"
                }))
            else:
                self._send(200, json.dumps({"ok": True, "status": "DONE", "response": "ok"}))
        else:
            self._send(404, '{"ok": false}')

    def log_message(self, format, *args):
        pass

class TestMCPProviderConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sock = socket.socket()
        cls.sock.bind(("127.0.0.1", 0))
        cls.port = cls.sock.getsockname()[1]
        cls.sock.close()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), _MockHermesAPIProvider)
        cls.httpd.last_payload = None
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        self.old_env = {k: os.environ.get(k) for k in [
            "HERMES_BASE_URL", "HERMES_MCP_PROVIDER", "HERMES_MCP_MODEL", 
            "HERMES_DEFAULT_PROVIDER", "HERMES_DEFAULT_MODEL"
        ]}
        os.environ["HERMES_BASE_URL"] = self.base_url
        for k in ["HERMES_MCP_PROVIDER", "HERMES_MCP_MODEL", "HERMES_DEFAULT_PROVIDER", "HERMES_DEFAULT_MODEL"]:
            if k in os.environ: del os.environ[k]
            
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes"
        )
        self.client.start()
        self.client.initialize()

    def tearDown(self):
        self.client.stop()
        for k, v in self.old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_mcp_run_task_defaults_to_mock(self):
        self.client.call_tool("hermes.run_task", {"task": "test"})
        payload = self.httpd.last_payload
        self.assertEqual(payload["provider"], "mock")
        self.assertEqual(payload["metadata"]["provider_source"], "default")

    def test_mcp_run_task_uses_provider_argument(self):
        self.client.call_tool("hermes.run_task", {
            "task": "test",
            "provider": "ollama",
            "model": "qwen3:14b",
            "base_url": "http://other:11434",
            "temperature": 0.7
        })
        payload = self.httpd.last_payload
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "qwen3:14b")
        self.assertEqual(payload["base_url"], "http://other:11434")
        self.assertEqual(payload["temperature"], 0.7)
        self.assertEqual(payload["metadata"]["provider_source"], "argument")

    def test_mcp_run_task_uses_env_provider(self):
        self.client.stop()
        os.environ["HERMES_MCP_PROVIDER"] = "claude"
        os.environ["HERMES_MCP_MODEL"] = "claude-3-sonnet"
        
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes"
        )
        self.client.start()
        self.client.initialize()
        
        self.client.call_tool("hermes.run_task", {"task": "test"})
        payload = self.httpd.last_payload
        self.assertEqual(payload["provider"], "claude")
        self.assertEqual(payload["model"], "claude-3-sonnet")
        self.assertEqual(payload["metadata"]["provider_source"], "env")

    def test_mcp_still_passes_through_approval_required(self):
        resp = self.client.call_tool("hermes.run_task", {"task": "trigger_approval"})
        self.assertFalse(resp["isError"])
        payload = json.loads(resp["content"][0]["text"])
        self.assertEqual(payload["status"], "approval_required")
        self.assertEqual(payload["proposal_id"], "p_123")

    def test_mcp_bridge_error_still_is_error_true(self):
        self.client.stop()
        os.environ["HERMES_BASE_URL"] = "http://127.0.0.1:1" # Invalid port
        client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes"
        )
        client.start()
        client.initialize()
        try:
            resp = client.call_tool("hermes.get_status", {})
            self.assertTrue(resp["isError"])
            payload = json.loads(resp["content"][0]["text"])
            self.assertEqual(payload["error"]["code"], "HERMES_API_UNAVAILABLE")
        finally:
            client.stop()

if __name__ == "__main__":
    unittest.main()
