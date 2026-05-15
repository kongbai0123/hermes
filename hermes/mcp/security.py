from hermes.mcp.types import MCPPermission, MCPServerConfig


READ_KEYWORDS = [
    "read",
    "list",
    "get",
    "fetch",
    "search",
    "find",
    "inspect",
    "query",
]

WRITE_KEYWORDS = [
    "delete",
    "remove",
    "drop",
    "destroy",
    "unlink",
    "write",
    "create",
    "update",
    "patch",
    "commit",
    "merge",
    "push",
]

SHELL_KEYWORDS = [
    "exec",
    "shell",
    "command",
    "powershell",
    "bash",
    "terminal",
]

TEST_KEYWORDS = [
    "test",
    "pytest",
    "unittest",
    "compile",
]

NETWORK_KEYWORDS = [
    "post",
    "send",
    "publish",
    "upload",
    "download",
]


def classify_mcp_tool(server_name: str, tool_name: str, description: str = "") -> MCPPermission:
    text = f"{server_name}.{tool_name} {description}".lower()

    if any(keyword in text for keyword in WRITE_KEYWORDS):
        return "write"
    if any(keyword in text for keyword in SHELL_KEYWORDS):
        return "shell"
    if any(keyword in text for keyword in TEST_KEYWORDS):
        return "test"
    if any(keyword in text for keyword in NETWORK_KEYWORDS):
        return "network"
    if any(keyword in text for keyword in READ_KEYWORDS):
        return "read"
    return "unknown"


def resolve_mcp_permission(
    server: MCPServerConfig,
    tool_name: str,
    description: str = "",
) -> tuple[MCPPermission, bool]:
    if tool_name in server.denied_tools:
        return "disabled", False

    if tool_name in server.allowed_tools:
        return "read", True

    if tool_name in server.tool_permissions:
        permission = server.tool_permissions[tool_name]
    else:
        permission = classify_mcp_tool(server.name, tool_name, description)
        if permission == "unknown":
            permission = server.default_permission

    if permission in {"unknown", "disabled", "write", "write_proposal", "shell", "network"}:
        return "disabled", False

    return permission, True

