from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import SystemMessage, ToolMessage

from tools import ALL_TOOLS
from prompts import SYSTEM_PROMPT
from guardrails import requires_confirmation

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


def call_model(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def route_after_agent(state: MessagesState):
    last_message = state["messages"][-1]
    if not getattr(last_message, "tool_calls", None):
        return END
    for tc in last_message.tool_calls:
        if requires_confirmation(tc["name"], tc["args"]):
            return "confirm"
    return "tools"


def confirm_node(state: MessagesState):
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]

    # هنا التنفيذ بيتوقف فعليًا وينتظر رد المستخدم
    user_decision = interrupt({
        "question": f"Confirm action: {tool_call['name']} with args {tool_call['args']}?"
    })

    if user_decision == "yes":
        return Command(goto="tools")
    else:
        cancel_message = ToolMessage(
            content="Action cancelled by the user.",
            tool_call_id=tool_call["id"],
        )
        return Command(goto="agent", update={"messages": [cancel_message]})


tool_node = ToolNode(ALL_TOOLS)

graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("confirm", confirm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    route_after_agent,
    {"confirm": "confirm", "tools": "tools", END: END},
)
graph.add_edge("tools", "agent")

memory = MemorySaver()
app = graph.compile(checkpointer=memory)