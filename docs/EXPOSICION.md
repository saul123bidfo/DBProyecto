# Guion de exposición

## Preparación

Iniciar el proyecto siguiendo README, con el seed en una base vacía. Comprobar “Base de datos conectada” y versión real en la barra lateral. Mostrar que los datos son ficticios de demostración y se almacenan en el motor. La aplicación administra todo el ejercicio desde una estación local; no pretende representar roles autenticados.

## Recorrido sugerido

1. Abrir el Explorador de Base de Datos. Mostrar las ocho tablas, las nueve FK, el diccionario y las restricciones. Explicar Usuario como pasajero o conductor opcional y por qué Oferta referencia el vehículo.
2. Abrir Usuarios y registrar un pasajero. Intentar repetir correo o teléfono: UNIQUE debe rechazarlo.
3. Crear una solicitud para ese pasajero con origen, destino y precio. Registrar dos ofertas desde los vehículos ABC-123 y BCD-234; comparar montos y tiempo de llegada.
4. Aceptar una oferta. Mostrar el nuevo Viaje pendiente y la Solicitud aceptada. Las ofertas restantes se muestran cerradas. Repetir la aceptación desde la API da conflicto; no crea otro viaje.
5. Iniciar y finalizar el viaje. Mostrar fechas reales y el precio final reconstruido mediante JOIN.
6. Registrar un pago seleccionando el viaje finalizado. El backend obtiene su importe pactado. Explicar por qué no se puede cobrar dos veces ni editar el importe.
7. Registrar una calificación del pasajero y otra del conductor. El selector de autor se filtra por participantes. Mostrar que el promedio del conductor se calcula con las evaluaciones recibidas del pasajero.
8. Intentar eliminar al pasajero o su conductor con historial. Mostrar rechazo y explicar RESTRICT frente a un borrado en cascada.
9. Ejecutar las seis consultas académicas. En promedio, modificar el mínimo de evaluaciones para demostrar HAVING. Si una consulta no devuelve filas después de cambiar los datos, explicar el conjunto vacío; no sustituirlo por resultados estáticos.
10. Actualizar la página para demostrar persistencia real. Desde otra sesión SQL, ejecutar `SELECT * FROM viaje;` y contrastar con la interfaz.

## Preguntas esperables

**¿Dónde está la 3FN?** Los nombres solo están en Usuario; el propietario solo en Vehículo; el precio negociado solo en Oferta; Viaje referencia Oferta y no vuelve a copiar el pasajero o conductor. La media se deriva mediante AVG.

**¿Por qué Pago tiene monto?** Es evidencia del cobro y se valida contra lo pactado al insertarse. No debe editarse después; método y comisión sí pueden corregirse en esta demostración.

**¿Cómo se evita la doble aceptación?** La operación bloquea la Solicitud mediante SELECT FOR UPDATE, verifica que esté abierta e inserta el viaje. Un trigger cierra la solicitud dentro de la misma transacción. Otra aceptación espera y luego encuentra la solicitud cerrada. Esa concurrencia debe comprobarse con la prueba HTTP en una instancia activa; la validación bootstrap solo comprueba las reglas secuenciales.

**¿Qué se corrigió en el informe?** Solo el orden 2.2/2.3 y la tabla técnica de la sección 7 con aclaraciones. El informe era ilustrativo; se documenta qué decisiones se adoptaron para convertirlo en un sistema ejecutable.

**¿Qué motor se comprobó?** MariaDB 11.8.6 en modo bootstrap. El objetivo de ejecución es MySQL 8.0.16+ con esquema compatible; la verificación directa de MySQL y de la aplicación completa se realiza al instalarla en un entorno que permita conexiones.
