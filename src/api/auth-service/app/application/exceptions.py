"""Excepciones de la capa de aplicación.

Representan fallos de reglas de negocio de forma independiente del transporte
HTTP. La capa de presentación las traduce a códigos de estado.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """Base de los errores de negocio del servicio."""

    def __init__(self, message: str, details: list[str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class ValidationError(ApplicationError):
    """Datos de entrada ausentes o con formato inválido (→ HTTP 400)."""


class WeakPasswordError(ApplicationError):
    """La contraseña no cumple la política de seguridad (→ HTTP 400)."""


class EmailAlreadyRegisteredError(ApplicationError):
    """Ya existe un usuario con ese email (→ HTTP 409)."""


# Mensaje genérico e indistinguible para todos los fallos de login (R002):
# no revela si el email existe ni cuál de los dos datos es incorrecto.
INVALID_CREDENTIALS_MESSAGE = "Correo electrónico o contraseña inválidos."


class InvalidCredentialsError(ApplicationError):
    """Credenciales que no corresponden a ninguna cuenta (→ HTTP 401).

    Cubre tanto el email inexistente como la contraseña incorrecta, con el
    mismo mensaje (R002).
    """

    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS_MESSAGE)


class AccountLockedError(ApplicationError):
    """Cuenta+origen bloqueada por fuerza bruta (R005) (→ HTTP 401).

    Usa el mismo mensaje genérico que :class:`InvalidCredentialsError` para no
    revelar el estado de bloqueo.
    """

    def __init__(self) -> None:
        super().__init__(INVALID_CREDENTIALS_MESSAGE)
