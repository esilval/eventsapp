"""Pruebas del repositorio SQLAlchemy de usuarios (F001-R006, F002-R007)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.application.exceptions import EmailAlreadyRegisteredError
from app.domain.user import User
from app.infrastructure.db import Base, create_db_engine, create_session_factory
from app.infrastructure.models import UserModel
from app.infrastructure.user_repository import SqlAlchemyUserRepository


@pytest.fixture
def session():
    engine = create_db_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    yield factory()
    factory.remove()


def test_R006_update_last_login_persiste_timestamp(session):
    """R006: update_last_login guarda la marca de último acceso."""
    repo = SqlAlchemyUserRepository(session)
    user = User.new(name="Ada", email="ada@example.com", password_hash="h")
    repo.add(user)
    assert repo.get_by_email("ada@example.com").last_login is None

    when = datetime(2026, 8, 12, 10, 30, tzinfo=timezone.utc)
    repo.update_last_login(user.id, when)

    persisted = repo.get_by_email("ada@example.com")
    # SQLite (solo en pruebas) descarta el tzinfo; PostgreSQL lo conserva. Se
    # normaliza a UTC para verificar que la marca temporal se persiste (R006).
    got = persisted.last_login
    if got.tzinfo is None:
        got = got.replace(tzinfo=timezone.utc)
    assert got == when


def test_F002_R007_segundo_alta_con_el_mismo_correo_choca_con_la_restriccion(session):
    """F002-R007: la restricción única de la BD impide dos cuentas con un correo.

    Simula la carrera: el segundo ``add`` llega sin que nadie haya comprobado
    antes la unicidad, como haría una petición concurrente.
    """
    repo = SqlAlchemyUserRepository(session)
    repo.add(User.new(name="Ana", email="ana@example.com", password_hash="h1"))

    with pytest.raises(EmailAlreadyRegisteredError):
        repo.add(User.new(name="Otra", email="ana@example.com", password_hash="h2"))

    count = session.scalar(
        select(func.count()).select_from(UserModel).where(UserModel.email == "ana@example.com")
    )
    assert count == 1
    assert repo.get_by_email("ana@example.com").name == "Ana"
