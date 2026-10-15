"""Puertos de seguridad: hashing de contraseñas y credenciales de sesión.

Abstraen los algoritmos concretos (bcrypt, JWT) para que la capa de aplicación
no dependa de una librería específica (Clean Architecture).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


class PasswordHasher(ABC):
    """Puerto para el hashing y verificación de contraseñas."""

    @abstractmethod
    def hash(self, plain_password: str) -> str:
        """Genera el hash (con salt embebido) de una contraseña en claro."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Comprueba si una contraseña en claro corresponde al hash dado."""
        raise NotImplementedError


# -- Credencial de sesión (feature 001-inicio-sesion-usuario) -------------


class TokenError(Exception):
    """Base de los fallos de validación de una credencial de sesión."""


class ExpiredTokenError(TokenError):
    """El token está bien firmado pero ha superado su expiración (R009)."""


class InvalidTokenError(TokenError):
    """El token está ausente, malformado o con firma inválida (R010)."""


@dataclass(frozen=True)
class IssuedToken:
    """Credencial de sesión recién emitida."""

    token: str
    jti: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenClaims:
    """Reclamaciones verificadas de una credencial de sesión."""

    user_id: str
    jti: str
    expires_at: datetime


class TokenService(ABC):
    """Puerto para emitir y verificar credenciales de sesión (R001, R009)."""

    @abstractmethod
    def issue(self, user_id: str) -> IssuedToken:
        """Emite una credencial de sesión asociada a ``user_id``."""
        raise NotImplementedError

    @abstractmethod
    def verify(self, token: str) -> TokenClaims:
        """Valida firma y expiración de ``token`` y devuelve sus claims.

        Lanza :class:`ExpiredTokenError` si expiró y :class:`InvalidTokenError`
        si está malformado o mal firmado.
        """
        raise NotImplementedError
