"""Generic LLM client wrappers for Google Gemini, Groq, DeepSeek, and OpenRouter."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from google import genai
from google.genai import types
from groq import Groq


class BaseLLMClient(ABC):
    """Abstract interface for LLM client wrappers."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name

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
        super().__init__(api_key, model_name)
        if not api_key:
            raise ValueError("Gemini API key is required to initialize GeminiClient.")
        self._client = genai.Client(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via the Gemini SDK."""
        config_kwargs: Dict[str, Any] = {"temperature": temperature}
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs)
        response = self._client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        return response.text or ""


class GroqClient(BaseLLMClient):
    """Wrapper for the official Groq SDK."""

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile") -> None:
        super().__init__(api_key, model_name)
        if not api_key:
            raise ValueError("Groq API key is required to initialize GroqClient.")
        self._client = Groq(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via the Groq SDK."""
        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


class DeepSeekClient(BaseLLMClient):
    """Client for DeepSeek API using OpenAI-compatible REST endpoint."""

    BASE_URL = "https://api.deepseek.com/chat/completions"

    def __init__(self, api_key: str, model_name: str = "deepseek-chat") -> None:
        super().__init__(api_key, model_name)
        if not api_key:
            raise ValueError("DeepSeek API key is required to initialize DeepSeekClient.")
        self._http_client = httpx.Client(timeout=60.0)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via DeepSeek API."""
        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }

        response = self._http_client.post(self.BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""


class OpenRouterClient(BaseLLMClient):
    """Unified client for OpenRouter API (Claude, DeepSeek, free tier models, etc.)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model_name: str = "anthropic/claude-3.5-sonnet",
        app_name: str = "EasyPrompt",
    ) -> None:
        super().__init__(api_key, model_name)
        if not api_key:
            raise ValueError("OpenRouter API key is required to initialize OpenRouterClient.")
        self.app_name = app_name
        self._http_client = httpx.Client(timeout=60.0)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via OpenRouter API."""
        messages: List[Dict[str, str]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/TudorvCampean/EasyPrompt",
            "X-Title": self.app_name,
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
        }

        response = self._http_client.post(self.BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"] or ""
