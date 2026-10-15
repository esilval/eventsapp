"""Pruebas de la política de contraseñas (AC-003)."""

from __future__ import annotations

import pytest

from utils.password_policy import is_strong_password, validate_password_strength


def test_valid_password_has_no_violations():
    assert validate_password_strength("Abcd123!") == []
    assert is_strong_password("Abcd123!") is True


@pytest.mark.parametrize(
    "password, expected_fragment",
    [
        ("Ab1!", "al menos 8 caracteres"),
        ("abcd123!", "mayúscula"),
        ("ABCD123!", "minúscula"),
        ("Abcdefg!", "número"),
        ("Abcd1234", "carácter especial"),
    ],
)
def test_each_rule_is_enforced(password, expected_fragment):
    violations = validate_password_strength(password)
    assert any(expected_fragment in v for v in violations), violations
    assert is_strong_password(password) is False


def test_empty_password_reports_multiple_violations():
    violations = validate_password_strength("")
    # Falla longitud, mayúscula, minúscula, número y especial.
    assert len(violations) == 5
