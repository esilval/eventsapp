"""Configuración de SQLAlchemy: engine, sesión y base declarativa.

Se mantiene agnóstico del motor concreto: la URL llega por configuración, de
modo que producción usa PostgreSQL y las pruebas usan SQLite in-memory.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM del servicio."""


def create_db_engine(database_url: str) -> Engine:
    """Crea el engine de SQLAlchemy a partir de la URL de conexión.

    Para SQLite in-memory se habilita ``check_same_thread=False`` y un pool
    estático para que la misma base persista entre hilos/conexiones durante los
    tests.
    """
    connect_args: dict = {}
    engine_kwargs: dict = {"future": True}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        if ":memory:" in database_url or database_url == "sqlite://":
            from sqlalchemy.pool import StaticPool

            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


def create_session_factory(engine: Engine) -> scoped_session:
    """Crea una fábrica de sesiones ligada al engine dado."""
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    return scoped_session(factory)
