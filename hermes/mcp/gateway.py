from typing import Callable, Iterable, Optional

from hermes.core.types import ToolResult
from hermes.mcp.config import MCPConfig
from hermes.mcp.security import resolve_mcp_permission
from hermes.mcp.types import MCPServerConfig, MCPToolDescriptor


class MCPGateway:
    def __init__(
        self,
        configs: MCPConfig | Iterable[MCPServerConfig],
        monitor=None,
        client_factory: Optional[Callable[[MCPServerConfig], object]] = None,
    ):
        self.configs = list(configs.servers if isinstance(configs, MCPConfig) else configs)
        self.monitor = monitor
        self.client_factory = client_factory
        self.clients = {}
        self.tools = {}

    def start_enabled_servers(self) -> None:
        for server in self.configs:
            if not server.enabled:
                self._trace("MCP_SERVER_DISABLED", {"server": server.name})
                continue
            try:
                client = self._create_client(server)
                client.start()
                try:
                    client.initialize()
                    self._trace("MCP_SERVER_READY", {"server": server.name})
                    self.clients[server.name] = client
                except Exception as exc:
                    self._trace("MCP_SERVER_FAILED", {"server": server.name, "error": str(exc)})
                    client.stop()
            except Exception as exc:
                self._trace("MCP_SERVER_FAILED", {"server": server.name, "error": str(exc)})

    def discover_tools(self) -> list[MCPToolDescriptor]:
        discovered: list[MCPToolDescriptor] = []
        for server in self.configs:
            client = self.clients.get(server.name)
            if not server.enabled or client is None:
                continue
            try:
                raw_tools = client.list_tools()
            except Exception as exc:
                self._trace("MCP_TOOLS_DISCOVERY_FAILED", {"server": server.name, "error": str(exc)})
                continue

            for raw_tool in raw_tools:
                name = raw_tool.get("name", "")
                description = raw_tool.get("description", "")
                permission, enabled = resolve_mcp_permission(server, name, description)
                descriptor = MCPToolDescriptor(
                    server_name=server.name,
                    name=name,
                    description=description,
                    input_schema=raw_tool.get("inputSchema") or raw_tool.get("input_schema") or {},
                    permission=permission,
                    enabled=enabled,
                )
                discovered.append(descriptor)
                self.tools[f"{server.name}.{name}"] = descriptor
                self._trace(
                    "MCP_TOOL_REGISTERED" if enabled else "MCP_TOOL_BLOCKED",
                    {
                        "server": server.name,
                        "tool": name,
                        "permission": permission,
                    },
                )

        self._trace("MCP_TOOLS_DISCOVERED", {"count": len(discovered)})
        return discovered

    def call(self, server_name: str, tool_name: str, arguments: dict) -> ToolResult:
        tool_id = f"mcp.{server_name}.{tool_name}"
        client = self.clients.get(server_name)
        if client is None:
            return ToolResult(ok=False, tool=tool_id, summary="MCP server unavailable", error=f"Server {server_name} is not started.")

        self._trace("MCP_TOOL_CALL", {"server": server_name, "tool": tool_name, "args": arguments})
        try:
            response = client.call_tool(tool_name, arguments)
            result = ToolResult(
                ok=True,
                tool=tool_id,
                summary="MCP tool call succeeded",
                content=self._extract_text_content(response),
                metadata={"server": server_name, "raw": response},
            )
        except Exception as exc:
            result = ToolResult(ok=False, tool=tool_id, summary="MCP tool call failed", error=str(exc), metadata={"server": server_name})

        self._trace(
            "MCP_TOOL_RESULT",
            {
                "server": server_name,
                "tool": tool_name,
                "ok": result.ok,
                "summary": result.summary,
                "error": result.error,
            },
        )
        return result

    def shutdown(self) -> None:
        for server_name, client in list(self.clients.items()):
            try:
                client.stop()
                self._trace("MCP_SERVER_STOPPED", {"server": server_name})
            except Exception as exc:
                self._trace("MCP_SERVER_FAILED", {"server": server_name, "error": str(exc)})
        self.clients.clear()

    def _create_client(self, server: MCPServerConfig):
        if self.client_factory:
            return self.client_factory(server)
        from hermes.mcp.client import MCPStdioClient

        if server.transport != "stdio":
            raise ValueError(f"Unsupported MCP transport: {server.transport}")
        if not server.command:
            raise ValueError(f"MCP server {server.name} has no command")
        return MCPStdioClient(server.command, server.args, server.name)

    def _trace(self, action: str, data: dict) -> None:
        if self.monitor and hasattr(self.monitor, "add_trace"):
            self.monitor.add_trace("MCP", action, data)

    def _extract_text_content(self, response: dict) -> str:
        content = response.get("content") if isinstance(response, dict) else None
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "\n".join(part for part in parts if part)
        if isinstance(response, dict) and "text" in response:
            return str(response["text"])
        return str(response)
