"""LLM provider interface (eval compares providers through this). No keys in the repo; Anthropic reads env."""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Completion: ...


class EchoProvider:
    """Deterministic test provider: `fn(system, user) -> text`."""

    name = "echo"

    def __init__(self, fn: Callable[[str, str], str]):
        self.fn = fn
        self.calls = 0

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Completion:
        self.calls += 1
        t = self.fn(system, user)
        return Completion(t, len(system.split()) + len(user.split()), len(t.split()), "echo")


class AnthropicProvider:
    """Model id comes from ANTHROPIC_MODEL (placeholder default; verify against current model list before use)."""

    name = "anthropic"

    def __init__(self, model: str | None = None, timeout: float = 30.0, max_retries: int = 2):
        import anthropic  # lazy: tests never import it

        self.model = model or os.environ.get("ANTHROPIC_MODEL") or "claude-haiku-5-5"
        self.client = anthropic.Anthropic(timeout=timeout, max_retries=max_retries)  # reads ANTHROPIC_API_KEY

    def complete(self, system: str, user: str, max_tokens: int = 400) -> Completion:
        r = self.client.messages.create(model=self.model, max_tokens=max_tokens, temperature=0, system=system,
                                        messages=[{"role": "user", "content": user}])
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return Completion(text, r.usage.input_tokens, r.usage.output_tokens, self.model)
