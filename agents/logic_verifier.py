"""LogicVerifier Agent: critic agent evaluating reasoning, edge cases, and domain criteria."""

import time
from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent, AgentResponse


class LogicVerifier(BaseAgent):
    """Agent responsible for auditing and validating the crafted plan before execution."""

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        start_time = time.perf_counter()

        user_goal = context.get("user_goal", "") if context else ""
        prompt = (
            f"Original User Goal: {user_goal}\n\n"
            f"Proposed Plan to Review:\n{input_text}\n\n"
            f"Provide a rigorous review, checking for flaws, edge cases, domain requirements, "
            f"and propose concrete improvements."
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
