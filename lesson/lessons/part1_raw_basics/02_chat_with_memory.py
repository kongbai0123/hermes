import json
import urllib.request
import urllib.error
import sys

# 設定終端機輸出為 UTF-8 避免 Windows CP950 編碼錯誤
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def chat_loop(model_name: str = "gemma4:latest"):
    """
    對話記憶 (Memory) 實作：
    我們會在記憶體中維護一個 messages 陣列，把每一次的對話紀錄（User 與 Assistant）
    都往內加，並在每一次發送請求時，將「整個對話歷史」傳送給模型。
    """
    url = "http://localhost:11434/api/chat"
    
    # 這是我們的對話記憶庫 (Memory)
    # 我們可以先加入一個 System Prompt，告訴模型如何扮演角色
    messages = [
        {
            "role": "system",
            "content": "你是一個熱心且有耐心的 AI 助手。請用繁體中文回答。"
        }
    ]
    
    print("=" * 50)
    print(f"  已載入本地模型: {model_name}")
    print("  記憶機制已啟動。輸入 'exit' 或 'quit' 可結束對話。")
    print("=" * 50)
    
    while True:
        try:
            # 取得使用者輸入
            user_input = input("\n你: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                print("對話結束，再見！")
                break
            
            # 1. 將使用者的話加入記憶中 (User Message)
            messages.append({"role": "user", "content": user_input})
            
            # 2. 準備傳送給 Ollama API 的 JSON 資料 (包含完整的 messages 歷史)
            data = {
                "model": model_name,
                "messages": messages,
                "stream": True
            }
            
            json_data = json.dumps(data).encode("utf-8")
            
            # 建立 HTTP 請求
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={"Content-Type": "application/json"}
            )
            
            print("助手: ", end="", flush=True)
            
            # 用來儲存模型這次回答的完整內容，待會要寫入記憶
            assistant_reply = ""
            
            # 發送 POST 請求並讀取串流回應
            with urllib.request.urlopen(req) as response:
                for line in response:
                    if line:
                        decoded_line = line.decode("utf-8").strip()
                        chunk = json.loads(decoded_line)
                        
                        content = chunk.get("message", {}).get("content", "")
                        print(content, end="", flush=True)
                        
                        # 累積回答內容
                        assistant_reply += content
                        
                        if chunk.get("done", False):
                            print()  # 換行
            
            # 3. 將模型的回答加入記憶中 (Assistant Message)
            messages.append({"role": "assistant", "content": assistant_reply})
            
        except urllib.error.URLError as e:
            print(f"\n[錯誤] 無法連線至 Ollama 伺服器：{e}")
            break
        except KeyboardInterrupt:
            print("\n對話被強制結束。")
            break
        except Exception as e:
            print(f"\n[錯誤] 發生未知錯誤：{e}")

if __name__ == "__main__":
    chat_loop()
