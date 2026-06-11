import uuid
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import ChatRequest, ChatResponse, HealthResponse, ConversationRecord
from app.agent import run_agent
from app.database import get_conversation_turn_count, log_conversation
from app.guardrails import check_rate_limit, check_max_turns, validate_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Firetal Internal Assistant",
    description="AI-agent med guardrails – proof of concept",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
    )


@app.post("/chat", response_model=ChatResponse, tags=["agent"])
def chat(body: ChatRequest, request: Request):
    # Guardrail 1: rate limiting
    check_rate_limit(request)

    # Guardrail 2: input sanitization
    message = validate_input(body.message)

    # Resolve or create conversation
    conversation_id = body.conversation_id or str(uuid.uuid4())

    # Guardrail 3: max turns per conversation (infinite-loop prevention)
    current_turn = get_conversation_turn_count(conversation_id)
    check_max_turns(current_turn + 1)

    # Call the agent (single-shot, no auto-loop)
    reply, tokens_used = run_agent(conversation_id, message)

    # Persist to Supabase
    record = ConversationRecord(
        conversation_id=conversation_id,
        user_id=body.user_id or "anonymous",
        user_message=message,
        agent_reply=reply,
        tokens_used=tokens_used,
        turn_number=current_turn + 1,
    )
    log_conversation(record)

    logger.info(
        "conversation=%s turn=%d tokens=%d",
        conversation_id,
        current_turn + 1,
        tokens_used,
    )

    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        tokens_used=tokens_used,
        turn_number=current_turn + 1,
    )
