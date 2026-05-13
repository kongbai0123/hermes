import unittest

from hermes.core.types import ToolResult
from hermes.harness.tools import ToolRegistry
from hermes.mcp.registry_bridge import register_mcp_tools
from hermes.mcp.types import MCPToolDescriptor


class FakeGateway:
    def __init__(self):
        self.calls = []

    def discover_tools(self):
        return [
            MCPToolDescriptor(
                server_name="files",
                name="read_file",
                description="Read a file",
                input_schema={"type": "object"},
                permission="read",
                enabled=True,
            ),
            MCPToolDescriptor(
                server_name="files",
                name="delete_file",
                description="Delete a file",
                input_schema={"type": "object"},
                permission="disabled",
                enabled=False,
            ),
        ]

    def call(self, server_name, tool_name, arguments):
        self.calls.append((server_name, tool_name, arguments))
        return ToolResult(ok=True, tool=f"mcp.{server_name}.{tool_name}", summary="ok", content="done")


class TestMCPRegistryBridge(unittest.TestCase):
    def test_registers_enabled_read_tool_with_stable_name_and_handler(self):
        gateway = FakeGateway()
        registry = ToolRegistry()

        registered = register_mcp_tools(registry, gateway)
        tool = registry.get_tool("mcp.files.read_file")

        self.assertEqual(registered, ["mcp.files.read_file"])
        self.assertIsNotNone(tool)
        self.assertEqual(tool.permission, "read")
        result = tool.handler(path="README.md")
        self.assertTrue(result.ok)
        self.assertEqual(gateway.calls, [("files", "read_file", {"path": "README.md"})])

    def test_does_not_register_disabled_tool(self):
        gateway = FakeGateway()
        registry = ToolRegistry()

        register_mcp_tools(registry, gateway)

        self.assertIsNone(registry.get_tool("mcp.files.delete_file"))


if __name__ == "__main__":
    unittest.main()
