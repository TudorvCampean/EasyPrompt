"""Base agent abstraction and common data structures using Pydantic."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from core.llm_clients import BaseLLMClient


class AgentResponse(BaseModel):
    """Standardized response produced by any agent in the pipeline."""

    agent_name: str
    content: str
    execution_time_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base agent enforcing Dependency Injection of LLM clients."""

    def __init__(
        self,
        name: str,
        llm_client: BaseLLMClient,
        system_instruction: str,
    ) -> None:
        self.name = name
        self.llm_client = llm_client
        self.system_instruction = system_instruction

    @abstractmethod
    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process input and return a standardized AgentResponse."""
        pass
