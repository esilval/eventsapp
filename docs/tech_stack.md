# EventsApp - Tech stack

## Overview

EventsApp es una solución de software diseñada para la gestión de eventos en su ciclo de vida y lo que ocurre alrededor de ellos. Por ende, el diseño de la aplicación desde su etapa de concepción hasta su desarrollo debe estar soportado por tecnologías que permitan la escalabilidad, flexibilidad y facilidad de mantenimiento de la aplicación.

## Propósito

Este documento tiene como propósito dar la guía para definir el stack tecnológico que soportará la aplicación EventsApp, así como las decisiones de diseño que se han tomado para garantizar la calidad del software y la experiencia del usuario.

Esta guía debe responder a las siguientes preguntas:

- ¿Qué tecnologías se utilizarán para el desarrollo de la aplicación?
- ¿Qué patrones de diseño se aplicarán para garantizar la calidad del software?

## Atributos de calidad

A continuación, se presentan los atributos de calidad que se consideran importantes para el desarrollo de la aplicación EventsApp:

- **Escalabilidad**: La aplicación debe ser capaz de crecer y adaptarse a medida que aumenta la cantidad de usuarios y eventos.
- **Flexibilidad**: La aplicación debe ser capaz de adaptarse a cambios en los requisitos y necesidades del negocio.
- **Mantenibilidad**: La aplicación debe ser fácil de mantener y actualizar, permitiendo la incorporación de nuevas funcionalidades sin afectar la estabilidad del sistema.
- **Seguridad**: La aplicación debe garantizar la protección de los datos de los usuarios y la integridad del sistema.
- **Usabilidad**: La aplicación debe ser fácil de usar y comprender, permitiendo a los usuarios realizar sus tareas de manera eficiente y efectiva.

## Tácticas de diseño

De acuerdo con los atributos de calidad mencionados anteriormente, se han definido las siguientes tácticas de diseño para garantizar la calidad del software y la experiencia del usuario:

- **Separación de responsabilidades**: Cada componente de la aplicación debe tener una única responsabilidad y no debe interferir con otros componentes.
- **Modularidad**: La aplicación debe estar compuesta por módulos independientes que puedan ser desarrollados, probados y mantenidos por separado.
- **Reutilización de componentes**: Se deben reutilizar componentes existentes en lugar de crear nuevos desde cero, lo que reduce el tiempo de desarrollo y mejora la calidad del software.
- **Pruebas automatizadas**: Se deben implementar pruebas automatizadas para garantizar la calidad del software y detectar errores de manera temprana en el ciclo de desarrollo.
- **Confidencialidad y autenticación**: Se deben implementar mecanismos de autenticación y autorización para garantizar que solo los usuarios autorizados puedan acceder a la aplicación y sus funcionalidades.
- **Integridad**: Se deben implementar mecanismos de validación y verificación de datos para garantizar la integridad de la información almacenada en la aplicación.

## Arquitectura

La arquitectura de la aplicación EventsApp se basa en una arquitectura de microservicios, lo que permite una mayor escalabilidad, flexibilidad y mantenibilidad. Cada servicio es independiente y puede ser desarrollado, probado y desplegado de manera separada.

## El Frontend

En primer lugar, EventsApp muestra una aplicación web en donde se muestra de manera amigable al usuario una interfaz que permita interactuar con la capa de servicios que permiten realizar las operaciones permitidas por EventApps. Debe respetar los principios de diseño de aplicaciones web modernas, como la separación de responsabilidades, la modularidad y la reutilización de componentes. Adicionalmente, la experiencia de usuario debe ser intuitiva y accesible, permitiendo a los usuarios navegar y realizar acciones de manera eficiente.

## El Backend

Dentro del diseño de la aplicación, se evaluaron dos posibilidades para realizar la arquitectura de la aplicación: una arquitectura monolítica y una arquitectura de microservicios. Después de un análisis detallado, se decidió optar por una arquitectura de microservicios debido a las siguientes razones:

- **Escalabilidad**: La arquitectura de microservicios permite escalar de manera independiente cada uno de los servicios, lo que facilita el crecimiento de la aplicación a medida que aumenta la cantidad de usuarios y eventos.
- **Flexibilidad**: La arquitectura de microservicios permite una mayor flexibilidad en el desarrollo y despliegue de la aplicación, ya que cada servicio puede ser desarrollado y desplegado de manera independiente.
- **Mantenibilidad**: La arquitectura de microservicios facilita la mantenibilidad de la aplicación, ya que cada servicio puede ser actualizado y mantenido de manera independiente sin afectar a otros servicios.
- **Resiliencia**: La arquitectura de microservicios permite una mayor resiliencia de la aplicación, ya que si un servicio falla, los demás servicios pueden seguir funcionando de manera independiente, lo que reduce el impacto de los fallos en la aplicación.

## Clean Architecture

La arquitectura limpia es un enfoque de diseño que se centra en la separación de preocupaciones y la organización del código en capas. En el contexto de EventsApp, la arquitectura limpia se implementará para garantizar que la aplicación sea mantenible, escalable y fácil de testear.

Para implementar la arquitectura limpia en EventsApp, se seguirán los siguientes principios:

- **Separación de capas**: La aplicación se dividirá en capas, cada una con una responsabilidad específica. Las capas principales serán: presentación, aplicación, dominio e infraestructura.
- **Independencia de frameworks**: La aplicación no dependerá de frameworks específicos, lo que permitirá cambiar o actualizar los frameworks sin afectar la lógica de negocio.
- **Dependencia de abstracciones**: Las capas superiores dependerán de abstracciones definidas en las capas inferiores, lo que permitirá una mayor flexibilidad y facilidad de mantenimiento.
- **Inversión de dependencias**: Las dependencias se invertirán para que las capas superiores no dependan de las capas inferiores, lo que permitirá una mayor independencia y facilidad de prueba.

### Scaffolding inicial

Para comenzar con la implementación de la arquitectura limpia, se creará una estructura básica de directorios y archivos que sigan los principios mencionados. Esta estructura servirá como base para el desarrollo de la aplicación.

```
service/
├── app/
│   ├── blueprints/
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── tests/
├── utils/
└── README.md
```

- **app/**: Contendrá el código fuente de la aplicación, organizado en las capas de presentación, aplicación, dominio e infraestructura.
- **blueprints/**: Contendrá los blueprints de Flask para organizar las rutas y vistas de la aplicación.
- **application/**: Contendrá la lógica de negocio y los casos de uso de la aplicación.
- **domain/**: Contendrá las entidades y objetos de valor que representan el modelo de dominio de la aplicación.
- **infrastructure/**: Contendrá la implementación de la infraestructura, como la conexión a la base de datos, servicios externos y otros componentes necesarios para el funcionamiento de la aplicación.
- **tests/**: Contendrá los casos de prueba para garantizar la calidad del software.
- **utils/**: Contendrá funciones y clases que serán utilizadas en diferentes partes de la aplicación, como validaciones, manejo de errores y utilidades de logging.

## Stack tecnológico

A continuación, se presentan las tecnologías que se utilizarán para el desarrollo de la aplicación EventsApp:

### Frontend

- **React**: Librería de JavaScript para construir interfaces de usuario.
- **Redux**: Librería para el manejo del estado de la aplicación.
- **Material-UI**: Librería de componentes de interfaz de usuario para React.

### Backend

- **Python**: Lenguaje de programación para el desarrollo del backend.
- **Flask-RESTful**: Extensión de Flask para el desarrollo de APIs RESTful.
- **SQLAlchemy**: ORM (Object-Relational Mapping) para interactuar con la base de datos.
- **PyTest**: Framework de pruebas para Python.

### Base de datos

- **PostgreSQL**: Sistema de gestión de bases de datos relacional de código abierto.

### Contenedores y orquestación

- **Docker**: Plataforma para desarrollar, enviar y ejecutar aplicaciones en contenedores.
- **Kubernetes**: Sistema de orquestación de contenedores para automatizar el despliegue, escalado y gestión de aplicaciones en contenedores.

### Cloud

- **AWS**: Plataforma de servicios en la nube para el despliegue y gestión de la aplicación.

### Seguridad

- **JWT (JSON Web Tokens)**: Estándar abierto para la transmisión segura de información entre partes como un objeto JSON.
- **OAuth 2.0**: Protocolo de autorización para permitir el acceso seguro a los recursos de la aplicación.

### Observabilidad

- **Prometheus**: Sistema de monitoreo y alerta para aplicaciones y servicios.
- **Grafana**: Plataforma de análisis y visualización de métricas para monitoreo y observabilidad de aplicaciones y servicios.
- **ELK Stack (Elasticsearch, Logstash, Kibana)**: Conjunto de herramientas para la gestión y análisis de logs y datos en tiempo real.