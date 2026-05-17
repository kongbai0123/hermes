import sys
import json
import argparse
from pathlib import Path

from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider
from hermes.evaluator.runner import ValidationRunner, ValidationTask

def main():
    parser = argparse.ArgumentParser(description="Hermes Validation Suite CLI")
    parser.add_argument("suite_file", type=str, help="Path to the JSON suite file")
    args = parser.parse_args()

    suite_path = Path(args.suite_file)
    if not suite_path.exists():
        print(f"Error: Suite file not found at {suite_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(suite_path, 'r', encoding='utf-8') as f:
            suite_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON suite: {e}", file=sys.stderr)
        sys.exit(1)

    suite = []
    for item in suite_data:
        try:
            task = ValidationTask(
                name=item["name"],
                task=item["task"],
                expected_outcome=item["expected_outcome"],
                expected_intent=item.get("expected_intent"),
                expected_status=item.get("expected_status"),
                metadata=item.get("metadata", {})
            )
            suite.append(task)
        except KeyError as e:
            print(f"Error: Missing required field {e} in suite item: {item}", file=sys.stderr)
            sys.exit(1)

    # Use MockLLMProvider for validation unless otherwise specified
    runtime = HermesRuntime(llm_provider=MockLLMProvider())
    runner = ValidationRunner(runtime)

    print(f"Running Validation Suite from: {suite_path}")
    print("-" * 40)

    results = runner.run_suite(suite)
    
    passed_count = 0
    failed_count = 0

    for res in results:
        if res.success:
            print(f"[PASS] {res.name}")
            passed_count += 1
        else:
            print(f"[FAIL] {res.name}")
            print(f"       Reason: {res.reason}")
            if res.error_message:
                print(f"       Error: {res.error_message}")
            failed_count += 1

    print("-" * 40)
    print(f"Summary: {passed_count} passed, {failed_count} failed")

    if failed_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
