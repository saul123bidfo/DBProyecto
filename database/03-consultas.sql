USE indrive_academico;

-- Viajes y participantes: Reconstruye el viaje sin duplicar los nombres ni el precio final.
SELECT v.id_viaje, p.nombres AS pasajero, c.nombres AS conductor, s.origen, s.destino, o.placa, o.monto AS monto_final, v.estado, v.hora_inicio, v.hora_fin FROM viaje v JOIN oferta o ON o.id_oferta=v.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario p ON p.id_usuario=s.id_usuario JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario c ON c.id_usuario=d.id_usuario ORDER BY v.id_viaje DESC LIMIT 200;

-- Calificaciones de conductores: Solo cuenta evaluaciones emitidas por el pasajero. El mínimo de evaluaciones es un parámetro.
SET @minimo = 1;
SELECT d.id_conductor, u.nombres, COUNT(*) AS evaluaciones, ROUND(AVG(c.puntaje),2) AS calificacion_promedio FROM conductor d JOIN usuario u ON u.id_usuario=d.id_usuario JOIN vehiculo a ON a.id_conductor=d.id_conductor JOIN oferta o ON o.placa=a.placa JOIN viaje v ON v.id_oferta=o.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN calificacion c ON c.id_viaje=v.id_viaje AND c.id_usuario=s.id_usuario GROUP BY d.id_conductor,u.nombres HAVING COUNT(*)>=@minimo ORDER BY calificacion_promedio DESC LIMIT 200;

-- Ofertas bajo el promedio: Compara cada oferta con el promedio de ofertas de su misma solicitud.
SELECT o.id_oferta,o.id_solicitud,o.placa,o.monto FROM oferta o WHERE o.monto < (SELECT AVG(o2.monto) FROM oferta o2 WHERE o2.id_solicitud=o.id_solicitud) ORDER BY o.id_solicitud,o.monto LIMIT 200;

-- Solicitudes sin ofertas: Encuentra solicitudes abiertas que aún no recibieron propuestas.
SELECT s.id_solicitud,u.nombres,s.origen,s.destino,s.precio_ofrecido FROM solicitud s JOIN usuario u ON u.id_usuario=s.id_usuario LEFT JOIN oferta o ON o.id_solicitud=s.id_solicitud WHERE o.id_oferta IS NULL AND s.estado='abierta' ORDER BY s.fecha_solicitud LIMIT 200;

-- Cobros por método: Importes y comisiones realmente registrados; no se presume una tasa fija.
SELECT metodo,COUNT(*) AS pagos,SUM(monto) AS total_cobrado,SUM(comision) AS total_comisiones,SUM(monto-comision) AS neto_conductores FROM pago GROUP BY metodo ORDER BY total_cobrado DESC LIMIT 200;

-- Negociaciones abiertas: Ofertas activas, vehículo y persona conductora.
SELECT s.id_solicitud,s.origen,s.destino,s.precio_ofrecido,o.id_oferta,o.monto,o.tiempo_llegada,o.placa,u.nombres AS conductor FROM solicitud s JOIN oferta o ON o.id_solicitud=s.id_solicitud JOIN vehiculo a ON a.placa=o.placa JOIN conductor d ON d.id_conductor=a.id_conductor JOIN usuario u ON u.id_usuario=d.id_usuario WHERE s.estado='abierta' ORDER BY s.id_solicitud,o.monto LIMIT 200;
