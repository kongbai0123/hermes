import json
import urllib.request
import urllib.error
import sys
import datetime

# 設定終端機輸出為 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==========================================
# 1. 定義 Agent 的「工具」(Tools)
# ==========================================

def get_current_time() -> str:
    """取得目前的系統時間"""
    now = datetime.datetime.now()
    return f"目前的系統時間是：{now.strftime('%Y-%m-%d %H:%M:%S')}"

def calculator(expression: str) -> str:
    """計算數學表達式的值 (例如 '123 * 456')"""
    try:
        # 安全地評估數學表達式（限制只能包含數字與運算子）
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "錯誤：表達式包含非法字元，安全限制只允許數學運算。"
        
        # 使用 eval 計算結果
        result = eval(expression)
        return f"計算結果：{expression} = {result}"
    except Exception as e:
        return f"計算錯誤：{e}"

# 將工具打包成一個字典，方便後面調用
TOOLS = {
    "get_current_time": get_current_time,
    "calculator": calculator
}

# ==========================================
# 2. 定義系統提示詞 (System Prompt)
# ==========================================
# 我們告訴模型有哪些工具可用，以及如果想用工具，必須輸出特定格式的 JSON。
SYSTEM_PROMPT = """你是一個配備了工具的智慧 Agent。你必須決定是否需要呼叫工具來回答使用者的問題。

你有以下工具可以使用：
1. 工具名稱: get_current_time
   說明: 當使用者詢問目前的日期或時間時使用。不需要參數。
   
2. 工具名稱: calculator
   說明: 當需要進行數學計算時使用。
   參數: 一個字串，代表要計算的數學表達式，例如 "245 * 789" 或 "(12 + 8) / 2"。

如果你需要使用工具，你【必須】只輸出一個 JSON 物件，格式如下：
{
    "action": "工具名稱",
    "action_input": "工具參數（如果是 get_current_time 請留空字串 \"\"）"
}

如果你不需要使用任何工具就能回答問題，請直接用繁體中文回答使用者，不要輸出 JSON。
請記得，不要在 JSON 前後加上 Markdown 的 ```json 標籤，只輸出純 JSON 文字。
"""

# ==========================================
# 3. 核心 API 請求函式
# ==========================================

def run_agent_turn(user_query: str, model_name: str = "gemma4:latest"):
    url = "http://localhost:11434/api/chat"
    
    # 建構訊息，包含 System Prompt 和使用者的問題
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    data = {
        "model": model_name,
        "messages": messages,
        "stream": False  # 本節課關閉串流，方便我們完整拿到 JSON 後進行解析
    }
    
    try:
        json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=json_data, headers={"Content-Type": "application/json"})
        
        print(f"使用者問題：'{user_query}'")
        print("🧠 Agent 思考中...")
        
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            reply = res_json.get("message", {}).get("content", "").strip()
            
        print(f"🤖 Agent 的回應：\n{reply}\n")
        
        # ==========================================
        # 4. 解析 Agent 的輸出並決定是否執行工具
        # ==========================================
        # 嘗試解析回傳內容是否為 JSON
        is_tool_call = False
        try:
            tool_call = json.loads(reply)
            action = tool_call.get("action")
            action_input = tool_call.get("action_input")
            
            if action in TOOLS:
                is_tool_call = True
                print(f"🛠️ [系統偵測] Agent 要求執行工具：{action}")
                print(f"📥 [系統偵測] 工具參數：'{action_input}'")
                
                # 執行對應的 Python 函數
                tool_func = TOOLS[action]
                if action == "get_current_time":
                    observation = tool_func()
                else:
                    observation = tool_func(action_input)
                
                print(f"📤 [系統執行結果] {observation}")
                
                # 接下來在 Lesson 4，我們將把這個結果（Observation）餵回給模型讓它做最終回答！
            else:
                print(f"⚠️ [系統警告] Agent 輸出了 JSON 但工具名稱 '{action}' 不存在。")
        except json.JSONDecodeError:
            # 如果不是 JSON，代表模型認為不需要工具，直接回答了
            pass
            
        if not is_tool_call:
            print("💬 [系統偵測] Agent 決定直接回答，無須呼叫工具。")
            
    except urllib.error.URLError as e:
        print(f"[錯誤] 無法連線至 Ollama：{e}")
    except Exception as e:
        print(f"[錯誤] 發生未知錯誤：{e}")

if __name__ == "__main__":
    print("=" * 60)
    print(" 測試情境 A：詢問時間（需要呼叫 get_current_time 工具）")
    print("=" * 60)
    run_agent_turn("請問現在幾點幾分？")
    
    print("\n" + "=" * 60)
    print(" 測試情境 B：數學計算（需要呼叫 calculator 工具）")
    print("=" * 60)
    run_agent_turn("幫我算一下 245 乘以 789 是多少？")
    
    print("\n" + "=" * 60)
    print(" 測試情境 C：一般閒聊（不需要任何工具）")
    print("=" * 60)
    run_agent_turn("你好，今天天氣真不錯！")
