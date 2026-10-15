"""Blueprint de autenticación.

Expone el registro (``POST /register``) y el inicio de sesión
(``POST /login``, ``POST /logout``, ``GET /me``). Es una capa fina: parsea la
petición, delega en el caso de uso y traduce los errores de negocio a códigos
HTTP.
"""

from __future__ import annotations

from flask import Blueprint, current_app, g, request
from flask_restful import Api, Resource

from app.application.authenticate_user import AuthenticateUserUseCase
from app.application.dtos import LoginRequest, RegisterUserRequest
from app.application.exceptions import (
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    ValidationError,
    WeakPasswordError,
)
from app.application.logout_user import LogoutUserUseCase
from app.application.register_user import RegisterUserUseCase
from app.blueprints.decorators import _extract_bearer_token, require_auth
from app.infrastructure.login_attempt_repository import (
    SqlAlchemyLoginAttemptRepository,
)
from app.infrastructure.revoked_token_repository import (
    SqlAlchemyRevokedTokenRepository,
)
from app.infrastructure.user_repository import SqlAlchemyUserRepository
from utils.responses import error, success

auth_bp = Blueprint("auth", __name__)
api = Api(auth_bp)


class RegisterResource(Resource):
    """Recurso de registro de usuario (spec 002-registro-usuario).

    Rechaza el cuerpo que no es un objeto JSON (R012) y traduce los errores del
    caso de uso: 400 para validación y política de contraseña, 409 para correo
    ya registrado (R005, R007) y 201 con la confirmación (R010).
    """

    def post(self):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error("El cuerpo de la petición debe ser un JSON válido."), 400

        req = RegisterUserRequest(
            name=payload.get("name", ""),
            email=payload.get("email", ""),
            password=payload.get("password", ""),
            phone=payload.get("phone"),
        )

        use_case = _build_register_use_case()
        try:
            result = use_case.execute(req)
        except (ValidationError, WeakPasswordError) as exc:
            return error(exc.message, exc.details), 400
        except EmailAlreadyRegisteredError as exc:
            return error(exc.message, exc.details), 409

        return (
            success(
                "Usuario registrado exitosamente.",
                {
                    "user": {
                        "id": result.id,
                        "name": result.name,
                        "email": result.email,
                        "phone": result.phone,
                    }
                },
            ),
            201,
        )


class LoginResource(Resource):
    """Recurso de inicio de sesión (R001, R002, R003, R005, R006)."""

    def post(self):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error("El cuerpo de la petición debe ser un JSON válido."), 400

        req = LoginRequest(
            email=payload.get("email", ""),
            password=payload.get("password", ""),
            origin=_client_origin(),
        )

        use_case = _build_authenticate_use_case()
        try:
            result = use_case.execute(req)
        except ValidationError as exc:  # R003
            return error(exc.message, exc.details), 400
        except (InvalidCredentialsError, AccountLockedError) as exc:  # R002, R005
            return error(exc.message), 401

        return (
            success(
                "Inicio de sesión exitoso.",
                {
                    "token": result.token,
                    "user": {
                        "id": result.user.id,
                        "name": result.user.name,
                        "email": result.user.email,
                    },
                },
            ),
            200,
        )


class LogoutResource(Resource):
    """Recurso de cierre de sesión (R008). Requiere credencial válida."""

    method_decorators = [require_auth]

    def post(self):
        token = _extract_bearer_token(request.headers.get("Authorization", ""))
        _build_logout_use_case().execute(token)
        return success("Sesión cerrada."), 200


class MeResource(Resource):
    """Recurso protegido de referencia (R007). Requiere credencial válida."""

    method_decorators = [require_auth]

    def get(self):
        session = current_app.extensions["auth_session_factory"]()
        user = SqlAlchemyUserRepository(session).get_by_id(g.auth_claims.user_id)
        if user is None:
            return error("No autenticado."), 401
        return (
            success(
                "Usuario autenticado.",
                {"user": {"id": user.id, "name": user.name, "email": user.email}},
            ),
            200,
        )


# -- ensamblado de casos de uso -------------------------------------------


def _client_origin() -> str:
    """Origen de la petición para el bloqueo por fuerza bruta (R005).

    Por defecto la IP directa (``remote_addr``). ``X-Forwarded-For`` solo debe
    usarse tras un proxy de confianza; se deja como riesgo documentado.
    """
    return request.remote_addr or ""


def _build_register_use_case() -> RegisterUserUseCase:
    session = current_app.extensions["auth_session_factory"]()
    hasher = current_app.extensions["auth_password_hasher"]
    return RegisterUserUseCase(SqlAlchemyUserRepository(session), hasher)


def _build_authenticate_use_case() -> AuthenticateUserUseCase:
    ext = current_app.extensions
    session = ext["auth_session_factory"]()
    config = ext["auth_config"]
    return AuthenticateUserUseCase(
        SqlAlchemyUserRepository(session),
        ext["auth_password_hasher"],
        ext["auth_token_service"],
        SqlAlchemyLoginAttemptRepository(session),
        max_attempts=config.login_max_attempts,
        window_seconds=config.login_window_seconds,
        decoy_password_hash=ext["auth_decoy_password_hash"],
    )


def _build_logout_use_case() -> LogoutUserUseCase:
    ext = current_app.extensions
    session = ext["auth_session_factory"]()
    return LogoutUserUseCase(
        ext["auth_token_service"], SqlAlchemyRevokedTokenRepository(session)
    )


api.add_resource(RegisterResource, "/register")
api.add_resource(LoginResource, "/login")
api.add_resource(LogoutResource, "/logout")
api.add_resource(MeResource, "/me")
