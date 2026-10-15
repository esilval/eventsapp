"""Implementación de ``PasswordHasher`` con bcrypt (passlib).

bcrypt genera y embebe un salt aleatorio dentro del propio hash, de modo que no
se requiere almacenar el salt por separado (spec 002, R008).

Límite conocido: bcrypt solo usa los primeros 72 bytes de la contraseña y
descarta el resto sin error. El registro admite hasta 128 caracteres (R015), así
que lo que pase de 72 bytes no aporta seguridad. Registro y login truncan igual,
de modo que la verificación sigue siendo coherente. Es un riesgo aceptado en
D5 del plan de ``specs/002-registro-usuario``; eliminarlo exige migrar a
Argon2id o a un prehash con hashes versionados.
"""

from __future__ import annotations

from passlib.hash import bcrypt

from app.domain.security import PasswordHasher


class BcryptPasswordHasher(PasswordHasher):
    """Hasher basado en bcrypt."""

    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def hash(self, plain_password: str) -> str:
        return bcrypt.using(rounds=self._rounds).hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        try:
            return bcrypt.verify(plain_password, password_hash)
        except (ValueError, TypeError):
            return False
