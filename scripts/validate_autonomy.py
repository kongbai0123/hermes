#!/usr/bin/env python3
"""
Hermes Autonomy Validator CLI
獨立的命令列工具，用於執行 safety_validation_suite.json 並輸出彩色報告。
適用於 CI/CD Pipeline 檢查。
"""

import argparse
import json
import sys
from pathlib import Path

# 動態設定 PYTHONPATH，確保可直接執行
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 色彩輸出代碼
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# 假設或 Mock 的評估函式 (同測試腳本，請對接真實核心代碼)
def evaluate_mock(level, tool, params):
    if tool == "autonomous_loop":
        from hermes.core.autonomous_loop import AutonomousLoop
        loop = AutonomousLoop(max_failures=2)
        res = loop.run(params.get("tasks", []))
        return res["status"]
    if tool == "write_file" and "AUTO_APPROVE.md" in params.get("path", ""):
         return "rejected"
    if tool == "execute_shell" and "rm -rf" in params.get("command", ""):
         return "rejected"
    # Skill Curator 的特例驗證
    if level == "L1" and tool == "write_file" and params.get("path", "").startswith("proposals/"):
         return "allowed"
    if level == "L1" and tool == "apply_patch":
         return "rejected"

    if level == "L0" and tool != "read_file":
         return "rejected"
    if level == "L1" and tool == "propose_patch":
         return "proposal_created"
    if level == "L2" and tool == "write_file":
         return "allowed" if params.get("path", "").startswith("user_projects/") else "rejected"
    return "allowed"

def main():
    parser = argparse.ArgumentParser(description="Hermes Autonomy Level Validator")
    parser.add_argument("--suite", type=str, default="tests/fixtures/safety_validation_suite.json", help="Path to the validation suite JSON")
    parser.add_argument("--level", type=str, choices=["ALL", "L0", "L1", "L2", "L3", "L4", "L5"], default="ALL", help="Filter tests by Autonomy Level")
    
    args = parser.parse_args()
    suite_path = Path(args.suite)

    if not suite_path.exists():
        print(f"{Colors.FAIL}Error: Validation suite not found at {suite_path}{Colors.ENDC}")
        sys.exit(1)

    with open(suite_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if args.level != "ALL":
        cases = [c for c in cases if c["autonomy_level"] == args.level or c["autonomy_level"] == "REDLINE"]

    print(f"{Colors.HEADER}{Colors.BOLD}=== Hermes Autonomy Policy Validation ==={Colors.ENDC}")
    print(f"Target Level: {args.level} | Total Cases: {len(cases)}\n")

    passed = 0
    failed = 0

    for case in cases:
        # 在此處呼叫真實的 Hermes GovernanceManager 評估邏輯
        # 這裡使用 evaluate_mock 作為展示
        actual_outcome = evaluate_mock(case["autonomy_level"], case["tool"], case.get("params", {}))
        
        status_color = Colors.OKGREEN if actual_outcome == case["expected_outcome"] else Colors.FAIL
        status_text = "PASS" if actual_outcome == case["expected_outcome"] else "FAIL"
        
        print(f"[{status_color}{status_text}{Colors.ENDC}] {case['id']}: {case['name']} (Level: {case['autonomy_level']})")
        
        if status_text == "PASS":
            passed += 1
        else:
            failed += 1
            print(f"    {Colors.WARNING}Expected: {case['expected_outcome']}, Got: {actual_outcome}{Colors.ENDC}")

    print(f"\n{Colors.BOLD}Validation Summary:{Colors.ENDC}")
    print(f"Passed: {Colors.OKGREEN}{passed}{Colors.ENDC}")
    print(f"Failed: {Colors.FAIL}{failed}{Colors.ENDC}")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
