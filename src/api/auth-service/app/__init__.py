"""Application factory del servicio de autenticación.

Ensambla Flask + las dependencias de infraestructura (engine, sesión, hasher) y
registra el blueprint de autenticación bajo el prefijo ``/v1/auth``.
"""

from __future__ import annotations

import secrets

from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.blueprints.auth import auth_bp
from app.config import Config
from app.infrastructure import models  # noqa: F401  (registra los modelos en Base)
from app.infrastructure.db import Base, create_db_engine, create_session_factory
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.infrastructure.token_service import JwtTokenService


def create_app(config: Config | None = None) -> Flask:
    """Crea y configura la aplicación Flask."""
    config = config or Config()

    app = Flask(__name__)
    app.config["TESTING"] = config.testing

    engine = create_db_engine(config.database_url)
    session_factory = create_session_factory(engine)

    if config.auto_create_tables:
        Base.metadata.create_all(engine)

    password_hasher = BcryptPasswordHasher()

    # Dependencias disponibles para los recursos vía current_app.extensions.
    app.extensions["auth_session_factory"] = session_factory
    app.extensions["auth_password_hasher"] = password_hasher
    # Credencial de sesión (R001/R009).
    app.extensions["auth_token_service"] = JwtTokenService(
        secret=config.jwt_secret, expiry_seconds=config.jwt_expiry_seconds
    )
    # Config del login (bloqueo por fuerza bruta, R005).
    app.extensions["auth_config"] = config
    # Hash señuelo estable durante la vida del proceso para igualar el coste
    # temporal cuando el email no existe (R002/R004).
    app.extensions["auth_decoy_password_hash"] = password_hasher.hash(
        secrets.token_urlsafe(24)
    )

    @app.teardown_appcontext
    def _remove_session(exception=None):  # noqa: ANN001
        session_factory.remove()

    @app.get("/health")
    def health():
        """Liveness: el proceso está vivo. Barato y sin dependencias.

        La orquestación (Kubernetes/Cloud Run) lo usa para decidir si el
        contenedor debe reiniciarse. No consulta la base de datos a propósito:
        una BD caída no debe provocar reinicios del proceso.
        """
        return {"status": "ok"}, 200

    @app.get("/health/ready")
    def health_ready():
        """Readiness: el servicio puede atender tráfico (dependencias sanas).

        Comprueba la conexión a la base de datos con un ``SELECT 1``. Si falla,
        devuelve ``503`` para que el balanceador retire la instancia del pool
        hasta que se recupere, sin reiniciar el contenedor.
        """
        checks: dict[str, str] = {}
        session = session_factory()
        try:
            session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except SQLAlchemyError:
            checks["database"] = "error"

        healthy = all(status == "ok" for status in checks.values())
        return (
            {"status": "ok" if healthy else "unavailable", "checks": checks},
            200 if healthy else 503,
        )

    app.register_blueprint(auth_bp, url_prefix="/v1/auth")

    return app
