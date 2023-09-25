from fastapi.testclient import TestClient
from datetime import datetime, timezone

from project.server import app
from project import db_logic, schema

client = TestClient(app)

def test_alerts_unauth():
    response = client.get("/alerts", cookies={"token": "unvalid"})
    assert response.status_code == 200
    assert "<form hx-post=\"/login\"" in response.text

def test_wronglogin():
    response = client.post("/login", data={"username": "admin", "password": "abc"})
    assert response.status_code == 401
    token = response.cookies.get('token', None)
    assert token is None

def test_login():
    response = client.post("/login", data={"username": "admin", "password": "password"})
    assert response.status_code == 200
    token = response.cookies.get('token', None)
    assert len(token) == 128

def test_alerts_auth():
    response = client.get("/alerts")
    assert response.status_code == 200
    assert "<form hx-post=\"/login\"" not in response.text

def test_db():
    id = db_logic.add_detection(1, datetime.now(timezone.utc).replace(
                                microsecond=0
                            ), '', b'')
    found = None
    for det in db_logic.detections():
        if det.id == id:
            found = det
            break
    assert found.camera_id == 1
    db_logic.delete_detection(id)
    found = None
    for det in db_logic.detections():
        if det.id == id:
            found = det
            break
    assert found is None

def test_sm():
    response = client.post("/settings/streamingmethod", data={"method": "hls"})
    assert response.status_code == 200
    user = db_logic.is_logged(client.cookies['token'])
    assert user.streaming_method == schema.StreamingMethod.hls


def test_instrusionde():
    response = client.get("/settings/intrusiondetection/3242")
    assert "checked" in response.content.decode()

def test_settings():
    prev_token = client.cookies['token']
    new_session = client.post("/login", data={"username": "admin", "password": "password"})
    response = client.get("/settings")
    assert response.status_code == 200
    assert prev_token in response.content.decode()


