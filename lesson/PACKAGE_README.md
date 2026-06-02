# LocalAgentTutor MCP Package

這個資料夾是從 `G:\program\agent\lesson` 封裝出的可攜版本。

## 一般使用

啟動教學式 UI：

```powershell
dist\LocalAgentTutorUI.exe
```

命令列選單：

```powershell
dist\LocalAgentTutor.exe
```

## MCP 使用

MCP server 位於：

```text
mcp_agent\server.py
```

已打包 MCP exe：

```text
dist\LocalAgentTutorMCP.exe
```

啟動批次檔：

```text
mcp_agent\run_mcp_server.cmd
```

設定範例：

```text
mcp_agent\mcp_config.example.json
```

## 注意

- Ollama 需要已啟動並有 `gemma4:latest` 模型。
- `workspace/` 是 MCP agent 讀取與測試的安全範圍。
- `run_tests` 預期會顯示一個測試失敗，這是教學用 bug。
