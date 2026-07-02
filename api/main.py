from fastapi import FastAPI, HTTPException
from graph import chat
from api.api_schema import ChatRequest, ChatReply, HealthResponse
from api.utlis import to_langchain_messages

app = FastAPI(title="SHL Assessment Recommender", version="1.0")

@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatReply)
def chat_endpoint(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    lc_messages = to_langchain_messages(request.messages)

    graph_input = {
        "messages": lc_messages,
        "structured_response": None,
    }

    try:
        output = chat.invoke(graph_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    structured = output.get("structured_response")

    if structured is None:
        # general_agent path — no structured recommendations
        last_ai_msg = output["messages"][-1]
        return ChatReply(reply=last_ai_msg.content, recommendations=[], end_of_conversation=False)

    return ChatReply(
        role="assistant",
        reply=structured.reply,
        recommendations=structured.recommendations,
        end_of_conversation=structured.end_of_conversation,
    )
