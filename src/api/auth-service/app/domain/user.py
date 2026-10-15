"""Entidad de dominio ``User``.

Representa a un usuario del sistema de forma independiente de cualquier
framework o mecanismo de persistencia (Clean Architecture: la capa de dominio
no conoce SQLAlchemy, Flask ni bcrypt).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Timestamp actual en UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class User:
    """Usuario registrado en EventsApp.

    Atributos derivados del modelo USERS (docs/diagrams/erDiagram.mmd).

    ``password`` guarda el hash de la contraseña (bcrypt, con el salt embebido
    dentro del propio hash). ``salt`` se mantiene por compatibilidad con el
    modelo de datos pero queda vacío al usar bcrypt.
    """

    id: str
    name: str
    email: str
    password: str  # hash de la contraseña
    phone: str | None = None
    salt: str = ""
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    last_login: datetime | None = None

    @classmethod
    def new(
        cls,
        *,
        name: str,
        email: str,
        password_hash: str,
        phone: str | None = None,
    ) -> "User":
        """Crea un usuario nuevo con id y timestamps generados."""
        now = _utcnow()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=password_hash,
            phone=phone,
            salt="",
            created_at=now,
            updated_at=now,
            last_login=None,
        )
