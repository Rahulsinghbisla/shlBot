from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str

class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False

class QueryFilters(BaseModel):
    keywords: List[str] = Field(description="Skills/tech/role keywords, e.g. ['Java', 'stakeholder']")
    job_level: Optional[str] = Field(default=None, description="e.g. Entry-Level, Mid-Professional, Manager")
    needs_clarification: bool = Field(description="True if info is too vague to search yet")
    clarifying_question: Optional[str] = None

class SupervisiorClass(BaseModel):
    route: Literal["shl_recommender", "general_node"]   # ✅ node names se match
    reason: str

class CheckLevelClass(BaseModel):
    level: str  
    is_level:bool

class LevelCheckResult(BaseModel):
    level: str = Field(default="", description="...")
    is_level: bool = Field(description="...")
    reply: str = Field(description="...")