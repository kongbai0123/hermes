import json
import os
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from hermes.mcp.client import MCPStdioClient


class _PolicyHandler(BaseHTTPRequestHandler):
    response_body = json.dumps({})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self.server.last_body = json.loads(body)
        encoded = self.response_body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


class TestClaudeCodeHermesMCPPolicy(unittest.TestCase):
    def setUp(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
        sock.close()
        self.base_url = f"http://127.0.0.1:{port}"
        _PolicyHandler.response_body = json.dumps(
            {
                "message": "Task completed",
                "task": "git push",
                "result": {
                    "status": "DONE",
                    "response": "proposal created",
                    "error": "",
                    "trace": [
                        {"action": "EXECUTIVE_DECISION", "data": {"intent": "propose_shell_command"}},
                        {"action": "OPERATOR_TOOL_RESULT", "data": {"tool": "propose_shell_command", "metadata": {"status": "pending"}}},
                        {"action": "AUDITOR_VERIFICATION", "data": {"final_status": "DONE"}},
                    ],
                },
            }
        )
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), _PolicyHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.previous_base_url = os.environ.get("HERMES_BASE_URL")
        os.environ["HERMES_BASE_URL"] = self.base_url
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes",
            timeout_seconds=2,
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

    def test_dangerous_task_is_passed_to_hermes_and_not_executed_by_mcp(self):
        response = self.client.call_tool("hermes.run_task", {"task": "幫我 git push"})

        payload = json.loads(response["content"][0]["text"])
        self.assertFalse(response["isError"])
        self.assertEqual(self.httpd.last_body["task"], "幫我 git push")
        self.assertEqual(self.httpd.last_body["provider"], "mock")
        self.assertEqual(payload["result"]["trace"][0]["data"]["intent"], "propose_shell_command")
        self.assertNotIn("execute_shell", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
