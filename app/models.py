from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tokens_used: int
    turn_number: int


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


class ConversationRecord(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    user_id: str
    user_message: str
    agent_reply: str
    tokens_used: int
    turn_number: int
    created_at: Optional[datetime] = None
