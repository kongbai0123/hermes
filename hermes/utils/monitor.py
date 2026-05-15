import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict
from hermes.core.types import RuntimeTrace

class Monitor:
    def __init__(self):
        self._initial_metrics = {
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "latency": [],
            "errors": [],
            "tool_calls": 0,
            "success_rate": 0.0
        }
        self.metrics = {
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "latency": [],
            "errors": [],
            "tool_calls": 0,
            "success_rate": 0.0
        }
        self.traces: List[Union[Dict[str, Any], RuntimeTrace]] = []

    def record_tokens(self, input_tokens: int, output_tokens: int):
        self.metrics["token_usage"]["input"] += input_tokens
        self.metrics["token_usage"]["output"] += output_tokens
        self.metrics["token_usage"]["total"] += (input_tokens + output_tokens)

    def record_latency(self, component: str, duration: float):
        self.metrics["latency"].append({
            "component": component,
            "duration": round(duration, 3),
            "timestamp": time.time()
        })

    def record_error(self, error_type: str, message: str, context: Optional[str] = None):
        self.metrics["errors"].append({
            "type": error_type,
            "message": message,
            "context": context,
            "timestamp": time.time()
        })

    def record_tool_call(self, ok: bool):
        self.metrics["tool_calls"] += 1
        if not ok:
            self.record_error("tool_call", "Tool call failed")

    def reset(self):
        self.metrics = {
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "latency": [],
            "errors": [],
            "tool_calls": 0,
            "success_rate": 0.0
        }
        self.traces = []

    def add_trace(self, state: str, action: str, data: Any = None):
        # 為了向後相容，保留字典格式的 add_trace
        self.traces.append({
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "action": action,
            "data": data
        })

    def get_summary(self) -> Dict[str, Any]:
        total_tool_calls = self.metrics["tool_calls"]
        total_errors = len(self.metrics["errors"])
        if total_tool_calls > 0:
            self.metrics["success_rate"] = round((total_tool_calls - total_errors) / total_tool_calls, 2)
        
        return {
            "metrics": self.metrics,
            "total_duration": sum(l["duration"] for l in self.metrics["latency"]) if self.metrics["latency"] else 0,
            "timestamp": datetime.now().isoformat()
        }

    def get_serializable_traces(self) -> List[Dict[str, Any]]:
        """將 traces 轉換為可序列化的字典清單"""
        serialized = []
        for t in self.traces:
            if hasattr(t, 'event_type'):
                # 如果是 RuntimeTrace (dataclass)
                item = asdict(t)
                # 為了前端相容，將 event_type 映射到 action，並加上 state 欄位
                item['action'] = t.event_type
                item['state'] = 'RUNTIME'
                item['timestamp'] = datetime.fromtimestamp(t.timestamp).isoformat()
                item['data'] = t.payload
                serialized.append(item)
            else:
                serialized.append(t)
        return serialized

    def export_traces(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.get_summary(), 
                "traces": self.get_serializable_traces()
            }, f, indent=4, ensure_ascii=False)
