# Work Agent Commands

## Allowed Commands

目前 `config.json` 中允許的命令是：

- `python --version`
- `python -m pytest`
- `pytest`
- `rg`

## Tool Usage Rules

### list_files

用途：

- 了解 `workspace/` 內有哪些檔案與資料夾

適合情境：

- 分析專案結構
- 找出要先讀哪些檔案

### read_file

用途：

- 讀取單一檔案內容

適合情境：

- 查看函式邏輯
- 摘要 README
- 分析錯誤來源

### search_text

用途：

- 搜尋關鍵字、函式名、錯誤字串

適合情境：

- 快速定位程式碼
- 找出某功能出現在哪裡

### run_command

用途：

- 執行白名單命令

適合情境：

- 跑測試
- 確認 Python 版本
- 在允許範圍內查詢 CLI 輸出

## Safety Rules

- 所有路徑都必須限制在 `workspace/`
- 不允許刪除檔案
- 不允許任意 shell 命令
- 若命令不在白名單內，必須直接拒絕

