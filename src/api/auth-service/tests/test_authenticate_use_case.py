"""Pruebas unitarias del caso de uso de inicio de sesión.

Cubre R001, R002, R003, R004, R005 y R006 con dobles en memoria.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.authenticate_user import AuthenticateUserUseCase
from app.application.dtos import LoginRequest
from app.application.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    ValidationError,
)
from app.domain.security import IssuedToken, TokenService
from app.domain.user import User


class FakeTokenService(TokenService):
    def issue(self, user_id: str) -> IssuedToken:
        return IssuedToken(
            token=f"token-for-{user_id}",
            jti="jti-fixed",
            expires_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
        )

    def verify(self, token: str):  # no usado en estas pruebas
        raise NotImplementedError


class InMemoryLoginAttemptRepository:
    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], list[datetime]] = {}

    def count_recent(self, email, origin, since) -> int:
        return sum(1 for t in self._by_key.get((email, origin), []) if t >= since)

    def record_failure(self, email, origin, when) -> None:
        self._by_key.setdefault((email, origin), []).append(when)

    def clear(self, email, origin) -> None:
        self._by_key.pop((email, origin), None)


def _make_use_case(user_repository, password_hasher, attempts=None):
    return AuthenticateUserUseCase(
        user_repository,
        password_hasher,
        FakeTokenService(),
        attempts or InMemoryLoginAttemptRepository(),
        max_attempts=3,
        window_seconds=300,
        decoy_password_hash=password_hasher.hash("decoy-unused"),
    )


@pytest.fixture
def registered_user(user_repository, password_hasher):
    user = User.new(
        name="Ada",
        email="ada@example.com",
        password_hash=password_hasher.hash("Secret-123!"),
    )
    user_repository.add(user)
    return user


def test_R001_credenciales_correctas_emiten_token(
    registered_user, user_repository, password_hasher
):
    use_case = _make_use_case(user_repository, password_hasher)

    result = use_case.execute(
        LoginRequest(email="ada@example.com", password="Secret-123!", origin="ip-1")
    )

    assert result.token == f"token-for-{registered_user.id}"
    assert result.user.email == "ada@example.com"
    assert result.user.id == registered_user.id


def test_R002_email_inexistente_y_password_incorrecta_dan_mismo_error(
    registered_user, user_repository, password_hasher
):
    use_case = _make_use_case(user_repository, password_hasher)

    with pytest.raises(InvalidCredentialsError) as no_user:
        use_case.execute(
            LoginRequest(email="nadie@example.com", password="x", origin="ip-1")
        )
    with pytest.raises(InvalidCredentialsError) as bad_pass:
        use_case.execute(
            LoginRequest(email="ada@example.com", password="wrong", origin="ip-1")
        )

    # Mensaje indistinguible en ambos casos (no revela si la cuenta existe).
    assert no_user.value.message == bad_pass.value.message


def test_R003_falta_campo_lanza_validation_error(user_repository, password_hasher):
    use_case = _make_use_case(user_repository, password_hasher)

    with pytest.raises(ValidationError):
        use_case.execute(LoginRequest(email="", password="x", origin="ip-1"))
    with pytest.raises(ValidationError):
        use_case.execute(LoginRequest(email="a@b.com", password="", origin="ip-1"))


def test_R004_no_expone_password_en_claro(
    registered_user, user_repository, password_hasher
):
    use_case = _make_use_case(user_repository, password_hasher)

    result = use_case.execute(
        LoginRequest(email="ada@example.com", password="Secret-123!", origin="ip-1")
    )

    # La contraseña en claro no aparece en el resultado devuelto.
    assert "Secret-123!" not in repr(result)


def test_R005_tres_fallos_bloquean_cuarto_intento(
    registered_user, user_repository, password_hasher
):
    attempts = InMemoryLoginAttemptRepository()
    use_case = _make_use_case(user_repository, password_hasher, attempts)

    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(
                LoginRequest(email="ada@example.com", password="wrong", origin="ip-1")
            )

    # El 4.º intento, aun con la contraseña correcta, queda bloqueado (R005).
    with pytest.raises(AccountLockedError):
        use_case.execute(
            LoginRequest(email="ada@example.com", password="Secret-123!", origin="ip-1")
        )


def test_R005_otro_origen_no_queda_bloqueado(
    registered_user, user_repository, password_hasher
):
    attempts = InMemoryLoginAttemptRepository()
    use_case = _make_use_case(user_repository, password_hasher, attempts)

    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(
                LoginRequest(email="ada@example.com", password="wrong", origin="ip-1")
            )

    # Desde otro origen, la contraseña correcta entra con normalidad.
    result = use_case.execute(
        LoginRequest(email="ada@example.com", password="Secret-123!", origin="ip-2")
    )
    assert result.user.id == registered_user.id


def test_R006_login_exitoso_actualiza_last_login(
    registered_user, user_repository, password_hasher
):
    use_case = _make_use_case(user_repository, password_hasher)
    assert registered_user.last_login is None

    use_case.execute(
        LoginRequest(email="ada@example.com", password="Secret-123!", origin="ip-1")
    )

    assert user_repository.get_by_email("ada@example.com").last_login is not None
