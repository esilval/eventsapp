"""Fixtures compartidas de la suite de pruebas."""

from __future__ import annotations

import pytest

from app import create_app
from app.config import TestConfig
from app.domain.repositories import UserRepository
from app.domain.security import PasswordHasher
from app.domain.user import User


@pytest.fixture
def app():
    """App Flask configurada con SQLite in-memory."""
    return create_app(TestConfig())


@pytest.fixture
def client(app):
    """Cliente de pruebas HTTP."""
    return app.test_client()


class InMemoryUserRepository(UserRepository):
    """Repositorio en memoria para pruebas del caso de uso."""

    def __init__(self) -> None:
        self._by_email: dict[str, User] = {}

    def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    def get_by_id(self, user_id: str) -> User | None:
        for user in self._by_email.values():
            if user.id == user_id:
                return user
        return None

    def add(self, user: User) -> None:
        self._by_email[user.email] = user

    def update_last_login(self, user_id: str, when) -> None:  # noqa: ANN001
        for user in self._by_email.values():
            if user.id == user_id:
                user.last_login = when
                return


class FakePasswordHasher(PasswordHasher):
    """Hasher trivial y determinista (rápido) para pruebas."""

    def hash(self, plain_password: str) -> str:
        return f"hashed::{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{plain_password}"


@pytest.fixture
def user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()
