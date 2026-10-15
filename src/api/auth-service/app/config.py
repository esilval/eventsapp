"""Configuración del servicio, tomada de variables de entorno.

Permite intercambiar el motor de base de datos sin tocar el código: PostgreSQL
en producción, SQLite in-memory en pruebas.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuración base."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///auth_service.db")
    # Crear las tablas al arrancar (útil en dev; en prod se usan migraciones).
    auto_create_tables: bool = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"
    testing: bool = False

    # --- Login: credencial de sesión (JWT) ---
    # Secreto de firma HS256; en producción SIEMPRE por entorno (activo crítico).
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    # Expiración de la credencial de sesión: 24 h (R009).
    jwt_expiry_seconds: int = int(os.getenv("JWT_EXPIRY_SECONDS", "86400"))

    # --- Login: protección de fuerza bruta (R005) ---
    # Fallos consecutivos que disparan el bloqueo.
    login_max_attempts: int = int(os.getenv("LOGIN_MAX_ATTEMPTS", "3"))
    # Ventana deslizante en la que se cuentan los fallos.
    login_window_seconds: int = int(os.getenv("LOGIN_WINDOW_SECONDS", "300"))
    # Duración del bloqueo tras alcanzar el umbral.
    login_lockout_seconds: int = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "300"))


@dataclass
class TestConfig(Config):
    """Configuración para la suite de pruebas: SQLite in-memory."""

    database_url: str = "sqlite://"
    auto_create_tables: bool = True
    testing: bool = True
    # Secreto fijo de prueba: los tests no dependen del entorno.
    jwt_secret: str = "test-jwt-secret"
