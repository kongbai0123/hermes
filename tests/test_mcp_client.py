import sys
import unittest
from pathlib import Path

from hermes.mcp.client import MCPStdioClient


class TestMCPStdioClient(unittest.TestCase):
    def setUp(self):
        self.server_script = Path("tests/mcp_echo_server.py").resolve()

    def test_stdio_client_initializes_lists_tools_and_calls_tool(self):
        client = MCPStdioClient(
            command=sys.executable,
            args=[str(self.server_script)],
            server_name="echo",
            timeout_seconds=2,
        )

        try:
            client.start()
            init_result = client.initialize()
            tools = client.list_tools()
            call_result = client.call_tool("read_note", {"path": "README.md"})
        finally:
            client.stop()

        self.assertEqual(init_result["serverInfo"]["name"], "echo-mcp")
        self.assertEqual([tool["name"] for tool in tools], ["read_note", "delete_note"])
        self.assertIn("read_note", call_result["content"][0]["text"])

    def test_stdio_client_raises_on_json_rpc_error(self):
        client = MCPStdioClient(
            command=sys.executable,
            args=[str(self.server_script)],
            server_name="echo",
            timeout_seconds=2,
        )

        try:
            client.start()
            client.initialize()
            with self.assertRaises(RuntimeError) as context:
                client.call_tool("fail", {})
        finally:
            client.stop()

        self.assertIn("forced failure", str(context.exception))


if __name__ == "__main__":
    unittest.main()
