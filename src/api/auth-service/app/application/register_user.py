"""Caso de uso: registrar un usuario.

Implementa ``specs/002-registro-usuario/spec.md``:

- Validación de forma en una sola pasada, con un detalle por problema: campos
  obligatorios (R002), formato del correo (R003), valores no textuales (R012),
  longitudes máximas (R015) y longitud y formato del teléfono opcional (R014,
  R016, R017).
- Política de contraseña (R004), solo si no hay errores de forma.
- Unicidad del correo normalizado (R005, R006), comprobada al final.
- Hash de la contraseña y persistencia (R001, R008). Devuelve la información
  de la confirmación de registro, sin datos sensibles (R009, R010).

Depende únicamente de abstracciones (``UserRepository``, ``PasswordHasher``),
respetando la inversión de dependencias de Clean Architecture.
"""

from __future__ import annotations

import re

from app.application.dtos import RegisterUserRequest, RegisterUserResult
from app.application.exceptions import (
    EmailAlreadyRegisteredError,
    ValidationError,
    WeakPasswordError,
)
from app.domain.repositories import UserRepository
from app.domain.security import PasswordHasher
from app.domain.user import User
from utils.password_policy import validate_password_strength

# Validación de email deliberadamente simple y pragmática.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Longitudes máximas (feature 002, R015). Se miden tras la normalización:
# nombre y correo sin espacios exteriores, contraseña tal cual.
NAME_MAX_LENGTH = 100
EMAIL_MAX_LENGTH = 254
PASSWORD_MAX_LENGTH = 128
# Teléfono opcional (feature 002, R016/R017): medido sin espacios exteriores.
PHONE_MAX_LENGTH = 20

# Dígitos 0-9 (no ``\d``, que acepta dígitos Unicode), espacios, guiones,
# paréntesis y un «+» opcional solo al principio. Exigir al menos un dígito se
# comprueba aparte con ``_DIGIT_RE`` por legibilidad.
_PHONE_RE = re.compile(r"\+?[0-9 ()\-]+")
_DIGIT_RE = re.compile(r"[0-9]")

# Un único mensaje de formato por campo: lo reciben tanto un texto mal formado
# como un valor que no es texto (feature 002, plan D2).
_FORMAT_ERRORS = {
    "name": "El nombre no tiene un formato válido.",
    "email": "El correo electrónico no tiene un formato válido.",
    "password": "La contraseña no tiene un formato válido.",
    "phone": "El teléfono no tiene un formato válido.",
}


def _as_text(value: object) -> str | None:
    """Devuelve ``value`` si es texto y ``None`` si es de cualquier otro tipo.

    Los DTOs están tipados como ``str``, pero llegan del JSON sin convertir: un
    número, un booleano o una lista no deben romper la normalización.
    """
    return value if isinstance(value, str) else None


class RegisterUserUseCase:
    """Registra un nuevo usuario aplicando las reglas de negocio."""

    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher) -> None:
        self._users = user_repository
        self._hasher = password_hasher

    def execute(self, request: RegisterUserRequest) -> RegisterUserResult:
        raw = {
            "name": request.name,
            "email": request.email,
            "password": request.password,
            "phone": request.phone,
        }
        # ``None`` es un campo ausente; cualquier otro valor no textual es un
        # error de formato de ese campo.
        not_text = {
            field for field, value in raw.items() if value is not None and _as_text(value) is None
        }

        name = (_as_text(request.name) or "").strip()
        email = (_as_text(request.email) or "").strip().lower()
        password = _as_text(request.password) or ""
        phone = (_as_text(request.phone) or "").strip() or None

        self._validate_basic_fields(name, email, password, phone, not_text)
        self._validate_password_policy(password)
        self._ensure_email_is_unique(email)

        user = User.new(
            name=name,
            email=email,
            password_hash=self._hasher.hash(password),
            phone=phone,
        )
        self._users.add(user)

        return RegisterUserResult(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
        )

    # -- reglas internas ---------------------------------------------------

    @staticmethod
    def _validate_basic_fields(
        name: str, email: str, password: str, phone: str | None, not_text: set[str]
    ) -> None:
        errors: list[str] = []
        if "name" in not_text:
            errors.append(_FORMAT_ERRORS["name"])
        elif not name:
            errors.append("El nombre es obligatorio.")
        elif len(name) > NAME_MAX_LENGTH:
            errors.append(f"El nombre no puede superar {NAME_MAX_LENGTH} caracteres.")
        if "email" in not_text:
            errors.append(_FORMAT_ERRORS["email"])
        elif not email:
            errors.append("El correo electrónico es obligatorio.")
        elif len(email) > EMAIL_MAX_LENGTH:
            errors.append(
                f"El correo electrónico no puede superar {EMAIL_MAX_LENGTH} caracteres."
            )
        elif not _EMAIL_RE.match(email):
            errors.append(_FORMAT_ERRORS["email"])
        if "password" in not_text:
            errors.append(_FORMAT_ERRORS["password"])
        elif not password:
            errors.append("La contraseña es obligatoria.")
        elif len(password) > PASSWORD_MAX_LENGTH:
            errors.append(f"La contraseña no puede superar {PASSWORD_MAX_LENGTH} caracteres.")
        if "phone" in not_text:
            errors.append(_FORMAT_ERRORS["phone"])
        elif phone is not None:
            # Longitud y formato son independientes: pueden salir los dos.
            if len(phone) > PHONE_MAX_LENGTH:
                errors.append(f"El teléfono no puede superar {PHONE_MAX_LENGTH} caracteres.")
            if not _PHONE_RE.fullmatch(phone) or not _DIGIT_RE.search(phone):
                errors.append(_FORMAT_ERRORS["phone"])
        if errors:
            raise ValidationError("Datos de registro inválidos.", errors)

    @staticmethod
    def _validate_password_policy(password: str) -> None:
        violations = validate_password_strength(password)
        if violations:
            raise WeakPasswordError(
                "La contraseña no cumple los criterios de seguridad.", violations
            )

    def _ensure_email_is_unique(self, email: str) -> None:
        if self._users.get_by_email(email) is not None:
            raise EmailAlreadyRegisteredError(
                "El correo electrónico ya está registrado."
            )
