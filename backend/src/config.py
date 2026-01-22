import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env deterministically (independent of CWD).
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

class Config:
    # Model
    MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "6"))
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
    RUN_MISSION_TIMEOUT = int(os.getenv("RUN_MISSION_TIMEOUT", "120"))
    
    # Search
    MAX_SEARCH_RESULTS = 3
    
    # Neo4j - Priority: Cloud URI > Localhost Fallback
    NEO4J_URI = os.getenv("NEO4J_URI", f"bolt://localhost:{os.getenv('NEO4J_BOLT_PORT', 7687)}")
    NEO4J_USER = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")[0]
    NEO4J_PASSWORD = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")[1]

    # Keys
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
