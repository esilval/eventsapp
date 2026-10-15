# Tasks: inicio de sesión de usuario

| Campo | Valor       |
| ----- | ----------- |
| Spec  | `spec.md`   |
| Plan  | `plan.md`   |
| Fecha | 2026-08-12  |

> Cada tarea debe ser verificable por sí sola y caber en una sola sesión de
> trabajo. Si una tarea necesita una decisión que no está en `plan.md`, la tarea
> está mal descompuesta.

## Leyenda

- `[ ]` pendiente · `[~]` en curso · `[x]` hecha
- `P` marca tareas paralelizables (sin dependencias entre sí)

## Tareas

### T001 `P` — Configuración de login (JWT y bloqueo)

- **Estado:** `[x]`
- **Requisitos:** R005, R009
- **Depende de:** —
- **Archivos:** `src/api/auth-service/app/config.py`
- **Hecho cuando:** `Config` expone `jwt_secret`, `jwt_expiry_seconds` (=86400), `login_max_attempts` (=3), `login_window_seconds` (=300) y `login_lockout_seconds` (=300), leídos de entorno con esos valores por defecto; `TestConfig` los hereda con un `jwt_secret` fijo de prueba.

### T002 `P` — Añadir dependencia PyJWT

- **Estado:** `[x]`
- **Requisitos:** R001
- **Depende de:** —
- **Archivos:** `src/api/auth-service/requirements.txt`
- **Hecho cuando:** `PyJWT` figura en `requirements.txt` y `pip install -r requirements.txt` lo instala en el `.venv` sin error.

### T003 `P` — Puerto de dominio `TokenService`

- **Estado:** `[x]`
- **Requisitos:** R001, R009
- **Depende de:** —
- **Archivos:** `src/api/auth-service/app/domain/security.py`
- **Hecho cuando:** existe la ABC `TokenService` con `issue(user_id: str) -> IssuedToken` (token, jti, expires_at) y `verify(token: str) -> TokenClaims`; no importa ninguna librería concreta (sin dependencias de PyJWT en `domain`).

### T004 `P` — Puertos de persistencia nuevos

- **Estado:** `[x]`
- **Requisitos:** R005, R006, R008
- **Depende de:** —
- **Archivos:** `src/api/auth-service/app/domain/repositories.py`
- **Hecho cuando:** `UserRepository` declara `update_last_login(user_id: str, when: datetime)`; existen las ABC `LoginAttemptRepository` (`count_recent(email, origin, since)`, `record_failure(email, origin, when)`, `clear(email, origin)`) y `RevokedTokenRepository` (`revoke(jti, expires_at)`, `is_revoked(jti) -> bool`).

### T005 `P` — DTOs y excepciones del login

- **Estado:** `[x]`
- **Requisitos:** R001, R002, R003, R005
- **Depende de:** —
- **Archivos:** `src/api/auth-service/app/application/dtos.py`, `src/api/auth-service/app/application/exceptions.py`
- **Hecho cuando:** existen `LoginRequest(email, password, origin)`, `LoginResult(token, user)` y `AuthenticatedUser(id, name, email)`; existen `InvalidCredentialsError` y `AccountLockedError`, ambas subclase de `ApplicationError` con el **mismo** mensaje genérico de credenciales inválidas.

### T006 `P` — Modelos ORM `login_attempts` y `revoked_tokens`

- **Estado:** `[x]`
- **Requisitos:** R005, R008
- **Depende de:** —
- **Archivos:** `src/api/auth-service/app/infrastructure/models.py`
- **Hecho cuando:** existen `LoginAttemptModel` (`id`, `email` index, `origin`, `created_at` tz-aware index) y `RevokedTokenModel` (`jti` PK, `expires_at` tz-aware); `Base.metadata.create_all` crea ambas tablas sin error en SQLite in-memory.

### T007 — Adaptador JWT del `TokenService` + pruebas

- **Estado:** `[x]`
- **Requisitos:** R001, R009
- **Depende de:** T001, T002, T003
- **Archivos:** `src/api/auth-service/app/infrastructure/token_service.py`, `src/api/auth-service/tests/test_token_service.py`
- **Hecho cuando:** `JwtTokenService` implementa `issue`/`verify` con PyJWT HS256, `exp = iat + jwt_expiry_seconds`, `jti` único y `sub = user_id`; pasan `test_R001_issue_produce_token_verificable` y `test_R009_verify_rechaza_token_expirado`.

### T008 `P` — Implementar `update_last_login` en el repositorio SQLAlchemy

- **Estado:** `[x]`
- **Requisitos:** R006
- **Depende de:** T004
- **Archivos:** `src/api/auth-service/app/infrastructure/user_repository.py`, `src/api/auth-service/tests/test_user_repository.py`
- **Hecho cuando:** `SqlAlchemyUserRepository.update_last_login` persiste el timestamp; pasa `test_R006_update_last_login_persiste_timestamp`.

### T009 `P` — Repositorio de intentos de login

- **Estado:** `[x]`
- **Requisitos:** R005
- **Depende de:** T001, T004, T006
- **Archivos:** `src/api/auth-service/app/infrastructure/login_attempt_repository.py`, `src/api/auth-service/tests/test_login_attempt_repository.py`
- **Hecho cuando:** `SqlAlchemyLoginAttemptRepository` implementa `count_recent`/`record_failure`/`clear` filtrando por `(email, origin)` y ventana temporal; pasa `test_R005_count_recent_respeta_ventana_y_origen`.

### T010 `P` — Repositorio de tokens revocados

- **Estado:** `[x]`
- **Requisitos:** R008
- **Depende de:** T004, T006
- **Archivos:** `src/api/auth-service/app/infrastructure/revoked_token_repository.py`, `src/api/auth-service/tests/test_revoked_token_repository.py`
- **Hecho cuando:** `SqlAlchemyRevokedTokenRepository` implementa `revoke`/`is_revoked`; pasa `test_R008_token_revocado_es_detectado`.

### T011 — Caso de uso `AuthenticateUserUseCase` + pruebas unitarias

- **Estado:** `[x]`
- **Requisitos:** R001, R002, R003, R004, R005, R006
- **Depende de:** T003, T004, T005
- **Archivos:** `src/api/auth-service/app/application/authenticate_user.py`, `src/api/auth-service/tests/test_authenticate_use_case.py`
- **Hecho cuando:** el caso de uso normaliza email, valida campos obligatorios, comprueba el bloqueo antes de verificar, verifica con `PasswordHasher.verify` (hash señuelo si el email no existe), en éxito emite token, actualiza último acceso y limpia intentos, y en fallo registra el intento; pasan `test_R001_credenciales_correctas_emiten_token`, `test_R002_email_inexistente_y_password_incorrecta_dan_mismo_error`, `test_R003_falta_campo_lanza_validation_error`, `test_R004_no_expone_password_en_claro`, `test_R005_tres_fallos_bloquean_cuarto_intento`, `test_R006_login_exitoso_actualiza_last_login`.

### T012 `P` — Caso de uso `LogoutUserUseCase` + prueba unitaria

- **Estado:** `[x]`
- **Requisitos:** R008
- **Depende de:** T004, T005
- **Archivos:** `src/api/auth-service/app/application/logout_user.py`, `src/api/auth-service/tests/test_logout_use_case.py`
- **Hecho cuando:** el caso de uso revoca el `jti` con su `expires_at` vía `RevokedTokenRepository`; pasa `test_R008_logout_revoca_jti`.

### T013 — Ensamblado de dependencias en el app factory

- **Estado:** `[x]`
- **Requisitos:** R001, R005, R008
- **Depende de:** T007, T008, T009, T010
- **Archivos:** `src/api/auth-service/app/__init__.py`
- **Hecho cuando:** `create_app` registra en `app.extensions` el `JwtTokenService` y las factorías de los repositorios de intentos y de tokens revocados; `/health` sigue respondiendo 200 y la app arranca sin error.

### T014 — Decorador `require_auth` + pruebas

- **Estado:** `[x]`
- **Requisitos:** R007, R009, R010
- **Depende de:** T007, T010, T013
- **Archivos:** `src/api/auth-service/app/blueprints/decorators.py`, `src/api/auth-service/tests/test_require_auth.py`
- **Hecho cuando:** `require_auth` extrae el `Bearer`, valida firma y `exp`, comprueba no-revocación y expone el usuario autenticado; devuelve 401 si falta/es inválido/expirado/revocado; pasan `test_R007_sin_token_rechaza`, `test_R009_token_expirado_rechaza`, `test_R010_token_malformado_rechaza`.

### T015 — Endpoint `POST /v1/auth/login` + pruebas de integración

- **Estado:** `[x]`
- **Requisitos:** R001, R002, R003, R005, R006
- **Depende de:** T011, T013
- **Archivos:** `src/api/auth-service/app/blueprints/auth.py`, `src/api/auth-service/tests/test_login_endpoint.py`
- **Hecho cuando:** `LoginResource` parsea la petición, obtiene el `origin` de la IP del cliente, delega en el caso de uso y traduce errores (400 validación, 401 credenciales/bloqueo con cuerpo idéntico); pasan `test_R001_login_ok_devuelve_token`, `test_R002_credenciales_invalidas_401_generico`, `test_R003_faltan_campos_400`, `test_R005_bloqueo_tras_tres_fallos`.

### T016 — Endpoint `POST /v1/auth/logout` + pruebas de integración

- **Estado:** `[x]`
- **Requisitos:** R008
- **Depende de:** T012, T013, T014
- **Archivos:** `src/api/auth-service/app/blueprints/auth.py`, `src/api/auth-service/tests/test_logout_endpoint.py`
- **Hecho cuando:** `LogoutResource` (protegido con `require_auth`) revoca el token; pasa `test_R008_logout_invalida_token_reusado` (logout 200, y reutilizar el token en un recurso protegido da 401).

### T017 — Endpoint protegido `GET /v1/auth/me` + pruebas de integración

- **Estado:** `[x]`
- **Requisitos:** R007, R009, R010
- **Depende de:** T013, T014
- **Archivos:** `src/api/auth-service/app/blueprints/auth.py`, `src/api/auth-service/tests/test_protected_access.py`
- **Hecho cuando:** `MeResource` (protegido) devuelve el usuario autenticado; pasan `test_R007_me_sin_token_401` y `test_R007_me_con_token_200`, `test_R009_me_token_expirado_401`, `test_R010_me_token_invalido_401`.

## Cobertura

| Requisito | Prioridad | Tareas |
| --------- | --------- | ------ |
| R001 | MUST | T002, T003, T007, T011, T013, T015 |
| R002 | MUST | T005, T011, T015 |
| R003 | MUST | T005, T011, T015 |
| R004 | MUST | T011 |
| R005 | MUST | T001, T005, T009, T011, T015 |
| R006 | MUST | T004, T008, T011, T015 |
| R007 | MUST | T014, T017 |
| R008 | MUST | T004, T010, T012, T013, T016 |
| R009 | MUST | T001, T003, T007, T014, T017 |
| R010 | SHOULD | T014, T017 |

_Todos los requisitos MUST (R001–R009) tienen al menos una tarea de
implementación y una tarea con prueba que lleva su ID. El SHOULD (R010) también
está cubierto. Ningún requisito queda sin tarea._
