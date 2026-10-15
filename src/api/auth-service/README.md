# auth-service

Microservicio de autenticación de **EventsApp**. Implementa el **registro**
(`docs/features/register_user.md`, spec `specs/002-registro-usuario/`) y el
**inicio de sesión** (`docs/features/user_login.md`, spec
`specs/001-inicio-sesion-usuario/`) siguiendo
**Clean Architecture** y el stack de `docs/tech_stack.md` (Python, Flask-RESTful,
SQLAlchemy, PostgreSQL, PyJWT, PyTest, Docker).

## Endpoints

| Método y ruta | Descripción | Auth |
|---------------|-------------|------|
| `POST /v1/auth/register` | Registra un nuevo usuario. | — |
| `POST /v1/auth/login` | Autentica y emite una credencial de sesión (JWT). | — |
| `POST /v1/auth/logout` | Invalida la credencial de sesión actual. | Bearer |
| `GET /v1/auth/me` | Devuelve el usuario autenticado (recurso protegido). | Bearer |
| `GET /health` | Liveness: el proceso está vivo (sin dependencias). | — |
| `GET /health/ready` | Readiness: dependencias sanas (verifica la BD). | — |

Los recursos con **Auth = Bearer** requieren la cabecera
`Authorization: Bearer <token>`.

### `POST /v1/auth/register`

**Request**

```json
{
  "name": "Ana",
  "email": "ana@example.com",
  "password": "Abcd123!",
  "phone": "3001234567"
}
```

`phone` es opcional. Un teléfono vacío o solo con espacios equivale a no
enviarlo.

| Código | Caso |
|--------|------|
| `201 Created` | Registro exitoso. Devuelve `{ message, user: { id, name, email, phone } }` con el correo normalizado (R010). |
| `400 Bad Request` | Cuerpo que no es un objeto JSON (sin `details`), errores de forma o contraseña débil (con `details`, un mensaje por problema). |
| `409 Conflict` | `{ "error": "El correo electrónico ya está registrado." }` (R005, R006, R007). |

**Ejemplo de `400`** con varios errores de forma a la vez:

```json
{
  "error": "Datos de registro inválidos.",
  "details": [
    "El nombre no puede superar 100 caracteres.",
    "El teléfono no tiene un formato válido."
  ]
}
```

**Orden de validación.** Primero se comprueban todos los errores de forma de
todos los campos en una sola pasada; si hay alguno, la respuesta los enumera
todos y no se evalúa nada más. Solo si la forma es correcta se aplica la
política de contraseña, y por último se comprueba que el correo no esté
registrado. Así, una petición con un teléfono inválido y una contraseña débil
recibe primero solo el error del teléfono.

| Error de forma | Mensaje de `details` |
|----------------|----------------------|
| Campo obligatorio ausente o vacío | «El nombre es obligatorio.», «El correo electrónico es obligatorio.», «La contraseña es obligatoria.» |
| Correo mal formado, o cualquier campo con un valor que no es texto | «El nombre / El correo electrónico / La contraseña / El teléfono no tiene un formato válido.» |
| Nombre > 100 caracteres | «El nombre no puede superar 100 caracteres.» |
| Correo > 254 caracteres | «El correo electrónico no puede superar 254 caracteres.» |
| Contraseña > 128 caracteres | «La contraseña no puede superar 128 caracteres.» |
| Teléfono > 20 caracteres | «El teléfono no puede superar 20 caracteres.» |
| Teléfono con caracteres no permitidos o sin dígitos | «El teléfono no tiene un formato válido.» |

### `POST /v1/auth/login`

**Request**

```json
{
  "email": "ana@example.com",
  "password": "Abcd123!"
}
```

| Código | Caso |
|--------|------|
| `200 OK` | Login exitoso. Devuelve `{ message, token, user: { id, name, email } }`. |
| `400 Bad Request` | Falta `email` o `password` (R003). |
| `401 Unauthorized` | Credenciales inválidas **o** cuenta bloqueada, con un cuerpo **genérico e indistinguible** (R002, R005). |

### `POST /v1/auth/logout`

Requiere `Authorization: Bearer <token>`. Revoca el token presentado.

| Código | Caso |
|--------|------|
| `200 OK` | Sesión cerrada; el token queda revocado (R008). |
| `401 Unauthorized` | Sin credencial válida. |

### `GET /v1/auth/me`

Requiere `Authorization: Bearer <token>`. Recurso protegido de referencia.

| Código | Caso |
|--------|------|
| `200 OK` | Devuelve `{ message, user: { id, name, email } }` (R007). |
| `401 Unauthorized` | Token ausente, inválido, expirado o revocado (R007, R009, R010). |

### `GET /health` y `GET /health/ready`

Dos sondas separadas, pensadas para orquestación en la nube (Kubernetes,
Cloud Run):

- **`/health`** (*liveness*): confirma que el proceso está vivo. Es barato y
  **no consulta la BD** a propósito —una BD caída no debe provocar reinicios del
  contenedor—. Siempre `200 OK` → `{ status: "ok" }`.
- **`/health/ready`** (*readiness*): confirma que el servicio puede atender
  tráfico. Verifica la conexión a la base de datos con `SELECT 1`.

| Código | Caso |
|--------|------|
| `200 OK` | Dependencias sanas → `{ status: "ok", checks: { database: "ok" } }`. |
| `503 Service Unavailable` | La BD no responde → `{ status: "unavailable", checks: { database: "error" } }`. |

Ejemplo de sondas en Kubernetes:

```yaml
livenessProbe:
  httpGet: { path: /health, port: 5000 }
readinessProbe:
  httpGet: { path: /health/ready, port: 5000 }
```

## Reglas de negocio

**Registro** (spec `002-registro-usuario`)

- **Campos obligatorios** (R002): nombre, correo y contraseña. Un nombre solo
  con espacios cuenta como ausente.
- **Normalización** (R001, R006): nombre y correo se guardan sin espacios
  exteriores; el correo, además, en minúsculas. `Ana@Example.COM` y
  `ana@example.com` son el mismo correo.
- **Formato del correo** (R003): `algo@dominio.tld`, sin espacios.
- **Correo único** (R005, R007): un correo ya registrado se rechaza con `409`
  explícito. Ante dos altas simultáneas, la restricción única de la base de
  datos garantiza que solo se cree una cuenta. El mensaje explícito permite
  averiguar si un correo tiene cuenta; es un riesgo aceptado en la spec.
- **Política de contraseña** (R004): mínimo 8 caracteres, con al menos una
  mayúscula, una minúscula, un dígito y un carácter especial. Se informan todas
  las reglas incumplidas a la vez.
- **Longitudes máximas** (R015): nombre 100, correo 254 y contraseña 128
  caracteres, medidas tras la normalización. Se comprueban antes de calcular el
  hash.
- **Teléfono opcional** (R014, R016, R017): como máximo 20 caracteres; solo
  dígitos del 0 al 9, espacios, guiones, paréntesis y un `+` inicial, con al
  menos un dígito. Se guarda tal como llega, sin espacios exteriores.
- **Tipos** (R012): un valor que no es texto (número, booleano, lista) se
  rechaza como formato inválido de ese campo, nunca con un error `500`.
- **Hashing + salting** (R008): las contraseñas se almacenan con **bcrypt** (el
  salt se genera y embebe dentro del hash; la columna `salt` del modelo ER queda
  sin uso). bcrypt solo usa los primeros **72 bytes** de la contraseña: lo que
  pase de ahí no aporta seguridad (riesgo aceptado, D5 del plan).
- **Confidencialidad** (R009): ni la contraseña ni su hash aparecen en
  respuestas ni en logs.
- **Login tras el registro** (R011): la cuenta creada sirve de inmediato para
  iniciar sesión; el registro no inicia sesión automáticamente.

**Inicio de sesión** (spec `001-inicio-sesion-usuario`)

- **Credencial de sesión** (R001, R009): JWT firmado (HS256) con expiración de
  **24 h**; transporta `sub` (id de usuario), `jti`, `iat` y `exp`.
- **Error indistinguible** (R002): email inexistente, contraseña incorrecta y
  cuenta bloqueada devuelven el **mismo** `401` sin revelar si la cuenta existe.
  La contraseña se verifica **siempre** (con un hash señuelo cuando el email no
  existe) para no filtrar cuentas por temporización.
- **Bloqueo por fuerza bruta** (R005): tras **3** intentos fallidos en una
  ventana de **5 min** para la misma combinación `(cuenta, origen)`, se bloquean
  nuevos intentos durante **5 min**. Un login exitoso limpia el contador.
- **Cierre de sesión** (R008): el logout añade el `jti` a una **lista de
  revocación**; las peticiones protegidas rechazan los tokens revocados (un JWT
  firmado no es invalidable solo por expiración).
- **Último acceso** (R006): el login exitoso registra `last_login`.

## Arquitectura

```
app/
├── blueprints/       # Presentación: recursos REST + decorador require_auth
├── application/      # Casos de uso (register, authenticate, logout), DTOs, excepciones
├── domain/           # Entidad User + puertos (UserRepository, PasswordHasher, TokenService)
└── infrastructure/   # SQLAlchemy (db, modelos, repositorios) + bcrypt hasher + JWT token service
utils/                # Política de contraseñas y helpers de respuesta
tests/                # PyTest (unitarias e integración)
```

La dirección de dependencias apunta hacia el dominio: `presentación` e
`infraestructura` dependen de `aplicación`, que depende de `dominio`. El dominio
no conoce Flask, SQLAlchemy, bcrypt ni PyJWT (inversión de dependencias).

**Puertos** (`domain`): `UserRepository` (`get_by_email`, `get_by_id`, `add`,
`update_last_login`), `PasswordHasher` (`hash`, `verify`), `TokenService`
(`issue`, `verify`), `LoginAttemptRepository` y `RevokedTokenRepository`.

**Tablas**: `users` (sin cambios de esquema; `last_login` pasa a escribirse),
`login_attempts` (fuerza bruta) y `revoked_tokens` (revocación de sesión).

## Desarrollo

```bash
cd src/api/auth-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ejecutar la suite de pruebas (SQLite in-memory, sin Postgres)
pytest -v

# Levantar el servicio en local (SQLite por defecto)
flask --app app run
# o con una base concreta:
DATABASE_URL="sqlite:///dev.db" flask --app app run
```

### Smoke manual

```bash
# 1) Registro
curl -X POST localhost:5000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ana","email":"ana@x.com","password":"Abcd123!"}'

# 2) Login -> guarda el token
TOKEN=$(curl -s -X POST localhost:5000/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@x.com","password":"Abcd123!"}' | python -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# 3) Acceso protegido
curl localhost:5000/v1/auth/me -H "Authorization: Bearer $TOKEN"

# 4) Logout (el token deja de servir)
curl -X POST localhost:5000/v1/auth/logout -H "Authorization: Bearer $TOKEN"
```

## Configuración (variables de entorno)

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `DATABASE_URL` | `sqlite:///auth_service.db` | URL de conexión SQLAlchemy. En producción: `postgresql+psycopg2://user:pass@host:5432/eventsapp`. |
| `AUTO_CREATE_TABLES` | `true` | Crea tablas al arrancar (dev). En producción usar migraciones. |
| `JWT_SECRET` | `change-me-in-production` | Secreto de firma HS256 del JWT. **Obligatorio por entorno en producción** (activo crítico). |
| `JWT_EXPIRY_SECONDS` | `86400` | Vida útil de la credencial de sesión (24 h). |
| `LOGIN_MAX_ATTEMPTS` | `3` | Intentos fallidos que disparan el bloqueo. |
| `LOGIN_WINDOW_SECONDS` | `300` | Ventana para contar los fallos (5 min). |
| `LOGIN_LOCKOUT_SECONDS` | `300` | Duración del bloqueo (5 min). |

## Docker

```bash
docker build -t eventsapp/auth-service .
docker run -p 5000:5000 \
  -e DATABASE_URL=postgresql+psycopg2://... \
  -e JWT_SECRET=... \
  eventsapp/auth-service
```

## Alcance

Este servicio cubre el **registro** (requisitos de
`specs/002-registro-usuario/`) y el **inicio de sesión** (requisitos R001–R010
de `specs/001-inicio-sesion-usuario/`).

Fuera de alcance (ver los non-goals de ambas specs): formulario web de registro
(irá en una feature de frontend), inicio de sesión automático tras el registro,
verificación de email, CAPTCHA o protección anti-bots en el registro, edición
de perfil, recuperación y cambio de contraseña, login social/SSO, MFA/2FA,
autorización por roles y sesiones persistentes ("recordarme").
