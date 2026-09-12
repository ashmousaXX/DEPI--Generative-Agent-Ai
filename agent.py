from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama
from tools import search_web
from typing import TypedDict

class State(TypedDict):
    question: str
    search_results: list
    answer: str

from langchain_groq import ChatGroq

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

def search_node(state):
    results = search_web(state["question"])
    return {
        "search_results": results
    }

def summarize_node(state):
    results = state["search_results"]
    context = "\n\n".join(
        result["content"]
        for result in results
    )

    prompt = f"""
    Answer the following question using the
    provided search results.
    Question:
    {state["question"]}
    Search results:
    {context}
    Give a short and clear answer.
    """
    response = llm.invoke(prompt)
    return {
        "answer": response.content
    }
graph = StateGraph(State)

graph.add_node("search", search_node)
graph.add_node("summarize", summarize_node)
graph.add_edge(START, "search")
graph.add_edge("search", "summarize")
graph.add_edge("summarize", END)

research_agent = graph.compile()