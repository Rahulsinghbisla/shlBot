from prompt import CHECK_LEVEL_PROMPT, SUPERVISOR_SYSTEM_PROMPT
from search import search_catalog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from schema import ChatResponse, CheckLevelClass, QueryFilters,SupervisiorClass,Recommendation
from state import llm_cls

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")
extractor = model.with_structured_output(QueryFilters)
responder = model.with_structured_output(ChatResponse)

def shl_recommender(state: llm_cls):
    messages = state["messages"]

    filters: QueryFilters = extractor.invoke([
        SystemMessage(content="Extract search filters from this recruiter conversation about hiring assessments."),
        *messages
    ])

    if filters.needs_clarification:
        reply = filters.clarifying_question or "Could you tell me more about the role and seniority level?"
        response = ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)
        return {"messages": [AIMessage(content=reply)], "structured_response": response}

    query_text = " ".join(filters.keywords)
    print("Job level in the chat node:", filters.job_level)
    matches = search_catalog(query_text, filters.job_level, limit=5)

    if not matches:
        response = ChatResponse(
            reply="I couldn't find a matching assessment in our catalog for that. Could you rephrase or give more detail?",
            recommendations=[], end_of_conversation=False
        )
        return {"messages": [AIMessage(content=response.reply)], "structured_response": response}

    # Case-insensitive lookup so minor LLM formatting differences don't break matching
    match_lookup = {m["name"].strip().lower(): m for m in matches}
    context = "\n".join(f"- {m['name']} | keys: {', '.join(m.get('keys', []))}" for m in matches)

    llm_response: ChatResponse = responder.invoke([
        SystemMessage(content=f"""Write a short, polite reply recommending assessments 
ONLY from this list (use exact names as given, do not modify or invent):
{context}

Return recommendations with name, url, and test_type (from keys)."""),
        *messages
    ])

    # Post-validation: strip hallucinated items, always pull real data from CATALOG (source of truth)
    verified_recs = []
    for rec in llm_response.recommendations:
        key = rec.name.strip().lower()
        if key in match_lookup:
            src = match_lookup[key]
            verified_recs.append(Recommendation(
                name=src["name"],
                url=src["link"],
                test_type=", ".join(src.get("keys", [])) or "Unknown"
            ))

    llm_response.recommendations = verified_recs
    llm_response.end_of_conversation = bool(verified_recs)

    return {
        "messages": [AIMessage(content=llm_response.reply)],
        "structured_response": llm_response
    }

def supervisior_node(state: llm_cls):
    print("supervisior_node invoked")
    messages = state.get("messages")
    
    llm_response = model.with_structured_output(SupervisiorClass).invoke(
        [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            *messages   # 👈 poori conversation history yaha unpack ho rahi hai
        ]
    )

    print(f"Supervisor routing decision: {llm_response.route} | Reason: {llm_response.reason}")
    return {"next": llm_response.route} 

def general_node(state: llm_cls):
    messages = state["messages"]
    response = model.invoke(messages)

    structured = ChatResponse(
        reply=response.content,
        recommendations=[],
        end_of_conversation=False
    )
    return {"messages": [AIMessage(content=response.content)], "structured_response": structured}

def condition(state: llm_cls):
    print("In the condition function, state:")
    route = state.get("next")
    print("State ", state)
    if route == "general_node":
        return "general_node"
    else :
        return "check_level"
    
def check_level(state: llm_cls):
    print("check_level invoked")
    
    llm_response = model.with_structured_output(CheckLevelClass).invoke(
        [
            SystemMessage(content=CHECK_LEVEL_PROMPT),
            *state["messages"]
        ]
    )
    print(f"Check Level Result: {llm_response.level} | Is Level Found: {llm_response.is_level}")
    return {"level": llm_response.level, "is_level": llm_response.is_level}

def condition2(state: llm_cls):
    print("In the condition2 function, state:")
    is_level = state.get("is_level")
    print("State in condition2 ", state)
    if is_level==True:
        return "shl_recommender"
    else:
        return "clarification_node" 
    
def clarification_node(state: llm_cls):
    print("clarification_node invoked")
    
    clarification_text = "I can certainly help with that. What seniority level are you looking for? (e.g., Entry-Level, Mid-Professional, Manager, Executive)"
    
    structured = ChatResponse(
        reply=clarification_text,
        recommendations=[],
        end_of_conversation=False
    )
    
    return {
        "messages": [AIMessage(content=clarification_text)],
        "structured_response": structured
    }
    