from typing import Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import SystemMessage, ToolMessage

from tools import LIGHTING_TOOLS, CLIMATE_TOOLS, SECURITY_TOOLS, ALL_TOOLS
from prompts import SUPERVISOR_PROMPT, LIGHTING_PROMPT, CLIMATE_PROMPT, SECURITY_PROMPT
from guardrails import requires_confirmation

load_dotenv()


# Same state as before (messages) plus one extra field that tracks which
# sub-agent is currently active, so tool calls and confirmations route back
# to the correct specialist instead of a single fixed agent.
class AgentState(MessagesState):
    current_agent: Optional[str]


llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

lighting_llm = llm.bind_tools(LIGHTING_TOOLS)
climate_llm = llm.bind_tools(CLIMATE_TOOLS)
security_llm = llm.bind_tools(SECURITY_TOOLS)


def supervisor_node(state: AgentState):
    """Reads the latest user message and decides which of the 3 specialists should handle it."""
    last_user_message = state["messages"][-1].content
    prompt = SUPERVISOR_PROMPT.format(request=last_user_message)
    response = llm.invoke([SystemMessage(content=prompt)])
    choice = response.content.strip().lower()

    if "light" in choice:
        next_agent = "lighting"
    elif "climate" in choice or "thermostat" in choice:
        next_agent = "climate"
    elif "security" in choice or "door" in choice:
        next_agent = "security"
    else:
        # Simple fallback in case the model replies with something unexpected,
        # so the graph doesn't crash on a bad routing decision.
        next_agent = "lighting"

    return {"current_agent": next_agent}


def route_from_supervisor(state: AgentState):
    return state["current_agent"]


def make_subagent_node(bound_llm, system_prompt):
    """Factory that builds a node for any sub-agent: same logic, different prompt and tools."""

    def node(state: AgentState):
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = bound_llm.invoke(messages)
        return {"messages": [response]}

    return node


lighting_node = make_subagent_node(lighting_llm, LIGHTING_PROMPT)
climate_node = make_subagent_node(climate_llm, CLIMATE_PROMPT)
security_node = make_subagent_node(security_llm, SECURITY_PROMPT)


def route_after_agent(state: AgentState):
    """Same logic as the original project: confirm, run the tool, or finish."""
    last_message = state["messages"][-1]
    if not getattr(last_message, "tool_calls", None):
        return END
    for tc in last_message.tool_calls:
        if requires_confirmation(tc["name"], tc["args"]):
            return "confirm"
    return "tools"


def confirm_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]

    # Execution actually pauses here and waits for the user's response.
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
        # Go back to whichever sub-agent requested the action, instead of a
        # single fixed agent like before.
        return Command(goto=state["current_agent"], update={"messages": [cancel_message]})


def route_after_tools(state: AgentState):
    """After execution, go back to whichever sub-agent made the tool call."""
    return state["current_agent"]


tool_node = ToolNode(ALL_TOOLS)

graph = StateGraph(AgentState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("lighting", lighting_node)
graph.add_node("climate", climate_node)
graph.add_node("security", security_node)
graph.add_node("confirm", confirm_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {"lighting": "lighting", "climate": "climate", "security": "security"},
)

for agent_name in ("lighting", "climate", "security"):
    graph.add_conditional_edges(
        agent_name,
        route_after_agent,
        {"confirm": "confirm", "tools": "tools", END: END},
    )

graph.add_conditional_edges(
    "tools",
    route_after_tools,
    {"lighting": "lighting", "climate": "climate", "security": "security"},
)

memory = MemorySaver()
app = graph.compile(checkpointer=memory)