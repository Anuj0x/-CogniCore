"""
Configuration management using modern Python patterns.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, validator


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""

    server_type: str = Field(..., description="Type of LLM server (ollama, lmstudio, oobabooga)")
    api_url: str = Field(..., description="LLM API endpoint URL")
    model: str = Field("", description="Model name (for Ollama)")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    temperature: float = Field(0.7, description="Response temperature")

    @validator('server_type')
    def validate_server_type(cls, v):
        allowed = {"ollama", "lmstudio", "oobabooga", "openai"}
        if v not in allowed:
            raise ValueError(f"server_type must be one of {allowed}")
        return v


class TelegramConfig(BaseModel):
    """Configuration for Telegram integration."""

    api_key: str = Field(..., description="Telegram Bot API key")
    chat_id: str = Field(..., description="Authorized chat ID")
    timeout: int = Field(30, description="Request timeout in seconds")
    enable_notifications: bool = Field(True, description="Enable push notifications")


class MemoryConfig(BaseModel):
    """Configuration for memory system."""

    max_tokens: int = Field(4000, description="Maximum tokens to keep in context")
    persistence_path: Path = Field(Path("memories.json"), description="Memory storage path")
    auto_summarize: bool = Field(True, description="Auto-summarize old memories")
    vector_store: bool = Field(False, description="Use vector storage for memories")


class AutoGPTConfig(BaseModel):
    """Main configuration for AutoGPT."""

    llm: LLMConfig
    telegram: Optional[TelegramConfig] = None
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    debug: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("INFO", description="Logging level")

    @validator('log_level')
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()

    @classmethod
    def load(cls) -> AutoGPTConfig:
        """Load configuration from environment variables."""
        # Load environment variables
        llm_config = LLMConfig(
            server_type=os.getenv("LLM_SERVER_TYPE", ""),
            api_url=os.getenv("LLM_API_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", ""),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        )

        # Telegram config (optional)
        telegram_config = None
        if os.getenv("TELEGRAM_API_KEY") and os.getenv("TELEGRAM_CHAT_ID"):
            telegram_config = TelegramConfig(
                api_key=os.getenv("TELEGRAM_API_KEY", ""),
                chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
                timeout=int(os.getenv("TELEGRAM_TIMEOUT", "30")),
                enable_notifications=os.getenv("TELEGRAM_NOTIFICATIONS", "true").lower() == "true",
            )

        return cls(
            llm=llm_config,
            telegram=telegram_config,
            memory=MemoryConfig(
                max_tokens=int(os.getenv("MEMORY_MAX_TOKENS", "4000")),
                persistence_path=Path(os.getenv("MEMORY_PATH", "memories.json")),
                auto_summarize=os.getenv("MEMORY_AUTO_SUMMARIZE", "true").lower() == "true",
                vector_store=os.getenv("MEMORY_VECTOR_STORE", "false").lower() == "true",
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Alias for backward compatibility
Config = AutoGPTConfig
