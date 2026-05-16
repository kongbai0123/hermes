# Hermes 代理執行指南 (Hermes Agent Operating Guide)

本文件是為在 Hermes 儲存庫中工作的 AI 代理提供的快速載入操作指南。如需更廣泛的產品和架構背景，請參閱 `docs/` 下的文件。

## 使命 (Mission)

Hermes 是一個本地優先的受管 AI 代理作業系統。它旨在將使用者請求轉化為可追蹤、受治理、可測試的成果，而非未經證實的聊天輸出。

核心定位：

```text
LLM = CPU
Hermes = OS
Dashboard = 工作台與干預主控台
Trace = 執行證據
```

## 不可逾越的規則 (Non-Negotiable Rules)

1. **不可假裝確定**。如果資訊缺失，請說明假設。
2. **偏好結構化執行**：計畫、執行、驗證、報告。
3. **保護使用者成果**。不可刪除或恢復無關檔案。
4. **保持生產變更微小且可測試**。
5. **高風險操作需要審核或提案流程**。
6. **無追蹤 (Trace) 即無可信執行**。
7. **不可讓 MCP、Shell、寫入、刪除或網路變更繞過 ToolRegistry、風險閘門 (Risk Gate)、管理層或審核員**。

## 運行模型 (Runtime Model)

Hermes 任務應遵循以下狀態流：

```text
閒置 (IDLE) -> 詢問 (ASKING) -> 計畫 (PLANNING) -> 執行 (EXECUTING) -> 驗證 (VERIFYING) -> 恢復 (RECOVERING) -> 完成 (DONE)
```

每個有意義的任務都應產生：
- 使用者意圖與假設。
- 風險分類。
- 帶有理由與預期結果的執行步驟。
- 工具執行結果。
- 審核員驗證。
- 基於實際結果的最終回覆。

## 管理鏈 (Management Chain)

Hermes 使用四種管理角色，並強調 **「計畫-執行-反思」** 的迭代循環：

| 層級 | 角色 | 職責 |
| --- | --- | --- |
| L1 | 執行總監 (Executive Director) | 定義意圖、風險評估、授權、成功標準 |
| L2 | 策略經理 (Strategy Manager) | **反覆策略與自我思考**：將任務分解為步驟，並根據反饋動態調整計畫 |
| L3 | 操作執行員 (Operator Worker) | **調用 ToolRegistry 工具與 Skills**：僅限執行受控工具與既有技能 |
| L4 | 審核/驗證員 (Auditor / Verifier) | 驗證輸出、檢查政策、標記漏洞、提供反思建議 |

> [!IMPORTANT]
> **技能邊界 (Skill Boundary)**：Agent 在執行任務時，應優先調用位於 `hermes/skills/` 下的程序化技能。這些技能是系統穩定性的保證，不可擅自修改其定義。

## 📦 目錄權限定義

### HERMES 工作區 (可自由寫入/執行)
1. **`user_project/`**：用戶專案區，Agent 可在此自由建立檔案、測試與開發。
2. **`scratch/`**：臨時暫存區，用於存放中間產物或實驗性腳本。

### HERMES 唯讀區 (不可修改)
1. **`hermes/skills/`**：程序化記憶區。Agent 僅能調用既有技能，不可修改技能定義。
2. **`docs/`**：架構與規範文件。

### HERMES 受控區 (需透過 Patch 審核)
1. **`hermes/` (核心代碼)**：包含 Runtime, Governance 等，修改需走提案流程。

## 工具政策 (Tool Policy)

優先順序：
```text
管理優先，工具次之。
安全優先，自主次之。
追蹤優先，奇技淫巧次之。
補丁優先，Shell 最末。
記憶優先，提示詞次之。
工作台優先，儀表板次之。
```

預設允許：
- 唯讀工作區檢查。
- 安全檔案列表/搜尋。
- 不改動生產狀態的單元測試與編譯檢查。
- 分類後的 MCP 唯讀工具。

需要提案或審核：
- 寫入原始碼檔案。
- 套用補丁 (Patch)。
- 執行 Shell。
- 外部網路變更。
- 安裝軟體包。
- Git push, merge, delete, 或 release 操作。

除非獲得明確批准與治理，否則禁止：
- 刪除操作 (Delete)。
- 未受限的原始 Shell。
- 未知的 MCP 工具。
- 秘密檔案或模型檔案變更。

## 文件導覽 (Documentation Map)

- `docs/architecture_overview.md`: 系統架構與數據流。
- `docs/security_model.md`: 風險閘門、審核、沙箱、稽核模型。
- `docs/roadmap.md`: 版本藍圖與執行優先級。
- `docs/mcp_integration_plan.md`: 受管 MCP 客戶端計畫。
- `docs/management_decision_layer.md`: 決策層規範。
- `docs/hermes_user_guide.md`: 面向人類的 Hermes Agent OS 指南。
- `docs/mcp.md`: MCP Server 使用與配置手冊。

## 測試預期 (Testing Expectation)

在宣稱完成前，請執行最相關的測試。對於廣泛的變更，請使用：

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

如果測試失敗，請報告：
- 確切指令。
- 通過/失敗結果。
- 錯誤摘要。
- 最小修復計畫。

