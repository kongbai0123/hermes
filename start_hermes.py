import http.server
import socketserver
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider, OllamaProvider
from hermes.api.files import list_workspace_files, read_workspace_file, stat_workspace_file, status_from_result

PORT = int(os.getenv("HERMES_PORT", "8000"))
PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HERMES_WORKSPACE", str(PROJECT_ROOT))
DIRECTORY = str(PROJECT_ROOT / "hermes" / "api")

# 初始化 Hermes Runtime
runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path=str(PROJECT_ROOT / "hermes_mcp.json"))

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def get_ollama_health(base_url="http://localhost:11434"):
    import urllib.request
    base_url = (base_url or "http://localhost:11434").rstrip("/")
    url = f"{base_url}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [m.get("name") for m in payload.get("models", []) if m.get("name")]
        return {
            "available": True,
            "base_url": base_url,
            "endpoint": url,
            "models": models,
            "error": "",
        }
    except Exception as e:
        return {
            "available": False,
            "base_url": base_url,
            "endpoint": url,
            "models": [],
            "error": str(e),
        }

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
        route = parsed.path.rstrip('/')
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
        elif route == "/api/patch/pending":
            patches = runtime.executor.approval_manager.pending_patches
            # 獲取當前授權狀態以便合併顯示
            grants = {g.scope_id: g for g in runtime.governance.scoped_grants if g.scope_type == "patch"}
            
            data = []
            for patch in patches.values():
                if patch.status != "pending":
                    continue
                
                data.append({
                    "id": patch.id,
                    "path": patch.path,
                    "reason": patch.reason,
                    "status": patch.status,
                    "created_at": patch.timestamp if hasattr(patch, 'timestamp') else "",
                    "grant": {
                        "is_authorized": patch.id in grants,
                        "expires_at": grants[patch.id].expires_at if patch.id in grants else None,
                        "granted_by": grants[patch.id].granted_by if patch.id in grants else None
                    } if patch.id in grants else None,
                    "changes": [
                        {
                            "path": change.path,
                            "operation": change.operation,
                            "reason": getattr(change, "reason", ""),
                            "original": getattr(change, "original", ""),
                            "replacement": getattr(change, "replacement", ""),
                        }
                        for change in patch.changes
                    ],
                })
            self._send_json(data)
        elif route == "/api/providers/health":
            base_url = query.get("base_url", ["http://localhost:11434"])[0]
            # 建立臨時 Provider 進行測試
            test_provider = OllamaProvider(base_url=base_url)
            health = test_provider.health_check()
            self._send_json({
                "ollama": {
                    "available": health["status"] == "ok",
                    "base_url": base_url,
                    "models": [m.get("name") for m in health.get("data", {}).get("models", [])] if health["status"] == "ok" else [],
                    "error": health.get("message")
                },
                "mock": {
                    "available": True,
                    "purpose": "UI flow test only"
                }
            })
        elif route == "/api/governance":
            data = {
                "budget": runtime.governance.token_budget,
                "consumed": runtime.governance.consumed_tokens,
                "permissions": runtime.governance.permissions,
                "scoped_grants": [
                    {
                        "permission": g.permission,
                        "scope_type": g.scope_type,
                        "scope_id": g.scope_id,
                        "expires_at": g.expires_at,
                        "granted_by": g.granted_by
                    }
                    for g in runtime.governance.scoped_grants
                ]
            }
            self._send_json(data)
        elif route.startswith("/api/"):
            self._send_json({
                "ok": False,
                "error": {
                    "code": "API_ROUTE_NOT_FOUND",
                    "message": f"Route not found: {route}",
                },
            }, status=404)
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        route = parsed.path.rstrip('/')
        
        if route == "/api/task":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            task = post_data.get("task", "")
            provider = post_data.get("provider", "ollama")
            model = post_data.get("model")
            base_url = post_data.get("base_url", "http://localhost:11434")
            temperature = float(post_data.get("temperature", 0.7))
            system_prompt = post_data.get("system_prompt")
            metadata = post_data.get("metadata")
            
            print(f"[Server] Received Task: {task}")
            try:
                runtime.configure_llm(create_llm_provider(
                    provider=provider,
                    model=model,
                    base_url=base_url,
                    temperature=temperature
                ))
                result = runtime.execute_task(task, user_system_prompt=system_prompt, task_metadata=metadata)
                self._send_json({
                    "message": "Task completed",
                    "task": task,
                    "result": result
                })
            except Exception as e:
                print(f"[Error] Task Execution Failed: {str(e)}")
                self._send_json({"detail": str(e)}, status=500)
        elif route == "/api/metrics/reset":
            runtime.monitor.reset()
            self._send_json(runtime.get_status())
        elif route.startswith("/api/shell/approve/"):
            proposal_id = route.rsplit("/", 1)[-1]
            token = runtime.executor.shell_approval_manager.approve(proposal_id)
            if not token:
                self._send_json({"detail": "Shell proposal ID not found or invalid."}, status=404)
                return
            self._send_json({"proposal_id": proposal_id, "token": token})
        elif route == "/api/shell/execute":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            proposal_id = post_data.get("proposal_id", "")
            token = post_data.get("token", "")
            result = runtime.executor.execute_approved_shell(proposal_id=proposal_id, approval_token=token)
            if not result.ok:
                self._send_json({"detail": result.error}, status=403)
                return
            self._send_json({
                "message": "Shell command executed",
                "details": {
                    "summary": result.summary,
                    "content": result.content,
                    "metadata": result.metadata,
                }
            })
        elif route.startswith("/api/patch/approve/"):
            patch_id = route.split("/")[-1]
            token = runtime.executor.approval_manager.approve(patch_id)
            if token:
                runtime.governance.grant_scoped_permission(
                    "filesystem_write",
                    scope_type="patch",
                    scope_id=patch_id,
                    ttl_seconds=60,
                    granted_by="user"
                )
                self._send_json({
                    "patch_id": patch_id, 
                    "token": token,
                    "grant": {
                        "permission": "filesystem_write",
                        "scope_type": "patch",
                        "scope_id": patch_id,
                        "ttl_seconds": 60
                    }
                })
            else:
                self._send_json({"error": "Patch not found"}, status=404)

        elif route.startswith("/api/patch/reject/"):
            patch_id = route.split("/")[-1]
            if patch_id in runtime.executor.approval_manager.pending_patches:
                # 撤銷相關授權
                runtime.governance.revoke_scoped_permission("filesystem_write", "patch", patch_id)
                # 從 pending 移除
                runtime.executor.approval_manager.pending_patches.pop(patch_id)
                self._send_json({"patch_id": patch_id, "status": "rejected"})
            else:
                self._send_json({"error": "Patch not found"}, status=404)

        elif route == "/api/patch/apply":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data)
            patch_id = params.get("patch_id")
            token = params.get("token")
            
            try:
                result = runtime.executor.apply_approved_patch(patch_id, token)
                if result.ok:
                    self._send_json({
                        "message": "Patch applied",
                        "details": {
                            "summary": result.summary,
                            "content": result.content,
                        }
                    })
                else:
                    self._send_json({"detail": result.error}, status=403)
            finally:
                if patch_id:
                    runtime.governance.revoke_scoped_permission(
                        "filesystem_write",
                        scope_type="patch",
                        scope_id=patch_id
                    )
        elif route == "/api/governance/grant":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            permission = post_data.get("permission", "")
            runtime.governance.grant_permission(permission)
            self._send_json({"ok": True, "permission": permission})
        elif route == "/api/governance/revoke":
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            permission = post_data.get("permission", "")
            runtime.governance.revoke_permission(permission)
            self._send_json({"ok": True, "permission": permission})
        else:
            self._send_json({"detail": "Route not found"}, status=404)

def main():
    with ReusableTCPServer(("", PORT), HermesHandler) as httpd:
        print(f"[Server] Hermes OS Dashboard running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Server] Shutting down...")
            httpd.shutdown()

if __name__ == "__main__":
    main()
