import os
from dotenv import load_dotenv

# Load once. No other file needs to call this.
load_dotenv()

class Config:
    # Model
    LLM_PROVIDER = "google"
    MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    
    # Search
    MAX_SEARCH_RESULTS = 3
    
    # Neo4j - Priority: Cloud URI > Localhost Fallback
    NEO4J_URI = os.getenv("NEO4J_URI", f"bolt://localhost:{os.getenv('NEO4J_BOLT_PORT', 7687)}")
    NEO4J_USER = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")[0]
    NEO4J_PASSWORD = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")[1]

    # Keys
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    @staticmethod
    def validate():
        if not Config.GOOGLE_API_KEY: raise ValueError("Missing GOOGLE_API_KEY")
        if not Config.TAVILY_API_KEY: raise ValueError("Missing TAVILY_API_KEY")