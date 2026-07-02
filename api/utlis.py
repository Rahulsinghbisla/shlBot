from langchain_core.messages import ChatMessage, HumanMessage, AIMessage, BaseMessage

def to_langchain_messages(chat_messages: list[ChatMessage]) -> list[BaseMessage]:
    converted = []
    for m in chat_messages:
        if m.role == "user":
            converted.append(HumanMessage(content=m.content))
        else:
            converted.append(AIMessage(content=m.content))
    return converted