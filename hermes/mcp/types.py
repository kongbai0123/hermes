from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

MCPTransport = Literal["stdio", "streamable_http"]

MCPPermission = Literal[
    "read",
    "write_proposal",
    "write",
    "network",
    "shell",
    "test",
    "unknown",
    "disabled",
]


@dataclass
class MCPServerConfig:
    name: str
    transport: MCPTransport
    command: Optional[str] = None
    args: list[str] = field(default_factory=list)
    url: Optional[str] = None
    enabled: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    denied_tools: list[str] = field(default_factory=list)
    default_permission: MCPPermission = "unknown"
    tool_permissions: Dict[str, MCPPermission] = field(default_factory=dict)


@dataclass
class MCPToolDescriptor:
    server_name: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    permission: MCPPermission = "unknown"
    enabled: bool = True

