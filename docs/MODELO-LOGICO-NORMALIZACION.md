# Modelo lógico, dependencias y normalización

Fuente: [DDL](../database/01-schema.sql); [diccionario físico](DICCIONARIO.md); [ER y EER](MODELOS-ER-EER.md). Las claves listadas suponen las reglas de negocio actuales. Los identificadores artificiales son PK; las demás claves candidatas están garantizadas por UNIQUE y NOT NULL.

## Relaciones

- USUARIO(**id_usuario**, nombres, telefono, correo, fecha_registro); candidatas: id_usuario, telefono, correo.
- CONDUCTOR(**id_conductor**, id_usuario FK → USUARIO.id_usuario, licencia); candidatas: id_conductor, id_usuario, licencia.
- VEHICULO(**placa**, id_conductor FK → CONDUCTOR.id_conductor, marca, modelo, color, anio); candidata: placa.
- SOLICITUD(**id_solicitud**, id_usuario FK → USUARIO.id_usuario, origen, destino, precio_ofrecido, estado, fecha_solicitud); candidata: id_solicitud.
- OFERTA(**id_oferta**, id_solicitud FK → SOLICITUD.id_solicitud, placa FK → VEHICULO.placa, monto, tiempo_llegada); candidatas: id_oferta y (id_solicitud, placa).
- VIAJE(**id_viaje**, id_oferta FK → OFERTA.id_oferta, estado, hora_inicio, hora_fin); candidatas: id_viaje, id_oferta.
- PAGO(**id_pago**, id_viaje FK → VIAJE.id_viaje, metodo, monto, comision, fecha_pago); candidatas: id_pago, id_viaje.
- CALIFICACION(**id_calificacion**, id_viaje FK → VIAJE.id_viaje, id_usuario FK → USUARIO.id_usuario, puntaje, comentario); candidatas: id_calificacion y (id_viaje, id_usuario).

Las nueve FK son obligatorias y aplican RESTRICT al borrar o actualizar el padre. Las fechas del viaje son las únicas columnas explícitamente anulables. Los valores por defecto, tamaños y precisión se muestran en el diccionario; las restricciones entre tablas se enumeran más abajo.

## Dependencias funcionales

Cada clave candidata determina todos los atributos de su relación. En particular:

| Relación | Determinantes | Atributos determinados |
|---|---|---|
| USUARIO | id_usuario; telefono; correo | nombres, telefono, correo, fecha_registro e id_usuario |
| CONDUCTOR | id_conductor; id_usuario; licencia | id_conductor, id_usuario, licencia |
| VEHICULO | placa | id_conductor, marca, modelo, color, anio |
| SOLICITUD | id_solicitud | id_usuario, origen, destino, precio_ofrecido, estado, fecha_solicitud |
| OFERTA | id_oferta; (id_solicitud, placa) | id_oferta, id_solicitud, placa, monto, tiempo_llegada |
| VIAJE | id_viaje; id_oferta | id_viaje, id_oferta, estado, hora_inicio, hora_fin |
| PAGO | id_pago; id_viaje | id_pago, id_viaje, metodo, monto, comision, fecha_pago |
| CALIFICACION | id_calificacion; (id_viaje, id_usuario) | id_calificacion, id_viaje, id_usuario, puntaje, comentario |

Cada punto y coma separa determinantes alternativos, no partes de una misma clave. Las dependencias se basan en las restricciones y supuestos del ejercicio: no se supone que modelo determine marca ni que un nombre identifique una persona.

## Justificación hasta 3FN

- **1FN:** los campos contienen valores individuales; las ofertas y vehículos se representan en filas separadas. No hay listas almacenadas en una celda.
- **2FN:** las claves simples no tienen partes propias. Para las candidatas compuestas de Oferta y Calificación se asume, respectivamente, que ni la solicitud ni la placa por sí sola determina el monto/tiempo de una oferta, y que ni el viaje ni el autor por sí solo determina su evaluación. Por tanto no se identifica dependencia parcial de atributos no clave.
- **3FN:** con las dependencias declaradas no se identifica un atributo no clave que determine otro no clave dentro de una tabla. Nombres quedan en Usuario, el conductor se obtiene por Vehículo y el monto pactado por Oferta. No se almacena el promedio del conductor. La conclusión depende de los supuestos, no se deduce únicamente de que las PK sean simples.

Pago guarda un monto que debe coincidir con Oferta al crearse: es una redundancia **entre relaciones** para registrar el cobro, verificada por trigger. Como id_viaje es candidata de Pago, esa duplicación por sí sola no prueba una infracción de 3FN dentro de Pago; sí exige explicar el control de consistencia.

## Dominios y reglas principales

Además de tipos y nulabilidad del diccionario: nombre no vacío; teléfono de al menos siete caracteres; correo con patrón básico; licencia de al menos cinco; placa de 5 a 10; marca, modelo y color no vacíos; año 1980–2100. Solicitud exige origen y destino distintos y precio positivo; estados abierta, aceptada o cancelada. Oferta exige monto positivo y llegada de 1–240 minutos. Viaje admite pendiente, en_curso y finalizado con fechas acordes. Pago acepta efectivo, tarjeta o transferencia, monto positivo y comisión entre 0 y monto. Calificación exige puntaje entero de 1–5.

Los triggers exigen, entre otras reglas, que el conductor no oferte en su solicitud, que solo una oferta se acepte por solicitud, que el pago corresponda a un viaje finalizado por el monto pactado y que solo participantes califiquen. Las solicitudes cerradas y el historial quedan protegidos. El control de esas reglas se debe explicar junto con las restricciones declarativas, no como si todas fueran FK.
