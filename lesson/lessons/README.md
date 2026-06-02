# Agent 實作課程詳細說明

為了避免數字重複混淆，並建立清晰的學習路徑，本資料夾已將課程分類為三個子目錄。

最方便的入口是：

```powershell
python LocalAgentTutor.py
```

---

## 第一軌：底層原理手寫軌 (`part1_raw_basics/`)
> **特色**：完全不依賴任何自訂模組或第三方套件，只用 Python 內建的 `urllib` 發送 HTTP 請求。適合用來理解 AI Agent 的底層通訊與邏輯運作。

* **執行目錄**：`G:\program\agent\lesson\`
* **執行命令範例**：`python lessons/part1_raw_basics/02_chat_with_memory.py`

### 01. 基礎連線與串流互動 (`01_chat.py`)
* **學習重點**：Ollama HTTP POST 與本地 `/api/chat` 對接、串流模式（Streaming）即時接收字詞、UTF-8 終端機編碼防錯處理。

### 02. 對話記憶機制 (`02_chat_with_memory.py`)
* **學習重點**：大語言模型的無狀態特性、如何在 Python 記憶體維護對話歷史陣列、System Prompt 角色定義。

### 03. 工具調用設計 (`03_tools.py`)
* **學習重點**：設計 System Prompt 來導引模型輸出特定 JSON，撰寫 Python 解析器攔截 JSON 並動態執行對應函數（例如 `get_current_time` 和 `calculator`）。

### 04. ReAct 思考與行動循環 (`04_react_agent.py`)
* **學習重點**：實作經典的 ReAct 流程 `Thought -> Action -> Observation -> Final Answer`。讓 Agent 自動推理並呼叫工具，取得結果後返回給大腦做二次思考。

### 05. 實用本地檔案整理助理 (`05_file_agent.py`)
* **學習重點**：給予 Agent 電腦實體工具（列出、讀取與寫入檔案），安全限制防止目錄遍歷漏洞，使 Agent 能夠自動化分析代碼並產出檔案摘要。

---

## 第二軌：模組化架構封裝軌 (`part2_modular_framework/`)
> **特色**：使用根目錄下封裝好的 `agent/` 模組。適合學習如何將 API 連線、記憶體管理、工具註冊與推理循環封裝成乾淨、可重用的模組。

* **執行目錄**：`G:\program\agent\lesson\`
* **執行命令範例**：`python lessons/part2_modular_framework/02_chat_memory.py`

### 01. 模組化模型生成 (`01_ollama_chat.py`)
* **學習重點**：將 Ollama 呼叫封裝至 `agent.llm.generate`，感受從幾十行 API 程式碼簡化成單行調用的效果。

### 02. 封裝的記憶體聊天 (`02_chat_memory.py`)
* **學習重點**：學習 `agent.memory` 如何物件化對話歷史，簡化聊天主迴圈程式。

### 03. 基礎工具封裝 (`03_tools_basic.py`)
* **學習重點**：學習註冊表設計模式（Registry Pattern），使新增、配置工具變得簡單一致。

### 04. 封裝的 ReAct 循環 (`04_react_loop.py`)
* **學習重點**：將整個 ReAct 重複推理邏輯抽出，成為一個通用的執行引擎。

### 05 至 08. 軟體工程自動化 Agent 系列
* **檔案列表**：
  * `05_code_reader.py` (讀取程式碼)
  * `06_patch_writer.py` (自動生成 Patch)
  * `07_test_runner.py` (自動跑 Pytest 測試)
  * `08_agent_cli.py` (終端互動工程師 Agent)
* **學習重點**：
  * **自主除錯雛形**：第一版不直接修改檔案，而是取得錯誤日誌、分析原因、產生 patch。這樣比較安全，也比較適合學習。

---

## 第三軌：實用技能補強軌 (`part3_practical_skills/`)
> **特色**：補上真正使用 agent 做事時需要的能力：Prompt 設計、安全邊界、Patch 審查、除錯工作流與 EXE 打包觀念。

* **執行目錄**：`G:\program\agent\lesson\`
* **執行命令範例**：`python lessons/part3_practical_skills/02_safety_boundaries.py`

### 01. Prompt 設計 (`01_prompt_design.py`)
* **學習重點**：比較鬆散 prompt 與結構化 prompt，理解輸出格式、角色、約束如何影響結果。

### 02. 安全邊界 (`02_safety_boundaries.py`)
* **學習重點**：測試路徑限制、命令白名單與禁止破壞性操作，理解為什麼 agent 不能一開始就全權操作電腦。

### 03. Patch 審查 (`03_patch_review.py`)
* **學習重點**：學會看 unified diff，判斷 agent 的修正是否只改必要範圍、是否需要補測試。

### 04. 除錯工作流 (`04_debug_workflow.py`)
* **學習重點**：把測試失敗、搜尋、讀檔、提出 patch 串成固定流程。

### 05. 打包 EXE 觀念 (`05_packaging_exe.py`)
* **學習重點**：理解 `.py` 是學習材料，`.exe` 是啟動器；打包不能取代閱讀與修改原始碼。
