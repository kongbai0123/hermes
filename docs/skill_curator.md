# ⚡ Hermes Skill Curator (自我進化策展人)

本文件定義了 Hermes 系統中的 Phase 5: Skill Curator 機制。Skill Curator 是 Hermes 實現自我反思與進化的核心元件，但嚴格受限於 L1 Proposal-only 自治等級。

## 1. 核心設計理念：Proposal-First (提案優先)

Hermes 絕對不允許在沒有人類審查的情況下，直接修改自己的 Markdown 規範或底層 Python 程式碼。Skill Curator 的職責是「觀察、分析、提出建議」，而非「擅自行動」。

> [!IMPORTANT]
> **自我進化金律 (Golden Rule of Self-Evolution)**：
> 所有由 Skill Curator 產生的技能更新或規則變更都必須是 **Proposal-only** 且必須由人類進行審查，系統不允許任何自動套用修改（Auto-apply）行為。

## 2. 運作流程 (The Evolution Loop)

```text
+------------------+     +------------------+     +------------------+
|    Observe       |     |     Analyze      |     |     Propose      |
|  (失敗軌跡收集)  | --> |  (失敗模式辨識)  | --> |  (生成結構提案)  |
|  Monitor Traces  |     |   RCA Diagnostics|     |  patch_proposal  |
+------------------+     +------------------+     +------------------+
                                                           |
                                                           v
                                                  +------------------+
                                                  |     Persist      |
                                                  |  proposals/*.json|
                                                  +------------------+
```

1. **Observe (觀察)**：Curator 每天（或每 N 次任務後）讀取系統中的 Monitor Traces，特別關注 `TOOL_FAILURE`、`BACKOFF_TRIGGERED` 等錯誤事件。
2. **Analyze (分析)**：辨識常見的失敗模式（例如：頻繁在特定目錄寫入失敗，代表可能對該目錄的權限認知有誤）。
3. **Propose (提案)**：透過 `ProposalGenerator` 產生一份結構化的 `patch_proposal.json`。
4. **Persist (儲存)**：將提案存入 `proposals/` 目錄，等待人類審查。

## 3. Proposal 結構

每一份提案都會包含以下資訊，確保人類審查時擁有充分的上下文：

```json
{
  "id": "prop-1715832000",
  "type": "skill_update",
  "target_file": "docs/autonomy_policy.md",
  "reason": "Observation: Tool 'read_file' repeatedly failed with error: 'permission denied'. Suggesting a policy clarification.",
  "patch": "<!-- Add specific clarification for this tool usage here -->",
  "risk_level": "medium",
  "requires_approval": true,
  "status": "pending_approval",
  "created_at": "2026-05-17T12:00:00"
}
```

* **id**: 唯一識別碼。
* **target_file**: 建議修改的目標文件（例如 `docs/autonomy_policy.md`）。
* **reason**: 為什麼提出這個修改（基於哪一次的 Trace 失敗）。
* **patch**: 具體的修改內容。
* **risk_level**: 風險評估 (`low` / `medium` / `high`)。
* **status**: 預設為 `pending_approval`。

## 4. 安全限制 (Safety Boundaries)

> [!CAUTION]
> **嚴格安全紅線**：
> 1. **無法自我批准**：Curator 產生的 JSON 提案必須具備 `requires_approval: true`。
> 2. **讀取範圍限制**：只能讀取 traces、logs 與 docs/，不能讀取使用者的敏感專案原始碼。
> 3. **透過 Validation Suite 保護**：系統將透過 `safety_validation_suite.json` 確保 `apply_proposal` 行為在沒有合法授權前必定被阻擋。
