from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionSchema(BaseModel):
    id: str
    session_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True


class CreateSessionRequest(BaseModel):
    session_name: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    session_name: Optional[str] = None
    message: str


class ChatRequest(BaseModel):
    query: str
    session_id: str
    enable_history: bool = True


class ChatResponse(BaseModel):
    response: str

