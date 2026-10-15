"""Puertos de persistencia del dominio.

Definen las abstracciones (interfaces) de las que depende la capa de
aplicación. Las implementaciones concretas viven en ``infrastructure`` — así se
respeta la inversión de dependencias de Clean Architecture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.user import User


class UserRepository(ABC):
    """Puerto de acceso a datos para la entidad ``User``."""

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Devuelve el usuario con ese email, o ``None`` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        """Devuelve el usuario con ese id, o ``None`` si no existe."""
        raise NotImplementedError

    @abstractmethod
    def add(self, user: User) -> None:
        """Persiste un nuevo usuario."""
        raise NotImplementedError

    @abstractmethod
    def update_last_login(self, user_id: str, when: datetime) -> None:
        """Registra la marca de último inicio de sesión del usuario (R006)."""
        raise NotImplementedError


class LoginAttemptRepository(ABC):
    """Puerto para el conteo de intentos de login fallidos (R005).

    El conteo se hace por combinación ``(email, origin)`` dentro de una ventana
    temporal, según la spec.
    """

    @abstractmethod
    def count_recent(self, email: str, origin: str, since: datetime) -> int:
        """Cuenta los fallos de ``(email, origin)`` desde ``since`` (inclusive)."""
        raise NotImplementedError

    @abstractmethod
    def record_failure(self, email: str, origin: str, when: datetime) -> None:
        """Registra un intento fallido para ``(email, origin)``."""
        raise NotImplementedError

    @abstractmethod
    def clear(self, email: str, origin: str) -> None:
        """Elimina los intentos fallidos de ``(email, origin)`` (tras éxito)."""
        raise NotImplementedError


class RevokedTokenRepository(ABC):
    """Puerto para la lista de revocación de credenciales de sesión (R008)."""

    @abstractmethod
    def revoke(self, jti: str, expires_at: datetime) -> None:
        """Marca el ``jti`` como revocado hasta su expiración."""
        raise NotImplementedError

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Indica si el ``jti`` está en la lista de revocación."""
        raise NotImplementedError
