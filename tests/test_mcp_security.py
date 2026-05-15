import unittest

from hermes.mcp.security import classify_mcp_tool, resolve_mcp_permission
from hermes.mcp.types import MCPServerConfig


class TestMCPSecurity(unittest.TestCase):
    def test_classifies_read_write_shell_test_and_network_tools(self):
        self.assertEqual(classify_mcp_tool("fs", "read_file"), "read")
        self.assertEqual(classify_mcp_tool("github", "list_issues"), "read")
        self.assertEqual(classify_mcp_tool("github", "create_issue"), "write")
        self.assertEqual(classify_mcp_tool("fs", "delete_file"), "write")
        self.assertEqual(classify_mcp_tool("local", "run_command"), "shell")
        self.assertEqual(classify_mcp_tool("python", "run_pytest"), "test")
        self.assertEqual(classify_mcp_tool("web", "upload_artifact"), "network")

    def test_denied_tools_override_allowed_tools(self):
        server = MCPServerConfig(
            name="fs",
            transport="stdio",
            allowed_tools=["read_file"],
            denied_tools=["read_file"],
            default_permission="read",
        )

        permission, enabled = resolve_mcp_permission(server, "read_file", "Read file")

        self.assertEqual(permission, "disabled")
        self.assertFalse(enabled)

    def test_allowed_tools_can_override_write_classification_to_read_only_scope(self):
        server = MCPServerConfig(
            name="audit",
            transport="stdio",
            allowed_tools=["create_report"],
            default_permission="unknown",
        )

        permission, enabled = resolve_mcp_permission(server, "create_report", "Generate local report preview")

        self.assertEqual(permission, "read")
        self.assertTrue(enabled)

    def test_unknown_default_blocks_unlisted_unknown_tool(self):
        server = MCPServerConfig(
            name="custom",
            transport="stdio",
            default_permission="unknown",
        )

        permission, enabled = resolve_mcp_permission(server, "mystery", "")

        self.assertEqual(permission, "disabled")
        self.assertFalse(enabled)


if __name__ == "__main__":
    unittest.main()
