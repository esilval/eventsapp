"""Caso de uso: cerrar sesión (logout).

Revoca la credencial de sesión presentada añadiendo su ``jti`` a la lista de
revocación, de modo que deje de dar acceso (R008). Depende solo de las
abstracciones ``TokenService`` y ``RevokedTokenRepository``.
"""

from __future__ import annotations

from app.domain.repositories import RevokedTokenRepository
from app.domain.security import TokenService


class LogoutUserUseCase:
    """Invalida la credencial de sesión activa de un usuario (R008)."""

    def __init__(
        self,
        token_service: TokenService,
        revoked_tokens: RevokedTokenRepository,
    ) -> None:
        self._tokens = token_service
        self._revoked = revoked_tokens

    def execute(self, token: str) -> None:
        """Revoca el token dado.

        Lanza los errores de ``TokenService.verify`` si el token es inválido o
        expirado; la capa de presentación los traduce a 401.
        """
        claims = self._tokens.verify(token)
        self._revoked.revoke(claims.jti, claims.expires_at)
