from agent import research_agent

question = input("Ask a research question: ")
result = research_agent.invoke({
    "question": question,
    "search_results": [],
    "answer": ""
})
print("\nAnswer:")
print(result["answer"])