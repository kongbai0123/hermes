# Hermes Autonomy Policy (自治分層策略)

本文件定義 Hermes 的自治等級（Autonomy Levels）。 

**核心原則**：Markdown 描述規則，Python Governance 執行規則。 

系統絕對不允許透過建立 `AUTO_APPROVE.md` 等檔案來繞過 `GovernanceManager` 的安全檢查。所有的權限放行都必須基於分層授權與沙盒隔離。

## 自治等級定義 (L0 - L5)

### L0: Read-only (唯讀模式)

- **適用情境**: 專案分析、程式碼走讀、報告整理。
- **Allowed Tools**: `read_file`, `search_workspace`, `list_directory`, `get_file_info`
- **Blocked Tools**: 所有 Write, Patch, Shell, Delete 工具。
- **Approval Requirement**: 不需要 (No approval needed)。
- **Governance Requirement**: 基礎唯讀權限。
- **Expected Trace**: 記錄讀取路徑與摘要結果。

### L1: Proposal-only (提案模式)

- **適用情境**: 提出程式碼修改建議、除錯分析提案。
- **Allowed Tools**: `propose_patch`, `propose_shell_command` (+ L0 Tools)
- **Blocked Tools**: 直接套用 Patch、直接執行 Shell。
- **Approval Requirement**: 提出提案不需要，但執行提案必須 Human Approval。
- **Governance Requirement**: 將操作推入 `pending_patches` 佇列。
- **Expected Trace**: 記錄生成的 Proposal 內容與等待審批狀態。

### L2: Scoped Write (受限寫入)

- **適用情境**: 生成新網站、Demo Project、輸出靜態檔案。
- **Allowed Tools**: `generate_static_site`, `write_file` (+ L0 Tools)
- **Blocked Tools**: 修改既有 Repo 核心程式碼、刪除檔案。
- **Approval Requirement**: 在指定的 `user_projects/` 範圍內可 Auto-approve。
- **Governance Requirement**: 強制校驗寫入路徑 (Path enforcement)。
- **Expected Trace**: 記錄寫入的檔案大小、路徑與成功狀態。

### L3: Approved Patch (授權修改)

- **適用情境**: 修改 README.md、更新 docs/、小幅度修復 Bug。
- **Allowed Tools**: `apply_patch`, `edit_file` (+ L2 Tools)
- **Blocked Tools**: 大規模重構、危險 Shell 指令。
- **Approval Requirement**: 強制需要明確的 Human Approval。
- **Governance Requirement**: 驗證 Patch 的正確性與授權 Token。
- **Expected Trace**: 記錄 Patch 前後的 diff 與 Approval Token 來源。

### L4: Governed Shell (受治腳本)

- **適用情境**: 執行測試 (pytest)、檢查狀態 (git status)、Linting。
- **Allowed Tools**: `execute_shell` (僅限 Allowlist 內的指令)
- **Blocked Tools**: `rm -rf`, 系統級安裝指令, 破壞性 Git 操作。
- **Approval Requirement**: 需要短期 Token 與 TTL (Time-To-Live) 授權。
- **Governance Requirement**: 嚴格的字串比對與 Allowlist 攔截。
- **Expected Trace**: 記錄完整 stdout/stderr、Exit Code 與執行耗時。

### L5: Sandbox Autonomous (沙盒全自治)

- **適用情境**: 高自治的 CI/CD 流程、批次腳本執行、實驗性功能探索。
- **Allowed Tools**: 所有工具 (於 Sandbox 範圍內)。
- **Blocked Tools**: 無法逃逸至 Host 系統的任何操作。
- **Approval Requirement**: 在 Docker 沙盒內部可全面 Auto-approve。
- **Governance Requirement**: 依賴 Docker 容器邊界、資源限制 (CPU/Memory) 與 Timeout 機制。
- **Expected Trace**: 記錄沙盒生命週期與邊界攔截事件。

---

> [!WARNING]
> **安全警告 (Security Warning)**: 切勿在此專案中新增 `AUTO_APPROVE.md`，也不要在任何 Prompt 中暗示 Hermes 可以繞過 Python 核心的 `SafeExecutor` 與 `ConstraintValidator`。
