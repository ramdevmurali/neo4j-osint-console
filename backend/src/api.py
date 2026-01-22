import logging
import uuid
from dotenv import load_dotenv

# Initialize Env FIRST
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.agent import agent_executor

app = FastAPI(title="Gotham OSINT API", version="1.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

class MissionRequest(BaseModel):
    task: str
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

@app.get("/")
def health():
    return {"status": "operational"}

@app.post("/run-mission")
async def run_mission(req: MissionRequest):
    logger.info(f"Task: {req.task} | Thread: {req.thread_id}")
    
    try:
        result = agent_executor.invoke(
            {"messages": [("user", req.task)]},
            config={"configurable": {"thread_id": req.thread_id}}
        )
        
        # Extract Response
        last_msg = result["messages"][-1]
        content = last_msg.content
        
        # Fallback for tool-only responses
        if not content and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            tc = last_msg.tool_calls[0]
            content = f"🤖 Executed tool: {tc['name']} (args: {tc['args']})"
            
        return {
            "result": content or "Task processed.",
            "thread_id": req.thread_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)