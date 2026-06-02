# Work Agent Architecture

## Summary

Work Agent 是一個輕量版的 harness-driven local agent。

它的重點不是「讓模型自由發揮」，而是把模型包在一個清楚、可驗證、可限制的工作流程中。這樣比較實用，也比較接近真實開發場景。

## Four Roles

### Agent Loop

`simple_agent/loop.py`

負責整體執行流程：

1. 接收使用者任務
2. 呼叫 Manager Model 做任務判斷
3. 執行對應工具
4. 收到 observation
5. 交給 Worker Model 整理回覆

### Manager Model

`simple_agent/roles.py`

負責把自然語言任務轉成簡單決策：

- 要用哪個 worker
- 要用哪個 tool
- 要帶什麼參數

它的工作像是「任務路由器」，而不是最終執行者。

### Worker Models

`simple_agent/roles.py`

負責把 observation 轉成能被開發者理解的結果：

- 結果摘要
- 下一步建議
- 風險提醒

### Tools

`simple_agent/tools.py`

目前工具以穩定、安全、可理解為優先：

- `list_files`
- `read_file`
- `search_text`
- `run_command`

## Why This Shape Works

這種設計符合 Harness Engineering 的核心精神：

- 把高風險的自由度縮小
- 把常用規則固定成流程
- 把錯誤轉成可觀察訊號
- 把知識寫進 repo，而不是只留在對話裡

