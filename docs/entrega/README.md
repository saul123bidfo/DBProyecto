# Entrega del curso: informe Word y presentación PowerPoint

Archivos editables para la revisión de Saúl. Los originales (`Informe_inDrive.docx` y `docs/Informe_inDrive_corregido.docx`) **no se modificaron**.

| Archivo | Contenido |
|---|---|
| [`Informe_inDrive_BD_final.docx`](Informe_inDrive_BD_final.docx) | Informe completo (38 páginas, 8 figuras, 21 tablas) |
| [`Presentacion_inDrive_BD.pptx`](Presentacion_inDrive_BD.pptx) | 16 diapositivas 16:9 con notas del orador repartidas entre los cuatro integrantes |
| [`diagramas/`](diagramas) | Los seis diagramas en SVG (editables) y PNG |
| [`assets/`](assets) | Logotipo de la Universidad Norbert Wiener (el de la carátula de Hidro-Mejora) y la captura real de GitHub Actions |

## Qué cambió en el informe

Parte de `docs/Informe_inDrive_corregido.docx`. Se conservan la portada, los cuatro integrantes, el docente y la investigación de las secciones 1 a 6, el FODA y las referencias.

- **Portada:** logotipo oficial vigente (el de la referencia de Hidro-Mejora), título del proyecto y «Informe del proyecto»; se mantienen facultad, asignatura, docente e integrantes.
- **Índice, numeración y coherencia:** jerarquía real de títulos (nivel 1 y 2), índice general con números de página y listas de figuras y tablas; leyendas numeradas con referencias automáticas; encabezados de tabla que estaban en blanco sobre blanco ahora tienen fondo; el texto de la sección 7 que decía «verificación en MySQL pendiente» se actualizó con la evidencia de GitHub Actions.
- **Secciones nuevas:** 8 Problemática y objetivos, 9 Propuesta de solución, 10 Desarrollo de la base de datos (ER, EER, modelo lógico, diccionario, normalización, álgebra, SQL, consultas, transacciones, pruebas y prototipo), anexos A–C. El FODA pasa a la sección 11 y las conclusiones a la 12, con conclusiones nuevas sobre la base de datos.

## Verificación

`python3 scripts/entrega/verificar_entrega.py` comprueba 63 puntos contra el código real: 8 tablas, 9 FK, 15 CHECK, 18 triggers, 42 atributos, 23 casos de integridad, 10 pruebas JS, 6 consultas, rutas de la API, módulos de la interfaz, datos del seed y resultados de las consultas (reproducidos en Python sobre el seed), y que la portada y la investigación sigan presentes.

## Límites que el informe y la presentación declaran

- **No se re-ejecutó el SQL** al preparar estos documentos (sin MariaDB ni Docker en el equipo de trabajo). Los resultados de las consultas se derivaron del seed y coinciden con `docs/VALIDACION-SQL.json`.
- La suite `tests/integrity.sql` se validó en **MariaDB 11.8.6**; la integración continua prueba el flujo completo en **MySQL 8.0.44** (ejecuciones 43644564327 y 43644591366, commit `5841e63`).
- **No hay capturas de la interfaz**: el recorrido manual en navegador sigue pendiente. La diapositiva 15 es un esquema, rotulado como tal.
- Las referencias teóricas (Chen 1976, Codd 1970, Elmasri y Navathe, Silberschatz et al.) y la rúbrica del curso deben cotejarse con el docente.
- El reparto de notas del orador es una propuesta (Deivis 1–4, Luis 5–8, Darly 9–12, Saúl 13–16); se puede reasignar.
- Al abrir el Word, si la paginación cambia respecto de LibreOffice, usar clic derecho → «Actualizar campos» en el índice.

## Regenerar

Solo biblioteca estándar de Python (más LibreOffice y `pdftotext` si se quiere paginar el índice, y un Chromium sin interfaz para los PNG):

```bash
python3 scripts/entrega/diagramas.py          # SVG y PNG (comprueba el DDL)
python3 scripts/entrega/construir_informe.py  # Word
python3 scripts/entrega/construir_pptx.py     # PowerPoint
python3 scripts/entrega/verificar_entrega.py  # cruce con el repositorio
```

En PowerPoint, los diagramas de las diapositivas 7, 8, 9 y 13 llevan su SVG incrustado: clic derecho → «Convertir en forma» permite editarlos.
