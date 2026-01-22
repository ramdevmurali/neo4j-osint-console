import logging

from tavily import TavilyClient

from src.config import Config
logger = logging.getLogger("tavily_search")

def perform_search(query: str, max_results: int = 3) -> list[dict]:
    if not Config.TAVILY_API_KEY:
        return [{"error": "API Key Missing"}]

    try:
        client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results
        )
        
        return [
            {
                "url": r["url"],
                "title": r["title"],
                "content": r["content"][:2000]
            } 
            for r in response.get("results", [])
        ]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
