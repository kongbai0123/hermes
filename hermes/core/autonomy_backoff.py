import logging
from typing import Dict, List, Any

class BackoffManager:
    """
    Hermes Autonomy Backoff Manager
    負責監控連續的工具執行失敗。當連續失敗次數達到閾值時，
    阻擋進一步的操作並發出 TOOL_FAILURE_BACKOFF 狀態。
    """
    def __init__(self, max_consecutive_failures: int = 2):
        self.max_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.failure_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)

    def record_failure(self, tool_name: str, error_msg: str) -> bool:
        """
        記錄一次工具失敗。若達到閾值則回傳 True (觸發 Backoff)。
        """
        self.consecutive_failures += 1
        self.failure_history.append({"tool": tool_name, "error": error_msg})
        
        self.logger.warning(f"[Backoff] Tool '{tool_name}' failed. Consecutive: {self.consecutive_failures}/{self.max_failures}")
        
        return self.is_blocked()

    def record_success(self, tool_name: str) -> None:
        """
        記錄一次工具成功，重置連續失敗計數器。
        """
        if self.consecutive_failures > 0:
            self.logger.info(f"[Backoff] Tool '{tool_name}' succeeded. Resetting consecutive failures from {self.consecutive_failures} to 0.")
        self.consecutive_failures = 0
        self.failure_history.clear()

    def is_blocked(self) -> bool:
        """
        檢查目前是否處於 Backoff 阻擋狀態。
        """
        return self.consecutive_failures >= self.max_failures

    def get_backoff_status(self) -> Dict[str, Any]:
        """
        取得阻擋狀態的詳細資訊，供 Trace 或 UI 呈現。
        """
        return {
            "is_blocked": self.is_blocked(),
            "consecutive_failures": self.consecutive_failures,
            "max_failures": self.max_failures,
            "history": self.failure_history
        }
