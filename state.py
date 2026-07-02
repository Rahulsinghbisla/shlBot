from typing import TypedDict, List,Literal
from xmlrpc.client import boolean
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Annotated

from schema import ChatResponse

class llm_cls(TypedDict):
    messages:Annotated[List[BaseMessage],add_messages]
    next: Literal["shl_recommender","general_node"]
    structured_response: ChatResponse
    level:str
    is_level:boolean