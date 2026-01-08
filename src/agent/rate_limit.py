"""Shared rate limit detection and backoff helpers."""

from __future__ import annotations

import random
from pydantic_ai.exceptions import ModelHTTPError


def detect_provider(model: str) -> str:
    """Infer provider name from model string."""
    model_lower = model.lower()
    if "claude" in model_lower or "anthropic" in model_lower:
        return "anthropic"
    if "deepseek" in model_lower:
        return "deepseek"
    if "gemini" in model_lower or model_lower.startswith("google-"):
        return "gemini"
    if "kimi" in model_lower or "moonshot" in model_lower:
        return "kimi"
    if "gpt" in model_lower or model_lower.startswith("openai:"):
        return "openai"
    return "other"


def is_rate_limit_error(err: Exception) -> bool:
    """Return True if error indicates rate limiting."""
    if isinstance(err, ModelHTTPError):
        if getattr(err, "status_code", None) != 429:
            return False
        body = getattr(err, "body", None)
        if isinstance(body, dict):
            error = body.get("error")
            if isinstance(error, dict) and error.get("type") in {
                "rate_limit_error",
                "rate_limit",
            }:
                return True
            code = body.get("code") or body.get("type")
            if code in {"rate_limit_error", "rate_limit"}:
                return True
        return True

    message = str(err).lower()
    return (
        "rate limit" in message
        or "rate_limit" in message
        or "too many requests" in message
        or "429" in message
    )


def rate_limit_backoff(
    attempt: int,
    provider: str,
    base_delay: float | None = None,
    max_delay: float | None = None,
) -> float:
    """Compute exponential backoff with jitter for rate limiting."""
    if base_delay is None:
        base_delay = 15.0 if provider == "anthropic" else 5.0
    if max_delay is None:
        max_delay = 120.0 if provider == "anthropic" else 60.0

    delay = min(max_delay, base_delay * (2 ** attempt))
    jitter = random.uniform(0.0, min(3.0, delay * 0.1))
    return delay + jitter
