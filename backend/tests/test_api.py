from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health_check():
    """
    Verifies the server starts and answers basic requests.
    """
    print("🧪 Testing Health Endpoint...")
    response = client.get("/")
    
    # Check if the server is alive (200 OK)
    assert response.status_code == 200
    
    # Check the payload (Updated to match your lean API)
    # If this fails, we print what we actually got
    expected = {"status": "operational"}
    actual = response.json()
    
    if actual != expected:
        print(f"⚠️  Mismatch! Expected: {expected}, Got: {actual}")
    
    assert actual == expected
    print("✅ Health Check Passed")

def test_run_mission_flow():
    """
    Smoke Test for the Agent Endpoint.
    """
    print("🧪 Testing Mission Endpoint (Dry Run)...")
    
    # We use a thread_id to keep it isolated
    payload = {
        "task": "What is 2 + 2? Answer briefly.",
        "thread_id": "test-api-automated"
    }
    
    response = client.post("/run-mission", json=payload)
    
    # 1. Check HTTP Status
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        assert response.status_code == 200
        
    # 2. Check Data Structure
    data = response.json()
    assert "result" in data
    assert "thread_id" in data
    assert data["status"] == "success"
    
    print(f"✅ Mission Response: {data['result']}")

if __name__ == "__main__":
    test_health_check()
    test_run_mission_flow()