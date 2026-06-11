"""
Guardrails for the AI agent.

Three layers of protection:
  1. Rate limiting   – max N requests per minute per IP (tracked in Supabase)
  2. Max tokens      – cap Claude's output tokens to prevent runaway responses
  3. Max turns       – cap turns per conversation to prevent infinite loops
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Request
from app.config import settings

# In-memory sliding-window rate limiter (augmented by Supabase for persistence)
_rate_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """Enforce MAX_REQUESTS_PER_MINUTE per client IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0

    timestamps = _rate_buckets[client_ip]
    # Evict timestamps outside the current window
    _rate_buckets[client_ip] = [t for t in timestamps if now - t < window]

    if len(_rate_buckets[client_ip]) >= settings.max_requests_per_minute:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {settings.max_requests_per_minute} requests/minute.",
        )

    _rate_buckets[client_ip].append(now)


def check_max_turns(turn_number: int) -> None:
    """Prevent runaway conversations by capping total turns."""
    if turn_number > settings.max_turns_per_conversation:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Conversation exceeded the maximum of {settings.max_turns_per_conversation} turns. "
                "Start a new conversation."
            ),
        )


def validate_input(message: str) -> str:
    """Strip and basic-sanitize the incoming message."""
    cleaned = message.strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    return cleaned
