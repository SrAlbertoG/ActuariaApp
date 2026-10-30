"""Prueba de salud y proteccion por token desde el backend"""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

client = TestClient(app)

def test_health_is_public():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_api_denied_token():
    assert client.get("/api/v1/ping").status_code == 401

def test_api_accept_token():
    headers = {"X-Session-Token" : get_settings().api_token}
    r = client.get("/api/v1/ping", headers=headers)
    assert r.status_code == 200
    assert r.json() == {"pong" : True}