# Hermes Persistence Model (持久化模型)

本文件盤點並定義 Hermes 系統中各類資料與狀態的持久化（Persistence）行為。了解哪些資料會在系統重啟後保留、哪些會遺失，對於建立可靠的 Agent 工作流至關重要。

## 核心持久化狀態 (Persistent State)

這些資料會實體寫入硬碟，並在 Hermes 或 Ollama 重啟後完整保留：

- **`user_projects/*`**: 所有由 Hermes 根據指令生成的網站、Demo 專案與程式碼檔案。
- **`docs/*`**: 系統架構、規範指引（如本文件與 Autonomy Policy）以及技能定義（Skills）。
- **JSON 記憶體 (`memory_semantic.json`, `user_model.json`)**: 目前基於 JSON 實作的基礎語義記憶與使用者模型分析（若已啟用儲存機制）。
- **Ollama 模型權重**: 儲存於本地 Ollama 服務器中的大語言模型本身。

## 暫態與揮發狀態 (Ephemeral State)

這些狀態存在於 Runtime 記憶體中，系統重啟後將會消失，設計上不應依賴其進行跨 Session 的持久化：

- **`runtime.trace` (Runtime Traces)**: 執行過程中的詳細軌跡與推理日誌。除非有額外的 Logger 將其寫入實體 `.log` 檔案，否則重啟即清空。
- **`pending_patches` (待審批佇列)**: 透過 Proposal 提出的修改建議，在尚未獲得 Human Approval 前，僅存在於記憶體中。
- **Approval Tokens & Scoped Grants**: 授權憑證、單次執行的 Token 以及具有 TTL (Time-To-Live) 的範圍權限。
- **對話上下文 (Session Context)**: 當前對話視窗內的短期記憶。

## 未來需產品化的持久化目標

以下模組目前尚未具備完整的持久化能力，是未來 Skill Curator 與長期記憶系統的開發重點：

- **向量化長期記憶 (Vector Long-term Memory)**: 將 JSON Memory 升級為真正的向量資料庫，以支援大規模檢索。
- **自我進化紀錄 (Audit Log / Evolution History)**: 完整的 Patch 套用歷史、Skill Curator 的提案紀錄與驗證結果。
- **持久化任務佇列 (Persistent Task Queue)**: 讓中斷的任務（如執行到一半的 CI/CD）在重啟後能接續執行。

## 系統能力聲明限制

為避免誤導使用者與模型自身，請勿宣稱 Hermes 目前具備以下能力：

- 「Hermes 關閉後會完整記得所有教訓與中斷狀態。」(X)
- *正確理解：「Hermes 具備部分持久化能力；檔案級結果會保留，但 runtime session 與完整長期記憶仍需進一步產品化。」*
