# Hermes-like Agent OS: Implementation Roadmap

這份文件從「系統工程學」的高度，重新定義 AI 助理的優化方向：將 AI 從單純的「推理引擎」進化為「可持續演化的執行系統 (Evolving Execution System)」。

## 核心願景：LLM 是 CPU，Hermes 是 OS
目標是建立一個具備 **程序記憶 (Procedural Memory)**、**認知架構 (Cognitive Architecture)** 與 **強健治理 (Governance)** 的 Agent 作業系統。

---

## 核心架構：Harness Engineering 三大支柱
1. **Prompt Engineering**：指令優化與語義對齊。
2. **Context Engineering**：結構化上下文供給與環境限制。
3. **Harness Engineering**：控制系統、觀察層、治理層與回收機制。

---

## 實踐路徑 (Implementation Phases)

### 階段一：觀測基礎與狀態機 (Observability & State Machine)
建立「系統感」的第一步，是讓執行過程透明化且可控。

- [ ] **Runtime State Machine (執行狀態機)**
    - 實作明確狀態切換：`IDLE` -> `PLANNING` -> `EXECUTING` -> `VERIFYING` -> `RECOVERING` -> `DONE/FAILED`。
- [ ] **Observation Layer (觀測層)**
    - **Observability System**：追蹤 Token 用量、工具延遲 (Latency)、成功率、推理偏移 (Reasoning Drift) 及幻覺追蹤。
- [ ] **基礎 Harness**：部署 Ollama 與 Continue，建立基本的限制 (Constraints)。

### 階段二：認知架構與五層記憶 (Cognitive Architecture)
超越簡單的 RAG，構建完整的認知存儲體系。

- [ ] **Memory Hierarchy (五層記憶體系)**
    1. **Context (工作記憶)**：當前任務的 Short-term Buffer。
    2. **Prompt Memory (長期規則)**：系統級 Prompt 與 `CONVENTIONS.md`。
    3. **Process Memory (技能記憶)**：已固化的程序化知識 (Skills)。
    4. **Session Search (情節記憶)**：歷史對話與執行 Trace 的語義檢索。
    5. **User Modeling (個性模型)**：用戶偏好、工作風格與權限邊界。

### 階段三：技能編譯與經驗固化 (Skill Compiler & Evolution)
實現從「推理」到「演化」的關鍵：將任務路徑抽象為可重用能力。

- [ ] **Skill Compiler (技能編譯器)**
    - 將 `Execution Trace` -> `Abstraction` -> `Parameterization` -> `Skill Packaging`。
    - **經驗固化**：將複雜的 Python Debug 流程或資料抓取流程轉化為「原子化技能」。
- [ ] **Skill System 2.0**：實作參數化調用，減少 AI 每次「重新思考」的成本。

### 階段四：治理、沙箱與驗證 (Governance & Robustness)
進入企業級穩定性，確保 AI 在受控環境下運行。

- [ ] **Governance Layer (治理層)**
    - **Permission Gating**：敏感指令審核、預算限制 (Budget Limit)、上下文邊界保護。
- [ ] **Execution Loop with Verifier**
    - 實作 **Plan -> Execute -> Verify -> Repair**。
    - **Verifier Architecture**：引入獨立的驗證邏輯，防止 AI 「自己相信自己」。
- [ ] **Process Isolation (沙箱化)**
    - 完善 Docker / SSH 隔離環境，確保 `rm -rf` 等風險操作受限。

---

## 優化決策環 (Optimization Decision Loop)
當系統失效或效率下降時，按此順序診斷：

1. **Context Check**：環境資訊是否污染？Context 是否精確？
2. **Skill Check**：是否缺乏對應的程序記憶 (Skill)？Skill 定義是否模糊？
3. **Harness Check**：治理層是否過嚴？觀察層是否發現推理偏移？
4. **Prompt Check**：指令規則是否需要修正？
5. **Model Check**：CPU (LLM) 算力是否足以支撐當前複雜度？

---
> **Hermes 哲學：問題從來不是模型太弱，而是缺乏控制系統。**
*Last Updated: 2026-05-11*
