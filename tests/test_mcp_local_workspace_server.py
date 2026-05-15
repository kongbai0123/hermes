import os
import sys
import unittest
from pathlib import Path
from tests.support import test_workspace

from hermes.core.llm_provider import MockLLMProvider
from hermes.core.runtime import HermesRuntime
from hermes.mcp.client import MCPStdioClient


class TestMCPLocalWorkspaceServer(unittest.TestCase):
    def setUp(self):
        self.root = test_workspace("mcp_local_workspace").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "README.md").write_text("# MCP Workspace\nHermes MCP read works.", encoding="utf-8")
        (self.root / ".env").write_text("SECRET=blocked", encoding="utf-8")
        self.previous_workspace = os.environ.get("HERMES_WORKSPACE")
        os.environ["HERMES_WORKSPACE"] = str(self.root)

    def tearDown(self):
        if self.previous_workspace is None:
            os.environ.pop("HERMES_WORKSPACE", None)
        else:
            os.environ["HERMES_WORKSPACE"] = self.previous_workspace

    def test_builtin_workspace_mcp_server_reads_file_and_blocks_sensitive_file(self):
        client = MCPStdioClient(
            command=sys.executable,
            args=["-m", "hermes.mcp.servers.local_workspace"],
            server_name="local_workspace",
            timeout_seconds=2,
        )

        try:
            client.start()
            client.initialize()
            tools = client.list_tools()
            read_result = client.call_tool("read_file", {"path": "README.md"})
            blocked_result = client.call_tool("read_file", {"path": ".env"})
        finally:
            client.stop()

        self.assertEqual([tool["name"] for tool in tools], ["list_files", "read_file", "search_files"])
        self.assertIn("Hermes MCP read works", read_result["content"][0]["text"])
        self.assertIn("Access Denied", blocked_result["content"][0]["text"])

    def test_runtime_executes_mcp_read_file_through_management_loop(self):
        config_path = self.root / "hermes_mcp.json"
        config_path.write_text(
            f"""{{
  "servers": [
    {{
      "name": "local_workspace",
      "transport": "stdio",
      "command": "{sys.executable.replace("\\", "\\\\")}",
      "args": ["-m", "hermes.mcp.servers.local_workspace"],
      "enabled": true,
      "default_permission": "read",
      "allowed_tools": ["list_files", "read_file", "search_files"],
      "denied_tools": ["write_file", "delete_file"]
    }}
  ]
}}""",
            encoding="utf-8",
        )

        runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path=str(config_path))
        try:
            result = runtime.execute_task("請用 MCP 讀取 README.md")
        finally:
            runtime.shutdown()

        self.assertEqual(result["status"], "DONE")
        actions = [trace["action"] for trace in result["trace"]]
        self.assertIn("MCP_SERVER_READY", actions)
        self.assertIn("MCP_TOOL_REGISTERED", actions)
        self.assertIn("OPERATOR_TOOL_CALL", actions)
        self.assertIn("MCP_TOOL_CALL", actions)
        strategy = next(trace for trace in result["trace"] if trace["action"] == "STRATEGY_PLAN")
        self.assertIn("mcp.local_workspace.read_file", str(strategy["data"]))
        tool_result = next(trace for trace in result["trace"] if trace["action"] == "OPERATOR_TOOL_RESULT")
        self.assertIn("Hermes MCP read works", tool_result["data"]["content"])


if __name__ == "__main__":
    unittest.main()
