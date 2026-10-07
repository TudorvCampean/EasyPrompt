"""Base agent abstraction and common data structures using Pydantic.

Agents are now provider-agnostic: they receive a RouterClient and a
model fallback chain, and communicate exclusively through the standard
OpenAI message format (role/content).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.router import RouterClient


class AgentResponse(BaseModel):
    """Standardized response produced by any agent in the pipeline."""

    agent_name: str
    content: str
    execution_time_seconds: float = 0.0
    model_used: str = ""
    provider_used: str = ""
    was_fallback: bool = False
    fallback_history: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base agent using RouterClient for provider-agnostic LLM access."""

    def __init__(
        self,
        name: str,
        router: RouterClient,
        model_chain: List[str],
        system_instruction: str,
    ) -> None:
        self.name = name
        self.router = router
        self.model_chain = model_chain
        self.system_instruction = system_instruction

    @abstractmethod
    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process input and return a standardized AgentResponse."""
        pass
