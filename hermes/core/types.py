from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

@dataclass
class ToolPlan:
    """模型產生的工具執行計畫"""
    tool: str
    args: Dict[str, Any]
    reason: str = ""

@dataclass
class ToolResult:
    """工具執行的統一回傳格式"""
    ok: bool
    tool: str
    summary: str
    content: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeTrace:
    """系統執行軌跡事件"""
    event_type: Literal["USER_CMD", "PLAN_REQUEST", "TOOL_PLAN", "TOOL_CALL", "TOOL_RESULT", "LLM_FINAL", "HERMES_ERROR"]
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())

@dataclass
class CapabilityPolicy:
    """Agent 權限管控政策"""
    allow_read: bool = True
    allow_write: bool = False
    allow_shell: bool = False
    allow_network: bool = False
