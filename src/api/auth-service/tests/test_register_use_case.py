"""Pruebas del caso de uso de registro (AC-001, AC-002, AC-003)."""

from __future__ import annotations

import pytest

from app.application.dtos import RegisterUserRequest
from app.application.exceptions import (
    EmailAlreadyRegisteredError,
    ValidationError,
    WeakPasswordError,
)
from app.application.register_user import RegisterUserUseCase
from tests.conftest import FakePasswordHasher


@pytest.fixture
def use_case(user_repository, password_hasher):
    return RegisterUserUseCase(user_repository, password_hasher)


def test_registers_user_with_basic_data(use_case, user_repository):
    result = use_case.execute(
        RegisterUserRequest(name="Ana", email="Ana@Example.com", password="Abcd123!")
    )

    assert result.id
    assert result.name == "Ana"
    # El email se normaliza a minúsculas.
    assert result.email == "ana@example.com"

    stored = user_repository.get_by_email("ana@example.com")
    assert stored is not None
    # La contraseña se almacena hasheada, nunca en claro.
    assert stored.password != "Abcd123!"
    assert stored.password == "hashed::Abcd123!"


def test_optional_phone_is_persisted(use_case, user_repository):
    use_case.execute(
        RegisterUserRequest(
            name="Ana", email="ana@example.com", password="Abcd123!", phone="123456"
        )
    )
    assert user_repository.get_by_email("ana@example.com").phone == "123456"


def test_duplicate_email_is_rejected(use_case):
    req = RegisterUserRequest(name="Ana", email="ana@example.com", password="Abcd123!")
    use_case.execute(req)

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(
            RegisterUserRequest(name="Otra", email="ana@example.com", password="Zxcv987!")
        )


def test_weak_password_is_rejected(use_case):
    with pytest.raises(WeakPasswordError) as exc_info:
        use_case.execute(
            RegisterUserRequest(name="Ana", email="ana@example.com", password="weak")
        )
    assert exc_info.value.details  # incluye las reglas incumplidas


@pytest.mark.parametrize(
    "name, email",
    [("", "ana@example.com"), ("Ana", ""), ("Ana", "no-es-un-email")],
)
def test_invalid_basic_fields_are_rejected(use_case, name, email):
    with pytest.raises(ValidationError):
        use_case.execute(
            RegisterUserRequest(name=name, email=email, password="Abcd123!")
        )


# -- Feature 002-registro-usuario: comportamiento existente (T001) ---------


def _account_count(user_repository) -> int:
    return len(user_repository._by_email)


def _req(**overrides) -> RegisterUserRequest:
    data = {"name": "Ana", "email": "ana@example.com", "password": "Abcd123!"}
    data.update(overrides)
    return RegisterUserRequest(**data)


def test_F002_R001_crea_una_cuenta_con_los_datos(use_case, user_repository):
    result = use_case.execute(_req())

    assert _account_count(user_repository) == 1
    stored = user_repository.get_by_email("ana@example.com")
    assert stored.id == result.id
    assert stored.name == "Ana"
    assert stored.email == "ana@example.com"


def test_F002_R001_recorta_espacios_exteriores_del_nombre(use_case, user_repository):
    use_case.execute(_req(name="  Ana López  "))

    assert user_repository.get_by_email("ana@example.com").name == "Ana López"


def test_F002_R002_nombre_solo_espacios_cuenta_como_ausente(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name="   "))

    assert "El nombre es obligatorio." in exc_info.value.details
    assert user_repository.get_by_email("ana@example.com") is None


def test_F002_R002_varios_campos_ausentes_en_un_solo_error(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name="", password=""))

    details = exc_info.value.details
    assert "El nombre es obligatorio." in details
    assert "La contraseña es obligatoria." in details
    assert _account_count(user_repository) == 0


@pytest.mark.parametrize("email", ["ana@ejemplo", "ana ejemplo.com"])
def test_F002_R003_rechaza_correo_con_formato_invalido(use_case, user_repository, email):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(email=email))

    assert "El correo electrónico no tiene un formato válido." in exc_info.value.details
    assert _account_count(user_repository) == 0


def test_F002_R004_contrasena_debil_enumera_todas_las_reglas(use_case, user_repository):
    with pytest.raises(WeakPasswordError) as exc_info:
        use_case.execute(_req(password="weak"))

    details = " ".join(exc_info.value.details)
    assert len(exc_info.value.details) == 4
    assert "8 caracteres" in details
    assert "mayúscula" in details
    assert "número" in details
    assert "carácter especial" in details
    assert _account_count(user_repository) == 0


def test_F002_R004_solo_falta_el_caracter_especial(use_case, user_repository):
    with pytest.raises(WeakPasswordError) as exc_info:
        use_case.execute(_req(password="Abcdefg1"))

    assert len(exc_info.value.details) == 1
    assert "carácter especial" in exc_info.value.details[0]
    assert _account_count(user_repository) == 0


def test_F002_R004_acepta_contrasena_minima_que_cumple_todo(use_case):
    assert use_case.execute(_req(password="Abcd123!")).id


def test_F002_R005_cuenta_existente_no_se_modifica(use_case, user_repository):
    use_case.execute(_req())
    original = user_repository.get_by_email("ana@example.com")
    original_hash = original.password

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(_req(name="Otra", password="Zxcv987!"))

    stored = user_repository.get_by_email("ana@example.com")
    assert stored.name == "Ana"
    assert stored.password == original_hash


def test_F002_R006_guarda_el_correo_normalizado(use_case, user_repository):
    result = use_case.execute(_req(email="  Ana@Example.COM "))

    assert result.email == "ana@example.com"
    assert user_repository.get_by_email("ana@example.com") is not None


def test_F002_R006_mayusculas_y_espacios_chocan_con_cuenta_existente(use_case):
    use_case.execute(_req())

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(_req(email="  ANA@Example.com "))


def test_F002_R014_guarda_el_telefono_aportado(use_case, user_repository):
    result = use_case.execute(_req(phone="600123456"))

    assert result.phone == "600123456"
    assert user_repository.get_by_email("ana@example.com").phone == "600123456"


def test_F002_R014_sin_telefono_la_cuenta_se_crea_igual(use_case, user_repository):
    result = use_case.execute(_req())

    assert result.phone is None
    assert user_repository.get_by_email("ana@example.com").phone is None


@pytest.mark.parametrize("phone", ["", "   "])
def test_F002_R014_telefono_vacio_cuenta_como_no_aportado(use_case, user_repository, phone):
    result = use_case.execute(_req(phone=phone))

    assert result.phone is None
    assert user_repository.get_by_email("ana@example.com").phone is None


# -- Feature 002-registro-usuario: valores no textuales (T006) -------------


def test_F002_R002_campo_nombre_ausente_es_obligatorio(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name=None))

    assert exc_info.value.details == ["El nombre es obligatorio."]
    assert _account_count(user_repository) == 0


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("name", 123, "El nombre no tiene un formato válido."),
        ("email", ["ana@example.com"], "El correo electrónico no tiene un formato válido."),
        ("password", 12345678, "La contraseña no tiene un formato válido."),
        ("name", True, "El nombre no tiene un formato válido."),
    ],
)
def test_F002_R012_valor_no_textual_es_error_de_formato(
    use_case, user_repository, field, value, message
):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(**{field: value}))

    assert exc_info.value.details == [message]
    assert _account_count(user_repository) == 0


def test_F002_R014_telefono_no_textual_es_error_de_formato(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(phone=600123456))

    assert exc_info.value.details == ["El teléfono no tiene un formato válido."]
    assert _account_count(user_repository) == 0


def test_F002_R003_correo_no_textual_y_mal_formado_dan_el_mismo_mensaje(use_case):
    messages = []
    for email in (42, "ana@ejemplo"):
        with pytest.raises(ValidationError) as exc_info:
            use_case.execute(_req(email=email))
        messages.append(exc_info.value.details)

    assert messages[0] == messages[1] == ["El correo electrónico no tiene un formato válido."]


def test_F002_R012_varios_valores_no_textuales_en_un_solo_error(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name=1, password=2, phone=3))

    assert exc_info.value.details == [
        "El nombre no tiene un formato válido.",
        "La contraseña no tiene un formato válido.",
        "El teléfono no tiene un formato válido.",
    ]


# -- Feature 002-registro-usuario: longitudes máximas (T007) ---------------

_EMAIL_DOMAIN = "@example.com"


def _email_of_length(length: int) -> str:
    return "a" * (length - len(_EMAIL_DOMAIN)) + _EMAIL_DOMAIN


def _password_of_length(length: int) -> str:
    return "Abcd123!" + "a" * (length - 8)


def test_F002_R015_acepta_los_limites_exactos(use_case, user_repository):
    email = _email_of_length(254)

    result = use_case.execute(
        _req(name="N" * 100, email=email, password=_password_of_length(128))
    )

    assert len(result.name) == 100
    assert len(result.email) == 254
    assert _account_count(user_repository) == 1


def test_F002_R015_rechaza_nombre_de_101(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name="N" * 101))

    assert exc_info.value.details == ["El nombre no puede superar 100 caracteres."]
    assert _account_count(user_repository) == 0


def test_F002_R015_correo_y_contrasena_largos_en_un_solo_error(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(email=_email_of_length(255), password=_password_of_length(129)))

    assert exc_info.value.details == [
        "El correo electrónico no puede superar 254 caracteres.",
        "La contraseña no puede superar 128 caracteres.",
    ]
    assert _account_count(user_repository) == 0


def test_F002_R015_nombre_se_mide_sin_espacios_exteriores(use_case, user_repository):
    result = use_case.execute(_req(name="  " + "N" * 100 + "   "))

    assert result.name == "N" * 100
    assert _account_count(user_repository) == 1


def test_F002_R015_contrasena_larga_se_rechaza_antes_de_hashear(user_repository):
    class SpyHasher(FakePasswordHasher):
        def __init__(self) -> None:
            self.calls = 0

        def hash(self, plain_password: str) -> str:
            self.calls += 1
            return super().hash(plain_password)

    hasher = SpyHasher()
    use_case = RegisterUserUseCase(user_repository, hasher)

    with pytest.raises(ValidationError):
        use_case.execute(_req(password=_password_of_length(10_000)))

    assert hasher.calls == 0


def test_F002_R015_correo_largo_y_mal_formado_solo_reporta_la_longitud(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(email="a" * 255))

    assert exc_info.value.details == ["El correo electrónico no puede superar 254 caracteres."]


# -- Feature 002-registro-usuario: teléfono (T008) -------------------------

_PHONE_20 = "+34 (600) 123-45-678"
_PHONE_LENGTH_ERROR = "El teléfono no puede superar 20 caracteres."
_PHONE_FORMAT_ERROR = "El teléfono no tiene un formato válido."


def test_F002_R016_acepta_telefono_de_20(use_case, user_repository):
    assert len(_PHONE_20) == 20

    result = use_case.execute(_req(phone=_PHONE_20))

    assert result.phone == _PHONE_20
    assert user_repository.get_by_email("ana@example.com").phone == _PHONE_20


def test_F002_R016_telefono_de_20_con_espacios_exteriores_se_acepta(use_case):
    result = use_case.execute(_req(phone="   " + _PHONE_20 + "  "))

    assert result.phone == _PHONE_20


def test_F002_R016_rechaza_telefono_de_21(use_case, user_repository):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(phone="6" * 21))

    assert exc_info.value.details == [_PHONE_LENGTH_ERROR]
    assert _account_count(user_repository) == 0


def test_F002_R016_telefono_y_nombre_largos_en_un_solo_error(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(name="N" * 101, phone="6" * 21))

    assert exc_info.value.details == [
        "El nombre no puede superar 100 caracteres.",
        _PHONE_LENGTH_ERROR,
    ]


def test_F002_R016_telefono_largo_con_contrasena_debil_solo_menciona_el_telefono(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(password="weak", phone="6" * 21))

    assert exc_info.value.details == [_PHONE_LENGTH_ERROR]


@pytest.mark.parametrize("phone", ["600123456", "+34 600 123 456", "(91) 555-12-34"])
def test_F002_R017_acepta_telefonos_con_caracteres_telefonicos(use_case, phone):
    assert use_case.execute(_req(phone=phone)).phone == phone


@pytest.mark.parametrize(
    "phone", ["abc", "600-ABC-123", "600+123", "++34600", "( - )", "٦٠٠١٢٣٤٥٦"]
)
def test_F002_R017_rechaza_telefonos_con_formato_invalido(use_case, user_repository, phone):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(phone=phone))

    assert exc_info.value.details == [_PHONE_FORMAT_ERROR]
    assert _account_count(user_repository) == 0


def test_F002_R017_telefono_y_correo_invalidos_en_un_solo_error(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(email="ana@ejemplo", phone="abc"))

    assert exc_info.value.details == [
        "El correo electrónico no tiene un formato válido.",
        _PHONE_FORMAT_ERROR,
    ]


def test_F002_R017_telefono_largo_y_con_letras_recibe_ambos_mensajes(use_case):
    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(_req(phone="a" * 25))

    assert exc_info.value.details == [_PHONE_LENGTH_ERROR, _PHONE_FORMAT_ERROR]
