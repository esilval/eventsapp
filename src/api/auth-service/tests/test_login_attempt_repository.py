"""Pruebas del repositorio de intentos de login (R005)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.infrastructure.db import Base, create_db_engine, create_session_factory
from app.infrastructure.login_attempt_repository import (
    SqlAlchemyLoginAttemptRepository,
)


@pytest.fixture
def session():
    engine = create_db_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory()
    factory.remove()


def test_R005_count_recent_respeta_ventana_y_origen(session):
    """R005: el conteo separa por (email, origin) y respeta la ventana."""
    repo = SqlAlchemyLoginAttemptRepository(session)
    t0 = datetime(2026, 8, 12, 10, 0, tzinfo=timezone.utc)
    window_start = t0 - timedelta(minutes=5)

    repo.record_failure("ada@example.com", "ip-1", t0)
    repo.record_failure("ada@example.com", "ip-1", t0 + timedelta(seconds=30))
    repo.record_failure("ada@example.com", "ip-2", t0)

    # Mismo email, distinto origen: se cuentan por separado.
    assert repo.count_recent("ada@example.com", "ip-1", window_start) == 2
    assert repo.count_recent("ada@example.com", "ip-2", window_start) == 1

    # Fuera de la ventana (since en el futuro): no cuenta.
    future = t0 + timedelta(minutes=10)
    assert repo.count_recent("ada@example.com", "ip-1", future) == 0

    # clear elimina solo la combinación indicada.
    repo.clear("ada@example.com", "ip-1")
    assert repo.count_recent("ada@example.com", "ip-1", window_start) == 0
    assert repo.count_recent("ada@example.com", "ip-2", window_start) == 1
