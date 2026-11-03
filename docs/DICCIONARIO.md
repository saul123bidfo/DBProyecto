# Diccionario del modelo físico

Exportado de INFORMATION_SCHEMA en MariaDB 11.8.6. La aplicación muestra el catálogo de su conexión activa; este anexo es una instantánea del esquema validado.

## calificacion

Evaluación del otro participante después del viaje

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_calificacion | int(11) | NO | — | PK | auto_increment |
| id_viaje | int(11) | NO | — | UNIQUE: uq_calificacion_autor, FK → viaje.id_viaje | — |
| id_usuario | int(11) | NO | — | UNIQUE: uq_calificacion_autor, FK → usuario.id_usuario | Autor; el destinatario es el otro participante |
| puntaje | tinyint(4) | NO | — | — | — |
| comentario | varchar(500) | NO | '' | — | — |

## conductor

Habilitación de una persona como conductor

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_conductor | int(11) | NO | — | PK | auto_increment |
| id_usuario | int(11) | NO | — | UNIQUE: id_usuario, FK → usuario.id_usuario | Perfil opcional de un usuario |
| licencia | varchar(20) | NO | — | UNIQUE: licencia | Licencia de conducir |

## oferta

Ofertas; la aceptación se representa mediante Viaje

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_oferta | int(11) | NO | — | PK | auto_increment |
| id_solicitud | int(11) | NO | — | UNIQUE: uq_oferta_solicitud_vehiculo, FK → solicitud.id_solicitud | — |
| placa | varchar(10) | NO | — | UNIQUE: uq_oferta_solicitud_vehiculo, FK → vehiculo.placa | Vehículo ofertante; determina al conductor |
| monto | decimal(10,2) | NO | — | — | Precio propuesto por el conductor, soles |
| tiempo_llegada | smallint(6) | NO | — | — | Minutos estimados de llegada |

## pago

Evidencia de cobro de un viaje finalizado

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_pago | int(11) | NO | — | PK | auto_increment |
| id_viaje | int(11) | NO | — | UNIQUE: id_viaje, FK → viaje.id_viaje | Un cobro por viaje |
| metodo | varchar(15) | NO | — | — | — |
| monto | decimal(10,2) | NO | — | — | Importe efectivamente cobrado, soles |
| comision | decimal(10,2) | NO | 0.00 | — | Importe de comisión, soles |
| fecha_pago | datetime | NO | current_timestamp() | — | — |

## solicitud

Solicitud y propuesta de precio del pasajero

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_solicitud | int(11) | NO | — | PK | auto_increment |
| id_usuario | int(11) | NO | — | FK → usuario.id_usuario | Pasajero solicitante |
| origen | varchar(200) | NO | — | — | — |
| destino | varchar(200) | NO | — | — | — |
| precio_ofrecido | decimal(10,2) | NO | — | — | Propuesta inicial en soles |
| estado | varchar(12) | NO | 'abierta' | — | — |
| fecha_solicitud | datetime | NO | current_timestamp() | — | — |

## usuario

Personas; cualquier usuario puede solicitar un viaje

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_usuario | int(11) | NO | — | PK | Identificador de persona |
| nombres | varchar(120) | NO | — | — | Nombres y apellidos |
| telefono | varchar(20) | NO | — | UNIQUE: telefono | Teléfono único con código de país |
| correo | varchar(160) | NO | — | UNIQUE: correo | Correo de contacto único |
| fecha_registro | datetime | NO | current_timestamp() | — | Fecha de alta |

## vehiculo

Vehículos de cada conductor

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| placa | varchar(10) | NO | — | PK | Placa única del vehículo |
| id_conductor | int(11) | NO | — | FK → conductor.id_conductor | Propietario del vehículo |
| marca | varchar(50) | NO | — | — | — |
| modelo | varchar(60) | NO | — | — | — |
| color | varchar(30) | NO | — | — | — |
| anio | smallint(6) | NO | — | — | Año de fabricación |

## viaje

Ejecución de una oferta aceptada; monto final derivado de Oferta

| Atributo | Tipo | Nulo | Predeterminado | Claves | Descripción |
|---|---|---|---|---|---|
| id_viaje | int(11) | NO | — | PK | auto_increment |
| id_oferta | int(11) | NO | — | UNIQUE: id_oferta, FK → oferta.id_oferta | — |
| estado | varchar(12) | NO | 'pendiente' | — | — |
| hora_inicio | datetime | YES | NULL | — | — |
| hora_fin | datetime | YES | NULL | — | — |

## Relaciones

| FK | Referencia | Borrado / actualización |
|---|---|---|
| calificacion.id_usuario | usuario.id_usuario | RESTRICT / RESTRICT |
| calificacion.id_viaje | viaje.id_viaje | RESTRICT / RESTRICT |
| pago.id_viaje | viaje.id_viaje | RESTRICT / RESTRICT |
| viaje.id_oferta | oferta.id_oferta | RESTRICT / RESTRICT |
| oferta.id_solicitud | solicitud.id_solicitud | RESTRICT / RESTRICT |
| oferta.placa | vehiculo.placa | RESTRICT / RESTRICT |
| solicitud.id_usuario | usuario.id_usuario | RESTRICT / RESTRICT |
| vehiculo.id_conductor | conductor.id_conductor | RESTRICT / RESTRICT |
| conductor.id_usuario | usuario.id_usuario | RESTRICT / RESTRICT |
