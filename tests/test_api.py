from fastapi.testclient import TestClient
from main import app
import pytest
import base64
import json

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_execute_main_with_args():
    # 准备参数: {"name": "Manus", "value": 100}
    obj = {"name": "Manus", "value": 100}
    args_b64 = base64.b64encode(json.dumps(obj).encode('utf-8')).decode('utf-8')
    
    payload = {
        "code": "def main(obj):\n    print(f\"Hello {obj['name']}, value is {obj['value']}\")",
        "language": "python3.11",
        "args": args_b64
    }
    
    response = client.post("/v1/sandbox/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "Hello Manus, value is 100" in data["data"]["stdout"]

def test_execute_api_security_failure():
    payload = {
        "code": "import os; os.system('ls')",
        "language": "python3.11"
    }
    response = client.post("/v1/sandbox/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 1
    assert "Forbidden import: os" in data["data"]["error"]
