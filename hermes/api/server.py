from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, create_llm_provider # 預設使用 Mock 以利展示

app = FastAPI(title="Hermes Agent OS API")

# 全域 Runtime 實例
runtime = HermesRuntime(llm_provider=MockLLMProvider())

class TaskRequest(BaseModel):
    task: str
    provider: str = "mock"
    model: Optional[str] = None
    base_url: str = "http://localhost:11434"
    temperature: float = 0.7
    system_prompt: Optional[str] = None

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
    result = runtime.execute_task(request.task, user_system_prompt=request.system_prompt)
    return {"message": "Task completed", "task": request.task, "result": result}

@app.get("/api/status")
async def get_status():
    return runtime.get_status()

@app.get("/api/logs")
async def get_logs():
    return runtime.monitor.traces

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

@app.get("/api/memory/sessions")
async def get_sessions():
    return runtime.memory.semantic.data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
