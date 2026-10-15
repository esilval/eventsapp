# Plan: Registro de usuario

| Campo  | Valor              |
| ------ | ------------------ |
| Spec   | `spec.md`          |
| Fecha  | 2026-10-14         |
| Estado | Approved · 452454615d65              |

> Este documento describe **cómo**. Si aquí aparece un requisito nuevo que no
> está en `spec.md`, el sitio correcto es `spec.md`, no aquí.
>
> Sustituye todo texto en cursiva; si una sección no aplica, escribe
> «No aplica.». Solo el usuario cambia el Estado, con `/sdd:approve`.

## Resumen

El registro ya existe en `auth-service` (`POST /v1/auth/register`, Flask +
Clean Architecture) y cumple casi toda la spec. Esta feature **cierra los
huecos** sin rediseñar nada: añade la validación de longitudes máximas (R015)
y de longitud y formato del teléfono (R016, R017),
endurece la entrada frente a valores no textuales (R002/R003/R012) y completa la
batería de pruebas para que cada requisito tenga una prueba que lo nombre
(R005–R011, en especial la carrera de R007 y la ausencia de la contraseña en
logs de R009). La decisión clave es mantener **toda la validación de forma en
una única pasada del caso de uso**, para que un mismo rechazo enumere todos los
campos inválidos a la vez, como exigen los criterios de R002, R015, R016 y R017.

## Comprobación de constitución

No aplica. El proyecto no tiene `specs/constitution.md`.

## Decisiones

### D1 — Longitudes máximas en la validación básica del caso de uso

- **Contexto:** R015 exige rechazar nombre > 100, correo > 254 y contraseña
  > 128, e indicar **todos** los campos excedidos en la misma respuesta (criterio
  «correo de 255 y contraseña de 129»). Hoy `RegisterUserUseCase` valida en tres
  fases que se cortan en la primera que falla: campos básicos
  (`ValidationError`), política de contraseña (`WeakPasswordError`) y unicidad.
- **Decisión:** añadir las tres comprobaciones de longitud a
  `_validate_basic_fields`, con constantes de módulo `NAME_MAX_LENGTH = 100`,
  `EMAIL_MAX_LENGTH = 254` y `PASSWORD_MAX_LENGTH = 128`. Se mide tras la
  normalización que ya hace el caso de uso: nombre y correo sin espacios
  exteriores (criterio de R015 sobre el nombre con espacios), contraseña tal
  cual. La longitud es `len()` de Python (puntos de código), que es lo que la
  spec llama «caracteres». Un campo que excede el máximo no se evalúa además
  contra la política de contraseña: la respuesta es un `ValidationError` (HTTP
  400) con un detalle por campo.
- **Alternativas descartadas:** *(a)* poner el máximo de la contraseña en
  `utils/password_policy.py`: sería reutilizable en un futuro cambio de
  contraseña, pero el exceso de longitud saldría en un `WeakPasswordError`
  separado y nunca en la misma respuesta que un correo demasiado largo,
  incumpliendo el criterio de R015. *(b)* delegar en el tamaño de columna de la
  BD (`String(255)`): SQLite no lo aplica y en PostgreSQL produce un error 500,
  no un 400 con detalle.
- **Consecuencias:** la «única pasada» cubre los **errores de forma** (campo
  ausente, formato, tipo y longitud), que es exactamente lo que la spec pide
  agrupar en R002, R015, R016 y R017. La política de contraseña (R004) y el
  correo duplicado (R005) se evalúan después, solo si no hay errores de forma,
  como aclara el criterio de R016. La comprobación de longitud ocurre **antes** de hashear,
  así que una contraseña enorme ya no consume CPU de bcrypt. Si en el futuro hay
  cambio de contraseña, habrá que reutilizar la constante desde aquí o moverla.

### D2 — Valores no textuales se rechazan como campo inválido

- **Contexto:** el recurso pasa `payload.get(...)` sin comprobar el tipo. Un
  JSON válido como `{"name": 123, ...}` hace que `.strip()` lance
  `AttributeError` y el servicio responde 500, lo que contradice R002/R003 y el
  espíritu de R012 (rechazar lo que no se puede interpretar sin romperse).
- **Decisión:** en el caso de uso, normalizar cada campo con una función
  auxiliar `_as_text(value) -> str | None` que devuelve `None` si el valor no es
  `str`. Un valor no textual se reporta con **el mismo mensaje de formato que un
  texto mal formado** de ese campo (ver «Mensajes de formato» abajo), dentro del
  mismo `ValidationError`; un campo ausente o vacío sigue reportándose como
  obligatorio. Para `phone` (R014), un valor no textual también es un error de
  validación, y no se le aplican además las comprobaciones de longitud y
  formato de D7: sale un solo mensaje.
- **Mensajes de formato:** un diccionario de módulo `_FORMAT_ERRORS` fija una
  frase por campo con su artículo correcto, siempre con la forma «… no tiene un
  formato válido.»: «El nombre …», «El correo electrónico …» (el mensaje que ya
  existe hoy), «La contraseña …» y «El teléfono …». Así el cliente recibe la
  misma frase para `{"phone": 600123456}` que para `{"phone": "abc"}`, y no se
  genera texto con plantillas del tipo «El \<campo\>», que producían «El
  contraseña». El cuerpo no-JSON o no-objeto
  ya se rechaza en el recurso (R012) y no cambia.
- **Alternativas descartadas:** *(a)* convertir con `str(value)`: aceptaría
  `{"password": 12345678}` como texto y escondería errores del cliente. *(b)*
  validar tipos en el blueprint: dispersa la validación en dos capas y el
  mensaje no saldría en la lista única de detalles. *(c)* un mensaje distinto
  para el error de tipo («tiene un tipo inválido»): es más preciso para quien
  depura, pero el cliente final no distingue entre ambos casos y duplicaría
  frases sin aportar acción distinta.
- **Consecuencias:** los DTOs siguen tipados como `str`, pero el caso de uso ya
  no confía en ello; se documenta en el docstring.

### D3 — El rechazo por correo duplicado se mantiene explícito (409)

- **Contexto:** la spec aceptó, con el riesgo documentado, que R005 diga
  explícitamente que el correo ya está registrado.
- **Decisión:** mantener `EmailAlreadyRegisteredError` → HTTP 409 con el
  mensaje «El correo electrónico ya está registrado.». La comprobación de
  unicidad sigue siendo la **última** fase: solo se revela la existencia de una
  cuenta cuando el resto de la petición es válida.
- **Alternativas descartadas:** responder 201 indistinguible: descartado en
  `/sdd:clarify` porque requiere notificar por correo, fuera de alcance.
- **Consecuencias:** se puede averiguar si un correo tiene cuenta; queda como
  riesgo aceptado en la spec y en la tabla de riesgos.

### D4 — Carrera de duplicados: la restricción única de la BD es la garantía

- **Contexto:** R007 exige que como máximo se cree una cuenta con dos registros
  simultáneos. La comprobación `get_by_email` del caso de uso no basta por sí
  sola (comprobar y luego insertar no es atómico).
- **Decisión:** no se cambia el código: `users.email` ya tiene `unique=True` y
  `SqlAlchemyUserRepository.add` traduce `IntegrityError` a
  `EmailAlreadyRegisteredError` tras el `rollback`. Se añaden pruebas que
  ejercitan ese camino: a nivel de repositorio (insertar dos `User` con el mismo
  correo) y a nivel de endpoint simulando que la lectura previa no ve la fila
  (un repositorio cuyo `get_by_email` devuelve `None` pero cuya inserción choca
  con la restricción), comprobando que se responde 409 y queda una sola fila.
- **Alternativas descartadas:** *(a)* bloqueo explícito (`SELECT … FOR UPDATE`
  o un lock de aplicación): no protege contra una fila que aún no existe y
  añade contención. *(b)* prueba con hilos reales sobre SQLite in-memory: el
  pool de conexiones de SQLite en memoria no comparte bien entre hilos y la
  prueba sería intermitente.
- **Consecuencias:** la garantía depende de que la restricción única exista en
  el esquema de producción; las migraciones deben mantenerla.

### D5 — Hash de contraseña: se mantiene bcrypt y se acepta el corte a 72 bytes

- **Contexto:** R008 exige un almacenamiento irrecuperable y con salt; bcrypt
  (passlib, 12 rondas) ya lo cumple. Al planificar R015 se comprobó que bcrypt
  **solo usa los primeros 72 bytes** de la contraseña: dos contraseñas que
  coinciden en esos 72 bytes verifican igual. Con 128 caracteres (y más bytes
  si hay caracteres no ASCII) se aceptan contraseñas cuyo final no aporta
  seguridad. Tampoco da error: lo trunca en silencio.
- **Decisión:** mantener bcrypt sin cambios en esta feature. 72 bytes son
  muchísima más entropía de la que exige la política (8 caracteres), registro y
  login truncan de forma coherente (R011 se cumple), y ningún requisito de la
  spec se incumple. Se documenta como riesgo técnico.
- **Alternativas descartadas:** *(a)* prehash SHA-256/HMAC + base64 antes de
  bcrypt: elimina el límite, pero cambia el formato de los hashes ya guardados
  y obliga a tocar la verificación del login (feature 001) con un esquema
  versionado. *(b)* migrar a Argon2id con `CryptContext` y rehash en el login:
  es la mejora correcta a medio plazo, pero amplía el alcance a la 001 y añade
  una dependencia. Ambas pueden hacerse luego en una feature de endurecimiento.
- **Consecuencias:** el máximo efectivo de la contraseña es de 72 bytes, aunque
  la API acepte 128 caracteres. El warning conocido de passlib 1.7.4 con
  bcrypt 4.x sigue diferido y fuera de esta feature.

### D6 — Prueba de R009 sobre respuestas y logs

- **Contexto:** R009 prohíbe que la contraseña o su hash aparezcan en respuestas
  o logs. El servicio hoy no escribe logs propios, pero Flask, werkzeug y
  SQLAlchemy sí pueden hacerlo (por ejemplo `echo=True` imprime los parámetros
  de las sentencias SQL).
- **Decisión:** prueba de endpoint con `caplog` a nivel `DEBUG` sobre todos los
  loggers, que registra una cuenta y provoca un rechazo, y comprueba que ni la
  contraseña en claro ni el hash guardado aparecen en ningún registro ni en el
  cuerpo de la respuesta. Se verifica también que `create_db_engine` no activa
  `echo`.
- **Alternativas descartadas:** un filtro de logging que oculte campos
  `password`: es defensa en profundidad útil, pero no hace falta mientras nadie
  registre el payload y añade código sin un caso real que proteger.
- **Consecuencias:** si alguien añade más adelante un log del cuerpo de la
  petición, esta prueba lo detecta.

### D7 — Teléfono: longitud y formato en la misma pasada de validación

- **Contexto:** R016 fija un máximo de 20 caracteres medidos sin espacios
  exteriores; R017 limita el contenido a dígitos, espacios, guiones, paréntesis
  y un «+» inicial, con al menos un dígito. Ambos exigen que el error salga junto
  a los de los demás campos. R014 aclara que un teléfono vacío o solo con
  espacios equivale a no aportarlo, que es lo que ya hace el caso de uso.
- **Decisión:** dentro de `_validate_basic_fields`, que pasa a recibir también
  el teléfono ya normalizado (`strip()` y `None` si queda vacío):
  1. si `phone` es `None`, no se valida nada más (R014);
  2. si supera `PHONE_MAX_LENGTH = 20`, se añade «El teléfono no puede superar
     20 caracteres.» (R016);
  3. si no casa con `_PHONE_RE = re.compile(r"^\+?[0-9 ()\-]+$")` o no contiene
     ningún dígito ASCII (`re.search(r"[0-9]", phone)`), se añade el mensaje de formato del teléfono de `_FORMAT_ERRORS`, «El
     teléfono no tiene un formato válido.» (R017). La spec fija «dígitos del 0
     al 9», de ahí `[0-9]`.
  Las dos comprobaciones son independientes: un teléfono de 25 letras recibe
  ambos mensajes. Se usa `[0-9]` y no `\d` porque en Python `\d` acepta
  dígitos Unicode (árabes, devanagari…) que la spec no contempla.
- **Alternativas descartadas:** *(a)* normalizar el teléfono a E.164 con una
  librería como `phonenumbers`: valida números reales por país, pero la spec
  pide un filtro de caracteres, no validez telefónica, y añade una dependencia
  pesada. *(b)* guardar el teléfono sin separadores (solo dígitos y «+»): es
  una decisión de producto que la spec no toma; se guarda tal cual, recortado.
  *(c)* una regex que también exija al menos un dígito (`(?=.*[0-9])`): funciona,
  pero es menos legible que una comprobación aparte.
- **Consecuencias:** la columna `phone String(50)` sobra de margen para 20
  caracteres; no hace falta migración. Las cuentas ya existentes con teléfonos
  que no cumplan R016/R017 no se tocan: la validación solo aplica en el alta.

## Componentes afectados

| Componente | Cambio | Requisitos que cubre |
| ---------- | ------ | -------------------- |
| `app/application/register_user.py` | Constantes de longitud máxima; `_as_text` para tolerar tipos no textuales; `_validate_basic_fields` añade longitudes y errores de tipo en una única lista de detalles; validación de longitud y formato del teléfono (D7); docstring actualizado a los IDs de la spec 002 | R001, R002, R003, R012, R014, R015, R016, R017 |
| `app/blueprints/auth.py` | Sin cambios funcionales; docstring de `RegisterResource` pasa a citar los IDs de la spec 002 | R005, R010, R012 |
| `app/infrastructure/user_repository.py` | Sin cambios (la traducción de `IntegrityError` ya cubre la carrera) | R007 |
| `app/infrastructure/password_hasher.py` | Sin cambios; comentario sobre el límite de 72 bytes de bcrypt (D5) | R008 |
| `tests/test_register_use_case.py` | Nuevas pruebas `test_F002_R0xx_*` de longitudes, tipos, normalización, teléfono, campos múltiples y política | R001, R002, R003, R004, R005, R006, R014, R015, R016, R017 |
| `tests/test_register_endpoint.py` | Nuevas pruebas HTTP de detalles por campo, 409 con mayúsculas, carrera, respuesta sin contraseña, logs, cuerpo inválido y límites | R002, R005, R006, R007, R009, R010, R012, R015 |
| `tests/test_user_repository.py` | Prueba de inserción duplicada → `EmailAlreadyRegisteredError` y una sola fila | R007 |
| `tests/test_password_hasher.py` (nuevo) | Mismo texto → hashes distintos; ninguno igual al texto; verificación correcta | R008 |
| `tests/test_register_then_login.py` (nuevo) | Registro con correo en mayúsculas y login con el correo en minúsculas por HTTP | R011 |

## Modelo de datos

Sin cambios de esquema. Las columnas actuales (`name String(255)`,
`email String(255) UNIQUE`, `password String(255)`, `phone String(50)`) ya
admiten los máximos de R015 y R016. La restricción única de `users.email` es la base de
R007 (D4) y debe conservarse en cualquier migración.

## Contratos

`POST /v1/auth/register` mantiene su contrato; solo se añaden mensajes de
detalle.

- **Petición:** `{ "name": str, "email": str, "password": str, "phone"?: str }`.
- **201** — `{ "message": "Usuario registrado exitosamente.", "user": { "id", "name", "email", "phone" } }` (R010, R014). Nunca incluye `password` ni el hash (R009).
- **400** — `{ "error": str, "details": [str, ...] }` para:
  - cuerpo no JSON o no objeto (R012), sin `details`;
  - campos ausentes, formato o tipo inválido y longitudes excedidas, un detalle por problema (R002, R003, R012, R015, R016, R017);
  - política de contraseña, un detalle por regla incumplida (R004).
- **409** — `{ "error": "El correo electrónico ya está registrado." }` (R005, R006, R007).

Mensajes de detalle nuevos o unificados:

| Caso | Mensaje |
| ---- | ------- |
| Nombre > 100 (R015) | «El nombre no puede superar 100 caracteres.» |
| Correo > 254 (R015) | «El correo electrónico no puede superar 254 caracteres.» |
| Contraseña > 128 (R015) | «La contraseña no puede superar 128 caracteres.» |
| Teléfono > 20 (R016) | «El teléfono no puede superar 20 caracteres.» |
| Nombre no textual (D2) | «El nombre no tiene un formato válido.» |
| Correo no textual (D2) o mal formado (R003) | «El correo electrónico no tiene un formato válido.» (sin cambios) |
| Contraseña no textual (D2) | «La contraseña no tiene un formato válido.» |
| Teléfono no textual (D2) o mal formado (R017) | «El teléfono no tiene un formato válido.» |

## Estrategia de pruebas

| Requisito | Tipo de prueba | Dónde vive |
| --------- | -------------- | ---------- |
| R001 | unitaria (nombre con espacios recortado) + integración (201 y cuenta creada) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R002 | unitaria (nombre solo espacios; nombre y contraseña ausentes en un solo error) + integración (400 con detalles) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R003 | unitaria parametrizada (`ana@ejemplo`, `ana ejemplo.com`) | `tests/test_register_use_case.py` |
| R004 | unitaria (`weak` → 4 reglas; `Abcdefg1` → solo especial; `Abcd123!` aceptada) | `tests/test_register_use_case.py`, `tests/test_password_policy.py` |
| R005 | unitaria (la cuenta existente conserva nombre y hash) + integración (409 con mensaje) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R006 | unitaria (guardado como `ana@example.com`) + integración (`  ANA@Example.com ` → 409) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R007 | integración (repositorio: duplicado → excepción y una fila; endpoint: lectura previa ciega → 409 y una fila) | `tests/test_user_repository.py`, `tests/test_register_endpoint.py` |
| R008 | integración con bcrypt real | `tests/test_password_hasher.py` |
| R009 | integración con `caplog` DEBUG + inspección del cuerpo | `tests/test_register_endpoint.py` |
| R010 | integración (id, nombre y correo normalizado en el 201) | `tests/test_register_endpoint.py` |
| R011 | integración end-to-end registro → login | `tests/test_register_then_login.py` |
| R012 | integración (texto plano, JSON mal formado, array, campo numérico → 400 y ninguna cuenta) | `tests/test_register_endpoint.py` |
| R014 | unitaria (con y sin teléfono; vacío o solo espacios → sin teléfono; no textual → error) | `tests/test_register_use_case.py` |
| R015 | unitaria (límites exactos aceptados, 101/255/129 rechazados, varios campos en un solo error, nombre de 100 caracteres con espacios aceptado) + integración (400) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R016 | unitaria (20 aceptado, 21 rechazado, 20 con espacios aceptado, teléfono de 21 + nombre de 101 en un solo error) + integración (400) | `tests/test_register_use_case.py`, `tests/test_register_endpoint.py` |
| R017 | unitaria parametrizada (válidos: `600123456`, `+34 600 123 456`, `(91) 555-12-34`; inválidos: `abc`, `600-ABC-123`, `600+123`, `++34600`, `( - )`, dígitos no ASCII) + teléfono y correo inválidos en un solo error | `tests/test_register_use_case.py` |

Requisito no funcional de latencia (p95 < 1 s): no se automatiza en la suite.
Referencia medida: un hash bcrypt de 12 rondas tarda unos 0,26 s en local, lo
que deja margen. Se valida manualmente si cambian las rondas.

## Riesgos técnicos

| Riesgo | Impacto | Mitigación |
| ------ | ------- | ---------- |
| bcrypt usa solo los primeros 72 bytes de la contraseña (D5) | Medio: la parte de la contraseña que pasa de 72 bytes no aporta seguridad | Documentado; migrar a Argon2id o a prehash en una feature de endurecimiento posterior |
| Enumeración de cuentas por el 409 (D3) | Medio: se puede averiguar si un correo tiene cuenta | Riesgo aceptado en la spec; la unicidad se comprueba al final; mitigable más adelante con limitación de tasa en el registro |
| Teléfonos ya guardados que no cumplen R016/R017 | Bajo: quedan datos heredados fuera de la nueva regla | La validación solo aplica en el alta (D7); limpiarlos, si hace falta, es otra feature |
| Sin limitación de tasa en el registro | Bajo-medio: altas masivas y CPU de bcrypt | Fuera de alcance (non-goal de anti-bots); la longitud máxima (D1) al menos acota el coste por petición |
| Warning passlib 1.7.4 / bcrypt 4.x | Bajo: ruido en los logs de la suite | Diferido, fuera de esta feature |

## Trazabilidad

Todos los requisitos MUST de la spec (R001–R012, R015, R016 y R017) aparecen en
la tabla de componentes y en la de pruebas. R014 (COULD) también tiene cobertura. El hueco en
la numeración es intencionado: ese requisito (formulario web) se eliminó en
`/sdd:clarify`. No queda ningún MUST sin cobertura.

Convención de nombres: como los IDs `R0xx` se repiten entre features, las
pruebas nuevas se llaman `test_F002_R0xx_<descripción>` para que `sdd trace` las
atribuya a esta feature y no a la 001.
