"""Global configuration settings for EasyPrompt."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Application settings and API configurations."""

    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")

    # Default Models
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    def validate_keys(self, required_services: Optional[List[str]] = None) -> None:
        """Validate that required API keys are configured."""
        if required_services is None:
            # By default check at least one primary LLM provider
            if not any([self.gemini_api_key, self.groq_api_key, self.openrouter_api_key]):
                raise ValueError(
                    "No API keys configured! Please set at least GEMINI_API_KEY, GROQ_API_KEY, "
                    "or OPENROUTER_API_KEY in your .env file."
                )
            return

        missing = []
        for service in required_services:
            key_name = f"{service.upper()}_API_KEY"
            if not getattr(self, f"{service.lower()}_api_key", None):
                missing.append(key_name)

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Please update your .env file."
            )


# Global settings instance
settings = Settings()
