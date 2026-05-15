import json
import os
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hermes.mcp.client import MCPStdioClient


class _BridgeHandler(BaseHTTPRequestHandler):
    routes = {}
    status_codes = {}

    def _send(self, status_code: int, body: str, content_type: str = "application/json"):
        encoded = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path not in self.routes:
            self._send(404, json.dumps({"detail": "missing"}))
            return
        body = self.routes[self.path]
        status = self.status_codes.get(self.path, 200)
        self._send(status, body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self.server.last_body = json.loads(body)
        self.server.last_headers = dict(self.headers.items())
        if self.path not in self.routes:
            self._send(404, json.dumps({"detail": "missing"}))
            return
        response_body = self.routes[self.path]
        status = self.status_codes.get(self.path, 200)
        self._send(status, response_body)

    def log_message(self, format, *args):
        return


class TestHermesMCPServerBridge(unittest.TestCase):
    def setUp(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
        sock.close()
        self.base_url = f"http://127.0.0.1:{port}"
        _BridgeHandler.routes = {
            "/api/status": json.dumps({"agent_id": "hermes", "current_state": "IDLE"}),
            "/api/logs": json.dumps([{"action": "USER_CMD", "data": {"task": "hello"}}]),
            "/api/task": json.dumps(
                {
                    "message": "Task completed",
                    "task": "please run",
                    "result": {
                        "status": "FAILED",
                        "error": "Task rejected by management policy.",
                        "trace": [{"action": "AUDITOR_VERIFICATION", "data": {"final_status": "REJECTED"}}],
                    },
                }
            ),
        }
        _BridgeHandler.status_codes = {}
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), _BridgeHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.previous_base_url = os.environ.get("HERMES_BASE_URL")
        self.previous_timeout = os.environ.get("HERMES_API_TIMEOUT_SECONDS")
        os.environ["HERMES_BASE_URL"] = self.base_url
        os.environ["HERMES_API_TIMEOUT_SECONDS"] = "1"
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes",
            timeout_seconds=5,
        )
        self.client.start()
        self.client.initialize()

    def tearDown(self):
        self.client.stop()
        self.httpd.shutdown()
        self.httpd.server_close()
        if self.previous_base_url is None:
            os.environ.pop("HERMES_BASE_URL", None)
        else:
            os.environ["HERMES_BASE_URL"] = self.previous_base_url
        if self.previous_timeout is None:
            os.environ.pop("HERMES_API_TIMEOUT_SECONDS", None)
        else:
            os.environ["HERMES_API_TIMEOUT_SECONDS"] = self.previous_timeout

    def test_run_task_bridges_to_api_task_and_passes_through_result(self):
        response = self.client.call_tool("hermes.run_task", {"task": "please run"})

        payload = json.loads(response["content"][0]["text"])
        self.assertFalse(response["isError"])
        self.assertEqual(payload["result"]["status"], "FAILED")
        self.assertEqual(self.httpd.last_body["task"], "please run")
        self.assertEqual(self.httpd.last_body["provider"], "mock")
        self.assertEqual(self.httpd.last_body["metadata"]["source"], "mcp")
        self.assertEqual(self.httpd.last_body["metadata"]["client"], "claude_code")
        self.assertEqual(self.httpd.last_body["metadata"]["tool"], "hermes.run_task")

    def test_get_status_and_get_trace_bridge_to_expected_endpoints(self):
        status_response = self.client.call_tool("hermes.get_status", {})
        trace_response = self.client.call_tool("hermes.get_trace", {})

        status_payload = json.loads(status_response["content"][0]["text"])
        trace_payload = json.loads(trace_response["content"][0]["text"])

        self.assertEqual(status_payload["current_state"], "IDLE")
        self.assertEqual(trace_payload[0]["action"], "USER_CMD")

    def test_bridge_marks_transport_failures_as_error(self):
        self.client.stop()
        missing_sock = socket.socket()
        missing_sock.bind(("127.0.0.1", 0))
        _, missing_port = missing_sock.getsockname()
        missing_sock.close()
        os.environ["HERMES_BASE_URL"] = f"http://127.0.0.1:{missing_port}"
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes",
            timeout_seconds=5,
        )
        self.client.start()
        self.client.initialize()

        response = self.client.call_tool("hermes.get_status", {})

        payload = json.loads(response["content"][0]["text"])
        self.assertTrue(response["isError"])
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error"]["code"], "HERMES_API_UNAVAILABLE")

    def test_bridge_marks_invalid_json_as_error(self):
        _BridgeHandler.routes["/api/status"] = "{not-json"

        response = self.client.call_tool("hermes.get_status", {})

        payload = json.loads(response["content"][0]["text"])
        self.assertTrue(response["isError"])
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error"]["code"], "INVALID_JSON_RESPONSE")


if __name__ == "__main__":
    unittest.main()
