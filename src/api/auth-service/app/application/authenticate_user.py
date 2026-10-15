"""Caso de uso: autenticar a un usuario (inicio de sesión).

Orquesta las reglas de ``spec.md`` (feature 001-inicio-sesion-usuario):
validación de campos (R003), bloqueo por fuerza bruta (R005), verificación de
contraseña sin filtrar la existencia de la cuenta (R002, R004), emisión de la
credencial de sesión (R001) y registro del último acceso (R006).

Depende únicamente de abstracciones (``UserRepository``, ``PasswordHasher``,
``TokenService``, ``LoginAttemptRepository``), respetando la inversión de
dependencias de Clean Architecture.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.application.dtos import AuthenticatedUser, LoginRequest, LoginResult
from app.application.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    ValidationError,
)
from app.domain.repositories import LoginAttemptRepository, UserRepository
from app.domain.security import PasswordHasher, TokenService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthenticateUserUseCase:
    """Autentica a un usuario aplicando las reglas de negocio del login."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        login_attempts: LoginAttemptRepository,
        *,
        max_attempts: int,
        window_seconds: int,
        decoy_password_hash: str,
    ) -> None:
        self._users = user_repository
        self._hasher = password_hasher
        self._tokens = token_service
        self._attempts = login_attempts
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        # Hash señuelo para igualar el coste temporal cuando el email no existe
        # (mitiga la enumeración de cuentas por temporización — R002).
        self._decoy_password_hash = decoy_password_hash

    def execute(self, request: LoginRequest) -> LoginResult:
        email = (request.email or "").strip().lower()
        password = request.password or ""
        origin = request.origin or ""

        self._validate_fields(email, password)

        now = _utcnow()
        self._ensure_not_locked(email, origin, now)

        user = self._users.get_by_email(email)
        stored_hash = user.password if user is not None else self._decoy_password_hash

        # Se verifica SIEMPRE (incluso sin usuario) para no revelar por tiempo si
        # la cuenta existe (R004).
        if user is None or not self._hasher.verify(password, stored_hash):
            self._attempts.record_failure(email, origin, now)
            raise InvalidCredentialsError()

        # Éxito: registrar último acceso (R006), limpiar intentos (R005) y emitir
        # la credencial de sesión (R001).
        self._users.update_last_login(user.id, now)
        self._attempts.clear(email, origin)
        issued = self._tokens.issue(user.id)

        return LoginResult(
            token=issued.token,
            user=AuthenticatedUser(id=user.id, name=user.name, email=user.email),
        )

    # -- reglas internas ---------------------------------------------------

    @staticmethod
    def _validate_fields(email: str, password: str) -> None:
        errors: list[str] = []
        if not email:
            errors.append("El correo electrónico es obligatorio.")
        if not password:
            errors.append("La contraseña es obligatoria.")
        if errors:
            raise ValidationError("Datos de inicio de sesión inválidos.", errors)

    def _ensure_not_locked(self, email: str, origin: str, now: datetime) -> None:
        since = now - timedelta(seconds=self._window_seconds)
        if self._attempts.count_recent(email, origin, since) >= self._max_attempts:
            raise AccountLockedError()
