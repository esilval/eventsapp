"""Prueba de extremo a extremo registro → login (feature 002, R011).

Ejercita el stack completo por HTTP: la cuenta creada por
``POST /v1/auth/register`` debe servir para iniciar sesión en
``POST /v1/auth/login`` con las mismas credenciales.
"""

from __future__ import annotations

_PASSWORD = "Abcd123!"


def test_F002_R011_la_cuenta_registrada_permite_iniciar_sesion(client):
    registered = client.post(
        "/v1/auth/register",
        json={"name": "Ana", "email": "Ana@Example.com", "password": _PASSWORD},
    )
    assert registered.status_code == 201
    user_id = registered.get_json()["user"]["id"]

    login = client.post(
        "/v1/auth/login",
        json={"email": "ana@example.com", "password": _PASSWORD},
    )

    assert login.status_code == 200
    body = login.get_json()
    assert body["token"]
    assert body["user"]["id"] == user_id

    # La credencial emitida identifica a la cuenta recién registrada.
    me = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.get_json()["user"]["id"] == user_id
