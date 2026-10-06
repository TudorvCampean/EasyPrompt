"""Executor Agent: synthesizes the verified plan and critique into the final solution."""

import time
from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent, AgentResponse


class Executor(BaseAgent):
    """Agent responsible for producing the final production-ready solution."""

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        start_time = time.perf_counter()

        user_goal = context.get("user_goal", "") if context else ""
        crafted_plan = context.get("crafted_plan", "") if context else ""
        critique = input_text

        prompt = (
            f"Original User Goal:\n{user_goal}\n\n"
            f"Crafted Plan:\n{crafted_plan}\n\n"
            f"Audit & Verification Notes:\n{critique}\n\n"
            f"Generate the final, comprehensive, and polished solution addressing all points above."
        )

        content = self.llm_client.generate(
            prompt=prompt,
            system_instruction=self.system_instruction,
        )

        elapsed = time.perf_counter() - start_time
        return AgentResponse(
            agent_name=self.name,
            content=content,
            execution_time_seconds=elapsed,
        )
