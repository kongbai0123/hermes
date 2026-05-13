# Hermes Management Decision Layer 實作計畫書

建立日期：2026-05-12

## 1. 目標

Hermes 需要從「單一代理 Runtime」升級為「具備管理層級的代理組織」。當使用者下達任務時，Hermes 不應直接讓模型一次決定、一次執行，而是模擬企業上下級管理：

```text
使用者指令
-> 上級決策層：判斷目標、風險、權限、完成定義
-> 中層分析層：拆解任務、設計方案、選擇工具、建立驗收標準
-> 下層執行層：按步驟呼叫工具、產出檔案或結果
-> 稽核監督層：檢查是否符合安全、測試、使用者要求
-> 最終回覆：用可觀測 Trace 告知使用者做了什麼
```

此架構的目的不是增加形式，而是讓 Hermes 能更穩定地處理「代理執行、生成專案、測試、修復、回報」這類多步驟任務。

## 2. 核心決策

### 2.1 採用四層代理治理架構

Hermes 的決策管理層建議分為四個角色：

| 層級 | 角色名稱 | 職責 | 是否可直接執行工具 |
| :--- | :--- | :--- | :--- |
| L1 | Executive Director | 決策、目標界定、風險分級、權限判斷 | 否 |
| L2 | Strategy Manager | 任務拆解、方案比較、建立執行計畫 | 否 |
| L3 | Operator Worker | 呼叫工具、建立檔案、執行測試、產出結果 | 是，受工具權限限制 |
| L4 | Auditor / Verifier | 驗證結果、檢查 Trace、安全審核、回歸測試 | 可執行讀取與測試工具 |

### 2.2 不使用多個模型常駐

初版不需要真的啟動多個模型程序。建議用同一個 LLM provider，透過不同 role prompt 與資料結構模擬組織層級。

原因：

- 節省本機資源，避免 Qwen3 14B 多次常駐造成記憶體壓力。
- 方便追蹤與測試。
- 可先讓資料流穩定，再擴充成多模型或多 agent。

### 2.3 所有層級都必須留下 Trace

每一層都要輸出結構化事件，例如：

```json
{
  "role": "StrategyManager",
  "action": "TASK_DECOMPOSED",
  "decision": "需要建立隔離專案並生成設計檔",
  "risk": "controlled_write",
  "next": "OperatorWorker"
}
```

Dashboard 應能顯示：

```text
USER_CMD
EXECUTIVE_DECISION
STRATEGY_PLAN
OPERATOR_TOOL_CALL
OPERATOR_TOOL_RESULT
AUDITOR_VERIFICATION
FINAL_REPLY
```

## 3. 架構設計

### 3.1 新增 Management Layer

建議新增模組：

```text
hermes/management/
  __init__.py
  roles.py
  decision.py
  orchestrator.py
  policy.py
```

各檔案職責：

| 檔案 | 職責 |
| :--- | :--- |
| `roles.py` | 定義管理層角色、輸入輸出格式、角色提示詞 |
| `decision.py` | 定義 `DecisionPacket`、`TaskPlan`、`ExecutionStep` |
| `policy.py` | 權限、風險分級、是否需要使用者批准 |
| `orchestrator.py` | 串接上級、中層、下層、稽核層 |

### 3.2 Runtime 串接方式

現有流程：

```text
HermesRuntime.execute_task()
-> LLM 判斷單一工具
-> SafeExecutor 執行
-> LLM 最終回答
```

升級後流程：

```text
HermesRuntime.execute_task()
-> ManagementOrchestrator.decide()
-> ExecutiveDirector.classify()
-> StrategyManager.plan()
-> OperatorWorker.execute_steps()
-> Auditor.verify()
-> HermesRuntime.finalize_response()
```

`HermesRuntime` 不應變成巨型檔案；它只負責狀態機與整體生命週期。管理流程應放到 `hermes/management/orchestrator.py`。

## 4. 資料結構

### 4.1 DecisionPacket

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

RiskLevel = Literal["low", "medium", "high", "requires_user_approval"]

@dataclass
class DecisionPacket:
    task: str
    intent: str
    risk_level: RiskLevel
    requires_tools: bool
    requires_write: bool
    requires_user_approval: bool
    success_criteria: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)
```

### 4.2 ExecutionStep

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Literal

StepType = Literal["read", "analyze", "generate", "write", "test", "verify", "reply"]

@dataclass
class ExecutionStep:
    id: str
    type: StepType
    tool: str | None
    args: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    expected: str = ""
```

### 4.3 ManagedTaskPlan

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class ManagedTaskPlan:
    decision: DecisionPacket
    steps: List[ExecutionStep]
    verification_steps: List[ExecutionStep] = field(default_factory=list)
```

## 5. 各層角色設計

### 5.1 上級決策層：Executive Director

任務：

- 判斷使用者真正想要的結果。
- 判斷是否需要工具、是否寫入、是否涉及高風險。
- 決定是否需要使用者批准。
- 定義完成標準。

輸入：

```text
使用者原始任務
目前 Hermes 能力清單
治理規則
```

輸出：

```json
{
  "intent": "create_design_project",
  "risk_level": "medium",
  "requires_tools": true,
  "requires_write": true,
  "requires_user_approval": false,
  "success_criteria": [
    "在 user_projects 底下建立隔離專案",
    "不可改動 Hermes 原始碼",
    "回覆中必須列出實際建立的檔案"
  ]
}
```

### 5.2 中層分析層：Strategy Manager

任務：

- 將目標拆成可執行步驟。
- 選擇工具。
- 產生 fallback 計畫。
- 明確寫出每步驗收方式。

範例輸出：

```json
{
  "steps": [
    {
      "id": "S1",
      "type": "write",
      "tool": "create_project_workspace",
      "args": {
        "name": "generated-project",
        "brief": "製作網頁設計"
      },
      "reason": "先建立隔離工作區，避免改動 Hermes 原始碼",
      "expected": "user_projects/generated-project 存在"
    },
    {
      "id": "S2",
      "type": "verify",
      "tool": "list_files",
      "args": {
        "path": "user_projects/generated-project"
      },
      "reason": "確認專案檔案已建立",
      "expected": "README.md 與 design_brief.md 存在"
    }
  ]
}
```

### 5.3 下層執行層：Operator Worker

任務：

- 僅能照 `ExecutionStep` 執行。
- 只能呼叫 `ToolRegistry` 已註冊工具。
- 不自行擴權，不自行 shell。
- 每一步產生 `TOOL_CALL` 與 `TOOL_RESULT`。

限制：

- 無權改變上層決策。
- 無權跳過驗證步驟。
- 工具失敗時必須回報給 Auditor 或 Strategy Manager。

### 5.4 稽核監督層：Auditor / Verifier

任務：

- 比對 `success_criteria` 與工具結果。
- 檢查是否越權。
- 檢查是否有未驗證的寫入。
- 決定是否需要 retry、repair 或 user approval。

稽核輸出：

```json
{
  "verified": true,
  "failed_criteria": [],
  "risk_notes": [
    "寫入範圍限制在 user_projects/generated-project"
  ],
  "final_status": "DONE"
}
```

## 6. 更好的補充規劃

### 6.1 增加 Risk Gate

每個任務先過風險閘門：

| 風險 | 行為 |
| :--- | :--- |
| low | 可直接回答或只讀工具 |
| medium | 可使用受控寫入工具，例如 `create_project_workspace` |
| high | 只能產生 patch proposal |
| requires_user_approval | 必須等使用者批准 |

高風險行為範例：

- 修改 Hermes 核心檔案。
- 套用 patch。
- 啟動外部程序。
- 大量寫入檔案。
- 網路下載模型。

### 6.2 加入 Simulation Mode

使用者想要「模擬演練」時，Hermes 可以只跑管理鏈，不執行工具：

```text
Executive decision -> Strategy plan -> Operator dry-run -> Auditor review
```

好處：

- 可以先看 Hermes 準備怎麼做。
- 適合高風險任務。
- 可作為訓練與治理展示。

### 6.3 加入 Debate / Review 模式

對複雜任務，中層可產生兩個方案：

```text
Strategy A: 快速執行
Strategy B: 穩健驗證
Auditor 選擇或合併
```

這可以降低單一模型錯判。

### 6.4 加入 Execution Budget

每個任務限制：

- 最多工具呼叫次數。
- 最多寫入檔案數。
- 最大 token 使用量。
- 最大執行時間。

超過時進入 `RECOVERING` 或要求使用者批准。

## 7. 實作階段

### Phase 1：資料結構與角色框架

目標：建立管理層資料模型，不改變既有 Runtime 行為。

預計新增：

```text
hermes/management/decision.py
hermes/management/roles.py
tests/test_management_decision.py
```

驗收：

- 可以建立 `DecisionPacket`。
- 可以建立 `ManagedTaskPlan`。
- 角色名稱、風險等級、成功條件可序列化成 trace。

### Phase 2：Risk Gate

目標：所有任務先分類風險。

預計新增：

```text
hermes/management/policy.py
tests/test_management_policy.py
```

驗收案例：

```text
請讀取 README.md -> low
請建立一個網頁專案 -> medium
請修改 runtime.py -> high
請刪除資料夾 -> requires_user_approval 或直接拒絕
```

### Phase 3：Strategy Planner

目標：將單步 ToolPlanner 擴充成多步驟計畫。

預計修改：

```text
hermes/core/tool_planner.py
hermes/management/orchestrator.py
tests/test_management_orchestrator.py
```

驗收：

使用者輸入：

```text
請建立一個網頁專案並驗證檔案存在
```

應產生：

```text
S1 create_project_workspace
S2 list_files
S3 final reply
```

### Phase 4：Operator 多步驟執行

目標：Runtime 可以依序執行多個工具。

預計修改：

```text
hermes/core/runtime.py
hermes/management/orchestrator.py
hermes/utils/monitor.py
```

驗收：

- Trace 顯示每一層角色與每一步工具呼叫。
- 任一步失敗時停止後續寫入，進入 `FAILED` 或 `RECOVERING`。
- 最終回覆要根據所有 step result，不是只根據最後一步。

### Phase 5：Dashboard 管理鏈視覺化

目標：Dashboard 顯示管理層鏈路。

預計修改：

```text
hermes/api/dashboard.html
tests/test_dashboard.py
```

UI 區塊：

```text
Management Chain
- Executive: intent / risk / approval
- Strategy: planned steps
- Operator: tool calls
- Auditor: verification
```

### Phase 6：Simulation Mode

目標：支援不執行工具的演練模式。

使用方式：

```text
/simulate 請建立一個網頁專案
```

行為：

- 產生完整管理鏈。
- 不呼叫寫入工具。
- 回覆預計會做什麼、風險是什麼、需要哪些批准。

## 8. 測試策略

### 單元測試

```powershell
python -m unittest tests/test_management_decision.py
python -m unittest tests/test_management_policy.py
python -m unittest tests/test_management_orchestrator.py
```

### 整合測試

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### Dashboard 測試

```powershell
python -m unittest tests/test_dashboard.py
```

### 模擬案例

1. 一般聊天：不應啟動工具。
2. 讀檔任務：Executive 判定 low，Operator 執行 `read_file`。
3. 建立專案：Executive 判定 medium，Operator 執行 `create_project_workspace`。
4. 修改核心檔：Executive 判定 high，只能產生 patch proposal。
5. 刪除任務：Auditor 直接拒絕或要求使用者批准，但目前政策建議拒絕。

## 9. 與現有能力的關係

目前 Hermes 已具備：

- `SafeExecutor`
- `ToolRegistry`
- `ToolPlanner`
- `Monitor Trace`
- `create_project_workspace`
- `propose_patch`
- `apply_approved_patch`
- `run_tests`

Management Decision Layer 不取代這些能力，而是把它們組織成一條更可靠的決策鏈。

## 10. 完成定義

本計畫完成時，Hermes 應能做到：

- 使用者下達任務後，Dashboard 顯示上級、中層、下層、稽核層。
- 上級決策層能判斷風險與是否需要批准。
- 中層能產生多步驟計畫。
- 下層能依序執行工具。
- 稽核層能驗證結果是否符合完成標準。
- 最終回覆必須說明「做了什麼、在哪裡、是否通過驗證」。
- 所有流程有 Trace，可供使用者檢查。

## 11. 建議優先順序

建議先做：

```text
Phase 1 -> Phase 2 -> Phase 4 -> Phase 5 -> Phase 3 -> Phase 6
```

理由：

- 先建立角色與風險分類，讓安全邊界穩。
- 再讓 Runtime 能執行多步驟。
- Dashboard 及早顯示管理鏈，方便使用者驗證。
- 最後才加更複雜的 planner 與 simulation mode。

## 12. 風險

| 風險 | 說明 | 對策 |
| :--- | :--- | :--- |
| 角色過多造成延遲 | 每層都問 LLM 會變慢 | 初版用 deterministic policy + 少量 LLM |
| 模型輸出格式錯誤 | 多步驟 JSON 容易壞 | 使用 dataclass 驗證與 fallback |
| 權限誤判 | 可能錯把高風險當中風險 | Risk Gate 採保守預設 |
| Dashboard 過於複雜 | 使用者看不懂管理鏈 | 預設摘要，點開看細節 |
| 代理自說自話 | 模型假裝執行 | 所有執行必須有 TOOL_RESULT |

## 13. 結論

Hermes 的下一個核心升級不只是更多工具，而是管理工具的「決策系統」。企業式上下級架構能讓 Hermes 在代理執行前先決策、分析、執行、稽核，避免直接把使用者指令交給模型自由發揮。

建議將本計畫作為 V0.4 / V0.5 之間的核心主線：

```text
V0.4: 多步驟任務規劃
V0.4.5: Management Decision Layer
V0.5: 受控寫入與 PR 建議模式
```
