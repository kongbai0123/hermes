from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from pathlib import Path

from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider
from hermes.api.files import list_workspace_files, read_workspace_file, stat_workspace_file, status_from_result

app = FastAPI(title="Hermes Agent OS API")

# 啟用 CORS 支援，允許 Workbench 從不同來源 (如 Live Server) 呼叫 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 獲取當前檔案所在目錄，確保路徑解析正確
BASE_DIR = Path(__file__).resolve().parent

# 全域 Runtime 實例
runtime = HermesRuntime(llm_provider=MockLLMProvider(), mcp_config_path="hermes_mcp.json")

# 掛載靜態檔案目錄 (用於 api.js, renderers.js 等)
static_path = BASE_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    app.mount("/api/static", StaticFiles(directory=str(static_path)), name="api_static")

class TaskRequest(BaseModel):
    task: str
    provider: str = "ollama"
    model: Optional[str] = None
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PermissionUpdateRequest(BaseModel):
    permission: str
    enabled: bool

@app.post("/api/task")
async def create_task(request: TaskRequest):
    if runtime.is_running:
        raise HTTPException(status_code=400, detail="Agent is already busy with another task.")
    
    llm_provider = create_llm_provider(
        provider=request.provider,
        model=request.model,
        base_url=request.base_url,
        temperature=request.temperature
    )
    runtime.configure_llm(llm_provider)

    # 目前仍是同步執行，但會回傳可顯示給使用者的結果。
    result = runtime.execute_task(
        request.task,
        user_system_prompt=request.system_prompt,
        task_metadata=request.metadata,
    )
    return {"message": "Task completed", "task": request.task, "result": result}

@app.get("/api/status")
async def get_status():
    return runtime.get_status()

@app.get("/api/logs")
async def get_logs():
    return runtime.monitor.get_serializable_traces()

@app.post("/api/metrics/reset")
async def reset_metrics():
    runtime.monitor.reset()
    return runtime.get_status()

@app.get("/api/governance/status")
async def get_governance():
    return {
        "budget": {
            "limit": runtime.governance.token_budget,
            "consumed": runtime.governance.consumed_tokens,
            "remaining": runtime.governance.token_budget - runtime.governance.consumed_tokens
        },
        "permissions": runtime.governance.permissions
    }

@app.patch("/api/governance/permission")
async def update_permission(request: PermissionUpdateRequest):
    if request.enabled:
        runtime.governance.grant_permission(request.permission)
    else:
        runtime.governance.revoke_permission(request.permission)
    return {"message": f"Permission {request.permission} updated to {request.enabled}"}

@app.get("/api/skills")
async def list_skills():
    return runtime.skills.list_skills()

@app.get("/api/patch/pending")
async def get_pending_patches():
    # 獲取暫存在 executor 中的提議
    patches = runtime.executor.approval_manager.pending_patches
    return [
        {
            "id": p.id,
            "task": p.task_id,
            "status": p.status,
            "risk": p.risk_level,
            "diff": runtime.executor.diff_engine.generate_patch_diff(p)
        } for p in patches.values() if p.status == "pending"
    ]

@app.post("/api/patch/approve/{patch_id}")
async def approve_patch(patch_id: str):
    token = runtime.executor.approval_manager.approve(patch_id)
    if not token:
        raise HTTPException(status_code=404, detail="Patch ID not found or invalid.")
    return {"patch_id": patch_id, "token": token}

@app.post("/api/patch/apply")
async def apply_patch(patch_id: str = Body(...), token: str = Body(...)):
    result = runtime.executor.apply_approved_patch(patch_id, token)
    if not result.ok:
        raise HTTPException(status_code=403, detail=result.error)
    return {"message": "Patch applied successfully", "details": result.summary}

@app.get("/api/shell/pending")
async def get_pending_shell_actions():
    actions = runtime.executor.shell_approval_manager.pending_actions
    return [
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

@app.post("/api/shell/approve/{proposal_id}")
async def approve_shell_action(proposal_id: str):
    token = runtime.executor.shell_approval_manager.approve(proposal_id)
    if not token:
        raise HTTPException(status_code=404, detail="Shell proposal ID not found or invalid.")
    return {"proposal_id": proposal_id, "token": token}

@app.post("/api/shell/execute")
async def execute_shell_action(proposal_id: str = Body(...), token: str = Body(...)):
    result = runtime.executor.execute_approved_shell(proposal_id=proposal_id, approval_token=token)
    if not result.ok:
        raise HTTPException(status_code=403, detail=result.error)
    return {
        "message": "Shell command executed",
        "details": {
            "summary": result.summary,
            "content": result.content,
            "metadata": result.metadata,
        }
    }

@app.get("/api/memory/sessions")
async def get_sessions():
    return runtime.memory.semantic.data

@app.get("/files/list")
@app.get("/api/files/list")
async def list_files(path: str = "."):
    result = list_workspace_files(runtime.constraints.workspace_root, path)
    return JSONResponse(result, status_code=status_from_result(result))

@app.get("/files/read")
@app.get("/api/files/read")
async def read_file(path: str):
    result = read_workspace_file(runtime.constraints.workspace_root, path)
    return JSONResponse(result, status_code=status_from_result(result))

@app.get("/api/files/stat")
async def stat_file(path: str):
    result = stat_workspace_file(runtime.constraints.workspace_root, path)
    return JSONResponse(result, status_code=status_from_result(result))

@app.get("/")
async def serve_dashboard():
    dashboard_path = BASE_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    raise HTTPException(status_code=404, detail="dashboard.html not found in api directory")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
