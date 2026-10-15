# Tasks: Registro de usuario

| Campo  | Valor       |
| ------ | ----------- |
| Spec   | `spec.md`   |
| Plan   | `plan.md`   |
| Fecha  | 2026-10-14  |
| Estado | Approved · 99106a5f0e5d       |

> Cada tarea debe ser verificable por sí sola y caber en una sola sesión de
> trabajo. Si una tarea necesita una decisión que no está en `plan.md`, la tarea
> está mal descompuesta.
>
> Solo el usuario cambia el Estado, con `/sdd:approve`. Las pruebas citan el
> requisito con el prefijo de la feature: `test_F002_R015_rechaza_nombre_largo`.

## Leyenda

- `[ ]` pendiente · `[~]` en curso · `[x]` hecha
- `P` marca tareas paralelizables (sin dependencias entre sí)

Todas las rutas son relativas a `src/api/auth-service/`. Las tareas T001–T005 y
T011 fijan con pruebas el comportamiento que **ya existe** y deben pasar sin tocar
código de producción; T006–T008 cambian `app/application/register_user.py` y van
en serie porque editan la misma función.

## Tareas

### T001 `P` — Pruebas del caso de uso para el comportamiento existente

- **Estado:** `[x]`
- **Requisitos:** R001, R002, R003, R004, R005, R006, R014
- **Depende de:** —
- **Archivos:** `tests/test_register_use_case.py`
- **Hecho cuando:** existen y pasan, sin cambios en `app/`, las pruebas
  `test_F002_R001_*` (cuenta creada; nombre recortado),
  `test_F002_R002_*` (nombre solo espacios = ausente; nombre y contraseña
  ausentes en un único `ValidationError` con ambos detalles),
  `test_F002_R003_*` parametrizada con `ana@ejemplo` y `ana ejemplo.com`,
  `test_F002_R004_*` (`weak` → 4 reglas; `Abcdefg1` → solo el especial;
  `Abcd123!` aceptada), `test_F002_R005_*` (la cuenta existente conserva nombre
  y hash), `test_F002_R006_*` (`  Ana@Example.COM ` se guarda como
  `ana@example.com`; `  ANA@Example.com ` choca con una cuenta existente) y
  `test_F002_R014_*` (con teléfono, sin teléfono, teléfono vacío o solo
  espacios → `None`).

### T002 `P` — Pruebas del hash de contraseña con bcrypt real

- **Estado:** `[x]`
- **Requisitos:** R008
- **Depende de:** —
- **Archivos:** `tests/test_password_hasher.py` (nuevo)
- **Hecho cuando:** `test_F002_R008_*` comprueban con `BcryptPasswordHasher`
  que la misma contraseña produce dos hashes distintos, que ninguno es igual a la
  contraseña en claro y que `verify` acepta la correcta y rechaza otra; la prueba
  pasa sin cambios en `app/`.

### T003 `P` — Prueba de duplicado en el repositorio (carrera)

- **Estado:** `[x]`
- **Requisitos:** R007
- **Depende de:** —
- **Archivos:** `tests/test_user_repository.py`
- **Hecho cuando:** `test_F002_R007_*` inserta con `SqlAlchemyUserRepository.add`
  dos `User` distintos con el mismo correo, comprueba que el segundo lanza
  `EmailAlreadyRegisteredError` y que en `users` queda una sola fila; pasa sin
  cambios en `app/`.

### T004 `P` — Prueba de extremo a extremo registro → login

- **Estado:** `[x]`
- **Requisitos:** R011
- **Depende de:** —
- **Archivos:** `tests/test_register_then_login.py` (nuevo)
- **Hecho cuando:** `test_F002_R011_*` registra por HTTP con `Ana@Example.com` y
  `Abcd123!`, inicia sesión en `POST /v1/auth/login` con `ana@example.com` y
  `Abcd123!`, y recibe 200 con un token; pasa sin cambios en `app/`.

### T005 `P` — Pruebas HTTP del endpoint para el comportamiento existente

- **Estado:** `[x]`
- **Requisitos:** R005, R006, R010, R012
- **Depende de:** —
- **Archivos:** `tests/test_register_endpoint.py`
- **Hecho cuando:** existen y pasan, sin cambios en `app/`:
  `test_F002_R005_*` (409 con «El correo electrónico ya está registrado.»),
  `test_F002_R006_*` (`  ANA@Example.com ` tras `ana@example.com` → 409),
  `test_F002_R010_*` (201 con id, nombre y correo normalizado) y
  `test_F002_R012_*` (texto plano, JSON con sintaxis inválida y array → 400 y
  ninguna cuenta creada). Las pruebas de carrera y de logs están en T011.

### T006 — Rechazar valores no textuales (D2)

- **Estado:** `[x]`
- **Requisitos:** R002, R003, R012, R014
- **Depende de:** T001, T005, T011
- **Archivos:** `app/application/register_user.py`,
  `tests/test_register_use_case.py`, `tests/test_register_endpoint.py`
- **Hecho cuando:** existen `_as_text` y el diccionario `_FORMAT_ERRORS` con las
  cuatro frases de formato del plan (D2), y el mensaje de correo mal formado sale
  de ese diccionario sin cambiar su texto; el caso de uso no lanza excepciones
  distintas de las de aplicación ante `name`, `email`, `password` o `phone` no
  textuales. Las pruebas `test_F002_R012_*` nuevas comprueban que
  `{"name": 123, ...}` responde 400 con «El nombre no tiene un formato válido.»,
  `{"password": 12345678, ...}` con «La contraseña no tiene un formato válido.»
  y `{"phone": 600123456, ...}` con un único detalle «El teléfono no tiene un
  formato válido.» (no 500), sin crear cuenta; toda la suite pasa.

### T007 — Longitudes máximas de nombre, correo y contraseña (D1)

- **Estado:** `[x]`
- **Requisitos:** R015
- **Depende de:** T006
- **Archivos:** `app/application/register_user.py`,
  `tests/test_register_use_case.py`, `tests/test_register_endpoint.py`
- **Hecho cuando:** existen `NAME_MAX_LENGTH = 100`, `EMAIL_MAX_LENGTH = 254` y
  `PASSWORD_MAX_LENGTH = 128`, comprobadas en `_validate_basic_fields` antes del
  hash; pasan `test_F002_R015_*` para: 100/254/128 aceptados; nombre de 101
  rechazado; correo de 255 y contraseña de 129 en un único error con ambos
  detalles; nombre de 100 caracteres con espacios exteriores aceptado; y por
  HTTP un exceso responde 400 sin crear cuenta. Toda la suite pasa.

### T008 — Longitud y formato del teléfono (D7)

- **Estado:** `[x]`
- **Requisitos:** R014, R016, R017
- **Depende de:** T007
- **Archivos:** `app/application/register_user.py`,
  `tests/test_register_use_case.py`, `tests/test_register_endpoint.py`
- **Hecho cuando:** existen `PHONE_MAX_LENGTH = 20` y
  `_PHONE_RE = ^\+?[0-9 ()\-]+$` más la comprobación de al menos un dígito
  `[0-9]`, dentro de la misma validación; pasan `test_F002_R016_*` (20 aceptado,
  incluido con espacios exteriores; 21 rechazado; teléfono de 21 y nombre de 101
  en un único error; teléfono de 21 con contraseña `weak` → el rechazo menciona
  el teléfono y no las reglas de contraseña; 400 por HTTP) y `test_F002_R017_*`
  parametrizada (aceptados `600123456`, `+34 600 123 456`, `(91) 555-12-34`;
  rechazados `abc`, `600-ABC-123`, `600+123`, `++34600`, `( - )` y
  `٦٠٠١٢٣٤٥٦`; teléfono y correo inválidos en un único error). El mensaje de
  formato del teléfono sale de `_FORMAT_ERRORS`. Toda la suite pasa.

### T009 — Documentación en el código

- **Estado:** `[x]`
- **Requisitos:** R008, R010
- **Depende de:** T008
- **Archivos:** `app/application/register_user.py`, `app/blueprints/auth.py`,
  `app/infrastructure/password_hasher.py`
- **Hecho cuando:** el docstring de `register_user.py` y el de
  `RegisterResource` citan los requisitos de la spec 002 en vez de los AC-00x
  del documento original, y `password_hasher.py` lleva un comentario sobre el
  corte de bcrypt a 72 bytes que remite a D5 del plan; la suite sigue pasando.

### T010 — Verificación final de trazabilidad

- **Estado:** `[x]`
- **Requisitos:** R001, R002, R003, R004, R005, R006, R007, R008, R009, R010, R011, R012, R015, R016, R017
- **Depende de:** T001, T002, T003, T004, T005, T006, T007, T008, T009, T011
- **Archivos:** —
- **Hecho cuando:** `pytest` en `src/api/auth-service` pasa completo y
  `sdd.py trace --check` no reporta errores `E-REQ-NO-TEST` ni `E-REQ-NO-TASK`
  para la feature 002.

### T011 — Pruebas HTTP de carrera de duplicados y de ausencia de la contraseña en logs

- **Estado:** `[x]`
- **Requisitos:** R007, R009
- **Depende de:** T005
- **Archivos:** `tests/test_register_endpoint.py`
- **Hecho cuando:** existen y pasan, sin cambios en `app/`:
  `test_F002_R007_*` (con `get_by_email` parcheado para devolver `None` tras un
  primer alta, el segundo alta responde 409 y queda una sola fila) y
  `test_F002_R009_*` (con `caplog` a nivel DEBUG en un alta exitosa y en una
  rechazada, ni la contraseña ni el hash guardado aparecen en logs ni en el
  cuerpo; el engine se crea sin `echo`). Va después de T005 porque edita el
  mismo archivo; se separó de T005 para que cada tarea sea más pequeña.

## Cobertura

| Requisito | Tareas |
| --------- | ------ |
| R001 | T001 |
| R002 | T001, T006 |
| R003 | T001, T006 |
| R004 | T001 |
| R005 | T001, T005 |
| R006 | T001, T005 |
| R007 | T003, T011 |
| R008 | T002, T009 |
| R009 | T011 |
| R010 | T005, T009 |
| R011 | T004 |
| R012 | T005, T006 |
| R014 | T001, T006, T008 |
| R015 | T007 |
| R016 | T008 |
| R017 | T008 |

T010 cita todos los MUST porque los verifica en conjunto (suite y `trace`), pero
no implementa ninguno; por eso no figura en esta tabla.

> Todo requisito MUST debe tener al menos una tarea.
