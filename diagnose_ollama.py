import urllib.request
import json

def diagnose():
    print("=== Ollama Connection Diagnostic ===")
    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            print(f"[OK] Successfully connected to Ollama!")
            print(f"[Info] Available Models: {models}")
            if models:
                print(f"[Suggest] Please use one of these names in your code.")
            else:
                print("[Warning] No models found. Please run 'ollama pull llama3' first.")
    except Exception as e:
        print(f"[Error] Could not connect to Ollama: {str(e)}")
        print("[Suggest] Make sure Ollama is running and accessible at localhost:11434")

if __name__ == "__main__":
    diagnose()
