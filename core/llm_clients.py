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

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Dynamically retrieve available models or return a fallback list."""
        pass


class GeminiClient(BaseLLMClient):
    """Wrapper for the official google-genai SDK."""

    FALLBACK_MODELS: List[str] = [
        "gemini-3.8-flash",
        "gemini-3.8-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
    ]

    def __init__(self, api_key: str, model_name: str = "gemini-3.8-flash") -> None:
        super().__init__(api_key, model_name)
        self._client: Optional[genai.Client] = (
            genai.Client(api_key=api_key) if api_key else None
        )

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via the Gemini SDK."""
        if not self._client:
            raise ValueError("Gemini API key is required to generate content.")

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

    def get_available_models(self) -> List[str]:
        """Fetch available Gemini models dynamically or fallback to predefined list."""
        if not self._client or not self.api_key:
            return list(self.FALLBACK_MODELS)
        try:
            models: List[str] = []
            for m in self._client.models.list():
                name = m.name or ""
                if name.startswith("models/"):
                    name = name[len("models/"):]
                if "gemini" in name.lower():
                    models.append(name)

            if "gemini-3.8-flash" in models:
                models.remove("gemini-3.8-flash")
                models.insert(0, "gemini-3.8-flash")
            return models if models else list(self.FALLBACK_MODELS)
        except Exception:
            return list(self.FALLBACK_MODELS)


class GroqClient(BaseLLMClient):
    """Wrapper for the official Groq SDK."""

    FALLBACK_MODELS: List[str] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile") -> None:
        super().__init__(api_key, model_name)
        self._client: Optional[Groq] = Groq(api_key=api_key) if api_key else None

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via the Groq SDK."""
        if not self._client:
            raise ValueError("Groq API key is required to generate content.")

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

    def get_available_models(self) -> List[str]:
        """Fetch available Groq models dynamically or fallback to predefined list."""
        if not self._client or not self.api_key:
            return list(self.FALLBACK_MODELS)
        try:
            res = self._client.models.list()
            models = [m.id for m in res.data if m.id]
            if "llama-3.3-70b-versatile" in models:
                models.remove("llama-3.3-70b-versatile")
                models.insert(0, "llama-3.3-70b-versatile")
            return models if models else list(self.FALLBACK_MODELS)
        except Exception:
            return list(self.FALLBACK_MODELS)


class DeepSeekClient(BaseLLMClient):
    """Client for DeepSeek API using OpenAI-compatible REST endpoint."""

    BASE_URL = "https://api.deepseek.com/chat/completions"
    MODELS_URL = "https://api.deepseek.com/models"

    FALLBACK_MODELS: List[str] = [
        "deepseek-chat",
        "deepseek-reasoner",
    ]

    def __init__(self, api_key: str, model_name: str = "deepseek-chat") -> None:
        super().__init__(api_key, model_name)
        self._http_client = httpx.Client(timeout=60.0)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via DeepSeek API."""
        if not self.api_key:
            raise ValueError("DeepSeek API key is required to generate content.")

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

    def get_available_models(self) -> List[str]:
        """Fetch available DeepSeek models or return fallback list."""
        if not self.api_key:
            return list(self.FALLBACK_MODELS)
        try:
            response = self._http_client.get(
                self.MODELS_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", []) if "id" in m]
                if "deepseek-chat" in models:
                    models.remove("deepseek-chat")
                    models.insert(0, "deepseek-chat")
                return models if models else list(self.FALLBACK_MODELS)
            return list(self.FALLBACK_MODELS)
        except Exception:
            return list(self.FALLBACK_MODELS)


class OpenRouterClient(BaseLLMClient):
    """Unified client for OpenRouter API (Claude, DeepSeek, free tier models, etc.)."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODELS_URL = "https://openrouter.ai/api/v1/models"

    FALLBACK_MODELS: List[str] = [
        "anthropic/claude-3.5-sonnet",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "mistralai/mistral-7b-instruct:free",
    ]

    def __init__(
        self,
        api_key: str,
        model_name: str = "anthropic/claude-3.5-sonnet",
        app_name: str = "EasyPrompt",
    ) -> None:
        super().__init__(api_key, model_name)
        self.app_name = app_name
        self._http_client = httpx.Client(timeout=60.0)

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Execute text completion via OpenRouter API."""
        if not self.api_key:
            raise ValueError("OpenRouter API key is required to generate content.")

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

    def get_available_models(self) -> List[str]:
        """Fetch available OpenRouter models dynamically."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            response = self._http_client.get(
                self.MODELS_URL,
                headers=headers,
                timeout=10.0,
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["id"] for m in data.get("data", []) if "id" in m]
                # Prioritize key models at top
                priorities = [
                    "anthropic/claude-3.5-sonnet",
                    "deepseek/deepseek-chat",
                    "deepseek/deepseek-r1:free",
                    "meta-llama/llama-3.3-70b-instruct:free",
                ]
                for p in reversed(priorities):
                    if p in models:
                        models.remove(p)
                        models.insert(0, p)
                return models if models else list(self.FALLBACK_MODELS)
            return list(self.FALLBACK_MODELS)
        except Exception:
            return list(self.FALLBACK_MODELS)
