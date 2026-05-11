# Hermes Read-Only Tool Calling v1 實作計畫書

*建立日期: 2026-05-11*

## 1. 目標

目前 Hermes 已經能透過本機 Ollama 的 `qwen3:14b` 回答使用者，但它仍主要依賴模型自身推理。下一步要讓 Hermes 開始具備「可觀測、受控、可驗證」的代理能力：先從只讀工具開始，讓 Hermes 能讀取專案資訊，再基於真實檔案內容回答。

本階段完成後，使用者可以問：

```text
請讀取 hermes/core/runtime.py，告訴我 Hermes 現在怎麼執行任務
```

Hermes 應該能實際呼叫只讀工具讀檔，並在 Dashboard 顯示工具調用與結果摘要。

## 2. 設計原則

1. **先只讀，後寫入**  
   本階段不開放寫檔、刪檔、任意 shell。先降低風險，確認代理閉環穩定。

2. **使用者可觀測**  
   Dashboard 必須顯示工具調用，例如 `TOOL_CALL read_file` 與 `TOOL_RESULT`，避免 AI 暗箱操作。

3. **工具結果參與回答**  
   Hermes 不應只靠模型猜測，而要把工具結果重新送回模型，生成最終回覆。

4. **權限邊界清楚**  
   只允許讀取 Hermes workspace 內的檔案，並阻擋路徑穿越，例如 `../secret.txt`。

5. **保留未來擴充點**  
   工具註冊、執行器、觀測紀錄應能擴充到後續的寫檔、shell、網頁查詢。

## 3. 預計修改範圍

| 模組 | 預計修改 | 目的 |
| :--- | :--- | :--- |
| `hermes/harness/constraints.py` | 強化路徑正規化與 workspace 邊界檢查 | 防止讀取工作區外部檔案 |
| `hermes/harness/executor.py` | 新增 `list_files`、`read_file` 只讀方法 | 提供安全工具 |
| `hermes/core/runtime.py` | 加入 Tool Calling v1 執行流程 | 從回答型 Runtime 升級為工具型 Runtime |
| `hermes/utils/monitor.py` | 記錄工具調用 trace | Dashboard 可觀測 |
| `hermes/api/server.py` | 回傳工具 trace 與最新結果 | 前端顯示工具過程 |
| `start_hermes.py` | 同步簡易 server API 行為 | 保持本地啟動方式一致 |
| `hermes/api/dashboard.html` | 顯示工具調用與工具結果 | 讓使用者看到 Hermes 做了什麼 |
| `tests/` | 增加工具、路徑安全、Runtime 行為測試 | 防止回歸 |

## 4. 實作階段

### Phase 1: 安全只讀工具

**內容**

- 新增 `SafeExecutor.list_files(path)`
- 新增 `SafeExecutor.read_file(path, max_chars=12000)`
- 使用 `pathlib.Path.resolve()` 做絕對路徑檢查
- 只允許讀取 `E:\program\hermes` 內部檔案
- 限制單次讀取長度，避免把超大檔塞進模型 context

**驗收**

```text
read_file("hermes/core/runtime.py") -> 成功
read_file("../secret.txt") -> 拒絕
list_files("hermes/core") -> 回傳檔案清單
```

### Phase 2: Tool Plan 格式

**內容**

讓模型輸出簡單 JSON plan，例如：

```json
{
  "tool": "read_file",
  "args": {
    "path": "hermes/core/runtime.py"
  },
  "reason": "需要讀取 Runtime 實作才能回答使用者問題"
}
```

初版不追求多步驟，只做單工具調用，避免複雜度過早升高。

**驗收**

```text
使用者要求讀 runtime.py -> Hermes 產生 read_file 工具計畫
一般聊天 -> Hermes 不調工具，直接回答
```

### Phase 3: Runtime 工具閉環

**流程**

```text
使用者任務
-> 建立上下文
-> 請模型判斷是否需要工具
-> 驗證工具名稱與參數
-> 執行只讀工具
-> 將工具結果送回模型
-> 產生最終回覆
-> 記錄 trace
```

**驗收**

使用者問：

```text
請讀取 hermes/core/runtime.py，摘要它的執行流程
```

Hermes 回覆中必須包含實際檔案內容推導出的資訊，例如狀態機、LLM provider、memory、monitor。

### Phase 4: Dashboard 可視化

**內容**

在終端機區塊顯示：

```text
>> [USER_CMD] 請讀取 runtime.py...
:: [TOOL_CALL] read_file hermes/core/runtime.py
:: [TOOL_RESULT] 讀取成功，12,000 chars
<< [HERMES_REPLY] ...
```

**驗收**

- 使用者能看到 Hermes 呼叫了哪個工具
- 工具失敗時顯示 `HERMES_ERROR`
- 成功時顯示 `HERMES_REPLY`

### Phase 5: 測試與穩定化

**必要測試**

- 路徑安全測試
- 讀檔成功測試
- 讀檔超出 workspace 拒絕測試
- Runtime 工具調用測試
- Dashboard 靜態行為測試
- 既有 `tests/test_core.py` 全部通過

**驗收命令**

```powershell
python -m unittest discover -s tests -p "test_*.py"
node -e "const fs=require('fs'); const html=fs.readFileSync('hermes/api/dashboard.html','utf8'); const scripts=[...html.matchAll(/<script>([\\s\\S]*?)<\\/script>/g)].map(m=>m[1]); for (const script of scripts) new Function(script); console.log('dashboard inline scripts parse OK:', scripts.length);"
```

## 5. 使用者體驗

完成後，使用者在 Dashboard 看到的行為會從：

```text
使用者提問 -> Hermes 直接回答
```

升級成：

```text
使用者提問
-> Hermes 判斷需要讀檔
-> 顯示工具調用
-> 顯示工具結果
-> Hermes 根據真實內容回答
```

這會讓 Hermes 開始符合「Harness Engineering」的精神：模型不是獨自猜測，而是在受控系統中使用工具、留下紀錄、接受觀測。

## 6. 風險與處理

| 風險 | 影響 | 處理方式 |
| :--- | :--- | :--- |
| 模型輸出不是合法 JSON | 工具計畫解析失敗 | 增加 JSON repair / fallback direct answer |
| 模型要求未授權工具 | 安全風險 | 僅允許工具白名單 |
| 路徑穿越 | 讀到 workspace 外部檔案 | 使用 `Path.resolve()` 與 allowed root 檢查 |
| 檔案過大 | context 過長、回覆慢 | 限制 `max_chars` 並提示截斷 |
| Dashboard trace 太多 | UI 雜亂 | 只顯示摘要，詳細資料留在 logs |

## 7. 不在本階段處理

- 任意 shell 執行
- 寫檔與修改程式
- 自動 commit / PR
- 瀏覽器自動化
- 多步驟工具鏈
- 背景排程與通知

這些功能會等只讀工具閉環穩定後，再進入 Tool Calling v2 / Agent Execution v1。

## 8. 完成定義

本計畫完成時，必須同時符合：

- Hermes 可以用 Qwen3 14B 回答一般問題
- Hermes 可以安全讀取 workspace 內指定檔案
- Hermes 會在 Dashboard 顯示工具調用與結果
- 所有新增與既有測試通過
- 使用者能理解 Hermes 不是只在猜，而是真的讀取了指定內容

