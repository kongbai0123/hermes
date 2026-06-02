import json
import urllib.request
import urllib.error
import sys
import os

# 設定終端機輸出為 UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==========================================
# 1. 定義「檔案操作」工具 (File Tools)
# ==========================================

WORKSPACE = "."  # 限制在當前資料夾操作

def list_files() -> str:
    """列出當前資料夾底下的所有檔案與資料夾名稱"""
    try:
        files = os.listdir(WORKSPACE)
        if not files:
            return "當前資料夾是空的。"
        return f"資料夾內的檔案列表：\n" + "\n".join([f"- {f}" for f in files])
    except Exception as e:
        return f"無法列出檔案列表：{e}"

def read_file_content(filename: str) -> str:
    """讀取指定文字檔案的內容"""
    try:
        # 防止目錄遍歷漏洞 (Directory Traversal)
        safe_path = os.path.basename(filename)
        full_path = os.path.join(WORKSPACE, safe_path)
        
        if not os.path.exists(full_path):
            return f"錯誤：找不到檔案 '{safe_path}'。"
            
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"檔案 '{safe_path}' 的內容如下：\n---\n{content}\n---"
    except Exception as e:
        return f"讀取檔案失敗：{e}"

def write_file_content(params_json: str) -> str:
    """
    建立新檔案或覆寫現有檔案。
    參數為 JSON 格式字串，例如：{"filename": "test.txt", "content": "哈囉"}
    """
    try:
        # 嘗試解析參數 JSON
        params = json.loads(params_json)
        filename = params.get("filename")
        content = params.get("content")
        
        if not filename or content is None:
            return "錯誤：參數必須包含 'filename' 和 'content'。"
            
        safe_path = os.path.basename(filename)
        full_path = os.path.join(WORKSPACE, safe_path)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功寫入檔案 '{safe_path}'！"
    except Exception as e:
        return f"寫入檔案失敗，請確認參數是否為有效的 JSON。錯誤原因：{e}"

# 工具映射表
TOOLS = {
    "list_files": list_files,
    "read_file_content": read_file_content,
    "write_file_content": write_file_content
}

# ==========================================
# 2. 系統提示詞 (System Prompt)
# ==========================================
SYSTEM_PROMPT = """你是一個本地檔案管理助理 Agent。你擁有操作本地檔案的能力，並且需要遵循 ReAct (Reasoning + Action) 流程。

你擁有以下工具可以使用：
1. list_files: 列出當前工作資料夾中的所有檔案。不需要參數。
2. read_file_content: 讀取某個特定檔案的文字內容。參數是檔案名稱字串，例如 "README.md"。
3. write_file_content: 寫入內容到某個檔案。參數是一個 JSON 字串，格式為：{"filename": "檔案名", "content": "檔案內容"}。

【輸出規範】：
如果你需要呼叫工具，你【必須】只輸出一個 JSON 物件，格式如下：
{
    "action": "工具名稱",
    "action_input": "工具參數（如果是 list_files 請帶空字串 \"\"；如果是 write_file_content 請帶 JSON 字串）"
}
注意：請不要加上 ```json 標記，直接輸出純 JSON。

當你取得工具的執行結果（Observation）後，你將在下一輪中看到它，並繼續思考。
當你完成任務時，請【直接以繁體中文回答】使用者的問題，不要輸出 JSON。
"""

# ==========================================
# 3. ReAct 執行循環
# ==========================================

def run_file_agent(user_query: str, model_name: str = "gemma4:latest", max_steps: int = 5):
    url = "http://localhost:11434/api/chat"
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    print("=" * 60)
    print(f"📂 檔案助理啟動，任務：'{user_query}'")
    print("=" * 60)
    
    for step in range(1, max_steps + 1):
        print(f"\n[步驟 {step}]")
        print("🧠 思考中...")
        
        data = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }
        
        try:
            json_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(url, data=json_data, headers={"Content-Type": "application/json"})
            
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                reply = res_json.get("message", {}).get("content", "").strip()
            
            messages.append({"role": "assistant", "content": reply})
            
            is_tool_call = False
            try:
                # 嘗試解析為 JSON 工具調用
                tool_call = json.loads(reply)
                action = tool_call.get("action")
                action_input = tool_call.get("action_input")
                
                if action in TOOLS:
                    is_tool_call = True
                    print(f"🛠️ 調用工具：{action}")
                    
                    tool_func = TOOLS[action]
                    # 執行工具
                    if action == "list_files":
                        observation = tool_func()
                    else:
                        observation = tool_func(action_input)
                        
                    print(f"📤 工具結果：\n{observation}")
                    
                    # 餵回 Observation
                    messages.append({
                        "role": "user",
                        "content": f"這是 {action} 工具的回傳結果 (Observation)：\n{observation}\n請根據此結果進行下一步。"
                    })
                else:
                    print(f"⚠️ [警告] 呼叫了不存在的工具：{action}")
                    messages.append({
                        "role": "user",
                        "content": f"錯誤：工具 '{action}' 不存在。請重新選擇可用工具。"
                    })
            except json.JSONDecodeError:
                pass
                
            if not is_tool_call:
                print("🏁 最終回答：")
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
        print("\n⚠️ 達到最大步驟限制，結束任務。")

if __name__ == "__main__":
    # 測試情境：列出檔案，讀取 01_chat.py 內容，然後生成一個摘要檔案！
    # 這是非常複雜的 Agent 多步任務！
    query = "先幫我列出當前資料夾的檔案，然後讀取 01_chat.py，最後寫一個名為 'summary.txt' 的檔案來簡短摘要它的功能。"
    run_file_agent(query)
