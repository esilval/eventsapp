"""Objetos de transferencia de datos (DTOs) del caso de uso de registro.

Aíslan la capa de aplicación del formato de request/response HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterUserRequest:
    """Datos de entrada para registrar un usuario."""

    name: str
    email: str
    password: str
    phone: str | None = None


@dataclass(frozen=True)
class RegisterUserResult:
    """Resultado de un registro exitoso (sin datos sensibles)."""

    id: str
    name: str
    email: str
    phone: str | None


# -- Inicio de sesión (feature 001-inicio-sesion-usuario) -----------------


@dataclass(frozen=True)
class LoginRequest:
    """Datos de entrada para autenticar a un usuario.

    ``origin`` identifica el origen de la petición (IP del cliente) y se usa
    junto al email para el bloqueo por fuerza bruta (R005).
    """

    email: str
    password: str
    origin: str = ""


@dataclass(frozen=True)
class AuthenticatedUser:
    """Vista mínima del usuario autenticado (sin datos sensibles)."""

    id: str
    name: str
    email: str


@dataclass(frozen=True)
class LoginResult:
    """Resultado de un login exitoso: credencial de sesión y usuario."""

    token: str
    user: AuthenticatedUser
