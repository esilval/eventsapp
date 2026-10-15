"""Pruebas de integración del acceso protegido GET /v1/auth/me.

Cubre R007 (acceso solo con credencial válida), R009 (expiración) y R010
(credencial inválida).
"""

from __future__ import annotations

from app.config import TestConfig as _TestConfig
from app.infrastructure.token_service import JwtTokenService

_PASSWORD = "Secret-123!"


def _register_and_login(client, email="ada@example.com"):
    client.post(
        "/v1/auth/register",
        json={"name": "Ada", "email": email, "password": _PASSWORD},
    )
    resp = client.post(
        "/v1/auth/login", json={"email": email, "password": _PASSWORD}
    )
    return resp.get_json()["token"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_R007_me_sin_token_401(client):
    assert client.get("/v1/auth/me").status_code == 401


def test_R007_me_con_token_200(client):
    token = _register_and_login(client)

    resp = client.get("/v1/auth/me", headers=_bearer(token))

    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "ada@example.com"


def test_R009_me_token_expirado_401(client):
    expired = JwtTokenService(_TestConfig().jwt_secret, expiry_seconds=-10).issue(
        "cualquier-id"
    )
    assert client.get("/v1/auth/me", headers=_bearer(expired.token)).status_code == 401


def test_R010_me_token_invalido_401(client):
    assert client.get("/v1/auth/me", headers=_bearer("no-es-jwt")).status_code == 401
