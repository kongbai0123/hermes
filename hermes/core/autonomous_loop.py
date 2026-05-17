from typing import List, Dict, Any
from .autonomy_backoff import BackoffManager

class AutonomousLoop:
    """
    Hermes Autonomous Loop (核心邏輯簡化版)
    整合了 BackoffManager 以避免在連續錯誤中無限迴圈。
    """
    def __init__(self, max_failures: int = 2):
        self.backoff_manager = BackoffManager(max_consecutive_failures=max_failures)
        self.trace_log: List[str] = []

    def run(self, mock_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        執行自主迴圈 (此處接收 mock 的執行序列以供測試)。
        """
        self.trace_log.append("LOOP_STARTED")

        for step, task in enumerate(mock_tasks):
            tool = task.get("tool", "unknown_tool")
            is_mock_success = task.get("success", True)
            error_msg = task.get("error_msg", "Mock execution failed")

            # 在執行任何工具前，檢查是否已經處於 Backoff 狀態
            if self.backoff_manager.is_blocked():
                self.trace_log.append("BLOCKED_BY_BACKOFF")
                return self._generate_backoff_response()

            # 模擬執行工具
            self.trace_log.append(f"EXECUTING: {tool}")
            
            if is_mock_success:
                self.backoff_manager.record_success(tool)
                self.trace_log.append(f"SUCCESS: {tool}")
            else:
                is_now_blocked = self.backoff_manager.record_failure(tool, error_msg)
                self.trace_log.append(f"FAILURE: {tool}")
                
                # 如果這一次失敗導致達到閾值，立即中斷迴圈
                if is_now_blocked:
                    self.trace_log.append("BACKOFF_TRIGGERED")
                    return self._generate_backoff_response()

        self.trace_log.append("LOOP_COMPLETED")
        return {"status": "COMPLETED", "trace": self.trace_log}

    def _generate_backoff_response(self) -> Dict[str, Any]:
        """生成標準的 Backoff 中止回應"""
        status = self.backoff_manager.get_backoff_status()
        return {
            "status": "FAILED",
            "error": "TOOL_FAILURE_BACKOFF",
            "reason": "Agent execution paused due to consecutive tool failures. Human intervention required.",
            "details": status,
            "trace": self.trace_log
        }
