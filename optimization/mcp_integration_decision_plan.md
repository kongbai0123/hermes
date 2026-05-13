# Hermes MCP Integration Decision Plan

建立日期：2026-05-13

## 1. 決策結論

Hermes 下一階段可以導入 MCP，但 MCP 必須被 Hermes 管理，而不是讓 MCP 管理 Hermes。

本計畫採用：

```text
Hermes as MCP Client
+ stdio transport
+ read-only first
+ ToolRegistry bridge
+ Management Decision Layer governance
+ Trace-first observability
```

暫不做：

```text
Hermes as MCP Server
Streamable HTTP
OAuth
Remote MCP Server
write/shell/delete 類 MCP tool 直通
```

核心原則：

```text
MCP = 外部工具協議層
ToolRegistry = Hermes 工具入口
Management Layer = 權限與風險治理
Auditor = 驗證與稽核
Dashboard = 可觀測介面
```

禁止架構：

```text
User Command -> LLM -> MCP Server
```

允許架構：

```text
User Command
-> HermesRuntime
-> Management Decision Layer
-> Risk Gate
-> Operator Worker
-> ToolRegistry
-> MCP Gateway
-> External MCP Server
-> ToolResult
-> Auditor
-> Final Reply
```

## 2. 任務目標

實作 Hermes MCP Integration Layer，讓 Hermes 能安全連接外部 MCP Server，探索 tools/list，將 MCP tools 轉換成 Hermes `ToolSpec`，並在受治理的情況下呼叫 read-only MCP tools。

完成後 Hermes 應能：

- 讀取 `hermes_mcp.json`。
- 啟動 enabled stdio MCP server。
- 呼叫 `initialize`、`tools/list`、`tools/call`。
- 將 MCP tools 轉成 `mcp.<server>.<tool>` 格式的 Hermes ToolSpec。
- 根據 permission 與 security policy 阻擋 unsafe tools。
- 讓 read-only MCP tool 由 Operator 透過 ToolRegistry 執行。
- 將 MCP response 轉成 `ToolResult`。
- 將所有 MCP events 寫入 Trace Timeline。
- 在 Dashboard 顯示 MCP servers、tools、recent calls。

## 3. 嚴格限制

初版必須遵守：

```text
1. 不開放 shell 類 MCP tool。
2. 不開放 delete 類 MCP tool。
3. 不直接執行 write 類 MCP tool。
4. unknown tool 預設 blocked。
5. MCP tool 不得繞過 ToolRegistry。
6. MCP tool 不得繞過 Management Decision Layer。
7. MCP tool 不得繞過 Trace。
8. MCP server 啟動失敗不得讓 Hermes crash。
9. 不把 MCP config 寫死在程式碼。
10. 不依賴外部 MCP server 才能通過測試。
```

## 4. 建議新增檔案

```text
hermes/mcp/
  __init__.py
  types.py
  config.py
  security.py
  client.py
  gateway.py
  registry_bridge.py

tests/
  test_mcp_config.py
  test_mcp_security.py
  test_mcp_gateway.py
  test_mcp_registry_bridge.py
  test_mcp_runtime_integration.py
```

## 5. 檔案職責

| 檔案 | 職責 |
| :--- | :--- |
| `types.py` | 定義 MCP server config、tool descriptor、permission types |
| `config.py` | 讀取與驗證 `hermes_mcp.json` |
| `security.py` | MCP tool 分類、allow/deny、risk mapping |
| `client.py` | stdio MCP client，處理 initialize、tools/list、tools/call |
| `gateway.py` | 管理 servers、tool discovery、tool call、ToolResult 轉換 |
| `registry_bridge.py` | 將 MCP tools 註冊到 Hermes ToolRegistry |
| `runtime.py` | 最小侵入載入 MCP Gateway 與註冊 tools |
| `dashboard.html` | 新增 MCP tab 顯示 server/tool/call 狀態 |

## 6. 設定檔設計

專案根目錄支援：

```text
hermes_mcp.json
```

初版範例：

```json
{
  "servers": [
    {
      "name": "local_filesystem",
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "mcp_server_filesystem"],
      "enabled": false,
      "default_permission": "read",
      "allowed_tools": ["list_directory", "read_file", "search_files"],
      "denied_tools": ["write_file", "delete_file", "move_file"]
    }
  ],
  "security": {
    "unknown_tools_default": "blocked",
    "write_tools_require_approval": true,
    "shell_tools_enabled": false,
    "network_mutation_requires_approval": true,
    "trace_all_mcp_calls": true
  }
}
```

初版建議：預設所有 server `enabled=false`，測試用 fake gateway，不依賴真外部服務。

## 7. Permission 與 Security 決策

MCP permission：

```text
read
write_proposal
write
network
shell
test
unknown
disabled
```

分類規則：

| 工具關鍵字 | permission |
| :--- | :--- |
| `delete/remove/drop/destroy/unlink` | `write`，初版 blocked |
| `write/create/update/patch/commit/merge/push` | `write`，初版 blocked |
| `exec/shell/command/powershell/bash/terminal` | `shell`，blocked |
| `test/pytest/unittest/compile` | `test` |
| `post/send/publish/upload/download` | `network`，mutation 需 approval |
| 其他已知安全查詢 | `read` |
| 未知 | `unknown`，blocked |

Config override 優先順序：

```text
denied_tools > allowed_tools > explicit permission override > auto classification > default permission
```

## 8. ToolRegistry Bridge 決策

MCP tool 註冊命名：

```text
mcp.<server_name>.<tool_name>
```

範例：

```text
mcp.local_filesystem.read_file
mcp.local_filesystem.list_directory
mcp.github.get_issue
```

Bridge 必須：

- 只註冊 enabled 且非 blocked 的 MCP tools。
- 將 MCP permission 映射成 Hermes `ToolSpec.permission`。
- handler 只能呼叫 `MCPGateway.call(server_name, tool_name, kwargs)`。
- 使用 `make_handler()` 避免 Python late binding bug。

## 9. Trace 決策

新增 MCP trace events：

```text
MCP_CONFIG_LOADED
MCP_SERVER_START
MCP_SERVER_READY
MCP_SERVER_FAILED
MCP_TOOLS_DISCOVERED
MCP_TOOL_REGISTERED
MCP_TOOL_BLOCKED
MCP_TOOL_CALL
MCP_TOOL_RESULT
MCP_TOOL_DENIED
MCP_TOOL_APPROVAL_REQUIRED
```

所有 MCP call 必須包含：

```json
{
  "server": "local_filesystem",
  "tool": "read_file",
  "permission": "read",
  "args": {}
}
```

## 10. Management Layer 整合

Executive Director 需要新增判斷欄位：

```text
requires_mcp: true / false
external_tool_risk: low / medium / high
```

Strategy Manager 可以產生：

```json
{
  "id": "S1",
  "type": "read",
  "tool": "mcp.github.get_issue",
  "args": {
    "owner": "kongbai0123",
    "repo": "hermes",
    "issue_number": 12
  },
  "reason": "讀取 GitHub issue 以理解需求",
  "expected": "取得 issue title/body/comments"
}
```

Operator 不需要知道工具是否來自 MCP；它只呼叫 ToolRegistry。

Auditor 必須檢查：

- MCP tool 是否在允許清單。
- MCP tool permission 是否符合 task risk。
- MCP call 是否有 ToolResult。
- 高風險 MCP tool 是否被阻擋或轉 proposal。
- 最終回答是否根據實際 MCP result。

## 11. Dashboard 決策

底部 tabs 新增：

```text
[ Trace ][ Tool Result ][ Patch Review ][ Files ][ Logs ][ MCP ]
```

MCP tab 顯示：

```text
Connected MCP Servers
- local_filesystem: connected / disabled / failed

Imported MCP Tools
- mcp.local_filesystem.read_file       read
- mcp.local_filesystem.write_file      blocked

Recent MCP Calls
- S1 mcp.local_filesystem.read_file ok 90ms
```

若 MCP tool 被阻擋，主回覆區應顯示：

```text
MCP Tool Blocked
Tool: mcp.github.create_pull_request
Reason: write_external requires approval
Suggested action: create ExternalActionProposal
```

## 12. Phase Plan

### P0：MCP Config + Types + Security + Bridge

目標：不啟動真 MCP server，也能完成設定讀取、權限分類、fake gateway、ToolRegistry 註冊。

任務：

- [ ] 建立 `hermes/mcp/types.py`
- [ ] 建立 `hermes/mcp/config.py`
- [ ] 建立 `hermes/mcp/security.py`
- [ ] 建立 `hermes/mcp/registry_bridge.py`
- [ ] 建立 fake MCP gateway 測試
- [ ] 測試 unknown/write/shell/delete 類 tool 不註冊或 blocked

驗收：

```powershell
python -m unittest tests.test_mcp_config
python -m unittest tests.test_mcp_security
python -m unittest tests.test_mcp_registry_bridge
```

### P1：MCP Client + Gateway + Trace

目標：完成 stdio client 與 gateway 抽象，但測試仍以 fake client 為主。

任務：

- [ ] 建立 `MCPStdioClient.start()`
- [ ] 建立 `initialize()`
- [ ] 建立 `list_tools()`
- [ ] 建立 `call_tool()`
- [ ] 建立 `stop()`
- [ ] `MCPGateway.call()` 將 response 轉成 `ToolResult`
- [ ] MCP server 啟動失敗只寫 Trace，不 crash

驗收：

```powershell
python -m unittest tests.test_mcp_gateway
```

### P2：Runtime + Management + Auditor

目標：HermesRuntime 啟動時載入 MCP config，將 read-only MCP tools 放入 ToolRegistry，並讓 Management Layer 可以使用。

任務：

- [ ] `HermesRuntime.__init__()` 加入 `self.mcp_gateway = None`
- [ ] 偵測 `hermes_mcp.json`
- [ ] 初始化 MCPGateway 失敗時寫 Trace
- [ ] 註冊 read-only MCP tools
- [ ] Auditor 加入 MCP permission 檢查
- [ ] Runtime 測試 MCP 初始化失敗不 crash

驗收：

```powershell
python -m unittest tests.test_mcp_runtime_integration
```

### P3：Dashboard MCP Tab

目標：使用者可以看到 MCP server 狀態、imported tools、recent calls。

任務：

- [ ] Dashboard tabs 新增 `MCP`
- [ ] 顯示 connected/disabled/failed servers
- [ ] 顯示 imported/blocked tools
- [ ] 顯示 recent MCP calls
- [ ] MCP blocked 時主回覆區顯示原因

驗收：

```powershell
python -m unittest tests.test_dashboard
```

### P4：ExternalActionProposal

目標：未來支援 write/network mutation，但必須走 approval flow。

任務：

- [ ] 定義 `ExternalActionProposal`
- [ ] write/shell/network mutation MCP tool 轉 proposal
- [ ] Dashboard 顯示 approval panel
- [ ] 使用者批准後才呼叫 MCP tool

本階段不在 P0/P1 初版中實作。

## 13. 測試總命令

每個階段完成後都必須執行：

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

完成標準：

```text
所有測試通過
MCP read-only tools 可註冊
write/shell/delete tools blocked
MCP calls 有 Trace
Runtime 初始化失敗不 crash
Dashboard 可看到 MCP 狀態
```

## 14. 已知限制

- 初版不支援 remote MCP。
- 初版不支援 OAuth。
- 初版不支援 Hermes as MCP Server。
- 初版不直接執行 write/shell/delete/network mutation tools。
- 初版以 fake MCP client/gateway 測試為主，避免外部 server 造成不穩定。

## 15. 建議 Commit Message

```text
feat(mcp): add governed MCP gateway for read-only external tools
```

說明：

```text
- add MCP config and type definitions
- add MCP security classifier
- add MCP gateway abstraction
- bridge MCP tools into Hermes ToolRegistry
- block write/shell/delete tools by default
- add tests for MCP config, security and registry bridge
```

## 16. 給執行代理的指令

執行此計畫時必須：

```text
1. 先檢查 Hermes repo 結構。
2. 不重構無關檔案。
3. 優先新增 hermes/mcp/。
4. 先用 fake MCP client 完成測試。
5. 所有新增功能都必須有 unittest。
6. 不啟用 shell/write/delete 類 MCP tool。
7. 修改 runtime.py 時保持最小侵入。
8. MCP tool 必須經 ToolRegistry 註冊。
9. MCP tool result 必須轉成 ToolResult。
10. MCP call 必須寫入 Monitor Trace。
11. 完成後執行完整 unittest。
```

## 17. 下一步

建議下一次實作從 P0 開始：

```text
types.py
config.py
security.py
registry_bridge.py
fake MCP gateway tests
```

P0 完成後再進入 stdio client，避免一開始就被外部 MCP server、npx、網路、stdio streaming 細節拖住。
