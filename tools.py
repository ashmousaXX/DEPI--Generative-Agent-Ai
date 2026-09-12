from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

tavily = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

def search_web(query: str):
    results = tavily.search(
        query=query,
        max_results=3
    )
    return results["results"]