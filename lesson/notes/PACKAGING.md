# LocalAgentTutor.exe 打包說明

## 觀念

`LocalAgentTutor.exe` 是學習入口，不是黑盒替代品。

它負責：

- 開始教學
- 啟動 Agent
- 執行測試
- 查看筆記
- 開啟原始碼資料夾

它不應該取代：

- `lessons/` 裡的課程原始碼
- `agent/` 裡的核心邏輯
- `notes/` 裡的學習筆記

## 建置

```powershell
cd G:\program\agent\lesson
.\build_exe.ps1
```

建置完成後會產生：

```text
dist\LocalAgentTutor.exe
```

## 使用提醒

執行 `.exe` 前請確認：

- Ollama 正在執行
- `ollama list` 看得到 `gemma4:latest`
- `.exe` 和專案資料夾搭配使用
