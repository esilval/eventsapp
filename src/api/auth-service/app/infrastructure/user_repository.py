"""Implementación de ``UserRepository`` sobre SQLAlchemy.

Traduce entre la entidad de dominio ``User`` y el modelo ORM ``UserModel``,
manteniendo el dominio libre de dependencias de persistencia.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.exceptions import EmailAlreadyRegisteredError
from app.domain.repositories import UserRepository
from app.domain.user import User
from app.infrastructure.models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """Repositorio de usuarios respaldado por una sesión de SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        model = self._session.scalars(stmt).first()
        return self._to_entity(model) if model is not None else None

    def get_by_id(self, user_id: str) -> User | None:
        model = self._session.get(UserModel, user_id)
        return self._to_entity(model) if model is not None else None

    def add(self, user: User) -> None:
        self._session.add(self._to_model(user))
        try:
            self._session.commit()
        except IntegrityError as exc:
            # Segunda línea de defensa ante condiciones de carrera en la
            # unicidad de email (además de la comprobación del caso de uso).
            self._session.rollback()
            raise EmailAlreadyRegisteredError(
                "El correo electrónico ya está registrado."
            ) from exc

    def update_last_login(self, user_id: str, when: datetime) -> None:
        """Registra la marca de último inicio de sesión del usuario (R006)."""
        self._session.execute(
            update(UserModel).where(UserModel.id == user_id).values(last_login=when)
        )
        self._session.commit()

    # -- mapeo entidad <-> modelo -----------------------------------------

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            name=user.name,
            phone=user.phone,
            email=user.email,
            password=user.password,
            salt=user.salt,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            password=model.password,
            phone=model.phone,
            salt=model.salt,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=model.last_login,
        )
