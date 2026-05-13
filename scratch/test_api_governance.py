import urllib.request
import json

url = "http://localhost:8000/api/task"
payload = {
    "task": "請讀取 README.md",
    "provider": "mock"
}
data = json.dumps(payload).encode("utf-8")
headers = {"Content-Type": "application/json"}

try:
    print(f"Sending task to {url}...")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        result = json.loads(response.read().decode("utf-8"))
        
        print("\n[Trace Analysis]")
        traces = result.get("result", {}).get("trace", [])
        for t in traces:
            print(f"State: {t.get('state', 'UNKNOWN')} | Action: {t.get('action')} | Summary: {t.get('summary')}")
            
        found_exec = any(t.get('action') == 'EXECUTIVE_DECISION' for t in traces)
        found_strat = any(t.get('action') == 'STRATEGY_PLAN' for t in traces)
        
        if found_exec and found_strat:
            print("\n✅ SUCCESS: Management layers L1 and L2 are active and recorded in trace.")
        else:
            print("\n❌ FAILURE: Management layers missing from trace.")

except Exception as e:
    print(f"Error: {e}")
