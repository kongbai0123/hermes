import http.server
import socketserver
import json
import os
from pathlib import Path
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider

PORT = int(os.getenv("HERMES_PORT", "8000"))
PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HERMES_WORKSPACE", str(PROJECT_ROOT))
DIRECTORY = str(PROJECT_ROOT / "hermes" / "api")

# 初始化 Hermes Runtime (使用 Mock 模式確保可立即執行)
runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path=str(PROJECT_ROOT / "hermes_mcp.json"))


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

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
        elif self.path == "/api/shell/pending":
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            actions = runtime.executor.shell_approval_manager.pending_actions
            data = [
                {
                    "id": proposal.id,
                    "command": proposal.command,
                    "cwd": proposal.cwd,
                    "reason": proposal.reason,
                    "risk": proposal.risk_level,
                    "status": proposal.status,
                    "created_at": proposal.created_at,
                }
                for proposal in actions.values()
                if proposal.status == "pending"
            ]
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
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
        elif self.path.startswith("/api/shell/approve/"):
            proposal_id = self.path.rsplit("/", 1)[-1]
            token = runtime.executor.shell_approval_manager.approve(proposal_id)
            if not token:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "Shell proposal ID not found or invalid."}, ensure_ascii=False).encode('utf-8'))
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"proposal_id": proposal_id, "token": token}, ensure_ascii=False).encode('utf-8'))
        elif self.path == "/api/shell/execute":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            proposal_id = post_data.get("proposal_id", "")
            token = post_data.get("token", "")
            result = runtime.executor.execute_approved_shell(proposal_id=proposal_id, approval_token=token)
            if not result.ok:
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"detail": result.error}, ensure_ascii=False).encode('utf-8'))
                return
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "message": "Shell command executed",
                "details": {
                    "summary": result.summary,
                    "content": result.content,
                    "metadata": result.metadata,
                }
            }, ensure_ascii=False).encode('utf-8'))

def main():
    print(f"[*] Hermes Agent OS Loading...")
    print(f"[*] Dashboard URL: http://localhost:{PORT}/dashboard.html")
    print(f"[*] API Server: Active")

    with ReusableTCPServer(("", PORT), HermesHandler) as httpd:
        print(f"[+] Hermes is LIVE. Please open the URL in your browser.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Stopping Hermes...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
