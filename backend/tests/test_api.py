from fastapi.testclient import TestClient
import src.api as api
import src.routes.agents as agents
import src.services.graph_queries as graph_queries
import src.agent as agent_module

def test_health_check():
    client = TestClient(api.app)
    response = client.get("/")
    
    assert response.status_code == 200
    
    expected = {"status": "operational"}
    actual = response.json()
    
    assert actual == expected

def test_run_mission_flow(monkeypatch):
    payload = {
        "task": "What is 2 + 2? Answer briefly.",
        "thread_id": "test-api-automated"
    }

    client = TestClient(api.app)
    monkeypatch.setattr(agents, "run_agent", lambda task, thread_id=None: "stubbed-response")
    response = client.post("/run-mission", json=payload)
    
    assert response.status_code == 200

    data = response.json()
    assert "result" in data
    assert "thread_id" in data
    assert data["status"] == "success"


def test_company_mood_endpoint(monkeypatch):
    client = TestClient(api.app)

    monkeypatch.setattr(
        agents,
        "get_company_mood",
        lambda company, timeframe="90d": {
            "mood_label": "Neutral",
            "confidence": 0.5,
            "drivers": ["Test driver"],
            "sources": [],
            "timeframe": timeframe,
        },
    )

    response = client.post("/agents/company-mood", json={"company": "TestCo", "timeframe": "30d"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["mood_label"] == "Neutral"


def test_graph_profile_snapshot(monkeypatch):
    client = TestClient(api.app)

    monkeypatch.setattr(
        graph_queries,
        "fetch_entity_profile",
        lambda name: {
            "name": name,
            "labels": ["Organization"],
            "properties": {"name": name, "founded": "2001"},
            "sources": [],
            "related": [],
            "snapshot": {"name": name, "hq": None, "founded": "2001", "ceo": None},
        },
    )

    response = client.get("/graph/profile?name=TestCo")
    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot"]["name"] in {"TestCo", "Tesco"}


def test_run_agent_backoff(monkeypatch):
    calls = {"count": 0}

    class DummyMsg:
        def __init__(self, content: str):
            self.content = content

    class DummyExecutor:
        def invoke(self, payload, config=None):
            calls["count"] += 1
            if calls["count"] < 2:
                raise Exception("429 RESOURCE_EXHAUSTED")
            return {"messages": [DummyMsg("done")]}

    monkeypatch.setattr(agent_module, "get_agent_executor", lambda: DummyExecutor())
    # semaphore shouldn't block single call; ensure backoff retries then succeeds
    result = agent_module.run_agent("test", thread_id=None)
    assert result == "done"
