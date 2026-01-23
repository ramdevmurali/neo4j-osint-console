import logging
import json

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.config import Config
from src.tools.graph import save_to_graph, check_graph
from src.tools.search import search_tavily


# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gotham_agent")

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
_agent_executor = None

def _build_agent():
    llm = ChatGoogleGenerativeAI(
        model=Config.MODEL_NAME,
        temperature=0,
        max_retries=Config.LLM_MAX_RETRIES,
        timeout=Config.LLM_TIMEOUT,
        convert_system_message_to_human=True
    )
    memory = MemorySaver()
    return create_react_agent(
        llm,
        tools,
        prompt=system_prompt,
        checkpointer=memory
    )

def get_agent_executor():
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = _build_agent()
    return _agent_executor

def run_agent(task: str, thread_id: str | None = None) -> str:
    agent_executor = get_agent_executor()
    payload = {"messages": [("user", task)]}
    if thread_id:
        result = agent_executor.invoke(payload, config={"configurable": {"thread_id": thread_id}})
    else:
        result = agent_executor.invoke(payload)

    last_msg = result["messages"][-1]
    content = last_msg.content
    # If LLM returned only tool calls, summarize the save_to_graph action
    if not content:
        # search from the end to find any tool call
        tool_calls = None
        for msg in reversed(result.get("messages", [])):
            calls = getattr(msg, "tool_calls", None)
            if calls:
                tool_calls = calls
                break
            if isinstance(msg, dict) and msg.get("tool_calls"):
                tool_calls = msg["tool_calls"]
                break

        if tool_calls:
            tc = tool_calls[0]
            name = tc.get("name") or tc.get("tool") or ""
            args = tc.get("args", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            if name == "save_to_graph":
                data = args.get("data", args) if isinstance(args, dict) else {}
                entities = data.get("entities", []) if isinstance(data, dict) else []

                def pick_entity(labels_priority):
                    for lbl in labels_priority:
                        for ent in entities:
                            if isinstance(ent, dict) and ent.get("label") == lbl and ent.get("name"):
                                return ent
                    for ent in entities:
                        if isinstance(ent, dict) and ent.get("name"):
                            return ent
                    return None

                primary = pick_entity(["Person", "Organization"])
                name_str = primary.get("name") if primary else None
                label_str = primary.get("label") if primary else None

                content = (
                    f"Saved to graph: {name_str} ({label_str})."
                    if name_str
                    else f"Saved to graph: {len(entities)} entities, {len(data.get('relationships', []))} relationships."
                )
            else:
                content = "Saved to graph."

    return content or "Task processed."
