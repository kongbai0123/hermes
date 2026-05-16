from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Literal
from hermes.core.runtime import HermesRuntime

@dataclass
class ValidationTask:
    name: str
    task: str
    expected_outcome: Literal["done", "rejected", "failed"]
    expected_intent: Optional[str] = None
    expected_status: Optional[str] = None  # e.g. "DONE", "FAILED"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    name: str
    success: bool
    actual_outcome: str
    actual_status: str
    actual_intent: Optional[str] = None
    reason: str = ""
    error_message: Optional[str] = None

class ValidationRunner:
    """
    Validation Runner: 負責執行安全與功能性測試套件，並比對預期與實際執行結果。
    """
    def __init__(self, runtime: HermesRuntime):
        self.runtime = runtime

    def run_case(self, case: ValidationTask) -> ValidationResult:
        """執行單一驗證案例"""
        # 執行任務
        result = self.runtime.execute_task(case.task)
        actual_status = result.get("status", "UNKNOWN")
        
        # 從 Trace 中提取 Intent
        actual_intent = None
        traces = self.runtime.monitor.traces
        exec_decisions = [t for t in traces if getattr(t, 'event_type', None) == "EXECUTIVE_DECISION"]
        if exec_decisions:
            actual_intent = exec_decisions[0].payload.get("intent")
        
        # 判定 Outcome
        # rejected: 任務因管理策略被阻擋 (status == FAILED 且有 rejection 訊息)
        # failed: 任務在執行過程中出錯
        # done: 任務順利完成
        
        is_rejected = actual_status == "FAILED" and "Rejected by ManagementPolicy" in (result.get("error") or "")
        
        actual_outcome = "unknown"
        if is_rejected:
            actual_outcome = "rejected"
        elif actual_status == "DONE":
            actual_outcome = "done"
        elif actual_status == "FAILED":
            actual_outcome = "failed"
            
        # 比對邏輯
        success = True
        reasons = []
        
        if case.expected_outcome != actual_outcome:
            success = False
            reasons.append(f"Expected outcome '{case.expected_outcome}', got '{actual_outcome}'")
            
        if case.expected_status and case.expected_status != actual_status:
            success = False
            reasons.append(f"Expected status '{case.expected_status}', got '{actual_status}'")
            
        if case.expected_intent and case.expected_intent != actual_intent:
            success = False
            reasons.append(f"Expected intent '{case.expected_intent}', got '{actual_intent}'")
            
        reason_str = " | ".join(reasons) if not success else "Outcome matched expectation."
        
        return ValidationResult(
            name=case.name,
            success=success,
            actual_outcome=actual_outcome,
            actual_status=actual_status,
            actual_intent=actual_intent,
            reason=reason_str,
            error_message=result.get("error")
        )

    def run_suite(self, suite: List[ValidationTask]) -> List[ValidationResult]:
        """執行整組測試套件"""
        results = []
        for case in suite:
            results.append(self.run_case(case))
        return results
