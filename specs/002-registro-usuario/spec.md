# Spec: Registro de usuario

| Campo  | Valor        |
| ------ | ------------ |
| ID     | `002-registro-usuario`     |
| Fecha  | 2026-10-14     |
| Estado | Approved · ba643a7f318e        |
| Issue  | —            |

> Este documento describe **qué** y **por qué**, nunca **cómo**.
> Toda decisión de implementación (librerías, esquemas, servicios) va en `plan.md`.
>
> Sustituye todo texto en cursiva; si una sección no aplica, escribe
> «No aplica.». Solo el usuario cambia el Estado, con `/sdd:approve`.

## Problema

Las funciones personalizadas de EventsApp (crear y gestionar eventos, confirmar
asistencia, guardar preferencias) necesitan saber quién es el usuario. Sin una
forma de crear una cuenta propia, **toda persona nueva** que llega a EventsApp
queda limitada a lo público desde su **primera visita**, y el inicio de sesión
(feature `001-inicio-sesion-usuario`) no tiene cuentas sobre las que operar.

## Contexto

- Fuente: `docs/features/register_user.md` (reglas de negocio y criterios
  AC-001..AC-005).
- El servicio de autenticación ya expone un registro funcional y con tests; esta
  spec formaliza ese comportamiento como contrato y fija lo que falta. La
  aplicación web aún no tiene ninguna pantalla.
- El inicio de sesión (`001`) ya está especificado e implementado y asume que el
  correo es el identificador de acceso, normalizado igual que en el registro.
- Restricción de negocio: la seguridad es atributo de calidad explícito; la
  contraseña nunca se guarda ni se transmite de vuelta en claro.

## Alcance

### Dentro

- Una persona puede crear una cuenta aportando nombre, correo electrónico y
  contraseña.
- El sistema valida los datos y explica qué está mal cuando no son válidos,
  incluidas todas las reglas de contraseña incumplidas.
- El sistema impide que dos cuentas compartan correo electrónico.
- La contraseña se almacena de forma irreversible y protegida.
- La persona recibe confirmación de que su cuenta se creó.
- La cuenta recién creada sirve para iniciar sesión con esas mismas credenciales.

### Fuera (non-goals)

- Inicio de sesión, cierre de sesión y gestión de la credencial de sesión
  (cubiertos por `001-inicio-sesion-usuario`).
- Inicio de sesión automático tras registrarse.
- Verificación del correo electrónico (enlace o código de confirmación).
- Registro con proveedores externos (Google, redes sociales, SSO).
- CAPTCHA u otra protección anti-bots en el registro.
- Edición del perfil, cambio de contraseña, recuperación de contraseña y baja de
  la cuenta.
- Roles o permisos de la cuenta creada.
- Formulario o pantalla de registro en la aplicación web (irá en una feature de
  frontend aparte; esta feature cubre solo el contrato del servicio).

## Requisitos

Notación EARS. Cada requisito lleva un ID estable que se referencia después en
`plan.md`, `tasks.md` y en los tests.

| ID   | Prioridad | Requisito |
| ---- | --------- | --------- |
| R001 | MUST      | CUANDO una persona envía nombre, correo electrónico y contraseña válidos y el correo no pertenece a ninguna cuenta, el sistema DEBERÁ crear una cuenta nueva con esos datos. |
| R002 | MUST      | SI falta el nombre, el correo electrónico o la contraseña, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar cada campo obligatorio ausente. |
| R003 | MUST      | SI el correo electrónico no tiene un formato de dirección válido, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar que el formato del correo es inválido. |
| R004 | MUST      | SI la contraseña no tiene al menos 8 caracteres, una letra mayúscula, una letra minúscula, un dígito y un carácter especial, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar todas las reglas incumplidas a la vez. |
| R005 | MUST      | SI el correo electrónico ya pertenece a una cuenta, ENTONCES el sistema DEBERÁ rechazar el registro sin crear ni modificar ninguna cuenta, indicando explícitamente que el correo electrónico ya está registrado. |
| R006 | MUST      | El sistema DEBERÁ tratar como el mismo correo electrónico dos direcciones que solo difieren en mayúsculas/minúsculas o en espacios al principio o al final, tanto al comprobar la unicidad como al guardarlo. |
| R007 | MUST      | SI llegan a la vez dos solicitudes de registro con el mismo correo electrónico, ENTONCES el sistema DEBERÁ crear como máximo una cuenta y rechazar la otra como correo ya registrado. |
| R008 | MUST      | El sistema DEBERÁ almacenar la contraseña de forma que no pueda recuperarse en claro y que dos cuentas con la misma contraseña no produzcan el mismo valor almacenado. |
| R009 | MUST      | El sistema NO DEBERÁ incluir la contraseña, ni su valor almacenado, en ninguna respuesta ni en los registros (logs) del sistema. |
| R010 | MUST      | CUANDO se crea la cuenta, el sistema DEBERÁ confirmar el registro exitoso devolviendo el identificador de la cuenta, el nombre y el correo electrónico normalizado. |
| R011 | MUST      | CUANDO una cuenta se ha creado, el sistema DEBERÁ permitir iniciar sesión con el correo electrónico y la contraseña usados en el registro. |
| R012 | MUST      | SI la petición de registro no es interpretable como datos estructurados, ENTONCES el sistema DEBERÁ rechazarla sin crear la cuenta. |
| R014 | COULD     | DONDE la persona aporte un teléfono, el sistema DEBERÁ guardarlo como dato opcional de la cuenta. |
| R015 | MUST      | SI el nombre supera 100 caracteres, el correo electrónico supera 254 caracteres o la contraseña supera 128 caracteres, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar cada campo que excede su longitud máxima. |
| R016 | MUST      | SI se aporta un teléfono que, sin espacios al principio ni al final, supera 20 caracteres, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar que el teléfono excede su longitud máxima, junto a los demás errores de forma (campo ausente, formato, tipo o longitud) de la misma petición. |
| R017 | MUST      | SI se aporta un teléfono que contiene caracteres distintos de dígitos del 0 al 9, espacios, guiones, paréntesis y un «+» opcional como primer carácter, o que no contiene ningún dígito del 0 al 9, ENTONCES el sistema DEBERÁ rechazar el registro sin crear la cuenta e indicar que el formato del teléfono es inválido, junto a los demás errores de forma (campo ausente, formato, tipo o longitud) de la misma petición. |

## Criterios de aceptación

### R001

- **Dado** un correo que no pertenece a ninguna cuenta **cuando** se registra con nombre «Ana», ese correo y la contraseña `Abcd123!` **entonces** existe exactamente una cuenta nueva con ese nombre y correo.
- **Dado** un nombre con espacios al principio o al final **cuando** se registra **entonces** la cuenta guarda el nombre sin esos espacios.

### R002

- **Dado** una petición sin nombre **cuando** se envía **entonces** se rechaza con un error de validación que menciona el nombre y no se crea ninguna cuenta.
- **Dado** una petición sin nombre ni contraseña **cuando** se envía **entonces** el error menciona ambos campos en la misma respuesta.
- **Dado** un nombre formado solo por espacios **cuando** se envía **entonces** se trata como nombre ausente.

### R003

- **Dado** el correo `ana@ejemplo` (sin dominio de nivel superior) o `ana ejemplo.com` **cuando** se registra **entonces** se rechaza indicando formato de correo inválido y no se crea ninguna cuenta.

### R004

- **Dado** la contraseña `weak` **cuando** se registra **entonces** se rechaza y la respuesta enumera, a la vez, longitud, mayúscula, dígito y carácter especial como reglas incumplidas.
- **Dado** la contraseña `Abcdefg1` (sin carácter especial) **cuando** se registra **entonces** se rechaza indicando solo la regla del carácter especial.
- **Dado** la contraseña `Abcd123!` (exactamente 8 caracteres y cumple todo) **cuando** se registra **entonces** se acepta.

### R005

- **Dado** una cuenta existente con `ana@example.com` **cuando** otra persona intenta registrarse con ese mismo correo **entonces** se rechaza como correo ya registrado y la cuenta existente conserva su nombre y contraseña.

### R006

- **Dado** una cuenta existente con `ana@example.com` **cuando** alguien se registra con `  ANA@Example.com ` **entonces** se rechaza como correo ya registrado.
- **Dado** un registro con `  Ana@Example.COM ` sobre un correo libre **cuando** se crea la cuenta **entonces** el correo guardado y devuelto es `ana@example.com`.

### R007

- **Dado** dos solicitudes de registro concurrentes con el mismo correo libre **cuando** el sistema las procesa **entonces** existe una única cuenta con ese correo y una de las dos solicitudes recibe el rechazo por correo ya registrado.

### R008

- **Dado** dos cuentas registradas con la misma contraseña **cuando** se inspecciona lo almacenado **entonces** el valor guardado para cada una es distinto y ninguno coincide con la contraseña en claro.

### R009

- **Dado** un registro exitoso o rechazado **cuando** se revisan la respuesta y los logs generados **entonces** no aparecen ni la contraseña en claro ni su valor almacenado.

### R010

- **Dado** un registro exitoso **cuando** se recibe la respuesta **entonces** indica éxito e incluye identificador, nombre y correo normalizado de la cuenta.

### R011

- **Dado** una cuenta recién registrada con `Ana@Example.com` y `Abcd123!` **cuando** se inicia sesión con `ana@example.com` y `Abcd123!` **entonces** el inicio de sesión tiene éxito según `001-inicio-sesion-usuario`.

### R012

- **Dado** un cuerpo de petición que es texto plano, o datos estructurados con sintaxis inválida, o una lista en lugar de un conjunto de campos **cuando** se envía **entonces** se rechaza como petición inválida y no se crea ninguna cuenta.

### R014

- **Dado** un registro válido con teléfono **cuando** se crea la cuenta **entonces** el teléfono queda guardado y se devuelve en la confirmación.
- **Dado** un registro válido sin teléfono **cuando** se crea la cuenta **entonces** la cuenta se crea igualmente sin teléfono.
- **Dado** un registro válido con el teléfono vacío o formado solo por espacios **cuando** se crea la cuenta **entonces** se trata como no aportado y la cuenta queda sin teléfono.

### R015

- **Dado** un nombre de exactamente 100 caracteres, un correo de exactamente 254 y una contraseña válida de exactamente 128 **cuando** se registra **entonces** se acepta.
- **Dado** un nombre de 101 caracteres **cuando** se registra **entonces** se rechaza indicando que el nombre excede la longitud máxima y no se crea ninguna cuenta.
- **Dado** un correo de 255 caracteres y una contraseña de 129 **cuando** se registra **entonces** el error menciona ambos campos en la misma respuesta.
- **Dado** un nombre de 100 caracteres seguido de espacios **cuando** se registra **entonces** la longitud se mide tras quitar los espacios exteriores y se acepta.

### R016

- **Dado** un registro válido con el teléfono `+34 (600) 123-45-678` (exactamente 20 caracteres) **cuando** se registra **entonces** se acepta y el teléfono queda guardado.
- **Dado** un registro con un teléfono de 21 caracteres **cuando** se registra **entonces** se rechaza indicando que el teléfono excede la longitud máxima y no se crea ninguna cuenta.
- **Dado** un teléfono de 21 caracteres y un nombre de 101 **cuando** se registra **entonces** el error menciona ambos campos en la misma respuesta.
- **Dado** un teléfono de 20 caracteres rodeado de espacios **cuando** se registra **entonces** la longitud se mide sin esos espacios y se acepta.
- **Dado** un teléfono de 21 caracteres y la contraseña `weak` **cuando** se registra **entonces** el rechazo menciona el teléfono; las reglas de contraseña incumplidas (R004) no tienen por qué aparecer en esa misma respuesta, porque solo se evalúan cuando no hay errores de forma.

### R017

- **Dado** los teléfonos `600123456`, `+34 600 123 456` y `(91) 555-12-34` **cuando** se registra cada uno **entonces** se aceptan.
- **Dado** el teléfono `abc` o `600-ABC-123` **cuando** se registra **entonces** se rechaza indicando formato de teléfono inválido y no se crea ninguna cuenta.
- **Dado** el teléfono `600+123` (un «+» que no está al principio) o `++34600` **cuando** se registra **entonces** se rechaza por formato inválido.
- **Dado** el teléfono `( - )` (sin ningún dígito) **cuando** se registra **entonces** se rechaza por formato inválido.
- **Dado** un teléfono escrito con dígitos de otro sistema de numeración, como `٦٠٠١٢٣٤٥٦` (dígitos arábigo-índicos) **cuando** se registra **entonces** se rechaza por formato inválido.
- **Dado** un teléfono `abc` y un correo sin formato válido **cuando** se registra **entonces** el error menciona ambos campos en la misma respuesta.

## Requisitos no funcionales

- **Latencia**: CUANDO el sistema recibe una solicitud de registro, DEBERÁ
  responder en menos de 1 s en el percentil 95 bajo carga nominal esperada (el
  almacenamiento seguro de la contraseña tiene un coste deliberado).
- **Privacidad**: la contraseña en claro nunca se persiste ni se escribe en logs
  (refuerza R008 y R009).
- **Riesgo aceptado — enumeración de cuentas**: el rechazo explícito de R005
  permite averiguar si un correo tiene cuenta. Se acepta a sabiendas, aunque el
  login (`001`, R002) no lo revela; el registro prioriza la claridad para el
  usuario.

## Supuestos

- El correo electrónico es el único identificador de acceso; no existe un
  «nombre de usuario» separado.
- La cuenta queda activa al crearse, sin paso de verificación (ver non-goals).
- El conjunto de caracteres especiales aceptado incluye al menos `! @ # $ % ^ & *`
  y los signos de puntuación ASCII habituales.
- El registro es público: no requiere sesión previa.

## Preguntas abiertas

> Cita entre paréntesis el requisito al que afecta cada pregunta:
> `- [ ] (R002) ¿Cuánto dura la sesión?`. Una pregunta abierta sobre un MUST
> impide aprobar la spec. Al resolverla, conviértela en requisito o criterio y
> borra la línea.

Ninguna. Las cuatro preguntas se resolvieron en `/sdd:clarify` (2026-10-14):
rechazo explícito del correo duplicado con el riesgo de enumeración aceptado
(R005), formulario web fuera de alcance, teléfono opcional (R014) y longitudes
máximas 100/254/128 (R015). En un segundo `/sdd:clarify` se fijó el contenido
válido del teléfono (R017) y que un teléfono vacío equivale a no aportarlo
(R014).

## Historial de cambios

> Lo rellena `/sdd:amend` cuando cambian los requisitos después de aprobar la
> spec: fecha, qué cambió, por qué y los IDs afectados.

- **2026-10-14** — Se añade **R016** (MUST): longitud máxima de 20 caracteres
  para el teléfono opcional, medida sin espacios exteriores y reportada junto a
  los demás campos inválidos. **Por qué:** durante `/sdd:plan` se detectó que
  R014 no fijaba un máximo y que un teléfono largo produciría un error 500 en
  PostgreSQL (columna de 50) en lugar de un rechazo de validación. 20 caracteres
  admite E.164 (15 dígitos y «+») más separadores. **IDs afectados:** R016
  (nuevo); R014 sin cambios.

- **2026-10-14** — Se añade **R017** (MUST): el teléfono solo admite dígitos,
  espacios, guiones, paréntesis y un «+» inicial, con al menos un dígito. Se
  añade a R014 un criterio que aclara que un teléfono vacío o solo con espacios
  equivale a no aportarlo (aclaración del comportamiento actual, mismo ID).
  **Por qué:** `/sdd:clarify` detectó que la spec no definía qué es un teléfono
  válido y hoy se aceptaría cualquier texto. **IDs afectados:** R017 (nuevo);
  R014 (criterio añadido, sin cambio de comportamiento).

- **2026-10-14** — Aclaraciones sin cambio de comportamiento, a raíz de
  `/sdd:analyze`. **R016 y R017:** «junto a los demás campos inválidos» pasa a
  «junto a los demás errores de forma (campo ausente, formato, tipo o
  longitud)», y se añade a R016 un criterio que lo ilustra: la política de
  contraseña (R004) y el correo duplicado (R005) se evalúan después y no tienen
  por qué salir en la misma respuesta. **R017:** «dígitos» pasa a «dígitos del 0
  al 9», con un criterio que rechaza dígitos de otros sistemas de numeración.
  **R012:** el criterio deja de mencionar el formato concreto de transporte.
  **Por qué:** la redacción anterior contradecía literalmente la validación por
  fases del plan, dejaba el conjunto de dígitos a interpretación y metía un
  detalle de implementación en la spec. **IDs afectados:** R012, R016, R017
  (mismo ID; ninguna prueba prevista cambia).
