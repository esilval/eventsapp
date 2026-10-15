# Plan: inicio de sesión de usuario

| Campo | Valor              |
| ----- | ------------------ |
| Spec  | `spec.md`          |
| Fecha | 2026-08-12         |

> Este documento describe **cómo**. Si aquí aparece un requisito nuevo que no
> está en `spec.md`, el sitio correcto es `spec.md`, no aquí.

## Resumen

Se añade el inicio de sesión al `auth-service` existente (Flask + Clean
Architecture), reutilizando el patrón del registro: puerto en `domain`, caso de
uso en `application`, adaptador en `infrastructure`, y un recurso fino en
`blueprints`. La credencial de sesión será un **JWT firmado** con expiración de
24 h (R009); el cierre de sesión (R008) se resuelve con una **lista de
revocación** persistida, porque un JWT puro no es invalidable. La protección
contra fuerza bruta (R005) se apoya en una **tabla de intentos** consultada por
`(email, origen)` dentro de la ventana de 5 minutos. El caso de uso de login
devuelve siempre el mismo error genérico (R002) y ejecuta la verificación de
contraseña incluso cuando el email no existe, para no filtrar cuentas por
temporización.

## Decisiones

### D1 — Credencial de sesión: JWT firmado (HS256) con expiración de 24 h

- **Contexto:** R001 exige emitir una credencial de sesión; R009 fija su
  expiración en 24 h; R007 exige que otras funciones personalizadas (en otros
  microservicios) puedan reconocer al usuario. El `tech_stack.md` nombra JWT
  explícitamente.
- **Decisión:** emitir un JWT con `sub` (id de usuario), `jti` (id único de
  token), `iat` y `exp` (iat + 24 h). Firma simétrica HS256 con un secreto de
  entorno (`JWT_SECRET`). Se introduce un puerto `TokenService`
  (`issue`/`verify`) en `domain/security.py`, implementado en
  `infrastructure/token_service.py` con PyJWT.
- **Alternativas descartadas:** *(a)* token opaco con estado en servidor (tabla
  `sessions`): invalidación trivial en logout, pero obliga a cada microservicio
  a llamar al auth-service en cada petición, rompiendo la independencia de la
  arquitectura de microservicios. *(b)* JWT sin `jti` ni revocación: imposible
  cumplir R008 (logout no invalidaría nada).
- **Consecuencias:** la validez del token es autocontenida y verificable sin
  tocar la BD, salvo por la comprobación de revocación (D2). Rotar `JWT_SECRET`
  invalida todos los tokens vivos. El secreto es un activo crítico.

### D2 — Logout mediante lista de revocación de `jti`

- **Contexto:** R008 exige que, tras cerrar sesión, la credencial deje de dar
  acceso. Un JWT firmado es válido hasta su `exp` por diseño.
- **Decisión:** tabla `revoked_tokens (jti PK, expires_at)`. El logout inserta
  el `jti` del token presentado. La validación de cada petición protegida
  comprueba, además de la firma y `exp`, que el `jti` no esté revocado. Una
  limpieza (basada en `expires_at`) puede purgar entradas caducadas.
- **Alternativas descartadas:** lista de revocación en memoria del proceso: se
  pierde al reiniciar y no se comparte entre instancias, incumpliendo R008 de
  forma intermitente.
- **Consecuencias:** las peticiones protegidas hacen una consulta puntual a la
  tabla de revocación. La tabla crece hasta la purga; el índice por `jti` la
  mantiene barata.

### D3 — Protección de fuerza bruta con tabla de intentos por `(email, origen)`

- **Contexto:** R005 exige bloquear 5 min tras 3 fallos consecutivos en una
  ventana de 5 min, por combinación cuenta+origen.
- **Decisión:** tabla `login_attempts (id, email, origin, created_at)` que
  registra cada intento **fallido**. Antes de verificar credenciales, el caso de
  uso cuenta los fallos de esa `(email, origin)` en los últimos 5 min; si son
  ≥ 3, responde con el error genérico sin verificar (bloqueo). Un login exitoso
  borra los intentos fallidos de esa `(email, origin)`. El `origin` se toma de
  la IP del cliente (`request.remote_addr`, o `X-Forwarded-For` si hay proxy de
  confianza) y se pasa al caso de uso como dato de entrada.
- **Alternativas descartadas:** *(a)* Redis con TTL por clave: es la opción
  ideal a escala (expiración automática, atómico), pero el servicio no tiene
  Redis aprovisionado hoy; añadirlo excede esta feature. *(b)* contador
  en memoria: no sobrevive a reinicios ni se comparte entre instancias.
- **Consecuencias:** una fila por intento fallido; se requiere purga/borrado en
  éxito para acotar el tamaño. La ventana deslizante se calcula por consulta
  temporal, no por job programado.

### D4 — Error genérico e indistinguible + verificación siempre (anti-enumeración)

- **Contexto:** R002 y el requisito no funcional de indistinguibilidad temporal
  prohíben revelar si un email existe, tanto por el mensaje como por el tiempo
  de respuesta.
- **Decisión:** un único código y mensaje (`HTTP 401`, "Correo electrónico o
  contraseña inválidos") para email inexistente, contraseña incorrecta y cuenta
  bloqueada. Cuando el email no existe, el caso de uso verifica la contraseña
  contra un **hash señuelo** para igualar el coste temporal de bcrypt.
- **Alternativas descartadas:** responder 404/registro-no-encontrado para email
  inexistente: filtra qué cuentas existen (enumeración), incumple R002.
- **Consecuencias:** un pequeño coste de CPU extra en intentos con email
  inexistente, aceptable frente a la protección anti-enumeración.

### D5 — Ampliar el puerto `UserRepository` en vez de crear otro

- **Contexto:** R006 exige registrar la marca de último acceso; el login ya usa
  `get_by_email`.
- **Decisión:** añadir `update_last_login(user_id, when)` al puerto
  `UserRepository` y su implementación SQLAlchemy. Reutiliza el `get_by_email`
  existente para la búsqueda.
- **Alternativas descartadas:** un `save(user)` genérico que reescriba toda la
  entidad: más superficie de escritura de la necesaria para este caso.
- **Consecuencias:** el puerto crece con una operación acotada y fácil de
  testear.

### D6 — Añadir `get_by_id` al puerto `UserRepository` (para `GET /me`)

- **Contexto:** el contrato de `GET /v1/auth/me` devuelve `{ id, name, email }`,
  pero la credencial de sesión solo transporta el id del usuario (`sub`) y el
  puerto únicamente ofrecía `get_by_email`. Añadir `name`/`email` a las claims
  del token contradiría D1 (claims mínimas y sin PII).
- **Decisión:** ampliar `UserRepository` con `get_by_id(user_id) -> User | None`;
  `MeResource` resuelve el perfil a partir del id de las claims. _(Ajuste
  detectado durante `/sdd:implement`: el plan original no enumeraba esta
  operación.)_
- **Alternativas descartadas:** *(a)* meter `name`/`email` en el JWT: engorda el
  token, filtra PII y rompe D1. *(b)* que `/me` devuelva solo el id: incumple el
  contrato del propio plan.
- **Consecuencias:** una operación de lectura más en el puerto y su adaptador,
  reutilizable por otros recursos protegidos.

## Componentes afectados

| Componente | Cambio | Requisitos que cubre |
| ---------- | ------ | -------------------- |
| `app/blueprints/auth.py` | Nuevos recursos `LoginResource` (`POST /login`), `LogoutResource` (`POST /logout`), `MeResource` (`GET /me`); ensamblado de dependencias del login | R001, R002, R003, R007, R008 |
| `app/application/authenticate_user.py` (nuevo) | Caso de uso de login: validación, bloqueo, verificación anti-timing, emisión de token, actualización de último acceso | R001–R006 |
| `app/application/logout_user.py` (nuevo) | Caso de uso de logout: revoca el `jti` del token | R008 |
| `app/application/dtos.py` | `LoginRequest`, `LoginResult`, `AuthenticatedUser` | R001, R003 |
| `app/application/exceptions.py` | `InvalidCredentialsError` (→401), `AccountLockedError` (→401, mismo mensaje) | R002, R005 |
| `app/domain/security.py` | Nuevo puerto `TokenService` (`issue`, `verify`); `PasswordHasher.verify` ya existe | R001, R004, R009 |
| `app/domain/repositories.py` | `UserRepository.update_last_login` y `UserRepository.get_by_id`; nuevos puertos `LoginAttemptRepository`, `RevokedTokenRepository` | R005, R006, R007, R008 |
| `app/infrastructure/token_service.py` (nuevo) | Adaptador JWT (PyJWT, HS256) del puerto `TokenService` | R001, R009 |
| `app/infrastructure/user_repository.py` | Implementa `update_last_login` | R006 |
| `app/infrastructure/login_attempt_repository.py` (nuevo) | Cuenta/registra/limpia intentos por `(email, origin)` en ventana | R005 |
| `app/infrastructure/revoked_token_repository.py` (nuevo) | Inserta y consulta `jti` revocados | R008 |
| `app/infrastructure/models.py` | Modelos ORM `LoginAttemptModel`, `RevokedTokenModel` (users sin cambios) | R005, R008 |
| `app/blueprints/decorators.py` (nuevo) | Decorador `require_auth`: valida firma, `exp` y no-revocación; inyecta el usuario | R007, R009, R010 |
| `app/__init__.py` | Registra el `TokenService` y las nuevas dependencias en `app.extensions` | R001, R005, R008 |
| `app/config.py` | `jwt_secret`, `jwt_expiry_seconds=86400`, `login_max_attempts=3`, `login_window_seconds=300`, `login_lockout_seconds=300` | R005, R009 |
| `requirements.txt` | Añade `PyJWT` | R001 |

## Modelo de datos

- **`users`**: sin cambios de esquema. El campo `last_login` ya existe; el login
  pasa a escribirlo (R006).
- **`login_attempts`** (nueva): `id` (PK), `email` (index), `origin`,
  `created_at` (timezone-aware, index). Guarda solo intentos fallidos. Consulta
  por `email + origin + created_at >= now-5min`. Se borra por `(email, origin)`
  al autenticar con éxito.
- **`revoked_tokens`** (nueva): `jti` (PK), `expires_at` (timezone-aware). Se
  consulta por `jti` en cada petición protegida; purgable por `expires_at`.
- Creación de tablas: vía `Base.metadata.create_all` (ya usado por el servicio
  con `auto_create_tables`); en producción, migración.

## Contratos

- `POST /v1/auth/login`
  - Request JSON: `{ "email": str, "password": str }`
  - `200`: `{ "message": "...", "token": str, "user": { "id", "name", "email" } }` (R001)
  - `400`: falta `email` o `password` (R003)
  - `401`: credenciales inválidas **o** cuenta bloqueada, mismo cuerpo genérico (R002, R005)
- `POST /v1/auth/logout` — requiere `Authorization: Bearer <token>`
  - `200`: `{ "message": "Sesión cerrada." }`; el `jti` queda revocado (R008)
  - `401`: sin token válido
- `GET /v1/auth/me` — requiere `Authorization: Bearer <token>` (recurso protegido de referencia)
  - `200`: `{ "user": { "id", "name", "email" } }` (R007, camino positivo)
  - `401`: token ausente, inválido, expirado o revocado (R007, R009, R010)
- Puerto `TokenService`: `issue(user_id: str) -> (token: str, jti: str, expires_at: datetime)`; `verify(token: str) -> Claims` (lanza en firma/exp inválidas).
- Puerto `UserRepository.update_last_login(user_id: str, when: datetime) -> None`.
- Puerto `UserRepository.get_by_id(user_id: str) -> User | None` (perfil para `GET /me`).

## Estrategia de pruebas

| Requisito | Tipo de prueba | Dónde vive |
| --------- | -------------- | ---------- |
| R001 | Unitaria (caso de uso) + integración (endpoint) | `tests/test_authenticate_use_case.py`, `tests/test_login_endpoint.py` |
| R002 | Integración: email inexistente y contraseña incorrecta devuelven idéntico 401 | `tests/test_login_endpoint.py` |
| R003 | Integración: falta email / falta password → 400 | `tests/test_login_endpoint.py` |
| R004 | Unitaria: se usa `PasswordHasher.verify`; el password en claro no aparece en la respuesta ni en logs capturados | `tests/test_authenticate_use_case.py` |
| R005 | Unitaria + integración: 3 fallos (mismo email+origen) bloquean el 4.º aun con password correcta; otro origen no queda bloqueado; expira a los 5 min | `tests/test_login_lockout.py` |
| R006 | Unitaria: login exitoso invoca `update_last_login` con timestamp | `tests/test_authenticate_use_case.py` |
| R007 | Integración: `GET /me` sin token → 401; con token válido → 200 | `tests/test_protected_access.py` |
| R008 | Integración: logout revoca el token; reutilizarlo → 401 | `tests/test_logout_endpoint.py` |
| R009 | Unitaria (token con `exp` pasado) + integración: token expirado → 401 | `tests/test_token_service.py`, `tests/test_protected_access.py` |
| R010 | Integración: token con firma inválida / malformado → 401 tratado como no autenticado | `tests/test_protected_access.py` |

## Riesgos técnicos

| Riesgo | Impacto | Mitigación |
| ------ | ------- | ---------- |
| `origin` (IP) es falsificable vía `X-Forwarded-For` | Evadir o abusar del bloqueo R005 | Confiar en `X-Forwarded-For` solo tras proxy de confianza; por defecto usar `remote_addr`. El bloqueo es cuenta **+** origen, no solo origen. |
| DoS dirigido: alguien bloquea a un usuario legítimo con fallos | Usuario legítimo no entra desde su origen | El bloqueo es por `(cuenta, origen)`: el usuario legítimo desde otro origen no queda bloqueado (criterio de R005). |
| Fuga de `JWT_SECRET` | Falsificación de tokens | Secreto solo por entorno, nunca en el repo; rotación invalida tokens; fuera de alcance: gestión de secretos avanzada. |
| Crecimiento de `login_attempts` / `revoked_tokens` | Degradación de consultas | Índices por columnas de consulta; borrado en login exitoso; purga por `expires_at`/ventana. |
| SQLite en pruebas vs PostgreSQL en prod (tipos datetime/tz) | Falsos verdes | Usar `DateTime(timezone=True)` como el modelo existente; timestamps en UTC (`_utcnow`). |

## Trazabilidad

Todos los requisitos MUST de `spec.md` (R001–R009) aparecen en la tabla de
componentes **y** en la de pruebas. El único SHOULD (R010) aparece en
componentes (`require_auth`) y pruebas. Cobertura completa; ningún requisito sin
componente ni prueba, y ningún componente que introduzca requisitos ausentes de
la spec.

| Requisito | Prioridad | ¿En componentes? | ¿En pruebas? |
| --------- | --------- | ---------------- | ------------ |
| R001 | MUST | Sí | Sí |
| R002 | MUST | Sí | Sí |
| R003 | MUST | Sí | Sí |
| R004 | MUST | Sí | Sí |
| R005 | MUST | Sí | Sí |
| R006 | MUST | Sí | Sí |
| R007 | MUST | Sí | Sí |
| R008 | MUST | Sí | Sí |
| R009 | MUST | Sí | Sí |
| R010 | SHOULD | Sí | Sí |
