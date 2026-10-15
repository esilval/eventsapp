# EventsApp

EventsApp es una aplicación web para crear y gestionar eventos de pequeña y
mediana escala: asistentes y acompañantes, confirmación y validación de
asistencia mediante código QR, novedades del evento e informes. Sustituye la
combinación habitual de Google Forms, hojas de cálculo y WhatsApp por una única
herramienta centralizada.

> Visión de producto completa: [docs/eventsapp.md](docs/eventsapp.md).

## Estado

| Funcionalidad | Documento | Spec SDD | Estado |
| ------------- | --------- | -------- | ------ |
| Registro de usuario | [register_user.md](docs/features/register_user.md) | [002-registro-usuario](specs/002-registro-usuario/) | ✅ Implementada (backend) |
| Inicio y cierre de sesión | [user_login.md](docs/features/user_login.md) | [001-inicio-sesion-usuario](specs/001-inicio-sesion-usuario/) | ✅ Implementada (backend) |
| Crear evento | [create_event.md](docs/features/create_event.md) | — | 📝 Definida |
| Confirmar asistencia | [confirm_assistance.md](docs/features/confirm_assistance.md) | — | 📝 Definida |
| Validar asistencia | [validate_assistance.md](docs/features/validate_assistance.md) | — | 📝 Definida |
| Novedades del evento | [event_novelties.md](docs/features/event_novelties.md) | — | 📝 Definida |
| Dashboard | [dashboard.md](docs/features/dashboard.md) | — | 📝 Definida |

Hoy existe un único microservicio, [`auth-service`](src/api/auth-service/). El
servicio de eventos (`src/api/events-service/`) y la aplicación web
(`src/webapp/eventsapp-web/`) tienen su directorio creado pero aún están vacíos.

## Funcionalidad

### Implementada

**Registro de usuario** (`POST /v1/auth/register`)

- Alta con nombre, correo electrónico y contraseña; teléfono opcional.
- El correo se normaliza (sin espacios exteriores y en minúsculas) y debe ser
  único; un correo ya registrado se rechaza con `409`, también ante dos altas
  simultáneas.
- Política de contraseña: al menos 8 caracteres, una mayúscula, una minúscula,
  un dígito y un carácter especial. Se informan todas las reglas incumplidas a
  la vez.
- Longitudes máximas: nombre 100, correo 254, contraseña 128 y teléfono 20
  caracteres.
- El teléfono solo admite dígitos del 0 al 9, espacios, guiones, paréntesis y un
  `+` inicial.
- Los errores de forma de todos los campos salen juntos en una sola respuesta
  `400`; un valor que no es texto se trata como formato inválido, nunca como
  error interno.
- La contraseña se guarda con bcrypt (hash con salt) y nunca aparece en
  respuestas ni en logs.

**Inicio y cierre de sesión** (`POST /v1/auth/login`, `POST /v1/auth/logout`,
`GET /v1/auth/me`)

- Credencial de sesión JWT con expiración de 24 h.
- Mensaje de error genérico que no revela si la cuenta existe, también por
  tiempo de respuesta.
- Bloqueo de 5 minutos tras 3 intentos fallidos por combinación de cuenta y
  origen.
- El cierre de sesión revoca la credencial; un token revocado, expirado o
  inválido se trata como no autenticado.
- Registro de la fecha del último inicio de sesión.

El contrato detallado de cada endpoint, con ejemplos de petición y respuesta,
está en el [README del auth-service](src/api/auth-service/README.md).

### Planificada (MVP)

- **Crear evento:** título, descripción, fechas y ubicación; el evento nace en
  estado «programado».
- **Confirmar asistencia:** el organizador comparte un código QR y cada
  asistente confirma su asistencia y la de sus acompañantes.
- **Validar asistencia:** el personal escanea el QR del asistente el día del
  evento y registra su entrada y la de sus acompañantes.
- **Novedades del evento:** registro de incidencias (logística, seguridad,
  programación…) que pueden cambiar el estado del evento, con auditoría del
  estado anterior y el nuevo.
- **Dashboard:** resumen de próximos eventos, novedades recientes y métricas
  como asistentes confirmados.

Las mejoras posteriores al MVP (notificaciones, invitaciones, integración con
calendarios y pagos, etc.) están listadas en [docs/eventsapp.md](docs/eventsapp.md).

## Arquitectura

Microservicios con Clean Architecture en cada servicio (capas `blueprints`,
`application`, `domain` e `infrastructure`). Backend en Python con
Flask-RESTful, SQLAlchemy y PostgreSQL; frontend previsto en React. El
razonamiento y el stack completo están en [docs/tech_stack.md](docs/tech_stack.md).

| Documento | Contenido |
| --------- | --------- |
| [Diagrama de contexto (C4 nivel 1)](docs/architecture/context_diagram.md) | Actores y sistemas externos |
| [Diagrama de contenedores (C4 nivel 2)](docs/architecture/container_diagram.md) | Aplicaciones y almacenes de datos |
| [Diagrama de componentes (C4 nivel 3)](docs/architecture/component_diagram.md) | Componentes de la API |
| [Diagrama de clases](docs/architecture/class_diagram.md) | Modelo de dominio |
| [Diseño de base de datos](docs/architecture/database.md) | Modelo entidad-relación |

Los diagramas fuente en Mermaid están en [docs/diagrams/](docs/diagrams/), y los
diagramas de secuencia de cada flujo en
[docs/diagrams/sequences/](docs/diagrams/sequences/).

## Especificaciones (SDD)

El proyecto sigue desarrollo orientado a especificaciones: cada funcionalidad
pasa por spec → plan → tareas, cada fase la aprueba una persona, y cada
requisito queda trazado hasta sus pruebas (`test_F00N_R0xx_…`).

| Feature | Spec (qué y por qué) | Plan (cómo) | Tareas |
| ------- | -------------------- | ----------- | ------ |
| 001 · Inicio de sesión | [spec.md](specs/001-inicio-sesion-usuario/spec.md) | [plan.md](specs/001-inicio-sesion-usuario/plan.md) | [tasks.md](specs/001-inicio-sesion-usuario/tasks.md) |
| 002 · Registro de usuario | [spec.md](specs/002-registro-usuario/spec.md) | [plan.md](specs/002-registro-usuario/plan.md) | [tasks.md](specs/002-registro-usuario/tasks.md) |

Los documentos de [docs/features/](docs/features/) son la descripción funcional
de partida; las specs de [specs/](specs/) son el contrato verificable que se
implementa.

## Estructura del repositorio

```
.
├── collections/          Colecciones y entornos de Postman
├── docs/
│   ├── architecture/     Diagramas C4, clases y base de datos
│   ├── diagrams/         Fuentes Mermaid y diagramas de secuencia
│   ├── features/         Descripción funcional de cada feature
│   ├── eventsapp.md      Visión de producto
│   └── tech_stack.md     Stack y decisiones de arquitectura
├── specs/                Specs, planes y tareas SDD por feature
└── src/
    ├── api/
    │   ├── auth-service/     Registro y sesión (implementado)
    │   └── events-service/   Gestión de eventos (pendiente)
    ├── webapp/eventsapp-web/ Aplicación web (pendiente)
    ├── docker-compose.yml
    └── .env.example
```

## Puesta en marcha

### Con Docker

```bash
cd src
cp .env.example .env    # opcional: todas las variables tienen valor por defecto
docker compose up --build
```

Levanta PostgreSQL y el `auth-service` en `http://localhost:5000`. Comprueba que
está listo con `GET /health/ready`.

> **Importante:** `docker-compose.yml` no define `JWT_SECRET`, así que el
> servicio firma los tokens con el valor por defecto
> `change-me-in-production`. Sirve para desarrollo local; en cualquier otro
> entorno hay que definir un secreto propio.

### Pruebas del auth-service

```bash
cd src/api/auth-service
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest
```

Las pruebas usan SQLite en memoria y no necesitan base de datos ni Docker.

### Postman

En [collections/auth-service/](collections/auth-service/) hay una colección con
todos los endpoints y entornos `dev` (localhost) y `prod`.
