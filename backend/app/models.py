from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    stage: str
    reply: str


class FinalizeResponse(BaseModel):
    stage: str
    brief: str


class SessionResponse(BaseModel):
    session_id: str
    stage: str
