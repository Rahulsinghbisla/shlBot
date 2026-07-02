from pydantic import BaseModel
from typing import List, Literal, Optional
from schema import Recommendation   

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]   

class ChatReply(BaseModel):
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False

class HealthResponse(BaseModel):
    status: str = "ok"