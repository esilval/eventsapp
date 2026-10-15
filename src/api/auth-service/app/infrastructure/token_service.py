"""Implementación de ``TokenService`` con JWT (PyJWT, HS256).

Emite credenciales de sesión autocontenidas y firmadas. La capa de aplicación
depende solo del puerto ``TokenService``; esta es la única parte del servicio
que conoce PyJWT.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.domain.security import (
    ExpiredTokenError,
    InvalidTokenError,
    IssuedToken,
    TokenClaims,
    TokenService,
)

_ALGORITHM = "HS256"


def _utcnow() -> datetime:
    """Timestamp actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class JwtTokenService(TokenService):
    """Adaptador JWT del puerto ``TokenService`` (R001, R009)."""

    def __init__(self, secret: str, expiry_seconds: int) -> None:
        self._secret = secret
        self._expiry_seconds = expiry_seconds

    def issue(self, user_id: str) -> IssuedToken:
        issued_at = _utcnow()
        # El ``exp`` de un JWT es un entero de segundos (NumericDate), así que
        # trabajamos con precisión de segundos para que issue/verify coincidan.
        expires_at = (issued_at + timedelta(seconds=self._expiry_seconds)).replace(
            microsecond=0
        )
        jti = str(uuid.uuid4())
        payload = {
            "sub": user_id,
            "jti": jti,
            "iat": issued_at,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self._secret, algorithm=_ALGORITHM)
        return IssuedToken(token=token, jti=jti, expires_at=expires_at)

    def verify(self, token: str) -> TokenClaims:
        try:
            claims = jwt.decode(token, self._secret, algorithms=[_ALGORITHM])
        except jwt.ExpiredSignatureError as exc:  # R009
            raise ExpiredTokenError(str(exc)) from exc
        except jwt.InvalidTokenError as exc:  # R010 (firma/estructura inválida)
            raise InvalidTokenError(str(exc)) from exc

        try:
            return TokenClaims(
                user_id=claims["sub"],
                jti=claims["jti"],
                expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
            )
        except KeyError as exc:
            raise InvalidTokenError(f"Falta la reclamación {exc} en el token.") from exc
