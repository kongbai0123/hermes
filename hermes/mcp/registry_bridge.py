from hermes.harness.tools import ToolSpec


def register_mcp_tools(tool_registry, mcp_gateway) -> list[str]:
    registered = []
    for mcp_tool in mcp_gateway.discover_tools():
        if not mcp_tool.enabled or mcp_tool.permission == "disabled":
            continue

        hermes_tool_name = f"mcp.{mcp_tool.server_name}.{mcp_tool.name}"

        def make_handler(server_name: str, tool_name: str):
            def handler(**kwargs):
                return mcp_gateway.call(server_name, tool_name, kwargs)

            return handler

        tool_registry.add_tool(
            ToolSpec(
                name=hermes_tool_name,
                description=f"[MCP:{mcp_tool.server_name}] {mcp_tool.description}",
                permission=mcp_tool.permission,
                handler=make_handler(mcp_tool.server_name, mcp_tool.name),
            )
        )
        registered.append(hermes_tool_name)
    return registered

