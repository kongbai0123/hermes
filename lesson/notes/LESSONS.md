# 邊做邊學課程

## Lesson 1：呼叫本機模型

執行：

```powershell
python lessons/01_ollama_chat.py
```

學習重點：

- Ollama 在本機提供 HTTP API。
- `agent/llm.py` 用 Python 標準函式庫送出請求。
- `stream=True` 可以讓模型像聊天工具一樣逐字輸出。

## Lesson 2：對話記憶

執行：

```powershell
python lessons/02_chat_memory.py
```

學習重點：

- LLM 本身是無狀態的。
- 記憶其實是把前幾輪對話重新放進 prompt。
- `system` 訊息用來固定 agent 的角色與規則。

## Lesson 3：工具

執行：

```powershell
python lessons/03_tools_basic.py
```

學習重點：

- agent 的「手」就是工具函式。
- 模型負責決定要不要用工具，程式負責真正執行。
- 工具結果要回傳成 observation，讓模型能繼續推理。

## Lesson 4：ReAct Loop

執行：

```powershell
python lessons/04_react_loop.py
```

學習重點：

- ReAct 是 Reasoning + Action。
- 流程是：模型要求工具 → 程式執行 → 把結果交回模型。
- 多步驟任務需要 loop，不是只問模型一次。

## Lesson 5：讀取與搜尋程式碼

執行：

```powershell
python lessons/05_code_reader.py
```

學習重點：

- 讀檔與搜尋是程式碼助理的核心能力。
- 所有路徑都限制在 `workspace/` 內。
- 搜尋優先使用 `rg`，找不到時退回 Python 搜尋。

## Lesson 6：產生 Patch

執行：

```powershell
python lessons/06_patch_writer.py
```

學習重點：

- 第一版 agent 不直接改檔。
- 修改建議用 unified diff 表示。
- 這樣你可以先審查，再決定是否套用。

## Lesson 7：測試與驗證

執行：

```powershell
python lessons/07_test_runner.py
```

學習重點：

- 程式碼助理不只要會寫，還要會驗證。
- `workspace/sample_project` 內故意留了一個測試失敗。
- 目標是讓 agent 讀測試輸出、定位錯誤、產生 patch。

## Lesson 8：完整 CLI Agent

執行：

```powershell
python lessons/08_agent_cli.py
```

可嘗試輸入：

```text
請分析 workspace 裡的程式結構
找出 sample_project 的測試失敗原因
請提出修正 divide by zero 的 patch
```

## 下一階段

- 加入「確認後套用 patch」。
- 加入備份與變更紀錄。
- 加入更嚴格的命令白名單設定檔。
- 加入 Web UI 或任務歷史面板。

