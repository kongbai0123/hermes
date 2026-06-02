# Work Agent Quality Rules

## Quality Priorities

V1 的優先順序如下：

1. 正確性
2. 可重現性
3. 易理解
4. 執行速度
5. 擴充性

## Response Standard

每次回覆最好至少包含：

- 根據什麼 observation 得出結論
- 結果摘要
- 下一步建議

如果有以下情況，必須明說：

- 沒有找到檔案
- 沒有找到關鍵字
- 命令不在白名單
- 測試無法執行
- 證據不足，只能提出猜測

## Harness Rules

這個專案採取的 harness 原則是：

- 用少量規則換取高穩定性
- 用文件當作系統記錄依據
- 用工具輸出當作第一手證據
- 用固定流程降低 prompt 漂移

## V1 Acceptance Criteria

若要算是合格的 V1，至少要做到：

- 能安全列出 `workspace/` 檔案
- 能安全讀取檔案
- 能搜尋關鍵字
- 能執行白名單命令
- 能把 observation 整理成可讀回覆
- 能拒絕 workspace 外路徑
- 能拒絕未允許命令

