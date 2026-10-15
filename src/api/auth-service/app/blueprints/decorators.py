"""Decorador de autenticación para recursos protegidos.

``require_auth`` valida la credencial de sesión (firma y expiración) y comprueba
que no esté revocada, antes de permitir el acceso a una función personalizada
(R007). Traduce cualquier fallo a un 401 genérico (R009, R010).
"""

from __future__ import annotations

from functools import wraps

from flask import current_app, g, request

from app.domain.security import TokenError
from app.infrastructure.revoked_token_repository import (
    SqlAlchemyRevokedTokenRepository,
)
from utils.responses import error

_UNAUTHENTICATED = "No autenticado."


def require_auth(func):
    """Exige una credencial de sesión válida en la cabecera ``Authorization``."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token(request.headers.get("Authorization", ""))
        if token is None:
            return error(_UNAUTHENTICATED), 401

        token_service = current_app.extensions["auth_token_service"]
        try:
            claims = token_service.verify(token)  # R009/R010
        except TokenError:
            return error(_UNAUTHENTICATED), 401

        session = current_app.extensions["auth_session_factory"]()
        revoked = SqlAlchemyRevokedTokenRepository(session)
        if revoked.is_revoked(claims.jti):  # R008
            return error(_UNAUTHENTICATED), 401

        # Identidad autenticada disponible para el recurso.
        g.auth_claims = claims
        return func(*args, **kwargs)

    return wrapper


def _extract_bearer_token(header: str) -> str | None:
    """Devuelve el token de un ``Authorization: Bearer <token>`` o ``None``."""
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]
