"""AI provider abstraction: Anthropic + OpenAI implementations."""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def chat(self, system: str, user_message: str, max_tokens: int = 1000) -> str:
        """Send a message and return the full response text."""

    @abstractmethod
    def chat_stream(self, system: str, user_message: str, max_tokens: int = 1000):
        """Send a message and yield response text chunks."""


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, system: str, user_message: str, max_tokens: int = 1000) -> str:
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def chat_stream(self, system: str, user_message: str, max_tokens: int = 1000):
        with self.client.messages.stream(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    MODEL = "gpt-4o"

    def __init__(self, api_key: str):
        import openai
        self.client = openai.OpenAI(api_key=api_key)

    def chat(self, system: str, user_message: str, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def chat_stream(self, system: str, user_message: str, max_tokens: int = 1000):
        stream = self.client.chat.completions.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_provider(config) -> tuple[AIProvider | None, bool]:
    """Get the configured AI provider. Returns (provider, ok)."""
    import os
    from gitfit.config import HAS_ANTHROPIC, HAS_OPENAI, get_api_key, get_openai_key

    provider_name = config.get("settings", {}).get("ai_provider", "anthropic")

    if provider_name == "openai":
        key = get_openai_key(config)
        if not key:
            return None, False
        if not HAS_OPENAI:
            return None, False
        try:
            return OpenAIProvider(api_key=key), True
        except Exception:
            return None, False
    else:
        # Default: anthropic
        key = get_api_key(config)
        if not key:
            return None, False
        if not HAS_ANTHROPIC:
            return None, False
        try:
            return AnthropicProvider(api_key=key), True
        except Exception:
            return None, False
