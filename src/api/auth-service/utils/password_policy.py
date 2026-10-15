"""Política de fortaleza de contraseñas.

Implementa los criterios de seguridad definidos en
``docs/features/register_user.md`` (regla de negocio AC-003):

- Longitud mínima de 8 caracteres.
- Al menos una letra mayúscula.
- Al menos una letra minúscula.
- Al menos un número.
- Al menos un carácter especial.

Se expone como función pura para poder reutilizarse en otros flujos
(cambio de contraseña, restablecimiento) sin acoplarla al caso de uso.
"""

from __future__ import annotations

import re

MIN_LENGTH = 8
# Conjunto de caracteres especiales aceptados como "carácter especial".
SPECIAL_CHARACTERS = r"""!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~"""

_SPECIAL_RE = re.compile(f"[{re.escape(SPECIAL_CHARACTERS)}]")


def validate_password_strength(password: str) -> list[str]:
    """Valida una contraseña contra la política de seguridad.

    Devuelve la lista de reglas incumplidas (mensajes legibles). Una lista
    vacía significa que la contraseña es válida.
    """
    violations: list[str] = []

    if not isinstance(password, str) or len(password) < MIN_LENGTH:
        violations.append(
            f"La contraseña debe tener al menos {MIN_LENGTH} caracteres."
        )
    if not re.search(r"[A-Z]", password or ""):
        violations.append("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password or ""):
        violations.append("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", password or ""):
        violations.append("La contraseña debe contener al menos un número.")
    if not _SPECIAL_RE.search(password or ""):
        violations.append(
            "La contraseña debe contener al menos un carácter especial "
            "(por ejemplo: !, @, #, $, %, ^, &, *)."
        )

    return violations


def is_strong_password(password: str) -> bool:
    """Atajo booleano: ``True`` si la contraseña cumple la política."""
    return not validate_password_strength(password)
