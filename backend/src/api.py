import logging

from fastapi import FastAPI
from src.agent import run_agent  # re-export for legacy tests

from src.routes.agents import router as agents_router
from src.routes.graph import router as graph_router

app = FastAPI(title="Gotham OSINT API", version="1.0")
logging.basicConfig(level=logging.INFO)


@app.get("/")
def health():
    return {"status": "operational"}


# Include routers
app.include_router(agents_router)
app.include_router(graph_router)

# Backward compatibility for tests expecting run_agent on api module
__all__ = ["app", "run_agent"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
