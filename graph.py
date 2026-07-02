from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from schema import ChatResponse, QueryFilters,Recommendation
from nodes import shl_recommender, clarification_node, supervisior_node, general_node, condition,check_level,condition2
from state import llm_cls

load_dotenv()


graph = StateGraph(llm_cls)
graph.add_node("supervisior",supervisior_node)
graph.add_node("check_level", check_level)
graph.add_node("clarification_node", clarification_node)
graph.add_node("shl_recommender", shl_recommender)
graph.add_node("general_node", general_node) 
graph.add_edge(START, "supervisior")
graph.add_conditional_edges(
    "supervisior",
    condition,
    {
        "check_level": "check_level",
        "general_node": "general_node"
    }
)
graph.add_conditional_edges(
    "check_level",
    condition2,
    {
        "shl_recommender": "shl_recommender",
        "clarification_node": "clarification_node"
    }
)
graph.add_edge("shl_recommender", END)
graph.add_edge( "general_node", END)
graph.add_edge("clarification_node", "__end__")
chat = graph.compile()

# while True: 
#     user_input = input("User: ")
#     mess = {"messages": [HumanMessage(content=user_input)], "structured_response": None}
#     output = chat.invoke(mess)
#     print("Agent:", output['messages'][-1].content)
#     if output['structured_response'] and output['structured_response'].recommendations:
#         print("Structured Response:", output['structured_response'].recommendations)