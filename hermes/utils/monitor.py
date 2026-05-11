import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class Monitor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.metrics = {
            "token_usage": {"input": 0, "output": 0, "total": 0},
            "latency": [],
            "errors": [],
            "tool_calls": 0,
            "success_rate": 0.0
        }
        self.traces: List[Dict[str, Any]] = []

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

    def add_trace(self, state: str, action: str, data: Any = None):
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
            "total_duration": sum(l["duration"] for l in self.metrics["latency"]),
            "timestamp": datetime.now().isoformat()
        }

    def export_traces(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"summary": self.get_summary(), "traces": self.traces}, f, indent=4, ensure_ascii=False)
