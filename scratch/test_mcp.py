import json
import os
from pathlib import Path
from hermes.mcp.config import load_mcp_config
from hermes.mcp.gateway import MCPGateway

PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("HERMES_WORKSPACE", str(PROJECT_ROOT))
config_path = PROJECT_ROOT / "hermes_mcp.json"

print(f"Loading config from {config_path}")
config = load_mcp_config(str(config_path))
print(f"Config loaded. Servers: {[s.name for s in config.servers]}")

gateway = MCPGateway(config)
print("Starting servers...")
gateway.start_enabled_servers()

print("Discovering tools...")
tools = gateway.discover_tools()
print(f"Discovered {len(tools)} tools.")
for tool in tools:
    print(f" - {tool.name} (server: {tool.server_name}, enabled: {tool.enabled})")

if any(t.name == "list_files" for t in tools):
    print("Calling list_files tool...")
    result = gateway.call("local_workspace", "list_files", {"path": "."})
    print(f"Result (ok={result.ok}):")
    print(result.content)
else:
    print("list_files tool not found.")

print("Shutting down...")
gateway.shutdown()
