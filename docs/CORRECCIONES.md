# Correcciones y ampliaciones

Original conservado: `Informe_inDrive.docx`. Copia de entrega: `docs/Informe_inDrive_corregido.docx`. Generación reproducible: `python3 scripts/correct-report.py`.

| Ubicación | Cambio | Justificación |
|---|---|---|
| Cuerpo §2 | Colocar 2.2 antes de 2.3, sin reescribir sus párrafos | Coherencia con numeración e índice |
| §7 Usuario | Precisar PK y contactos únicos | Identidad y eliminación de duplicados prohibidos |
| §7 Conductor | Añadir FK id_usuario UNIQUE; promedio calculado | Perfil 0..1, sin acumulador inconsistente |
| §7 Vehículo | Añadir FK id_conductor | Materializar pertenencia declarada |
| §7 Solicitud | Añadir FK pasajero y fecha; concretar estados | Materializar quién solicita y conservar historial |
| §7 Oferta | Añadir FK solicitud y placa; conductor derivado; aceptación derivada del viaje | Representar vehículo concreto y evitar duplicar propietario/estado |
| §7 Viaje | Añadir FK oferta UNIQUE y estado; monto_final derivado | Aceptación única, avance del proceso, precio coherente |
| §7 Pago | Añadir FK viaje UNIQUE y fecha | Cobro vinculado y conservación del importe histórico |
| §7 Calificación | Añadir FK viaje y autor, UNIQUE compuesto y rango 1..5 | Participación verificable y una evaluación por autor |
| Después de la tabla §7 | Cuatro párrafos técnicos | Identificar motor elegido, reglas adoptadas, normalización y anexos; declarar verificación pendiente |

No se modifican misión, visión, productos, organigrama, FODA, conclusiones ni referencias. No se certifican cifras corporativas actuales. No se sustituye el motor de un modelo existente: el documento no indicaba ninguno. Los scripts, diagramas, 3FN y consultas se incorporan como desarrollos académicos nuevos, con su procedencia explícita.

La distinción entre hipótesis y fuente es importante: máximo un pago por viaje, escala de puntajes, estados y restricciones de edición son decisiones mínimas adoptadas para hacer ejecutable el ejemplo; no son políticas oficiales de inDrive.
