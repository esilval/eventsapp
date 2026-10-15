"""Helpers para construir respuestas JSON uniformes.

Centraliza el formato de las respuestas de la API para que todos los endpoints
(actuales y futuros) devuelvan una estructura consistente.
"""

from __future__ import annotations

from typing import Any


def success(message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Respuesta de éxito estándar."""
    body: dict[str, Any] = {"message": message}
    if data is not None:
        body.update(data)
    return body


def error(message: str, details: list[str] | None = None) -> dict[str, Any]:
    """Respuesta de error estándar.

    ``details`` permite adjuntar una lista de mensajes específicos (por ejemplo,
    las reglas de contraseña incumplidas).
    """
    body: dict[str, Any] = {"error": message}
    if details:
        body["details"] = details
    return body
