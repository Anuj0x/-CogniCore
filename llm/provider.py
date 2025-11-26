"""
Modern LLM provider with unified interface.
"""
from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import LLMConfig
from ..core.logger import logger


class LLMResponse:
    """Standardized LLM response."""

    def __init__(self, content: str, raw_response: Any = None, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.raw_response = raw_response
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.tokens_used = self.metadata.get('tokens_used', 0)

    def __str__(self) -> str:
        return self.content


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """Initialize the provider."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )

    async def shutdown(self) -> None:
        """Shutdown the provider."""
        if self.session:
            await self.session.close()
            self.session = None

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM."""
        pass

    async def test_connection(self) -> bool:
        """Test connection to LLM."""
        try:
            await self.initialize()
            test_prompt = "Hello, respond with 'OK' if you can hear me."
            response = await self.generate(test_prompt, max_tokens=10)
            return "OK" in response.content.upper()
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


class OllamaProvider(LLMProvider):
    """Provider for Ollama-hosted models."""

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using Ollama API."""
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', self.config.temperature)

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        async with self.session.post(
            f"{self.config.api_url}/api/generate",
            json=payload
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Ollama API error: {response.status} - {await response.text()}")

            data = await response.json()

            return LLMResponse(
                content=data.get("response", ""),
                raw_response=data,
                metadata={
                    "model": data.get("model"),
                    "tokens_used": data.get("eval_count", 0),
                    "total_duration": data.get("total_duration", 0),
                    "load_duration": data.get("load_duration", 0),
                }
            )


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI API."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_url  # Store API key in api_url field for now

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using OpenAI API."""
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', self.config.temperature)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.model or "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"OpenAI API error: {response.status} - {await response.text()}")

            data = await response.json()

            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                raw_response=data,
                metadata={
                    "model": data.get("model"),
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                    "finish_reason": choice.get("finish_reason"),
                }
            )


class LMStudioProvider(LLMProvider):
    """Provider for LMStudio/Oobabooga."""

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using LMStudio API."""
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', self.config.temperature)

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }

        async with self.session.post(
            f"{self.config.api_url}/v1/completions",
            json=payload
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"LMStudio API error: {response.status} - {await response.text()}")

            data = await response.json()

            return LLMResponse(
                content=data.get("choices", [{}])[0].get("text", ""),
                raw_response=data,
                metadata={
                    "model": self.config.model,
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                }
            )


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Factory function to create appropriate LLM provider."""
    providers = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "lmstudio": LMStudioProvider,
        "oobabooga": LMStudioProvider,  # Same API as LMStudio
    }

    provider_class = providers.get(config.server_type.lower())
    if not provider_class:
