"""Executor Agent: synthesizes the verified plan and critique into the final solution."""

import time
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse


class Executor(BaseAgent):
    """Agent responsible for producing the final production-ready solution."""

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        start_time = time.perf_counter()

        user_goal = context.get("user_goal", "") if context else ""
        crafted_plan = context.get("crafted_plan", "") if context else ""
        critique = input_text

        messages: List[Dict[str, str]] = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({
            "role": "user",
            "content": (
                f"Original User Goal:\n{user_goal}\n\n"
                f"Crafted Plan:\n{crafted_plan}\n\n"
                f"Audit & Verification Notes:\n{critique}\n\n"
                f"Generate the final, comprehensive, and polished solution addressing all points above."
            ),
        })

        result = self.router.complete(
            messages=messages,
            model_chain=self.model_chain,
        )

        elapsed = time.perf_counter() - start_time
        return AgentResponse(
            agent_name=self.name,
            content=result.content,
            execution_time_seconds=elapsed,
            model_used=result.model_used,
            provider_used=result.provider_used,
            was_fallback=result.was_fallback,
            fallback_history=result.fallback_history,
        )
