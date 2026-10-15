"""Pruebas del hasher bcrypt real (feature 002-registro-usuario, R008).

Usan pocas rondas para que sean rápidas: el coste no cambia el formato ni la
generación de un salt aleatorio por hash.
"""

from __future__ import annotations

import pytest
from passlib.hash import bcrypt

from app.infrastructure.password_hasher import BcryptPasswordHasher

PASSWORD = "Abcd123!"


@pytest.fixture
def hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher(rounds=4)


def test_F002_R008_misma_contrasena_produce_hashes_distintos(hasher):
    first = hasher.hash(PASSWORD)
    second = hasher.hash(PASSWORD)

    assert first != second


def test_F002_R008_ningun_hash_contiene_la_contrasena_en_claro(hasher):
    hashes = [hasher.hash(PASSWORD), hasher.hash(PASSWORD)]

    for password_hash in hashes:
        assert PASSWORD not in password_hash
        # Es un hash bcrypt (unidireccional), no un cifrado recuperable.
        assert bcrypt.identify(password_hash)


def test_F002_R008_verify_acepta_la_correcta_y_rechaza_otra(hasher):
    password_hash = hasher.hash(PASSWORD)

    assert hasher.verify(PASSWORD, password_hash) is True
    assert hasher.verify("Zxcv987!", password_hash) is False
