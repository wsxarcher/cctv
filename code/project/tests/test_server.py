from fastapi.testclient import TestClient

from project.server import app

client = TestClient(app)

def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello World",
    }