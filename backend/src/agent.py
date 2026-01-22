from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.config import Config
from src.search import perform_search
from src.graph_ops import insert_knowledge
from src.schema import KnowledgeGraphUpdate
import logging
from langgraph.checkpoint.memory import MemorySaver 
from src.graph_ops import insert_knowledge, lookup_entity


# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gotham_agent")

# 1. Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model=Config.MODEL_NAME,
    temperature=0,
    convert_system_message_to_human=True
)

# 2. Define Tools
@tool
def search_tavily(query: str):
    """
    Search the web for information using Tavily.
    Use this to gather facts before saving them to the database.
    """
    return perform_search(query, max_results=Config.MAX_SEARCH_RESULTS)

@tool
def save_to_graph(data: KnowledgeGraphUpdate):
    """
    Save extracted entities and relationships to the Knowledge Graph.
    Use this AFTER gathering information.
    Input must be a valid JSON object matching the KnowledgeGraphUpdate schema.
    """
    if isinstance(data, dict):
        data = KnowledgeGraphUpdate(**data)
    return insert_knowledge(data)
@tool
def check_graph(name: str):
    """
    Use this tool BEFORE saving to check if an entity already exists in the database.
    Useful for preventing duplicates (e.g. checking if 'Bill Gates' already exists as 'William Gates').
    """
    return lookup_entity(name)

from langgraph.checkpoint.memory import MemorySaver # <--- NEW IMPORT


# 3. Create the Agent with Memory
tools = [search_tavily, save_to_graph, check_graph]

system_prompt = """
You are a Knowledge Graph Populator. Your ONLY goal is to save structured data to the Neo4j Database.

RULES:
1. **ALWAYS SAVE:** Even if you already know the answer from your training data, you MUST call the `save_to_graph` tool to persist it.
2. **VERIFY FIRST:** Use `check_graph` to see if entities exist before saving to avoid duplicates.
3. **NO CHIT-CHAT:** Do not just answer the user textually. Your job is considered "Complete" ONLY when the `save_to_graph` tool has been successfully called.
4. **SOURCES:** If you rely on internal knowledge, use "Internal Knowledge" as the source_url in the save tool. Otherwise, use `search_tavily`.
"""
# Initialize Memory (In-RAM persistence)
memory = MemorySaver()

# Pass the checkpointer to the agent
agent_executor = create_react_agent(
    llm, 
    tools, 
    prompt=system_prompt,
    checkpointer=memory # <--- THIS ENABLES MEMORY
)

