# Hermes MCP Integration Plan

## Decision

Hermes should support MCP as a governed external tool protocol.

The correct architecture is:

```text
User Command
  ↓
Hermes Runtime
  ↓
Management Decision Layer
  ↓
Risk Gate
  ↓
Operator Worker
  ↓
ToolRegistry
  ↓
MCP Gateway
  ↓
External MCP Server
  ↓
ToolResult
  ↓
Auditor
  ↓
Final Reply
```

The forbidden architecture is:

```text
User Command -> LLM -> MCP Server
```

## Initial Scope

Initial MCP support should be:

```text
Hermes as MCP Client
stdio transport
read-only first
fake gateway tests
local workspace MCP server
ToolRegistry bridge
Trace-first observability
Dashboard MCP tab
```

Out of initial scope:

- Hermes as MCP Server
- Streamable HTTP
- OAuth
- remote MCP
- write/delete/shell tool direct execution

## Module Layout

```text
hermes/mcp/
  __init__.py
  types.py
  config.py
  security.py
  client.py
  gateway.py
  registry_bridge.py
  servers/
    __init__.py
    local_workspace.py
```

## Config

Root config file:

```text
hermes_mcp.json
```

It should define:

- server name
- transport
- command
- args
- enabled flag
- allowed tools
- denied tools
- default permission
- security defaults

## Permission Classification

Default classification:

| Tool Pattern | Permission |
| --- | --- |
| read, list, get, search | read |
| write, create, update, patch, commit, merge, push | write |
| delete, remove, drop, unlink | write / blocked |
| exec, shell, command, powershell, bash | shell |
| pytest, unittest, compile | test |
| post, send, publish, upload | network |
| unknown | blocked or approval-required |

Override priority:

```text
denied_tools > allowed_tools > explicit config > auto classification > default permission
```

## Runtime Integration

Runtime should only handle lifecycle:

- detect config
- construct gateway
- start enabled servers
- register tools
- shutdown cleanly

Runtime should not contain MCP protocol details.

## Trace Events

MCP should emit:

- `MCP_SERVER_START`
- `MCP_SERVER_READY`
- `MCP_SERVER_FAILED`
- `MCP_TOOLS_DISCOVERED`
- `MCP_TOOL_REGISTERED`
- `MCP_TOOL_BLOCKED`
- `MCP_TOOL_CALL`
- `MCP_TOOL_RESULT`
- `MCP_TOOL_DENIED`
- `MCP_TOOL_APPROVAL_REQUIRED`

## Dashboard MCP Tab

Dashboard should show:

- connected MCP servers
- imported MCP tools
- permission badges
- blocked tools
- recent MCP calls
- failed MCP initialization

Suggested tabs:

```text
[ Trace ][ Tool Result ][ Patch Review ][ Files ][ MCP ][ Raw JSON ]
```

## Test Requirements

Required tests:

- config load
- security classification
- registry bridge
- fake gateway
- stdio client
- local workspace MCP server
- runtime integration
- trace events
- Dashboard MCP rendering

Full verification command:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

