"""Health endpoint smoke test using FastAPI's TestClient."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import __version__
from app.api.health import router


def test_health_ok():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": __version__}
