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

def chat_with_model(prompt: str, model_name: str = "gemma4:latest"):
    """
    與本地運行的 Ollama 模型進行對話，並即時串流輸出結果。
    我們只使用 Python 內建的 urllib 庫，不需要安裝任何額外的套件！
    """
    url = "http://localhost:11434/api/chat"
    
    # 建立傳送給 Ollama API 的 JSON 資料
    data = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": True  # 開啟串流模式，讓模型可以一個字一個字吐出回答
    }
    
    # 將資料編碼為 bytes
    json_data = json.dumps(data).encode("utf-8")
    
    # 建立 HTTP 請求
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"正在傳送問題給 {model_name}...")
    print("回答: ", end="", flush=True)
    
    try:
        # 發送 POST 請求並讀取串流回應
        with urllib.request.urlopen(req) as response:
            for line in response:
                if line:
                    # 解析每一行回傳的 JSON 區塊
                    decoded_line = line.decode("utf-8").strip()
                    chunk = json.loads(decoded_line)
                    
                    # 取得模型產生的字詞
                    content = chunk.get("message", {}).get("content", "")
                    print(content, end="", flush=True)
                    
                    # 如果完成，跳行
                    if chunk.get("done", False):
                        print("\n")
                        
    except urllib.error.URLError as e:
        print(f"\n[錯誤] 無法連線至 Ollama 伺服器：{e}")
        print("請確認您已開啟 Ollama，且模型名稱正確！")
    except Exception as e:
        print(f"\n[錯誤] 發生未知錯誤：{e}")

if __name__ == "__main__":
    # 測試提示詞
    user_prompt = "請用一句話解釋什麼是人工智慧 Agent？"
    chat_with_model(user_prompt)
