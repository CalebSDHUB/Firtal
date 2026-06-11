"""
Supabase client and query helpers.
Uses the service-role key so the agent can write conversation logs
without requiring end-user auth tokens.
"""

from supabase import create_client, Client
from app.config import settings
from app.models import ConversationRecord
import logging

logger = logging.getLogger(__name__)


def _clean_supabase_url(url: str) -> str:
    """Accept both the bare project URL and the full REST URL that Supabase
    sometimes shows in the dashboard (e.g. https://xxx.supabase.co/rest/v1/).
    supabase-py only wants the bare project root."""
    for suffix in ("/rest/v1/", "/rest/v1"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url.rstrip("/")


def get_supabase() -> Client:
    url = _clean_supabase_url(settings.supabase_url)
    return create_client(url, settings.supabase_service_role_key)


def get_conversation_turn_count(conversation_id: str) -> int:
    """Return how many turns have already happened in this conversation."""
    try:
        client = get_supabase()
        result = (
            client.table("conversations")
            .select("id", count="exact")
            .eq("conversation_id", conversation_id)
            .execute()
        )
        return result.count or 0
    except Exception as exc:
        logger.warning("Could not fetch turn count: %s", exc)
        return 0


def log_conversation(record: ConversationRecord) -> None:
    """Persist a conversation turn to Supabase."""
    try:
        client = get_supabase()
        client.table("conversations").insert(
            {
                "conversation_id": record.conversation_id,
                "user_id": record.user_id,
                "user_message": record.user_message,
                "agent_reply": record.agent_reply,
                "tokens_used": record.tokens_used,
                "turn_number": record.turn_number,
            }
        ).execute()
    except Exception as exc:
        # Log but don't surface DB errors to the end user
        logger.error("Failed to log conversation: %s", exc)


def get_conversation_history(conversation_id: str) -> list[dict]:
    """Fetch ordered message history for multi-turn context."""
    try:
        client = get_supabase()
        result = (
            client.table("conversations")
            .select("user_message, agent_reply, turn_number")
            .eq("conversation_id", conversation_id)
            .order("turn_number", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as exc:
        logger.warning("Could not fetch history: %s", exc)
        return []
