# Hermes MCP Closed Loop Test Plan

建立日期：2026-05-13

## 目標

驗證 Hermes MCP 功能不是只有模組存在，而是能完成以下閉環：

```text
hermes_mcp.json
-> MCP stdio server 啟動
-> tools/list discovery
-> ToolRegistry 註冊 mcp.<server>.<tool>
-> Management Decision Layer 規劃 MCP execution step
-> Operator 呼叫 MCP tool
-> MCP ToolResult 回到 Runtime
-> Auditor 驗證
-> Dashboard MCP tab 顯示 server/tool/call
```

## 測試範圍

- 內建 read-only MCP server：`hermes.mcp.servers.local_workspace`
- MCP tools：
  - `list_files`
  - `read_file`
  - `search_files`
- 禁止工具：
  - `write_file`
  - `delete_file`
  - `move_file`
  - `run_command`

## 驗收條件

- `python -m unittest discover -s tests -p "test_*.py"` 通過。
- API 任務 `請用 MCP 讀取 README.md` 回傳 `DONE`。
- Trace 包含：
  - `MCP_SERVER_READY`
  - `MCP_TOOL_REGISTERED`
  - `MCP_TOOL_CALL`
  - `MCP_TOOL_RESULT`
  - `AUDITOR_VERIFICATION`
- Dashboard MCP tab 顯示 `local_workspace` 與 read-only tools。

## 已知限制

- 目前只開 read-only MCP。
- shell/write/delete MCP tool 仍需 proposal/approval flow。
- 遠端 MCP、OAuth、HTTP transport 尚未實作。
