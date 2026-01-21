import os
from tavily import TavilyClient
from pydantic import BaseModel
from dotenv import load_dotenv
import logging

# Load secrets
load_dotenv()

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tavily_search")

# Initialize Client
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    # We don't raise an error immediately to allow import, but we warn
    logger.warning("⚠️ TAVILY_API_KEY is missing in .env")

class SearchResult(BaseModel):
    url: str
    title: str
    content: str

def perform_search(query: str, max_results: int = 3) -> list[dict]:
    """
    Searches the web and returns clean text content.
    Returns a list of dictionaries.
    """
    if not tavily_api_key:
        logger.error("Attempted search without API key.")
        return []

    client = TavilyClient(api_key=tavily_api_key)
    
    try:
        logger.info(f"🔍 Searching for: {query}")
        response = client.search(
            query=query, 
            search_depth="advanced", 
            max_results=max_results,
            include_raw_content=False
        )
        
        results = []
        for result in response.get("results", []):
            # We enforce a clean structure here
            results.append({
                "url": result["url"],
                "title": result["title"],
                "content": result["content"][:2000]  # Limit context window usage
            })
        
        logger.info(f"✅ Found {len(results)} results.")
        return results
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return []

if __name__ == "__main__":
    # Self-Test
    print("--- Testing Tavily Search ---")
    results = perform_search("latest developments in LangGraph 2024", max_results=1)
    for r in results:
        print(f"TITLE: {r['title']}")
        print(f"URL:   {r['url']}")
        print(f"SNIPPET: {r['content'][:100]}...")