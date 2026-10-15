"""Pruebas de integración del endpoint POST /v1/auth/logout (R008)."""

from __future__ import annotations

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


def test_R008_logout_invalida_token_reusado(client):
    token = _register_and_login(client)

    # El token da acceso antes del logout.
    assert client.get("/v1/auth/me", headers=_bearer(token)).status_code == 200

    # Logout revoca el token.
    assert client.post("/v1/auth/logout", headers=_bearer(token)).status_code == 200

    # Reutilizar el token ya no da acceso (R008).
    assert client.get("/v1/auth/me", headers=_bearer(token)).status_code == 401


def test_R008_logout_sin_token_401(client):
    assert client.post("/v1/auth/logout").status_code == 401
