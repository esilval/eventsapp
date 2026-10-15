# Spec: inicio de sesión de usuario

| Campo  | Valor        |
| ------ | ------------ |
| ID     | `001-inicio-sesion-usuario`     |
| Fecha  | 2026-08-12     |
| Estado | Draft        |
| Issue  | _(opcional)_ |

> Este documento describe **qué** y **por qué**, nunca **cómo**.
> Toda decisión de implementación (librerías, esquemas, servicios) va en `plan.md`.

## Problema

Hoy un usuario puede registrarse en EventsApp (`POST /v1/auth/register` ya
existe), pero no tiene ninguna forma de volver a identificarse en visitas
posteriores. Sin inicio de sesión, ninguna función personalizada (crear y
gestionar eventos, confirmar asistencia, ver el dashboard) puede saber quién es
el usuario ni restringir el acceso a sus datos. Le duele a **todo usuario
registrado** en **cada visita**: sin autenticación, la cuenta que creó no sirve
para nada.

## Contexto

- Ya existe un servicio de autenticación con el registro de usuarios resuelto.
  La entidad de usuario del dominio ya contempla un campo de "último inicio de
  sesión" y el mecanismo de contraseñas ya expone una operación de verificación,
  lo que indica que el login estaba previsto desde el diseño.
- Las contraseñas se almacenan como hash con salt; nunca se guarda ni se
  transmite la contraseña en claro (regla heredada del registro).
- EventsApp es una aplicación web con backend en microservicios. El resto de
  features (crear evento, confirmar asistencia, dashboard) asumen que existe un
  usuario autenticado.
- Restricción de negocio: la seguridad es un atributo de calidad explícito del
  producto; el login debe proteger contra ataques de fuerza bruta y no filtrar
  qué cuentas existen.

## Alcance

### Dentro

- Un usuario registrado puede autenticarse presentando su correo electrónico y
  contraseña.
- El sistema responde de forma distinguible entre credenciales correctas e
  incorrectas, sin revelar cuál de los dos campos falló.
- Tras autenticarse, el usuario recibe una credencial de sesión que le permite
  acceder a las funciones personalizadas.
- El usuario puede cerrar sesión, invalidando su sesión activa.
- El sistema protege el login contra intentos repetidos de fuerza bruta.
- El sistema registra el momento del último inicio de sesión exitoso.

### Fuera (non-goals)

- Registro de usuarios (ya cubierto por `docs/features/register_user.md`).
- Recuperación o restablecimiento de contraseña olvidada.
- Verificación de correo electrónico antes del primer login.
- Inicio de sesión con proveedores externos (Google, redes sociales, SSO).
- Autenticación de segundo factor (MFA/2FA).
- Autorización por roles o permisos (qué puede hacer cada usuario una vez dentro).
- Funcionalidad "recordarme" / sesiones persistentes de larga duración.

## Requisitos

Notación EARS. Cada requisito lleva un ID estable que se referencia después en
`plan.md`, `tasks.md` y en los tests.

| ID   | Prioridad | Requisito |
| ---- | --------- | --------- |
| R001 | MUST      | CUANDO un usuario envía un correo electrónico y una contraseña que coinciden con una cuenta existente, el sistema DEBERÁ autenticarlo y emitir una credencial de sesión asociada a esa cuenta. |
| R002 | MUST      | SI el correo electrónico no corresponde a ninguna cuenta o la contraseña no coincide, ENTONCES el sistema DEBERÁ rechazar el intento con un mensaje genérico que no revele cuál de los dos datos es incorrecto ni si la cuenta existe. |
| R003 | MUST      | SI la petición de inicio de sesión no incluye correo electrónico o no incluye contraseña, ENTONCES el sistema DEBERÁ rechazar el intento indicando que ambos campos son obligatorios, sin llegar a verificar credenciales. |
| R004 | MUST      | El sistema DEBERÁ verificar la contraseña contra el hash almacenado sin exponer, registrar ni transmitir la contraseña en claro en ningún punto. |
| R005 | MUST      | SI se acumulan 3 intentos fallidos consecutivos para una misma combinación de cuenta y origen de la petición dentro de una ventana de 5 minutos, ENTONCES el sistema DEBERÁ bloquear durante 5 minutos nuevos intentos de inicio de sesión para esa combinación cuenta+origen y responder con el mismo mensaje genérico de R002. |
| R006 | MUST      | CUANDO un usuario se autentica correctamente, el sistema DEBERÁ registrar la marca de tiempo de ese inicio de sesión como su último acceso. |
| R007 | MUST      | MIENTRAS un usuario no presente una credencial de sesión válida, el sistema DEBERÁ impedir el acceso a las funciones personalizadas y a los datos asociados a una cuenta. |
| R008 | MUST      | CUANDO un usuario con sesión activa solicita cerrar sesión, el sistema DEBERÁ invalidar su credencial de sesión de modo que deje de dar acceso a las funciones personalizadas. |
| R009 | MUST      | Una credencial de sesión DEBERÁ expirar 24 horas después de su emisión. |
| R010 | SHOULD    | SI un usuario presenta una credencial de sesión expirada o inválida, ENTONCES el sistema DEBERÁ rechazar el acceso y tratarlo como no autenticado. |

## Criterios de aceptación

### R001

- **Dado** un usuario registrado con correo y contraseña conocidos **cuando** envía esas credenciales correctas **entonces** el sistema responde con éxito y devuelve una credencial de sesión asociada a su cuenta.
- **Dado** un correo registrado escrito con distinta capitalización o espacios alrededor **cuando** el usuario envía la contraseña correcta **entonces** el sistema lo autentica igualmente (el correo se normaliza como en el registro).

### R002

- **Dado** un correo que no existe en el sistema **cuando** se intenta iniciar sesión **entonces** el sistema rechaza con un mensaje genérico de credenciales inválidas y no indica que la cuenta no existe.
- **Dado** un correo existente con una contraseña incorrecta **cuando** se intenta iniciar sesión **entonces** el sistema rechaza con el mismo mensaje genérico e indistinguible del caso de correo inexistente.

### R003

- **Dado** una petición sin correo electrónico **cuando** se envía **entonces** el sistema responde con un error de validación indicando que faltan campos obligatorios, sin verificar credenciales.
- **Dado** una petición sin contraseña **cuando** se envía **entonces** el sistema responde con un error de validación equivalente.

### R004

- **Dado** un intento de inicio de sesión (exitoso o fallido) **cuando** el sistema procesa la petición **entonces** la contraseña en claro no aparece en la respuesta ni en los registros/logs del sistema.

### R005

- **Dado** una combinación cuenta+origen con 3 intentos fallidos consecutivos dentro de una ventana de 5 minutos **cuando** se realiza un cuarto intento —incluso con la contraseña correcta— **entonces** el sistema lo rechaza con el mensaje genérico mientras dure el bloqueo.
- **Dado** una combinación cuenta+origen bloqueada **cuando** transcurren los 5 minutos de bloqueo **entonces** el sistema vuelve a aceptar intentos de inicio de sesión.
- **Dado** una cuenta con intentos fallidos desde un origen bloqueado **cuando** el mismo usuario intenta iniciar sesión con la contraseña correcta desde un origen distinto no bloqueado **entonces** el sistema procesa el intento con normalidad.

### R006

- **Dado** un usuario que se autentica correctamente **cuando** el login tiene éxito **entonces** el registro de su último acceso queda actualizado con la marca de tiempo de ese inicio de sesión.

### R007

- **Dado** un cliente sin credencial de sesión válida **cuando** solicita una función personalizada o datos de una cuenta **entonces** el sistema rechaza el acceso como no autenticado.

### R008

- **Dado** un usuario con sesión activa **cuando** solicita cerrar sesión **entonces** el sistema invalida su credencial y un intento posterior de usar esa misma credencial es tratado como no autenticado.

### R009

- **Dado** una credencial de sesión emitida hace más de 24 horas **cuando** el usuario la presenta para acceder a una función personalizada **entonces** el sistema la considera expirada y trata la petición como no autenticada.

## Requisitos no funcionales

- **Latencia**: CUANDO el sistema recibe un intento de inicio de sesión, DEBERÁ
  responder en menos de 500 ms en el percentil 95, bajo carga nominal esperada.
- **Indistinguibilidad temporal**: el tiempo de respuesta ante credenciales
  incorrectas no debe permitir deducir, de forma sistemática, si un correo está
  registrado (mitigación de enumeración de cuentas por temporización).
- **Privacidad**: la contraseña en claro nunca se persiste ni se escribe en
  logs (refuerza R004).

## Supuestos

- El usuario ya completó el registro; el login no crea cuentas.
- La cuenta está activa y no requiere un paso previo de verificación de correo
  (ver non-goals).
- El identificador de acceso es el correo electrónico, igual que en el registro
  (no hay "nombre de usuario" separado).
- El almacén de usuarios existente expone la búsqueda por correo y el hash de
  contraseña necesarios para verificar credenciales.

## Preguntas abiertas

_Ninguna. Las tres ambigüedades iniciales se resolvieron en `/sdd:clarify`
(2026-08-12): bloqueo de 3 intentos / ventana de 5 min / duración 5 min por
cuenta+origen; expiración de sesión a las 24 h._
