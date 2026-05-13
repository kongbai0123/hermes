import unittest

from hermes.mcp.gateway import MCPGateway
from hermes.mcp.types import MCPServerConfig


class FakeMCPClient:
    def __init__(self, tools=None, response=None, fail_initialize=False, fail_call=False):
        self.started = False
        self.tools = tools or []
        self.response = response or {"content": [{"type": "text", "text": "ok"}]}
        self.fail_initialize = fail_initialize
        self.fail_call = fail_call

    def start(self):
        self.started = True

    def initialize(self):
        if self.fail_initialize:
            raise RuntimeError("boom")
        return {"serverInfo": {"name": "fake"}}

    def list_tools(self):
        return self.tools

    def call_tool(self, name, arguments):
        if self.fail_call:
            raise RuntimeError("call failed")
        return self.response

    def stop(self):
        self.started = False


class TestMCPGateway(unittest.TestCase):
    def test_discovers_tools_with_resolved_permissions(self):
        config = MCPServerConfig(
            name="files",
            transport="stdio",
            enabled=True,
            command="python",
            default_permission="read",
            denied_tools=["delete_file"],
        )
        client = FakeMCPClient(
            tools=[
                {"name": "read_file", "description": "Read file", "inputSchema": {"type": "object"}},
                {"name": "delete_file", "description": "Delete file", "inputSchema": {"type": "object"}},
            ]
        )
        gateway = MCPGateway([config], client_factory=lambda server: client)

        gateway.start_enabled_servers()
        tools = gateway.discover_tools()

        self.assertEqual([tool.name for tool in tools], ["read_file", "delete_file"])
        self.assertTrue(tools[0].enabled)
        self.assertEqual(tools[0].permission, "read")
        self.assertFalse(tools[1].enabled)
        self.assertEqual(tools[1].permission, "disabled")

    def test_call_converts_mcp_response_to_tool_result(self):
        config = MCPServerConfig(name="files", transport="stdio", command="python")
        gateway = MCPGateway([config], client_factory=lambda server: FakeMCPClient())
        gateway.start_enabled_servers()

        result = gateway.call("files", "read_file", {"path": "README.md"})

        self.assertTrue(result.ok)
        self.assertEqual(result.tool, "mcp.files.read_file")
        self.assertEqual(result.content, "ok")

    def test_call_failure_returns_failed_tool_result(self):
        config = MCPServerConfig(name="files", transport="stdio", command="python")
        gateway = MCPGateway([config], client_factory=lambda server: FakeMCPClient(fail_call=True))
        gateway.start_enabled_servers()

        result = gateway.call("files", "read_file", {"path": "README.md"})

        self.assertFalse(result.ok)
        self.assertEqual(result.tool, "mcp.files.read_file")
        self.assertIn("call failed", result.error)


if __name__ == "__main__":
    unittest.main()
