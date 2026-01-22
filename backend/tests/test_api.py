from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health_check():
    print("🧪 Testing Health Endpoint...")
    response = client.get("/")
    
    assert response.status_code == 200
    
    expected = {"status": "operational"}
    actual = response.json()
    
    if actual != expected:
        print(f"⚠️  Mismatch! Expected: {expected}, Got: {actual}")
    
    assert actual == expected
    print("✅ Health Check Passed")

def test_run_mission_flow():
    print("🧪 Testing Mission Endpoint (Dry Run)...")
    
    payload = {
        "task": "What is 2 + 2? Answer briefly.",
        "thread_id": "test-api-automated"
    }
    
    response = client.post("/run-mission", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        assert response.status_code == 200
        
    data = response.json()
    assert "result" in data
    assert "thread_id" in data
    assert data["status"] == "success"
    
    print(f"✅ Mission Response: {data['result']}")

if __name__ == "__main__":
    test_health_check()
    test_run_mission_flow()
