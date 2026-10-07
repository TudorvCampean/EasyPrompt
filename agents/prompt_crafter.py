"""PromptCrafter Agent: analyzes the user query and crafts an optimized prompt & plan."""

import time
from typing import Any, Dict, List, Optional
from agents.base_agent import BaseAgent, AgentResponse


class PromptCrafter(BaseAgent):
    """Agent responsible for deconstructing user requirements and crafting structured prompts."""

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        start_time = time.perf_counter()

        messages: List[Dict[str, str]] = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({
            "role": "user",
            "content": (
                f"User Goal: {input_text}\n\n"
                f"Craft a detailed, structured, and comprehensive specification/plan "
                f"addressing this goal."
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
