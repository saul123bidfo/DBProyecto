# Cobertura del sílabo IS6032

Fuente: **IS6032_BASE DE DATOS v7.pdf**, sílabo de Base de Datos, código UPNW-GAC-FOR-035, versión y revisión 07, fecha 09/02/2026, período 2026-I, sección IV. Se consultó el PDF facilitado por el estudiante; no se incorporó al repositorio. La semana 13 menciona procesamiento de consultas y transacciones; EXPLAIN es una herramienta de apoyo propuesta para evidenciar el tema, no una palabra exigida literalmente en esa semana.

Estados: **demostrado** = hay implementación con ejecución o pruebas identificadas; **documentado** = hay explicación o modelo sin evidencia de demostración completa; **pendiente** = falta evidencia o trabajo. Las calificaciones se refieren al proyecto, no a la evaluación individual del estudiante.

| Semana | Tema del sílabo, resumido | Estado y evidencia |
|---|---|---|
| 1 | Modelo relacional y notación de modelado ER | **Documentado:** [ER](MODELOS-ER-EER.md) y [modelo](MODELO-LOGICO-NORMALIZACION.md); revisión visual pendiente |
| 2 | Modelado EER de relaciones semánticas complejas | **Documentado:** [especialización parcial](MODELOS-ER-EER.md#eer-perfil-de-conductor); no se demuestra un caso de generalización complejo |
| 3 | Teoría matemática de relaciones aplicada a tablas | **Parcial:** [relaciones y claves](MODELO-LOGICO-NORMALIZACION.md); falta desarrollar formalmente dominio, tupla, relación y propiedades |
| 4 | Álgebra relacional para consultar relaciones | **Documentado:** [dos ejemplos](ALGEBRA-RELACIONAL.md); validación académica pendiente |
| 5 | SQL para definición, descripción y restricciones de esquemas; consultas | **Demostrado:** [DDL](../database/01-schema.sql), [consultas](../database/03-consultas.sql) y [CI del proyecto](GUIA-ENTREGA.md); descripción conceptual de evaluación pendiente |
| 6 | SQL declarativo, operaciones de álgebra y diferencias entre ambos | **Parcial:** [ejemplos SQL/álgebra](ALGEBRA-RELACIONAL.md); falta comparación explícita de duplicados, NULL y orden |
| 7 | Diseño lógico y traducción (E)ER a relacional | **Documentado:** [modelo lógico](MODELO-LOGICO-NORMALIZACION.md) y [ER/EER](MODELOS-ER-EER.md); falta detallar todos los pasos de traducción |
| 8 | E1: evaluación parcial | No es un contenido técnico del repositorio; preparación y resultado dependen del curso |
| 9 | Traducción de EER a esquema relacional | **Documentado parcialmente:** perfil de Conductor y su FK única en [EER](MODELOS-ER-EER.md#eer-perfil-de-conductor); falta desarrollo paso a paso |
| 10 | Aplicaciones RDBMS en arquitectura cliente-servidor | **Demostrado:** React, Express y MySQL, con [CI](../.github/workflows/ci.yml); recorrido manual de navegador pendiente |
| 11 | Escalabilidad con RDBMS y datos estructurados/semiestructurados en XML | **Parcial:** [prueba de carga](RENDIMIENTO-500.md#resultado-observado); XML explicado abajo, sin implementación. Escalado horizontal no probado |
| 12 | Redundancia, dependencias funcionales y normalización | **Documentado:** [claves, DF y 1FN–3FN](MODELO-LOGICO-NORMALIZACION.md); supuestos de negocio por confirmar |
| 13 | Algoritmos de procesamiento de consultas: búsqueda y unión; transacciones | **Parcial:** transacciones probadas según [evidencia](GUIA-ENTREGA.md); [EXPLAIN estimado ejecutado](RENDIMIENTO-500.md#resultado-observado). Falta explicar algoritmos de búsqueda/unión y comparar optimización con datos representativos |
| 14 | Modelo y categorías de sistemas NoSQL | **Documentado brevemente:** comparación abajo; falta cuadro completo de categorías y casos de uso |
| 15 | MongoDB como modelo documental y modelo de grafos | **Documentado brevemente:** ejemplos abajo; no hay prácticas ejecutadas con MongoDB ni motor de grafos |

## Alcance del logro de la asignatura

El sílabo plantea analizar datos reales de una organización local y proponer mejoras para decisiones oportunas. Este repositorio usa datos ficticios y un modelo académico inspirado en inDrive; no acredita por sí mismo el análisis de datos reales de una organización local ni una mejora validada. Confirmar con el docente cómo se evaluará ese logro; no atribuir al proyecto una vinculación organizacional no demostrada.

## Aclaraciones y comparaciones teóricas

**SQL y álgebra:** SQL suele trabajar con multiconjuntos y permite valores NULL y ORDER BY; el álgebra relacional clásica trabaja con conjuntos y no garantiza orden. `DISTINCT` elimina duplicados en SQL; NULL requiere lógica de tres valores y condiciones como IS NULL.

**Escalabilidad:** la prueba varía concurrencia dentro de un runner y una sola instancia. Escalar verticalmente sería aumentar recursos de esa instancia; horizontalmente, repartir carga entre instancias y resolver coordinación y persistencia. No se ha implementado ni probado escalado horizontal.

**XML:** un viaje podría intercambiarse como `<viaje><origen>Lima</origen></viaje>`; XML organiza datos en elementos anidados. El proyecto usa JSON para HTTP y tablas MySQL; no genera ni valida XML.

**NoSQL:** entre sus categorías están clave-valor, documentos, columnas anchas y grafos. Responden a necesidades diferentes; no sustituyen automáticamente las garantías o consultas relacionales. Un documento hipotético en MongoDB podría agrupar una solicitud y sus ofertas en BSON, con decisiones sobre duplicación y consistencia. No se conecta MongoDB.

**Grafos:** usuarios y viajes podrían modelarse como nodos y aristas para explorar relaciones o rutas. El proyecto actual usa JOIN en MySQL; no utiliza una base de grafos ni implementa búsquedas de rutas.

**EXPLAIN:** muestra el plan estimado del optimizador, como orden de acceso y claves seleccionadas. El [plan observado](RENDIMIENTO-500.md#resultado-observado) depende del seed; un índice elegido para datos pequeños no demuestra que sea óptimo con otra distribución. Se necesita comparar planes y tiempos con datos representativos antes de afirmar una optimización.
