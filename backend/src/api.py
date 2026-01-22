import logging
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.agent import run_agent

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
        content = run_agent(req.task, thread_id=req.thread_id)

        return {
            "result": content,
            "thread_id": req.thread_id,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
