# Matriz de requisitos IS6032 y evidencias

La matriz relaciona los temas indicados para el curso con materiales de este proyecto; no sustituye la rúbrica oficial, que aún debe cotejarse.

| Tema | Evidencia | Estado |
|---|---|---|
| Problema, alcance y arquitectura cliente-servidor | [README](../README.md), [análisis](ANALISIS.md) | Documentados; cotejar con informe DOCX y rúbrica |
| ER y cardinalidades | [ER/EER](MODELOS-ER-EER.md), [DDL](../database/01-schema.sql) | Preparado; revisar renderizado visual |
| EER | [especialización de Usuario](MODELOS-ER-EER.md#eer-perfil-de-conductor) | Parcial; sin crear una tabla nueva |
| Modelo lógico y diccionario | [relaciones](MODELO-LOGICO-NORMALIZACION.md), [diccionario](DICCIONARIO.md) | Preparados a partir del DDL |
| DF, claves y 1FN–3FN | [normalización](MODELO-LOGICO-NORMALIZACION.md) | Justificación condicionada a reglas declaradas |
| Álgebra relacional | [dos ejemplos](ALGEBRA-RELACIONAL.md) | Preparados; cotejar simbología con docente |
| SQL | [seis consultas](../database/03-consultas.sql) | Validación previa en MariaDB documentada |
| Integridad | [DDL y triggers](../database/01-schema.sql), [prueba SQL](../tests/integrity.sql) | Evidencia previa MariaDB; CI también comprueba flujo y rechazos API |
| Transacciones y concurrencia | [transacción](../server/db.js), [prueba API](../tests/api.integration.js) | Consultar ejecución de Actions del commit de esta rama |
| Demostración | [guía](GUIA-ENTREGA.md) | Pendiente de ensayo manual y capturas reales |

No presentar cifras, resultados o capturas simuladas como pruebas. El informe original y su copia corregida no se reescribieron en esta tarea.
