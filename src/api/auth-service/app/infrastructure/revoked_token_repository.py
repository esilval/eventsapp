"""Implementación de ``RevokedTokenRepository`` sobre SQLAlchemy (R008).

Mantiene la lista de revocación de credenciales de sesión: el cierre de sesión
inserta el ``jti`` del token y las peticiones protegidas consultan si está
revocado.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.repositories import RevokedTokenRepository
from app.infrastructure.models import RevokedTokenModel


class SqlAlchemyRevokedTokenRepository(RevokedTokenRepository):
    """Lista de revocación respaldada por SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def revoke(self, jti: str, expires_at: datetime) -> None:
        # Idempotente: revocar dos veces el mismo jti no debe fallar.
        if self._session.get(RevokedTokenModel, jti) is not None:
            return
        self._session.add(RevokedTokenModel(jti=jti, expires_at=expires_at))
        self._session.commit()

    def is_revoked(self, jti: str) -> bool:
        return self._session.get(RevokedTokenModel, jti) is not None
