"""Generic LLM client wrappers for Google Gemini API and Groq API."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMClient(ABC):
    """Abstract interface for LLM client wrappers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate text completion from the model."""
        pass


class GeminiClient(BaseLLMClient):
    """Wrapper for the official google-genai SDK."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client = None  # Initialized when SDK is connected

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via Gemini SDK."""
        # To be implemented in the next step
        raise NotImplementedError("GeminiClient logic will be implemented next.")


class GroqClient(BaseLLMClient):
    """Wrapper for the official Groq SDK."""

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile") -> None:
        self.api_key = api_key
        self.model_name = model_name
        self._client = None  # Initialized when SDK is connected

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via Groq SDK."""
        # To be implemented in the next step
        raise NotImplementedError("GroqClient logic will be implemented next.")
