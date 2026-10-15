"""Pruebas de las sondas de salud (`/health`, `/health/ready`)."""

from __future__ import annotations

from unittest.mock import patch

from sqlalchemy.exc import OperationalError


def test_liveness_ok(client):
    """`/health` devuelve 200 sin consultar dependencias."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_readiness_ok_when_db_reachable(client):
    """`/health/ready` devuelve 200 con la BD accesible (SQLite in-memory)."""
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


def test_readiness_503_when_db_down(client, app):
    """Si la BD no responde, `/health/ready` devuelve 503 (readiness fallida)."""
    session_factory = app.extensions["auth_session_factory"]
    session = session_factory()
    with patch.object(
        session,
        "execute",
        side_effect=OperationalError("SELECT 1", {}, Exception("db down")),
    ):
        resp = client.get("/health/ready")

    assert resp.status_code == 503
    body = resp.get_json()
    assert body["status"] == "unavailable"
    assert body["checks"]["database"] == "error"
