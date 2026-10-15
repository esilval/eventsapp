"""Pruebas del endpoint HTTP POST /v1/auth/register (AC-001..AC-004; spec 002: R005-R012).

Ejercitan el stack completo (Flask + caso de uso + SQLAlchemy + bcrypt) sobre
SQLite in-memory.
"""

from __future__ import annotations

ENDPOINT = "/v1/auth/register"


def test_register_returns_201_and_confirmation(client):
    resp = client.post(
        ENDPOINT,
        json={"name": "Ana", "email": "ana@example.com", "password": "Abcd123!"},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["message"] == "Usuario registrado exitosamente."
    assert body["user"]["email"] == "ana@example.com"
    assert body["user"]["id"]
    # Nunca se devuelve la contraseña ni su hash.
    assert "password" not in body["user"]


def test_duplicate_email_returns_409(client):
    payload = {"name": "Ana", "email": "dup@example.com", "password": "Abcd123!"}
    assert client.post(ENDPOINT, json=payload).status_code == 201

    resp = client.post(ENDPOINT, json=payload)
    assert resp.status_code == 409
    assert "error" in resp.get_json()


def test_weak_password_returns_400_with_details(client):
    resp = client.post(
        ENDPOINT,
        json={"name": "Ana", "email": "weak@example.com", "password": "weak"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]
    assert body["details"]  # lista de reglas incumplidas


def test_missing_fields_return_400(client):
    resp = client.post(ENDPOINT, json={"email": "x@example.com"})
    assert resp.status_code == 400


def test_non_json_body_returns_400(client):
    resp = client.post(ENDPOINT, data="no soy json", content_type="text/plain")
    assert resp.status_code == 400


# -- Feature 002-registro-usuario: comportamiento existente (T005) ---------

_VALID = {"name": "Ana", "email": "ana@example.com", "password": "Abcd123!"}


def _account_count(app) -> int:
    from sqlalchemy import func, select

    from app.infrastructure.models import UserModel

    session = app.extensions["auth_session_factory"]()
    try:
        return session.scalar(select(func.count()).select_from(UserModel))
    finally:
        app.extensions["auth_session_factory"].remove()


def test_F002_R005_correo_existente_responde_409_explicito(client, app):
    assert client.post(ENDPOINT, json=_VALID).status_code == 201

    resp = client.post(ENDPOINT, json={**_VALID, "name": "Otra", "password": "Zxcv987!"})

    assert resp.status_code == 409
    assert resp.get_json()["error"] == "El correo electrónico ya está registrado."
    assert _account_count(app) == 1


def test_F002_R006_correo_con_mayusculas_y_espacios_responde_409(client, app):
    assert client.post(ENDPOINT, json=_VALID).status_code == 201

    resp = client.post(ENDPOINT, json={**_VALID, "email": "  ANA@Example.com "})

    assert resp.status_code == 409
    assert resp.get_json()["error"] == "El correo electrónico ya está registrado."
    assert _account_count(app) == 1


def test_F002_R010_confirmacion_incluye_id_nombre_y_correo_normalizado(client):
    resp = client.post(ENDPOINT, json={**_VALID, "email": "  Ana@Example.COM "})

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["message"] == "Usuario registrado exitosamente."
    assert body["user"]["id"]
    assert body["user"]["name"] == "Ana"
    assert body["user"]["email"] == "ana@example.com"


def test_F002_R012_texto_plano_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(ENDPOINT, data="no soy json", content_type="text/plain")

    assert resp.status_code == 400
    assert resp.get_json()["error"]
    assert _account_count(app) == 0


def test_F002_R012_sintaxis_invalida_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(
        ENDPOINT, data='{"name": "Ana", "email": ', content_type="application/json"
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]
    assert _account_count(app) == 0


def test_F002_R012_lista_en_lugar_de_campos_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(ENDPOINT, json=[_VALID])

    assert resp.status_code == 400
    assert resp.get_json()["error"]
    assert _account_count(app) == 0


# -- Feature 002-registro-usuario: carrera y logs (T011) -------------------


def test_F002_R007_carrera_con_lectura_previa_ciega_responde_409(client, app, monkeypatch):
    from app.infrastructure.user_repository import SqlAlchemyUserRepository

    assert client.post(ENDPOINT, json=_VALID).status_code == 201

    # Simula la petición concurrente: su comprobación de unicidad no ve la fila
    # recién insertada, así que solo la restricción única puede frenarla.
    blind_reads: list[str] = []

    def blind_get_by_email(self, email):
        blind_reads.append(email)
        return None

    monkeypatch.setattr(SqlAlchemyUserRepository, "get_by_email", blind_get_by_email)
    resp = client.post(ENDPOINT, json={**_VALID, "name": "Otra"})

    # El 409 sale de la restricción única, no de la comprobación previa.
    assert blind_reads == ["ana@example.com"]
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "El correo electrónico ya está registrado."
    assert _account_count(app) == 1


def _stored_password_hash(app, email: str) -> str:
    from sqlalchemy import select

    from app.infrastructure.models import UserModel

    session = app.extensions["auth_session_factory"]()
    try:
        return session.scalar(select(UserModel.password).where(UserModel.email == email))
    finally:
        app.extensions["auth_session_factory"].remove()


def test_F002_R009_ni_la_contrasena_ni_su_hash_aparecen_en_logs_ni_respuestas(
    client, app, caplog
):
    import logging

    # Raíz a DEBUG: cualquier log nuevo de la app o de Flask se captura. Los
    # loggers ``sqlalchemy.*`` conservan su nivel (WARN): se verifica la
    # configuración real del servicio, en la que el SQL solo se vuelca si se
    # activa ``echo`` o se sube ese logger a INFO, y entonces esta prueba falla.
    caplog.set_level(logging.DEBUG)

    weak_password = "weakpass"
    ok = client.post(ENDPOINT, json=_VALID)
    duplicate = client.post(ENDPOINT, json=_VALID)
    weak = client.post(ENDPOINT, json={**_VALID, "email": "otra@example.com", "password": weak_password})
    stored_hash = _stored_password_hash(app, "ana@example.com")

    assert ok.status_code == 201
    assert duplicate.status_code == 409
    assert weak.status_code == 400
    assert stored_hash
    bodies = [resp.get_data(as_text=True) for resp in (ok, duplicate, weak)]
    for secret in (_VALID["password"], stored_hash, weak_password):
        assert secret not in caplog.text
        for body in bodies:
            assert secret not in body


def test_F002_R009_el_engine_no_registra_sentencias_sql(app):
    engine = app.extensions["auth_session_factory"].session_factory.kw["bind"]

    # ``None`` (por defecto) o ``False``: SQLAlchemy no vuelca SQL ni parámetros.
    assert not engine.echo


# -- Feature 002-registro-usuario: valores no textuales (T006) -------------


def test_F002_R012_nombre_numerico_responde_400_y_no_500(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "name": 123})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["El nombre no tiene un formato válido."]
    assert _account_count(app) == 0


def test_F002_R012_contrasena_numerica_responde_400(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "password": 12345678})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["La contraseña no tiene un formato válido."]
    assert _account_count(app) == 0


def test_F002_R012_telefono_numerico_da_un_unico_detalle(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "phone": 600123456})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["El teléfono no tiene un formato válido."]
    assert _account_count(app) == 0


# -- Feature 002-registro-usuario: longitudes máximas (T007) ---------------


def test_F002_R015_exceso_de_longitud_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "name": "N" * 101})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["El nombre no puede superar 100 caracteres."]
    assert _account_count(app) == 0


# -- Feature 002-registro-usuario: teléfono (T008) -------------------------


def test_F002_R016_telefono_largo_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "phone": "6" * 21})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["El teléfono no puede superar 20 caracteres."]
    assert _account_count(app) == 0


def test_F002_R017_telefono_con_letras_responde_400_sin_crear_cuenta(client, app):
    resp = client.post(ENDPOINT, json={**_VALID, "phone": "600-ABC-123"})

    assert resp.status_code == 400
    assert resp.get_json()["details"] == ["El teléfono no tiene un formato válido."]
    assert _account_count(app) == 0
