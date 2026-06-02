# Work Agent Workflow

## Default Workflow

Work Agent 的預設流程應該固定，不要每次都重新發明：

1. `Understand`
   - 先判斷任務類型
   - 只抓必要上下文

2. `Observe`
   - 列檔案、搜尋關鍵字、讀重點檔案
   - 若需要執行命令，只能使用白名單

3. `Explain`
   - 先回報觀察到的事實
   - 避免在證據不足時直接下結論

4. `Verify`
   - 若任務與測試、版本、指令有關，優先用工具驗證
   - 若無法驗證，要明說限制

5. `Suggest`
   - 提出下一步
   - 需要修改時，先提出 patch 或修改方向

## Recommended Task Templates

### Analyze Codebase

- 先列出 `workspace/` 結構
- 找出主要檔案
- 讀取 1 到 3 個關鍵檔案
- 整理成簡短架構說明

### Debug Failure

- 先跑測試或命令
- 抓錯誤訊息
- 搜尋相關符號
- 讀取出錯檔案
- 提出可能原因與修正方向

### Read And Explain

- 讀指定檔案
- 若內容過長，先摘要
- 補上重點段落的說明

## Anti-Patterns

- 沒先看證據就直接給結論
- 一開始就做過多工具呼叫
- 工具結果不夠清楚卻硬要總結
- 把所有規則都塞進單一 prompt

