from typing import Dict, Any, Tuple
from hermes.core.llm_provider import LLMProvider

class Verifier:
    """
    驗證者架構: 負責檢查 AI 的執行結果，防止「自我幻覺」。
    """
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def verify_plan(self, task: str, plan: str) -> Tuple[bool, str]:
        """
        在執行前驗證計畫是否合理且安全。
        """
        prompt = f"Task: {task}\nProposed Plan: {plan}\n\nDoes this plan achieve the task safely? Answer with YES or NO followed by reason."
        response = self.llm.completion(prompt=prompt, system_prompt="You are a strict security and logic auditor.")
        
        text = response["text"].strip().upper()
        if text.startswith("YES"):
            return True, "Plan verified"
        return False, f"Plan rejected: {text}"

    def verify_result(self, task: str, action_output: str) -> Tuple[bool, str]:
        """
        在結束前驗證執行結果是否符合預期。
        """
        prompt = f"Task: {task}\nOutput: {action_output}\n\nDid the output successfully fulfill the task? Answer with YES or NO followed by reason."
        response = self.llm.completion(prompt=prompt, system_prompt="You are a quality assurance inspector.")
        
        text = response["text"].strip().upper()
        if text.startswith("YES"):
            return True, "Result verified"
        return False, f"Result invalid: {text}"
