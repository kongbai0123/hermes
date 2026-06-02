# 學習筆記

## 路線

1. 先確認本機模型可以回覆。
2. 再加入記憶，理解 LLM 本身不會自動記住對話。
3. 加入工具，讓模型可以取得真實世界資訊。
4. 用 ReAct loop 讓模型能多步驟解題。
5. 把工具限制在 `workspace/`，避免誤讀或誤改系統檔案。
6. 產生 patch，不直接改檔。
7. 執行測試並分析失敗原因。

## 常用指令

```powershell
python lessons/01_ollama_chat.py
python lessons/04_react_loop.py
python agent/main.py
python -m unittest discover -s workspace/sample_project
```

## 第一版限制

- 不做 Web UI。
- 不做 RAG。
- 不直接套用 patch。
- 不執行任意 shell 指令。

