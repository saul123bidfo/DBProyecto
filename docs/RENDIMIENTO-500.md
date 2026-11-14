# Prueba de lectura: 500 solicitudes por escenario

Se ejecuta en [GitHub Actions](../.github/workflows/rendimiento.yml), con MySQL 8.0.44 y la API iniciados en el mismo runner y con los datos ficticios de [02-seed.sql](../database/02-seed.sql). No se dirige a servicios públicos. El script bloquea su ejecución si no está en Actions y no recibe el indicador explícito de aislamiento; usa una URL fija de loopback.

Tras verificar la conexión y calentar una vez cada consulta, se ejecutan **500 solicitudes por nivel**: 5, 25 y 50 en paralelo; son 1.500 medidas en total. Las seis consultas existentes se alternan de forma determinista (83 o 84 solicitudes por consulta). Aunque el endpoint usa POST, ejecuta SQL SELECT del catálogo y no modifica registros. Los escenarios se ejecutan secuencialmente.

Se mide desde antes de enviar HTTP hasta terminar de leer y analizar la respuesta. El promedio y percentiles incluyen tanto respuestas correctas como fallidas; los percentiles usan rango más cercano (ordenar y elegir la posición techo de p × N). El rendimiento incluye solicitudes completadas por segundo y exitosas por segundo. Los errores HTTP, de red o timeout se agrupan por mensaje; la API oculta los detalles SQL al cliente, por lo que el log del servidor se conserva como artefacto para diagnosticar códigos. Después de cada escenario se comprueba /api/health. Cualquier error o fallo de salud provoca fallo del job una vez guardado el informe.

El flujo guarda por 14 días el JSON de resultados, los planes EXPLAIN y el log del servidor como artefacto. Para repetir: ejecutar el workflow `Rendimiento de consultas aisladas` en la rama y consultar su log o artefacto. También se activa automáticamente al actualizar esta rama. No requiere instalar nada en el equipo del estudiante.

## Interpretación

La prueba verifica 500 solicitudes **totales** en cada escenario; 50 es el máximo de solicitudes simultáneamente en vuelo, no 500 usuarios simultáneos. La muestra es pequeña, el dataset es mínimo, cliente y servidor comparten runner, el caché se calienta y el pool de aplicación admite hasta ocho conexiones. El resultado no garantiza capacidad de producción, carga sostenida, escrituras ni rendimiento con volumen real; tampoco hay SLA establecido para decidir una latencia aceptable.

Se ejecuta EXPLAIN estimado para las seis consultas, antes de la carga. El archivo conserva filas del plan, selección de índices y estimaciones devueltas por MySQL para ese seed; no equivale a EXPLAIN ANALYZE ni demuestra una optimización en otros tamaños de datos. Una comparación antes/después y una prueba con datos representativos siguen pendientes.

## Resultado observado

[Actions 43649023528](https://github.com/saul123bidfo/DBProyecto/actions/runs/43649023528), commit bbc2205, 14 de noviembre de 2026; Node 20.19.2, Linux x64 y MySQL 8.0.44. Una sola ejecución; seed con cinco usuarios, cuatro ofertas y un viaje.

| Concurrencia | Correctas / total | Fallidas | Duración (s) | Promedio (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Correctas/s |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 500/500 | 0 | 0,38 | 3,78 | 3,23 | 6,26 | 10,91 | 1.317,24 |
| 25 | 500/500 | 0 | 0,32 | 15,69 | 14,52 | 24,12 | 59,31 | 1.563,51 |
| 50 | 500/500 | 0 | 0,26 | 25,37 | 25,84 | 32,43 | 38,17 | 1.925,84 |

No se observaron errores HTTP/SQL en estas 1.500 respuestas; /api/health confirmó conexión MySQL después de cada escenario. Son ráfagas muy breves: las tasas son aproximaciones de esa ejecución, no capacidad sostenida. No se fijó un umbral de latencia. El p99 no aumenta de manera uniforme; con muestras cortas y runner compartido no se debe interpretar como tendencia. No se midieron CPU ni memoria.

EXPLAIN sobre el seed eligió `ix_solicitud_estado_fecha` y `uq_oferta_solicitud_vehiculo` para solicitudes sin ofertas. En ofertas bajo promedio estimó lectura `ALL` sobre cuatro filas y subconsulta dependiente; para promedios informó `Using temporary; Using filesort`. Son observaciones del plan de datos diminutos, no prueba de un problema de producción ni justificación suficiente para agregar índices. Repetir con volúmenes y distribución representativos, métricas de recursos y comparación antes/después es trabajo pendiente.

