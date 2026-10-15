"""Pruebas del repositorio de tokens revocados (R008)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.infrastructure.db import Base, create_db_engine, create_session_factory
from app.infrastructure.revoked_token_repository import (
    SqlAlchemyRevokedTokenRepository,
)


@pytest.fixture
def session():
    engine = create_db_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory()
    factory.remove()


def test_R008_token_revocado_es_detectado(session):
    """R008: un jti revocado se detecta; uno cualquiera no."""
    repo = SqlAlchemyRevokedTokenRepository(session)
    expires_at = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)

    assert repo.is_revoked("jti-1") is False

    repo.revoke("jti-1", expires_at)
    assert repo.is_revoked("jti-1") is True

    # Idempotencia: revocar de nuevo no falla.
    repo.revoke("jti-1", expires_at)
    assert repo.is_revoked("jti-1") is True

    # Otro jti sigue sin estar revocado.
    assert repo.is_revoked("jti-2") is False
