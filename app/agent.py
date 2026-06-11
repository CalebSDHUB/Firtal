"""
Firetal Internal Assistant – a simple single-agent that helps staff navigate
internal systems, processes, and tools.

Guardrails applied here:
  - max_tokens caps Claude's output (no runaway responses)
  - conversation history is loaded from Supabase (finite, ordered turns)
  - no tool-calling loop: the agent responds once per turn (no auto-loop)
"""

import anthropic
from app.config import settings
from app.database import get_conversation_history

SYSTEM_PROMPT = """Du er Firetal's interne assistent. Du hjælper medarbejdere med at navigere
interne systemer, processer og værktøjer. Svar altid kortfattet og præcist.

Kendte systemer: Supabase (database), GitHub (kode & CI/CD), Sliplane (deployment),
BigQuery (dataanalyse), Henosia/Next.js (frontend platform).

Regler:
- Svar på dansk medmindre brugeren skriver på engelsk.
- Giv aldrig adgang til credentials eller secrets.
- Hvis du er usikker, henvis til det relevante team.
- Hold svar under 3 afsnit.
"""


def build_messages(history: list[dict], user_message: str) -> list[dict]:
    """Combine past turns + new user message into Anthropic message format."""
    messages: list[dict] = []
    for turn in history:
        messages.append({"role": "user", "content": turn["user_message"]})
        messages.append({"role": "assistant", "content": turn["agent_reply"]})
    messages.append({"role": "user", "content": user_message})
    return messages


def run_agent(conversation_id: str, user_message: str) -> tuple[str, int]:
    """
    Call Claude once and return (reply_text, tokens_used).

    Infinite-loop prevention:
      1. max_tokens hard-caps the output length.
      2. We call the API exactly once per user turn – no automatic retry/re-entry loop.
      3. Conversation history is capped at max_turns_per_conversation (enforced upstream).
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    history = get_conversation_history(conversation_id)
    messages = build_messages(history, user_message)

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=settings.max_tokens_per_response,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    reply = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens
    return reply, tokens_used
