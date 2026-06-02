# LocalAgentTutor MCP Agent

這個資料夾提供一個無額外套件依賴的 MCP stdio server，讓支援 MCP 的客戶端可以呼叫 LocalAgentTutor。

## 可用工具

- `package_info`：查看封裝根目錄、exe、workspace 是否存在
- `list_lessons`：列出全部 18 堂課
- `run_lesson`：用數字、課程代碼或 script path 執行課程
- `ask_agent`：詢問本機 Codex-like ReAct agent
- `run_tests`：執行 bundled sample project 測試
- `open_tutor_ui`：開啟教學式 UI

## 設定方式

封裝後範例路徑：

```text
G:\program\LocalAgentTutor_MCP_Package
```

MCP client 設定可參考：

```json
{
  "mcpServers": {
    "local-agent-tutor": {
      "command": "cmd",
      "args": [
        "/c",
        "G:\\program\\LocalAgentTutor_MCP_Package\\mcp_agent\\run_mcp_server.cmd"
      ],
      "env": {
        "LOCAL_AGENT_TUTOR_ROOT": "G:\\program\\LocalAgentTutor_MCP_Package"
      }
    }
  }
}
```

