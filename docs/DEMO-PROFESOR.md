# Demostración para el profesor (≈ 12 minutos)

Todo se hace en local. La base de demostración (504 solicitudes: 500 ficticias + 4 del seed original) **no se modifica** durante el recorrido.
Los datos son ficticios y el sistema no representa al inDrive real.

## Antes de empezar (5 minutos antes)

1. Iniciar Docker Desktop / el servicio Docker.
2. `scripts/demo-500/iniciar-indrive-lab.sh` (conserva los datos; no repite la carga de los 500 registros).
3. Abrir **http://127.0.0.1:3000** y comprobar en la barra lateral «Base de datos conectada · 8.0.44».
4. Abrir MySQL Workbench con una conexión a `127.0.0.1`, puerto **3307**, usuario `indrive_app` y la clave `DB_PASSWORD` del archivo `.env` (o `root` con `MYSQL_ROOT_PASSWORD`). Abrir `scripts/demo-500/verificar-demo.sql` y `scripts/demo-500/consultas-profesor.sql`.
5. Tener a mano `scripts/demo-500/resultados-rendimiento.txt` y una terminal en la carpeta del proyecto.

## Guion

| # | Qué mostrar | Qué decir |
|---|---|---|
| 1 | **Vista general**: tarjetas y los 4 gráficos | «Cada cifra la calcula MySQL en el momento: `COUNT … GROUP BY` para solicitudes por estado y viajes por mes, `SUM … GROUP BY` para pagos por método, `AVG … HAVING` para la calificación de conductores.» Total: 504 solicitudes (abiertas 243, aceptadas 221, canceladas 40). |
| 2 | **Solicitudes** → 504 registros, 21 páginas de 25. Buscar `Wiener` y luego el nombre de un pasajero. Pulsar **Siguiente** | «La paginación y la búsqueda se hacen en la base con `LIMIT/OFFSET` y `LIKE`; la interfaz no guarda los datos.» |
| 3 | **MySQL Workbench**: ejecutar `verificar-demo.sql` | Resultado esperado: 500 solicitudes de demostración exactas, 0 huérfanos, 0 violaciones. «Es la misma información que muestra la aplicación.» |
| 4 | Workbench: `consultas-profesor.sql` (JOIN de 5 tablas, GROUP BY) | Contrastar una fila con la pantalla de **Ofertas** o **Viajes**. |
| 5 | **Explorador de Base de Datos** → Diagrama ER, Tablas y diccionario, Integridad e índices | 8 tablas, 9 claves foráneas, todas `RESTRICT`; 15 `CHECK`; 18 triggers. Mostrar el nombre de los encabezados en español y que los nombres SQL no cambian. |
| 6 | Explorador → **Conceptos del curso** | Recorrer ER, EER (especialización parcial usuario → conductor), modelo lógico (generado del motor), normalización hasta 3FN, transacciones y concurrencia. Resaltar la etiqueta «Implementado» frente a «Explicación académica». |
| 7 | **Consultas SQL** → *Viajes y participantes* (JOIN) → **Ejecutar** | Mostrar el SQL real y el tiempo en ms. |
| 8 | *Calificaciones de conductores* → cambiar «Mínimo de evaluaciones» a 5 → Ejecutar | Explica `HAVING`. |
| 9 | *Ofertas bajo el promedio* → **Ver plan de ejecución** | «Esto es `EXPLAIN`: así procesa MySQL la consulta. `eq_ref` y `PRIMARY` significan acceso por índice; `ALL` en la tabla externa es un recorrido completo, correcto en 744 filas.» (procesamiento de consultas) |
| 10 | **Rendimiento**: `python3 scripts/demo-500/prueba-rendimiento.py http://127.0.0.1:3000 50` y abrir `resultados-rendimiento.txt` | 500 peticiones, 0 errores. Aclarar: **500 peticiones no son 500 usuarios simultáneos**; se probaron 1, 10, 50 y 100 clientes simultáneos de lectura. |
| 11 | **Transacciones**: Explorador → Conceptos → «Transacciones (ACID)» y «Concurrencia» | `BEGIN` → `SELECT … FOR UPDATE` sobre la solicitud → `INSERT INTO viaje` (el trigger `viaje_ai` cierra la solicitud) → `COMMIT`. Si dos personas aceptan a la vez, la segunda espera el bloqueo y recibe 409: queda un solo viaje. |

### Si el profesor pide ver la aceptación en vivo

No lo hagas sobre la demostración real (añadiría un viaje). Usa la instancia desechable, que arranca en memoria con el seed original y se borra al terminar:

```bash
scripts/demo-500/demo-aislada.sh start    # http://127.0.0.1:3100
# En la interfaz: Usuarios → Solicitudes → dos Ofertas → Aceptar → Viajes (Iniciar/Finalizar) → Pagos → Calificaciones
scripts/demo-500/demo-aislada.sh test     # pruebas de integración, incluida la aceptación simultánea (201 y 409)
scripts/demo-500/demo-aislada.sh stop     # elimina todo; los 500 registros no se tocan
```

Para ver el rechazo de una operación inválida, intenta en esa instancia registrar dos usuarios con el mismo correo (UNIQUE) o eliminar un usuario con solicitudes (`RESTRICT`).

## Si algo falla

- La página no abre: `docker compose ps` debe mostrar `app` y `db` como *healthy*; si no, `scripts/demo-500/iniciar-indrive-lab.sh`.
- Puerto ocupado: cambia `PORT` o `DB_PORT` en `.env` (ver `docs/ARRANQUE.md`).
- **Nunca** ejecutes `docker compose down -v` ni limpiezas de Docker: borrarían el volumen con los 500 registros.
- Para terminar: `scripts/demo-500/detener-indrive-lab.sh` (usa `stop`, conserva los datos).

## Qué no hace el sistema (para responder con claridad)

No tiene autenticación, mapas, GPS ni pasarela de pago real; los pagos son registros académicos. No usa NoSQL: ese tema solo se explica como concepto.
