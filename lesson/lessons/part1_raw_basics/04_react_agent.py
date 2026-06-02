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
# 1. 定義工具 (Tools)
# ==========================================

def get_current_time() -> str:
    """取得目前的系統時間"""
    now = datetime.datetime.now()
    return f"目前的系統時間是：{now.strftime('%Y-%m-%d %H:%M:%S')}"

def calculator(expression: str) -> str:
    """計算數學表達式的值 (例如 '123 * 456')"""
    try:
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "錯誤：表達式包含非法字元，安全限制只允許數學運算。"
        
        result = eval(expression)
        return f"計算結果：{expression} = {result}"
    except Exception as e:
        return f"計算錯誤：{e}"

TOOLS = {
    "get_current_time": get_current_time,
    "calculator": calculator
}

# ==========================================
# 2. ReAct 系統提示詞 (System Prompt)
# ==========================================
SYSTEM_PROMPT = """你是一個具有推理與行動能力的 AI Agent。你將遵循以下 ReAct (Reasoning + Action) 流程來解決使用者的問題：

每一輪，你必須決定是否需要使用工具來獲得答案。
你有以下工具可以使用：
1. get_current_time: 獲取當前日期與時間。無需參數。
2. calculator: 計算數學表達式。參數為表達式字串（例如 "245 * 789"）。

【輸出規範】：
如果你需要呼叫工具，你【必須】只輸出一個 JSON 物件，格式如下：
{
    "action": "工具名稱",
    "action_input": "工具參數（若是 get_current_time 請帶空字串 \"\"）"
}
注意：請不要加上 ```json 標記，直接輸出純 JSON。

當你取得工具的執行結果（Observation）後，你將在下一輪中看到它。
如果你已經擁有足夠的資訊，或者不需要工具，請【直接以繁體中文回答】使用者的問題，不要輸出 JSON。
"""

# ==========================================
# 3. ReAct 執行循環 (ReAct Loop)
# ==========================================

def run_react_agent(user_query: str, model_name: str = "gemma4:latest", max_steps: int = 5):
    url = "http://localhost:11434/api/chat"
    
    # 建立最初的對話歷史，包含系統提示詞與使用者問題
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    print("=" * 60)
    print(f"🚀 開始執行任務：'{user_query}'")
    print("=" * 60)
    
    # 開始 ReAct 思考與行動循環
    for step in range(1, max_steps + 1):
        print(f"\n[步驟 {step}]")
        print("🧠 Agent 思考中...")
        
        data = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }
        
        try:
            # 發送請求給本地 LLM
            json_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=json_data, headers={"Content-Type": "application/json"})
            
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                reply = res_json.get("message", {}).get("content", "").strip()
            
            # 將模型這一輪的輸出加入歷史紀錄
            messages.append({"role": "assistant", "content": reply})
            
            # 檢查模型是否發起工具調用
            is_tool_call = False
            try:
                # 嘗試將回覆解析成 JSON
                tool_call = json.loads(reply)
                action = tool_call.get("action")
                action_input = tool_call.get("action_input")
                
                if action in TOOLS:
                    is_tool_call = True
                    print(f"🎯 Agent 決定使用工具：{action}")
                    print(f"📥 輸入參數：'{action_input}'")
                    
                    # 執行工具
                    tool_func = TOOLS[action]
                    if action == "get_current_time":
                        observation = tool_func()
                    else:
                        observation = tool_func(action_input)
                    
                    print(f"📤 工具回傳結果 (Observation)：{observation}")
                    
                    # 將工具回傳的結果，作為 User 的回饋餵給模型，讓它在下一步繼續思考
                    messages.append({
                        "role": "user", 
                        "content": f"這是 {action} 工具的回傳結果 (Observation)：{observation}。請根據此結果進行下一步回答或思考。"
                    })
                else:
                    print(f"⚠️ [警告] Agent 呼叫了不存在的工具：{action}")
                    messages.append({
                        "role": "user",
                        "content": f"錯誤：工具 '{action}' 不存在。請重新選擇 get_current_time 或 calculator，或者直接回答。"
                    })
                    
            except json.JSONDecodeError:
                # 如果無法解析為 JSON，說明模型給出了最終答案
                pass
            
            # 如果沒有發起工具調用，代表這就是最終答案，結束循環！
            if not is_tool_call:
                print("🏁 Agent 給出最終回答：")
                print("-" * 40)
                print(reply)
                print("-" * 40)
                break
                
        except urllib.error.URLError as e:
            print(f"[錯誤] 無法連線至 Ollama：{e}")
            break
        except Exception as e:
            print(f"[錯誤] 發生未知錯誤：{e}")
            break
    else:
        print("\n⚠️ 達到最大思考步驟上限，強制終止 Agent。")

if __name__ == "__main__":
    # 我們給它一個需要「時間」和「計算」相結合的複雜問題！
    # 範例問題：計算現在的年份乘以 2 是多少？
    # 這個問題需要先用 get_current_time 查時間，取得年份 (2026)，再用 calculator 計算 (2026 * 2)。
    run_react_agent("請問現在的年份乘以 2 等於多少？")
