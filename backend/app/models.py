from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    stage: str
    reply: str


class FinalizeResponse(BaseModel):
    stage: str
    brief: str
    auto_message: Optional[str] = None  # e.g. the Feasibility Agent's first verdict


class SessionResponse(BaseModel):
    session_id: str
    stage: str
