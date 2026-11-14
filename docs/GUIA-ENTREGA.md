# Guía de evidencia, demostración y entrega

## Evidencia y preparación

La ejecución [Actions del 3 de noviembre de 2026](https://github.com/saul123bidfo/DBProyecto/actions/runs/41713761020) para el commit 5fb82b7 pasó build, pruebas JavaScript, inicialización MySQL 8.0.44, integración API (incluida aceptación simultánea de la misma oferta) y arranque Docker con health HTTP. Es evidencia histórica de main; no acredita automáticamente cambios posteriores.

El repositorio registra también una validación anterior en MariaDB 11.8.6 en [VALIDACION-SQL.json](VALIDACION-SQL.json). La suite [integrity.sql](../tests/integrity.sql) usa códigos de MariaDB, por lo que no se debe atribuir directamente a MySQL. Consultar Actions del commit de la rama para conocer el resultado de las pruebas nuevas; no declarar PASS antes de observarlo. La prueba de integración escribe historial y debe ejecutarse únicamente en una base de prueba aislada. El flujo de CI crea su propia instancia.

Para COMMIT y ROLLBACK: el helper [transaction](../server/db.js) ejecuta commit si la operación termina y rollback si falla; el flujo de integración verifica persistencia observable y conflictos. La prueba SQL previa incluye un flujo positivo seguido de ROLLBACK. Una demostración manual independiente de ambos límites y el recorrido visual siguen pendientes hasta registrar resultados reales.

## Recorrido sugerido

1. En una instancia de prueba, confirmar conexión y mostrar ocho tablas, nueve FK y el diagrama.
2. Registrar usuario y solicitud; demostrar rechazo de contacto duplicado.
3. Presentar dos ofertas de vehículos distintos, aceptar una y mostrar solicitud aceptada y viaje pendiente.
4. Iniciar y finalizar viaje; registrar pago y calificaciones de participantes. Explicar que el cobro es un registro académico.
5. Intentar borrar un usuario con historial y explicar RESTRICT. Mostrar un CHECK o trigger rechazando un dato inválido.
6. Ejecutar una consulta con JOIN y otra con LEFT JOIN, contrastar su álgebra y explicar resultados reales.
7. Mostrar la prueba concurrente y el enlace al resultado CI del commit exacto; no simular resultados.

Tomar capturas reales del navegador y los resultados solamente después del ensayo. Confirmar que no aparezcan datos personales ni contraseñas. No reinicializar ni borrar bases con información de compañeros.

## Insumos para informe y presentación posteriores

Usar [matriz](MATRIZ-REQUISITOS.md), [ER/EER](MODELOS-ER-EER.md), [modelo y 3FN](MODELO-LOGICO-NORMALIZACION.md), [álgebra](ALGEBRA-RELACIONAL.md), diccionario y evidencias CI. En una PPT futura, reservar la portada institucional para logo oficial, curso, docente e integrantes confirmados; en las demás diapositivas usar verdes, negro, blanco, diagramas legibles y capturas reales. No inventar nombres, logo, resultados o referencias. Los datos institucionales y la revisión del DOCX y la rúbrica quedan pendientes.
