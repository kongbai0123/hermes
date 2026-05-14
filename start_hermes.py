import http.server
import socketserver
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider
from hermes.api.files import list_workspace_files, read_workspace_file, stat_workspace_file, status_from_result

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

    def _send_json(self, payload, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/api/status":
            self._send_json(runtime.get_status())
        elif route == "/api/logs":
            self._send_json(runtime.monitor.get_serializable_traces())
        elif route in ("/api/files/list", "/files/list"):
            result = list_workspace_files(runtime.constraints.workspace_root, query.get("path", ["."])[0])
            self._send_json(result, status_from_result(result))
        elif route in ("/api/files/read", "/files/read"):
            result = read_workspace_file(runtime.constraints.workspace_root, query.get("path", [""])[0])
            self._send_json(result, status_from_result(result))
        elif route in ("/api/files/stat", "/files/stat"):
            result = stat_workspace_file(runtime.constraints.workspace_root, query.get("path", [""])[0])
            self._send_json(result, status_from_result(result))
        elif route == "/api/shell/pending":
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
            self._send_json(data)
        elif route == "/api/governance":
            data = {
                "budget": runtime.governance.token_budget,
                "consumed": runtime.governance.consumed_tokens,
                "permissions": runtime.governance.permissions
            }
            self._send_json(data)
        else:
            return super().do_GET()

    def do_POST(self):
        if self.path == "/api/task":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            task = post_data.get("task", "")
            provider = post_data.get("provider", "ollama")
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
