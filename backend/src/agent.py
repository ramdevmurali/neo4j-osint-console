from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from src.config import Config
from src.search import perform_search
from src.graph_ops import insert_knowledge
from src.schema import KnowledgeGraphUpdate
import logging
from langgraph.checkpoint.memory import MemorySaver # <--- NEW IMPORT


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

# ... (Previous imports remain the same) ...
from langgraph.checkpoint.memory import MemorySaver # <--- NEW IMPORT

# ... (LLM and Tools setup remain the same) ...

# 3. Create the Agent with Memory
tools = [search_tavily, save_to_graph]

system_prompt = """
You are an Autonomous OSINT Agent. Your ONLY goal is to build a Knowledge Graph.
1. You MUST search for information if you don't have it.
2. You MUST use 'save_to_graph' to save every entity and relationship you find.
3. DO NOT just summarize the findings in text. If you don't call 'save_to_graph', you have FAILED.
4. When saving, be granular.
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

