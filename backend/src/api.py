from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field # <--- Added Field
from src.agent import agent_executor
import logging
import uuid # <--- To generate IDs if needed

# Initialize API
app = FastAPI(title="Gotham OSINT API", version="1.1")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

# Define the Request Body
class MissionRequest(BaseModel):
    task: str
    # New Optional Field: thread_id
    # If the user doesn't provide one, we'll create a new conversation
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

@app.get("/")
def health_check():
    return {"status": "operational", "system": "Project Gotham"}

@app.post("/run-mission")
async def run_mission(request: MissionRequest):
    """
    Endpoint to trigger the Autonomous Agent with Memory.
    """
    task = request.task
    thread_id = request.thread_id
    
    logger.info(f"🚀 Received Mission: {task} (Thread: {thread_id})")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        result = agent_executor.invoke(
            {"messages": [("user", task)]},
            config=config
        )
        
        # --- IMPROVED RESPONSE LOGIC ---
        messages = result["messages"]
        last_msg = messages[-1]
        response_text = last_msg.content
        
        # 1. If content is empty, check if it was a Tool Call
        if not response_text and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            tool_name = last_msg.tool_calls[0]['name']
            tool_args = last_msg.tool_calls[0]['args']
            response_text = f"🤖 Agent is executing tool: {tool_name} with args: {tool_args}"
            
        # 2. If still empty (rare), look backwards for the last text message
        if not response_text:
            for msg in reversed(messages):
                if msg.content:
                    response_text = msg.content
                    break
        
        # 3. Final Fallback
        if not response_text:
            response_text = "✅ Task processed (No text output generated)."

        return {
            "mission": task,
            "result": response_text,
            "thread_id": thread_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Mission Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))