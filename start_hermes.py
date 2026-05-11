import http.server
import socketserver
import json
import os
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider

PORT = 8000
DIRECTORY = "hermes/api"

# 初始化 Hermes Runtime (使用 Mock 模式確保可立即執行)
runtime = HermesRuntime(llm_provider=MockLLMProvider())

class HermesHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(runtime.get_status(), ensure_ascii=False).encode('utf-8'))
        elif self.path == "/api/logs":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            traces = runtime.monitor.get_serializable_traces()
            self.wfile.write(json.dumps(traces, ensure_ascii=False).encode('utf-8'))
        elif self.path == "/api/governance":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            data = {
                "budget": runtime.governance.token_budget,
                "consumed": runtime.governance.consumed_tokens,
                "permissions": runtime.governance.permissions
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == "/api/task":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            task = post_data.get("task", "")
            provider = post_data.get("provider", "mock")
            model = post_data.get("model")
            base_url = post_data.get("base_url", "http://localhost:11434")
            temperature = float(post_data.get("temperature", 0.7))
            system_prompt = post_data.get("system_prompt")
            
            # 非同步模擬執行
            print(f"[Server] Received Task: {task}")
            runtime.configure_llm(create_llm_provider(
                provider=provider,
                model=model,
                base_url=base_url,
                temperature=temperature
            ))
            result = runtime.execute_task(task, user_system_prompt=system_prompt)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "Task completed",
                "task": task,
                "result": result
            }, ensure_ascii=False).encode('utf-8'))
        elif self.path == "/api/metrics/reset":
            runtime.monitor.reset()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(runtime.get_status(), ensure_ascii=False).encode('utf-8'))

print(f"[*] Hermes Agent OS Loading...")
print(f"[*] Dashboard URL: http://localhost:{PORT}/dashboard.html")
print(f"[*] API Server: Active")

with socketserver.TCPServer(("", PORT), HermesHandler) as httpd:
    print(f"[+] Hermes is LIVE. Please open the URL in your browser.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping Hermes...")
        httpd.shutdown()
