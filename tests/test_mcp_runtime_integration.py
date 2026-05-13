import json
import sys
import unittest
from pathlib import Path

from hermes.core.llm_provider import MockLLMProvider
from hermes.core.runtime import HermesRuntime


class TestMCPRuntimeIntegration(unittest.TestCase):
    def setUp(self):
        self.config_dir = Path("tests/mcp_runtime_workspace")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.server_script = Path("tests/mcp_echo_server.py").resolve()

    def test_runtime_loads_mcp_config_and_registers_read_only_tools(self):
        config_path = self.config_dir / "hermes_mcp.json"
        config_path.write_text(
            json.dumps(
                {
                    "servers": [
                        {
                            "name": "echo",
                            "transport": "stdio",
                            "command": sys.executable,
                            "args": [str(self.server_script)],
                            "enabled": True,
                            "default_permission": "read",
                            "denied_tools": ["delete_note"],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path=str(config_path))
        try:
            read_tool = runtime.tools.get_tool("mcp.echo.read_note")
            blocked_tool = runtime.tools.get_tool("mcp.echo.delete_note")

            self.assertIsNotNone(runtime.mcp_gateway)
            self.assertIsNotNone(read_tool)
            self.assertEqual(read_tool.permission, "read")
            self.assertIsNone(blocked_tool)
            result = read_tool.handler(path="README.md")
            self.assertTrue(result.ok)
            self.assertEqual(result.tool, "mcp.echo.read_note")
        finally:
            runtime.shutdown()

    def test_runtime_mcp_initialization_failure_does_not_crash(self):
        config_path = self.config_dir / "broken_hermes_mcp.json"
        config_path.write_text(
            json.dumps(
                {
                    "servers": [
                        {
                            "name": "broken",
                            "transport": "stdio",
                            "command": sys.executable,
                            "args": ["missing_mcp_server.py"],
                            "enabled": True,
                            "default_permission": "read",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path=str(config_path))
        try:
            self.assertIsNotNone(runtime.mcp_gateway)
            result = runtime.execute_task("你好")
            self.assertEqual(result["status"], "DONE")
        finally:
            runtime.shutdown()


if __name__ == "__main__":
    unittest.main()
