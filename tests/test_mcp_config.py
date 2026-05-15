import json
import unittest
from pathlib import Path

from hermes.mcp.config import MCPConfig, load_mcp_config


class TestMCPConfig(unittest.TestCase):
    def test_loads_servers_and_security_defaults(self):
        config_dir = Path("tests/mcp_config_workspace")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "hermes_mcp.json"
        config_path.write_text(
            json.dumps(
                {
                    "servers": [
                        {
                            "name": "local_filesystem",
                            "transport": "stdio",
                            "command": "python",
                            "args": ["-m", "fake_server"],
                            "enabled": True,
                            "default_permission": "read",
                            "allowed_tools": ["read_file"],
                            "denied_tools": ["delete_file"],
                        },
                        {
                            "name": "github",
                            "transport": "stdio",
                            "command": "npx",
                            "enabled": False,
                        },
                    ],
                    "security": {
                        "unknown_tools_default": "blocked",
                        "trace_all_mcp_calls": True,
                    },
                }
            ),
            encoding="utf-8",
        )

        config = load_mcp_config(str(config_path))

        self.assertIsInstance(config, MCPConfig)
        self.assertEqual(len(config.servers), 2)
        self.assertEqual(config.servers[0].name, "local_filesystem")
        self.assertEqual(config.servers[0].allowed_tools, ["read_file"])
        self.assertEqual(config.servers[0].denied_tools, ["delete_file"])
        self.assertFalse(config.servers[1].enabled)
        self.assertEqual(config.security["unknown_tools_default"], "blocked")

    def test_missing_config_returns_empty_config(self):
        config = load_mcp_config("missing-hermes-mcp.json")

        self.assertEqual(config.servers, [])
        self.assertEqual(config.security["unknown_tools_default"], "blocked")


if __name__ == "__main__":
    unittest.main()
