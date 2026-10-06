"""PromptCrafter Agent: analyzes the user query and crafts an optimized prompt & plan."""

import time
from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent, AgentResponse


class PromptCrafter(BaseAgent):
    """Agent responsible for deconstructing user requirements and crafting structured prompts."""

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        start_time = time.perf_counter()

        # Generates structured prompt plan using the injected LLM client
        prompt = (
            f"User Goal: {input_text}\n\n"
            f"Craft a detailed, structured, and comprehensive specification/plan "
            f"addressing this goal."
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
