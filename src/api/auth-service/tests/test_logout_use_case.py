"""Pruebas unitarias del caso de uso de logout (R008)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.logout_user import LogoutUserUseCase
from app.domain.security import TokenClaims, TokenService


class StubTokenService(TokenService):
    def issue(self, user_id: str):  # no usado
        raise NotImplementedError

    def verify(self, token: str) -> TokenClaims:
        return TokenClaims(
            user_id="user-1",
            jti="jti-123",
            expires_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
        )


class InMemoryRevokedTokenRepository:
    def __init__(self) -> None:
        self._revoked: dict[str, datetime] = {}

    def revoke(self, jti, expires_at) -> None:
        self._revoked[jti] = expires_at

    def is_revoked(self, jti) -> bool:
        return jti in self._revoked


def test_R008_logout_revoca_jti():
    """R008: el logout revoca el jti del token presentado."""
    revoked = InMemoryRevokedTokenRepository()
    use_case = LogoutUserUseCase(StubTokenService(), revoked)

    assert revoked.is_revoked("jti-123") is False

    use_case.execute("cualquier-token")

    assert revoked.is_revoked("jti-123") is True
