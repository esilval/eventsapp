"""Pruebas del decorador ``require_auth`` (R007, R009, R010, y R008 revocación)."""

from __future__ import annotations

import pytest
from flask import Flask, g

from app.blueprints.decorators import require_auth
from app.infrastructure.db import Base, create_db_engine, create_session_factory
from app.infrastructure.revoked_token_repository import (
    SqlAlchemyRevokedTokenRepository,
)
from app.infrastructure.token_service import JwtTokenService

_SECRET = "test-jwt-secret"


@pytest.fixture
def app():
    app = Flask(__name__)
    engine = create_db_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    app.extensions["auth_session_factory"] = session_factory
    app.extensions["auth_token_service"] = JwtTokenService(_SECRET, expiry_seconds=3600)

    @app.get("/protected")
    @require_auth
    def protected():
        return {"user_id": g.auth_claims.user_id}, 200

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_R007_sin_token_rechaza(client):
    assert client.get("/protected").status_code == 401


def test_R007_con_token_valido_permite(client):
    token = JwtTokenService(_SECRET, 3600).issue("user-1").token
    resp = client.get("/protected", headers=_bearer(token))
    assert resp.status_code == 200
    assert resp.get_json()["user_id"] == "user-1"


def test_R009_token_expirado_rechaza(client):
    expired = JwtTokenService(_SECRET, expiry_seconds=-10).issue("user-1").token
    assert client.get("/protected", headers=_bearer(expired)).status_code == 401


def test_R010_token_malformado_rechaza(client):
    assert client.get("/protected", headers=_bearer("no-es-un-jwt")).status_code == 401
    # Firmado con otro secreto → inválido.
    otro = JwtTokenService("otro-secreto", 3600).issue("user-1").token
    assert client.get("/protected", headers=_bearer(otro)).status_code == 401


def test_R008_token_revocado_rechaza(app, client):
    issued = JwtTokenService(_SECRET, 3600).issue("user-1")
    session = app.extensions["auth_session_factory"]()
    SqlAlchemyRevokedTokenRepository(session).revoke(issued.jti, issued.expires_at)

    assert client.get("/protected", headers=_bearer(issued.token)).status_code == 401
