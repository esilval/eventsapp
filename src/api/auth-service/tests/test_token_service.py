"""Pruebas del adaptador JWT ``JwtTokenService`` (R001, R009)."""

from __future__ import annotations

import pytest

from app.domain.security import ExpiredTokenError, InvalidTokenError
from app.infrastructure.token_service import JwtTokenService


def test_R001_issue_produce_token_verificable():
    """R001: un token emitido se verifica y expone el usuario y su jti."""
    service = JwtTokenService(secret="test-jwt-secret", expiry_seconds=86400)

    issued = service.issue("user-123")
    claims = service.verify(issued.token)

    assert claims.user_id == "user-123"
    assert claims.jti == issued.jti
    assert claims.expires_at == issued.expires_at


def test_R009_verify_rechaza_token_expirado():
    """R009: un token ya expirado es rechazado como expirado."""
    service = JwtTokenService(secret="test-jwt-secret", expiry_seconds=-10)

    issued = service.issue("user-123")

    with pytest.raises(ExpiredTokenError):
        service.verify(issued.token)


def test_R010_verify_rechaza_firma_invalida():
    """R010: un token firmado con otro secreto se rechaza como inválido."""
    issuer = JwtTokenService(secret="secret-a", expiry_seconds=86400)
    verifier = JwtTokenService(secret="secret-b", expiry_seconds=86400)

    issued = issuer.issue("user-123")

    with pytest.raises(InvalidTokenError):
        verifier.verify(issued.token)
