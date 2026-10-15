"""Implementación de ``LoginAttemptRepository`` sobre SQLAlchemy (R005).

Registra intentos de login fallidos y los cuenta por ``(email, origin)`` dentro
de una ventana temporal, para el bloqueo por fuerza bruta.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.repositories import LoginAttemptRepository
from app.infrastructure.models import LoginAttemptModel


class SqlAlchemyLoginAttemptRepository(LoginAttemptRepository):
    """Repositorio de intentos fallidos respaldado por SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def count_recent(self, email: str, origin: str, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(LoginAttemptModel)
            .where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.origin == origin,
                LoginAttemptModel.created_at >= since,
            )
        )
        return int(self._session.scalar(stmt) or 0)

    def record_failure(self, email: str, origin: str, when: datetime) -> None:
        self._session.add(
            LoginAttemptModel(email=email, origin=origin, created_at=when)
        )
        self._session.commit()

    def clear(self, email: str, origin: str) -> None:
        self._session.execute(
            delete(LoginAttemptModel).where(
                LoginAttemptModel.email == email,
                LoginAttemptModel.origin == origin,
            )
        )
        self._session.commit()
