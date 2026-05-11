from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import time

@dataclass
class ToolPlan:
    """模型生成的工具執行計畫"""
    tool: str
    args: Dict[str, Any]
    reason: str = ""

@dataclass
class ToolResult:
    """工具執行後的標準回傳格式"""
    ok: bool
    tool: str
    summary: str
    content: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeTrace:
    """Runtime 執行過程中的事件追蹤"""
    event_type: str
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class CapabilityPolicy:
    """代理權限策略定義"""
    read_only: bool = True
    allow_shell: bool = False
    allow_write: bool = False
    workspace_root: str = "."
