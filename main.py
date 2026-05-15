from hermes.core.runtime import HermesRuntime
from hermes.core.llm_provider import MockLLMProvider, OllamaProvider
from hermes.utils.paths import optimization_file
import json

def main():
    print("=== Hermes Agent OS: Phase 1 (Full) ===")
    
    # 這裡可以切換為 OllamaProvider() 若本地已有 Ollama 運行
    provider = MockLLMProvider() 
    runtime = HermesRuntime(llm_provider=provider)
    
    # 執行一個模擬任務
    print("\n[Action] Running simulated task: 'Optimize local file structure'...")
    runtime.execute_task("Optimize local file structure")
    
    # 獲取系統狀態與觀測數據
    status = runtime.get_status()
    print("\n=== System Status ===")
    print(json.dumps(status, indent=4, ensure_ascii=False))
    
    # 導出執行軌跡
    trace_path = optimization_file("last_execution_trace.json")
    runtime.monitor.export_traces(trace_path)
    print(f"\n[Info] Execution trace exported to: {trace_path}")

if __name__ == "__main__":
    main()
