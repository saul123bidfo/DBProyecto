# Cobertura preliminar del sílabo IS6032

No se ha recibido la distribución oficial de las semanas 1 a 15. El código y nombre del curso figuran en el [plan de estudios de la universidad](https://www.uwiener.edu.pe/wp-content/uploads/2025/04/P14-INGENIERIA-DE-SISTEMAS-E-INFORMATICA.pdf), pero ese documento no permite confirmar el temario semanal de esta asignatura. Solo se asignan semanas a los temas que indicó el equipo; faltan confirmar versión, semestre y contenido literal del sílabo. La matriz no acredita por sí sola que se cumpla la rúbrica.

Estados: **demostrado** = hay una implementación o prueba con evidencia identificada; **documentado** = explicación o modelo sin demostración de ejecución; **pendiente** = no hay evidencia suficiente.

| Semana | Tema confirmado | Estado y evidencia |
|---|---|---|
| 1 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 2 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 3 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 4 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 5 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 6 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 7 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 8 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 9 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 10 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 11 | Escalabilidad y XML, según indicación del equipo | Escalabilidad: prueba limitada [documentada](RENDIMIENTO-500.md), consultar ejecución real. XML: comparación teórica abajo; sin almacenamiento XML implementado |
| 12 | Pendiente de sílabo | Pendiente de asignación y cotejo |
| 13 | Procesamiento y optimización de consultas con EXPLAIN, según indicación del equipo | EXPLAIN preparado en CI; comprobar el artefacto de la ejecución. Optimización antes/después con datos representativos pendiente |
| 14 | NoSQL, MongoDB y grafos, según indicación del equipo para semanas 14–15 | Comparación teórica abajo; no hay MongoDB ni base de grafos implementados. Distribución exacta por semana pendiente |
| 15 | NoSQL, MongoDB y grafos, según indicación del equipo para semanas 14–15 | Comparación teórica abajo; implementación y ejercicios ejecutados pendientes |

## Cobertura por tema sin asignación semanal inferida

| Tema | Estado | Evidencia |
|---|---|---|
| Arquitectura cliente-servidor | Demostrado en CI; recorrido visual pendiente | [README](../README.md), [CI](../.github/workflows/ci.yml) |
| ER/EER y modelo lógico | Documentado; revisión visual pendiente | [diagramas](MODELOS-ER-EER.md), [modelo lógico](MODELO-LOGICO-NORMALIZACION.md) |
| Claves, integridad y transacciones | Implementado y probado en ejecuciones previas | [DDL](../database/01-schema.sql), [prueba API](../tests/api.integration.js), [evidencia](GUIA-ENTREGA.md) |
| 1FN, 2FN, 3FN y dependencias | Documentado bajo supuestos declarados | [normalización](MODELO-LOGICO-NORMALIZACION.md) |
| Álgebra relacional | Documentado; validación docente pendiente | [ejemplos](ALGEBRA-RELACIONAL.md) |
| SQL | Implementado; consultas y pruebas previas | [consultas](../database/03-consultas.sql), [validación](VALIDACION-SQL.json) |

## Comparaciones breves, sin implementación adicional

**Escalabilidad:** la prueba varía concurrencia dentro de un runner y una sola instancia. Escalar verticalmente sería aumentar recursos de esa instancia; horizontalmente, repartir carga entre instancias y resolver coordinación y persistencia. No se ha implementado ni probado escalado horizontal.

**XML:** un viaje podría intercambiarse como `<viaje><origen>Lima</origen></viaje>`; XML organiza datos en elementos anidados. El proyecto usa JSON para HTTP y tablas MySQL; no genera ni valida XML.

**NoSQL y MongoDB:** un documento hipotético podría agrupar una solicitud y sus ofertas en JSON/BSON. Frente al esquema relacional con FK y JOIN, la elección exige decidir cómo manejar duplicación, cambios y consistencia. El proyecto no conecta MongoDB ni mide esa alternativa.

**Grafos:** usuarios y viajes podrían modelarse como nodos y aristas para explorar relaciones o rutas. El proyecto actual usa JOIN en MySQL; no utiliza una base de grafos ni implementa búsquedas de rutas.

**EXPLAIN:** muestra el plan estimado del optimizador, como orden de acceso y claves seleccionadas. Un índice elegido para datos pequeños no demuestra que sea óptimo con otra distribución; comparar planes y tiempos con datos representativos antes de concluir que una consulta está optimizada.
