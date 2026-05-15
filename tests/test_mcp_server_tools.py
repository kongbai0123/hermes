import json
import sys
import unittest

from hermes.mcp.client import MCPStdioClient


class TestHermesMCPServerTools(unittest.TestCase):
    def setUp(self):
        self.client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp_server.server"],
            server_name="hermes",
            timeout_seconds=2,
        )

    def tearDown(self):
        self.client.stop()

    def test_initialize_and_list_only_high_level_tools(self):
        self.client.start()
        init_result = self.client.initialize()
        tools = self.client.list_tools()

        self.assertEqual(init_result["serverInfo"]["name"], "hermes-mcp-server")
        self.assertEqual(
            [tool["name"] for tool in tools],
            ["hermes.run_task", "hermes.get_status", "hermes.get_trace"],
        )

    def test_unknown_tool_returns_structured_error(self):
        self.client.start()
        self.client.initialize()

        with self.assertRaises(RuntimeError) as context:
            self.client.call_tool("hermes.nope", {})

        self.assertIn("Unknown tool", str(context.exception))

    def test_dangerous_low_level_tools_are_not_exposed(self):
        self.client.start()
        self.client.initialize()
        tools = self.client.list_tools()

        tool_names = [tool["name"] for tool in tools]
        self.assertNotIn("hermes.execute_shell", tool_names)
        self.assertNotIn("hermes.delete_file", tool_names)
        self.assertNotIn("hermes.git_push", tool_names)


if __name__ == "__main__":
    unittest.main()
