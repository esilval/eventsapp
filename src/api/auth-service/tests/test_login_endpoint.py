"""Pruebas de integración del endpoint POST /v1/auth/login.

Cubre R001, R002, R003, R005 (y R006 vía éxito).
"""

from __future__ import annotations

_PASSWORD = "Secret-123!"


def _register(client, email):
    return client.post(
        "/v1/auth/register",
        json={"name": "Ada", "email": email, "password": _PASSWORD},
    )


def test_R001_login_ok_devuelve_token(client):
    _register(client, "ada@example.com")

    resp = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["token"]
    assert body["user"]["email"] == "ada@example.com"


def test_R002_credenciales_invalidas_401_generico(client):
    _register(client, "ada@example.com")

    bad_pass = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": "nope"}
    )
    no_user = client.post(
        "/v1/auth/login", json={"email": "nadie@example.com", "password": "nope"}
    )

    assert bad_pass.status_code == 401
    assert no_user.status_code == 401
    # Cuerpo indistinguible: no revela si la cuenta existe.
    assert bad_pass.get_json() == no_user.get_json()


def test_R003_faltan_campos_400(client):
    sin_password = client.post("/v1/auth/login", json={"email": "ada@example.com"})
    sin_email = client.post("/v1/auth/login", json={"password": _PASSWORD})

    assert sin_password.status_code == 400
    assert sin_email.status_code == 400


def test_R005_bloqueo_tras_tres_fallos(client):
    _register(client, "ada@example.com")

    for _ in range(3):
        r = client.post(
            "/v1/auth/login", json={"email": "ada@example.com", "password": "wrong"}
        )
        assert r.status_code == 401

    # El 4.º intento con la contraseña correcta queda bloqueado (R005).
    blocked = client.post(
        "/v1/auth/login", json={"email": "ada@example.com", "password": _PASSWORD}
    )
    assert blocked.status_code == 401
