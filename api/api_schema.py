from pydantic import BaseModel
from typing import List, Literal, Optional
from schema import Recommendation   # tera existing schema

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]   # poori history client se aayegi, stateless

class ChatReply(BaseModel):
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False

class HealthResponse(BaseModel):
    status: str = "ok"