import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from hermes.mcp.types import MCPServerConfig


DEFAULT_SECURITY: Dict[str, Any] = {
    "unknown_tools_default": "blocked",
    "write_tools_require_approval": True,
    "shell_tools_enabled": False,
    "network_mutation_requires_approval": True,
    "trace_all_mcp_calls": True,
}


@dataclass
class MCPConfig:
    servers: List[MCPServerConfig] = field(default_factory=list)
    security: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SECURITY))


def load_mcp_config(path: str = "hermes_mcp.json") -> MCPConfig:
    config_path = Path(path)
    if not config_path.exists():
        return MCPConfig()

    data = json.loads(config_path.read_text(encoding="utf-8"))
    security = dict(DEFAULT_SECURITY)
    security.update(data.get("security") or {})

    servers = []
    for item in data.get("servers") or []:
        servers.append(
            MCPServerConfig(
                name=item["name"],
                transport=item.get("transport", "stdio"),
                command=item.get("command"),
                args=list(item.get("args") or []),
                url=item.get("url"),
                enabled=bool(item.get("enabled", True)),
                allowed_tools=list(item.get("allowed_tools") or []),
                denied_tools=list(item.get("denied_tools") or []),
                default_permission=item.get("default_permission", "unknown"),
                tool_permissions=dict(item.get("tool_permissions") or {}),
            )
        )

    return MCPConfig(servers=servers, security=security)

