"""Modelos ORM (SQLAlchemy) del servicio de autenticación.

Mapea la tabla ``users`` definida en ``docs/diagrams/erDiagram.mmd``. El email
lleva restricción de unicidad + índice para garantizar la regla AC-002 también
a nivel de base de datos.

Añade además las tablas de soporte al inicio de sesión
(feature 001-inicio-sesion-usuario): ``login_attempts`` (fuerza bruta, R005) y
``revoked_tokens`` (cierre de sesión, R008).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db import Base


class UserModel(Base):
    """Representación persistente de un usuario."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Guarda el hash bcrypt (con el salt embebido).
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Presente por compatibilidad con el modelo ER; sin uso con bcrypt.
    salt: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LoginAttemptModel(Base):
    """Intento de inicio de sesión fallido (R005).

    Se registra una fila por fallo; el conteo por ``(email, origin)`` dentro de
    la ventana temporal determina el bloqueo. Se borran las filas de una
    combinación al autenticarse con éxito.
    """

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class RevokedTokenModel(Base):
    """Credencial de sesión revocada por cierre de sesión (R008).

    ``jti`` es el identificador único del token; ``expires_at`` permite purgar
    las entradas cuyo token ya habría expirado igualmente.
    """

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
