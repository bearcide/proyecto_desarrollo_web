# ADR 001: Selección del Stack Tecnológico y Patrón de Arquitectura

* **Estado**: Aceptado
* **Fecha**: 2026-09-17
* **Squad**: InscripcionMadeEasy
* **Autores**: Aguilar Chavez Cristian Michael [Scrum Master]
Hernandez Martinez Cecilia Sayuri [Product Owner]
Garcia Riba Emilio [Team lead]


## 1. Contexto y Problema
Tras las entrevistas de validación de mercado realizadas a nuestros tres principales grupos de interés (Estudiantes, Profesores y Administrativos), identificamos que nuestra plataforma necesita resolver la ineficiencia, el estrés y la incertidumbre que genera el proceso de inscripción actual.

Los resultados de la encuesta revelan una necesidad clara de modernización, pero también una fuerte preocupación por la implementación y la adaptación al cambio:

    El problema validado: El sistema actual genera un alto nivel de estrés en los estudiantes durante el día de la inscripción. Aunque existe una necesidad de mejora, los estudiantes tienen opiniones mixtas: algunos temen que un nuevo sistema les cause mayor estrés, mientras que la mayoría (tras explicarles la propuesta) lo considera una mejora sustancial para reducir la carga mental de preocuparse por la inscripción.

    La postura de los administrativos: Ellos son los usuarios indirectos que gestionan los horarios y números de inscripción. Su principal preocupación es que un sistema tan crítico falle durante la implementación. Además, muestran una clara preferencia por implementar mejoras sobre su sistema actual en lugar de adaptar un sistema completamente nuevo desde cero, buscando así minimizar el riesgo operativo.

    La postura de los profesores: Son usuarios indirectos que muestran interés en la idea, pero se mantienen neutrales ante su implementación. Su mayor preocupación radica en cómo reaccionarán los estudiantes ante un cambio en el sistema de inscripción.

Requerimiento técnico y arquitectura:
Para resolver esta problemática, requerimos una arquitectura web basada en Django que nos permita desarrollar ágilmente y garantizar el desacoplamiento entre la lógica de negocio y la infraestructura. El objetivo es ofrecer un SaaS robusto que no solo permita a los estudiantes inscribirse en su horario asignado, sino que incorpore un motor de automatización basado en su número de inscripción para agilizar el proceso. Esto debe garantizar la estabilidad y seguridad que los administrativos exigen para no comprometer un proceso tan crítico.

## 2. Decisión
Hemos decidido adoptar las siguientes tecnologías y patrones para el desarrollo del proyecto:
Lenguaje y Framework Backend: Python con Django.

    Justificación: Django es ideal para este proyecto porque incluye un ORM robusto, un sistema de autenticación nativo y un panel de administración listo para usar. Esto nos permite desarrollar rápidamente el núcleo del sistema (gestión de horarios, números de inscripción y reglas de automatización) sin depender de configuraciones complejas. Además, su madurez garantiza la estabilidad que los administrativos demandan para un proceso crítico.

Framework Frontend: HTML5 + Bootstrap 5 (con Django Templates).

    Justificación: Para un SaaS ligero, no necesitamos la sobrecarga de un framework SPA (como React o Vue) que ralentice la carga en equipos modestos o conexiones lentas. Django Templates + Bootstrap nos permite renderizar vistas rápidas y responsivas (esencial para estudiantes que se inscriben desde el celular) con un esfuerzo mínimo. Esto acelera el time-to-market y reduce la curva de aprendizaje para el equipo.

Base de Datos Principal: PostgreSQL.

    Justificación: Aunque Django funciona bien con SQLite para desarrollo, para un SaaS en producción que manejará transacciones concurrentes (múltiples estudiantes inscribiéndose al mismo tiempo) y datos relacionales complejos (estudiantes, materias, horarios, números de inscripción), PostgreSQL es la opción ideal. Ofrece la integridad referencial y el rendimiento necesario para evitar caídas o duplicados durante los picos de inscripción, abordando la principal preocupación de los administrativos.

Patrón de Arquitectura: MVC (Modelo-Vista-Controlador) desacoplado mediante Servicios.

    Justificación: Django sigue nativamente el patrón MVC (aunque lo llame MVT). Sin embargo, para garantizar el desacoplamiento que mencionas en tu contexto, implementaremos una capa de Servicios (carpeta services.py o similar) donde residirá la lógica de negocio pesada (como el algoritmo de asignación automática por número de inscripción). Esto permite que las vistas sean ligeras, que la lógica sea reutilizable y que, si en el futuro migramos a una API REST (con Django REST Framework), el núcleo del sistema no tenga que reescribirse.

## 3. Alternativas Consideradas
Opción A (Descartada): Node.js con Express + React (SPA) Aunque ofrece un frontend muy dinámico, implicaba mantener dos repositorios separados, duplicar la lógica de autenticación y añadir una capa de complejidad innecesaria (API REST + servidor de frontend) para un sistema que prioriza la ligereza. Además, el equipo no dominaba el ecosistema de JavaScript moderno, lo que habría retrasado el time-to-market que exige un SaaS en etapa temprana.

Opción B (Descartada): MySQL Si bien es una base de datos sólida y popular, PostgreSQL ofrece un mejor soporte para concurrencia (crítico durante los picos de inscripción) y tipos de datos avanzados como JSONB, que podríamos usar para almacenar configuraciones flexibles de horarios o reglas de automatización por institución sin alterar el esquema relacional. Para un SaaS multi-institución, esa flexibilidad es clave.

Opción C (Descartada): Django Monolítico con lógica en las vistas Colocar toda la lógica de negocio (como el algoritmo de asignación automática por número de inscripción) directamente en las vistas o modelos dificultaría el mantenimiento, las pruebas unitarias y una futura migración a una API. Se optó por una arquitectura MVC desacoplada con capa de servicios para aislar el núcleo del sistema y facilitar su evolución.

Opción D (Descartada): MongoDB (NoSQL) Aunque es flexible para datos no estructurados, el dominio del problema es altamente relacional (estudiantes, materias, horarios, números de inscripción, historial académico). Usar una base de datos documental habría complicado las consultas transaccionales y la integridad referencial, justo lo que los administrativos temen que falle en un proceso tan crítico.

Opción E (Descartada): Frontend con Tailwind CSS en lugar de Bootstrap Tailwind es excelente para diseños personalizados, pero requiere un proceso de compilación adicional y un mayor esfuerzo de diseño desde cero. Bootstrap ofrece componentes preconstruidos (tablas, formularios, modales) que aceleran el desarrollo de las vistas de inscripción y administración, manteniendo la ligereza que buscamos sin sacrificar velocidad de entrega.

## 4. Consecuencias
* **Positivas**:
Separación clara de responsabilidades entre capas: La lógica de negocio (como el algoritmo de asignación automática por número de inscripción) quedará aislada en una capa de servicios, mientras que las vistas de Django y las plantillas HTML+Bootstrap se encargarán únicamente de la presentación. Esto facilita el mantenimiento y permite modificar las reglas de inscripción sin tocar la interfaz.

Curva de aprendizaje alineada con la experiencia previa del squad: El equipo ya domina Python y Django, y Bootstrap es un estándar conocido. Esto reduce el tiempo de capacitación y permite enfocarnos en resolver el problema de negocio (la automatización de inscripciones) en lugar de aprender nuevas tecnologías desde cero.

Facilidad para crear pruebas unitarias sobre el dominio sin depender de la base de datos: Al aislar la lógica en servicios, podremos probar el motor de asignación automática con datos simulados (mocks) sin necesidad de levantar PostgreSQL. Esto acelera el desarrollo, mejora la calidad del código y reduce el riesgo de fallos en producción, algo que preocupa especialmente a los administrativos.

Estabilidad y seguridad desde el primer día: Django incluye protecciones nativas contra CSRF, XSS e inyección SQL, y PostgreSQL garantiza la integridad referencial en las transacciones concurrentes. Esto responde directamente a la preocupación de los administrativos sobre que el sistema "no falle" durante los picos de inscripción.

Ligereza y rapidez de carga: Al no usar un framework SPA, las vistas se renderizan en el servidor y llegan listas al navegador, lo que beneficia a estudiantes con conexiones lentas o dispositivos modestos, reduciendo su estrés el día de la inscripción.
* **Riesgos / Limitaciones**:
Mayor tiempo inicial invertido en la configuración de la estructura (scaffolding): Definir la capa de servicios, los repositorios y las reglas de importación entre capas requiere una inversión inicial de tiempo que no se ve reflejada en funcionalidades visibles de inmediato. Sin embargo, este esfuerzo se recupera conforme el proyecto crece.

Necesidad de mantener disciplinadamente las reglas de importación entre capas: Si el equipo no respeta la separación (por ejemplo, colocando lógica de negocio directamente en las vistas), el desacoplamiento se pierde y el código se vuelve difícil de mantener. Se requerirá revisión de código (code review) y posiblemente herramientas de linting para hacer cumplir estas reglas.

Dependencia del ecosistema Django: Aunque es una ventaja en velocidad de desarrollo, también implica que cualquier actualización mayor de Django o cambio en sus políticas de soporte a largo plazo requerirá migraciones planificadas. Es un riesgo controlado, pero debe monitorearse.

Riesgo de cuello de botella en PostgreSQL durante picos extremos: Aunque PostgreSQL soporta alta concurrencia, si una institución grande concentra miles de inscripciones en pocos minutos, será necesario implementar estrategias como connection pooling, índices optimizados y posiblemente caché con Redis. Esto debe considerarse en la fase de escalamiento del SaaS.

Resistencia al cambio por parte de los administrativos: La encuesta reveló que prefieren mejoras sobre su sistema actual antes que adoptar un sistema completamente nuevo. Esto significa que el SaaS deberá incluir un plan de migración gradual, capacitación y soporte cercano para mitigar la percepción de riesgo y facilitar la adopción.