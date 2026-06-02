"""Minimal ReAct loop for the local agent."""

from __future__ import annotations

from dataclasses import dataclass

from agent.llm import generate
from agent.memory import ConversationMemory
from agent.tools import TOOL_GUIDE, execute_tool, parse_action


SYSTEM_PROMPT = f"""You are a local Codex-like teaching agent.

You help the user understand and inspect code inside the allowed workspace.
Never claim you modified files. You may propose patches, but they are not applied.

Use this exact protocol:
- If you need a tool, answer with one JSON object only:
  {{"type": "action", "tool": "list_files", "args": {{"path": "."}}}}
- If you are done, answer normally with a clear final answer.

{TOOL_GUIDE}
"""


@dataclass
class ReactAgent:
    memory: ConversationMemory
    max_steps: int = 6

    @classmethod
    def create(cls) -> "ReactAgent":
        return cls(memory=ConversationMemory(system_prompt=SYSTEM_PROMPT))

    def answer(self, user_message: str) -> str:
        prompt = self.memory.render(user_message)
        observations: list[str] = []

        for step in range(1, self.max_steps + 1):
            response = str(generate(prompt, system=SYSTEM_PROMPT, temperature=0.1))
            action = parse_action(response)
            if not action:
                final = response.strip()
                self.memory.add("user", user_message)
                self.memory.add("assistant", final)
                return final

            tool_name = str(action.get("tool", ""))
            args = action.get("args", {})
            if not isinstance(args, dict):
                args = {}

            print(f"\n[tool step {step}] {tool_name} {args}")
            result = execute_tool(tool_name, args)
            observation = result.to_observation()
            print(f"[observation] {observation[:1200]}\n")
            observations.append(f"Action: {tool_name} {args}\nObservation: {observation}")

            prompt = (
                self.memory.render(user_message)
                + "\n"
                + "\n\n".join(observations)
                + "\n\nContinue. Use another action if needed, otherwise give final answer."
            )

        final = "I reached the maximum tool steps. Here are the observations:\n\n" + "\n\n".join(observations)
        self.memory.add("user", user_message)
        self.memory.add("assistant", final)
        return final

