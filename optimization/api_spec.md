# Hermes Agent OS: API Specification

本文件定義了 Hermes Agent OS 與 UI/UX 介面互動的標準 RESTful API 接口。

## 1. 任務與執行 (Task & Execution)
管理 AI 的核心任務執行與狀態追蹤。

| 接口 | 方法 | 功能 | 參數 |
| :--- | :--- | :--- | :--- |
| `/api/task` | `POST` | 發送新任務 | `{ "task": "string" }` |
| `/api/status` | `GET` | 獲取目前狀態機與運行資訊 | - |
| `/api/task/abort` | `POST` | 中斷目前任務 | - |

## 2. 治理與權限 (Governance Dashboard)
對應 UI 中的「治理儀表板」，管理預算與授權。

| 接口 | 方法 | 功能 | 參數 |
| :--- | :--- | :--- | :--- |
| `/api/governance/status` | `GET` | 獲取預算用量與權限清單 | - |
| `/api/governance/permission` | `PATCH` | 動態調整權限 (Gating) | `{ "permission": "string", "enabled": bool }` |
| `/api/governance/budget` | `PATCH` | 調整 Token 或時間預算 | `{ "token_limit": int }` |

## 3. 記憶與認知 (Memory Explorer)
探索與管理 Agent 的五層記憶。

| 接口 | 方法 | 功能 | 參數 |
| :--- | :--- | :--- | :--- |
| `/api/memory/context` | `GET` | 查詢特定主題的相關記憶 | `?query=string` |
| `/api/memory/user` | `GET/PATCH` | 獲取或更新用戶偏好模型 | `{ "preferences": {} }` |
| `/api/memory/sessions` | `GET` | 獲取歷史執行軌跡 (Traces) | - |

## 4. 技能中心 (Skill Hub)
管理已固化的程序化記憶。

| 接口 | 方法 | 功能 | 參數 |
| :--- | :--- | :--- | :--- |
| `/api/skills` | `GET` | 列出所有已註冊技能 | - |
| `/api/skills/register` | `POST` | 手動註冊或固化新技能 | `{ "name": "string", "code": "string" }` |

## 5. 觀測與診斷 (Observability)
提供效能圖表與錯誤分析數據。

| 接口 | 方法 | 功能 | 參數 |
| :--- | :--- | :--- | :--- |
| `/api/metrics` | `GET` | 獲取 Token 趨勢、延遲分佈 | - |
| `/api/logs` | `GET` | 獲取系統日誌與 Debug 資訊 | - |
