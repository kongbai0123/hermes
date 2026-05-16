# 🌐 Hermes MCP Server 使用指南

Hermes 提供了一個 Model Context Protocol (MCP) 橋接伺服器，讓您可以透過支持 MCP 的客戶端（如 Claude Code、Cursor）直接調用 Hermes 的自主代理能力與治理工具。

## 🚀 快速啟動

### 1. 啟動 Hermes 核心服務
MCP 伺服器依賴 Hermes 的 HTTP API，請先啟動主程序：
```bash
python start_hermes.py
# 預設運行於 http://localhost:8000
```

### 2. 在 MCP 客戶端中配置 Hermes
將以下配置加入您的 MCP 客戶端設定檔（例如 `claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "hermes": {
      "command": "python",
      "args": ["-m", "hermes.mcp_server.server"],
      "env": {
        "HERMES_BASE_URL": "http://localhost:8000",
        "HERMES_MCP_PROVIDER": "ollama",
        "HERMES_MCP_MODEL": "qwen3:14b",
        "HERMES_OLLAMA_BASE_URL": "http://localhost:11434"
      }
    }
  }
}
```

---

## 🛠️ 可用工具 (Tools)

### `hermes.run_task`
觸發一個 Hermes 自主代理任務。此工具會透傳 Hermes 的治理語意，包含 `approval_required` 與 `blocked` 狀態。

**參數範例：**
```json
{
  "task": "請分析當前目錄結構並摘要 README.md",
  "provider": "ollama",
  "model": "qwen3:14b",
  "temperature": 0.7
}
```

### `hermes.get_status`
獲取 Hermes 引擎當前狀態（IDLE/RUNNING）與診斷資訊。

### `hermes.get_trace`
獲取最近一次執行任務的完整管理鏈追蹤 (Trace)。

---

## ⚙️ 配置優先級 (Configuration Priority)

當調用 `hermes.run_task` 時，參數的決定優先級如下：

1. **Tool Arguments** (調用工具時直接傳入的參數)
2. **HERMES_MCP_* Env** (專屬於 MCP 入口的環境變數)
3. **HERMES_DEFAULT_* Env** (Hermes 全域預設環境變數)
4. **Fallback Default** (預設為 `mock` 模式，用於流程測試)

### 常用環境變數參考
| 變數名 | 說明 | 範例 |
| --- | --- | --- |
| `HERMES_BASE_URL` | Hermes API 地址 | `http://localhost:8000` |
| `HERMES_MCP_PROVIDER` | MCP 預設 Provider | `ollama`, `claude`, `mock` |
| `HERMES_MCP_MODEL` | MCP 預設模型 | `qwen3:14b`, `claude-3-sonnet` |
| `HERMES_OLLAMA_BASE_URL`| Ollama API 地址 | `http://localhost:11434` |
| `HERMES_MCP_TIMEOUT` | API 請求逾時 (秒) | `30` |

---

## 🛡️ 治理語意透傳 (Pass-Through Governance)

Hermes MCP Server 遵循 **Pass Through Hermes** 策略，不會重新解釋或簡化 Hermes 的執行結果：

- **Approval Required**: 如果任務觸發了需要審核的操作，MCP 會回傳包含 `proposal_id` 的成功回應。這**不是** MCP 錯誤 (`isError: false`)，而是 Hermes 的正常治理決策。
- **Blocked**: 如果任務違反了治理規則（如高風險 Shell 指令），MCP 會回傳 `status: blocked`。
- **Trace & Risk**: 所有的 Trace ID 與風險評估數據均完整保留在回應的 JSON text 中。

> [!IMPORTANT]
> **MCP isError: true** 僅代表「橋接層失敗」（例如無法連線到 Hermes API 或 JSON 解析錯誤），而不代表 Hermes 內部的執行失敗或攔截。

---

## 🔍 除錯與診斷

如果您發現 MCP 呼叫無反應，請依序檢查：

1. **Hermes API 是否存活**: `curl http://localhost:8000/api/status`
2. **Provider 健康檢查**: `curl http://localhost:8000/api/providers/health`
3. **模型是否存在**: `ollama list`
4. **MCP 日誌**: 檢查您的客戶端（如 Claude Code）的 stderr 輸出，橋接錯誤會在那裡顯示。

---

## ⚠️ 常見錯誤
- **HERMES_API_UNAVAILABLE**: 請確認 `start_hermes.py` 正在運行且 `HERMES_BASE_URL` 設定正確。
- **INVALID_JSON_RESPONSE**: 通常發生在 API 回傳了非 JSON 內容（如 HTML 404 頁面）。
- **Provider defaults to mock**: 如果您沒設定環境變數也沒傳入參數，任務會以 Mock 模式執行，不會產生實際變更。
