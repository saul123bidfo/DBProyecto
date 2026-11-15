-- Consultas para mostrar al profesor (solo lectura). Pegar en MySQL Workbench, conexión "inDrive Lab - MySQL 8".
USE indrive_academico;

-- 1) Los 500 registros de demostración (solicitudes de viaje ficticias en Lima, precios en soles)
SELECT COUNT(*) AS solicitudes_demo
FROM solicitud s JOIN usuario u ON u.id_usuario = s.id_usuario
WHERE u.correo LIKE '%@demo.indrive-lab.test';

-- 2) Ver las solicitudes (primeras 50; quite LIMIT para ver las 500)
SELECT s.id_solicitud, u.nombres AS pasajero, s.origen, s.destino,
       s.precio_ofrecido AS `precio S/`, s.estado, s.fecha_solicitud
FROM solicitud s JOIN usuario u ON u.id_usuario = s.id_usuario
WHERE u.correo LIKE '%@demo.indrive-lab.test'
ORDER BY s.id_solicitud LIMIT 50;

-- 3) Resumen por estado
SELECT s.estado, COUNT(*) AS solicitudes, ROUND(AVG(s.precio_ofrecido),2) AS `precio medio S/`
FROM solicitud s JOIN usuario u ON u.id_usuario = s.id_usuario
WHERE u.correo LIKE '%@demo.indrive-lab.test' GROUP BY s.estado;

-- 4) Solicitud -> ofertas -> conductor y vehículo (JOIN de 5 tablas)
SELECT s.id_solicitud, p.nombres AS pasajero, s.origen, s.destino, s.precio_ofrecido AS `pide S/`,
       o.monto AS `ofrece S/`, o.tiempo_llegada AS min_llegada, o.placa, c.nombres AS conductor
FROM solicitud s
JOIN usuario p ON p.id_usuario = s.id_usuario
JOIN oferta o ON o.id_solicitud = s.id_solicitud
JOIN vehiculo v ON v.placa = o.placa
JOIN conductor d ON d.id_conductor = v.id_conductor
JOIN usuario c ON c.id_usuario = d.id_usuario
WHERE p.correo LIKE '%@demo.indrive-lab.test'
ORDER BY s.id_solicitud, o.monto LIMIT 50;

-- 5) Viajes finalizados con pago y calificaciones
SELECT j.id_viaje, p.nombres AS pasajero, c.nombres AS conductor, o.placa, o.monto AS `monto S/`,
       pg.metodo, pg.comision AS `comision S/`, j.hora_inicio, j.hora_fin,
       (SELECT GROUP_CONCAT(k.puntaje ORDER BY k.id_calificacion) FROM calificacion k WHERE k.id_viaje = j.id_viaje) AS puntajes
FROM viaje j
JOIN oferta o ON o.id_oferta = j.id_oferta
JOIN solicitud s ON s.id_solicitud = o.id_solicitud
JOIN usuario p ON p.id_usuario = s.id_usuario
JOIN vehiculo v ON v.placa = o.placa
JOIN conductor d ON d.id_conductor = v.id_conductor
JOIN usuario c ON c.id_usuario = d.id_usuario
JOIN pago pg ON pg.id_viaje = j.id_viaje
WHERE j.estado = 'finalizado'
ORDER BY j.id_viaje LIMIT 30;

-- 6) Ingresos por método de pago (soles)
SELECT metodo, COUNT(*) AS pagos, SUM(monto) AS `total S/`, SUM(comision) AS `comisiones S/`
FROM pago GROUP BY metodo ORDER BY `total S/` DESC;

-- 7) Ranking de conductores por calificación recibida de pasajeros
SELECT u.nombres AS conductor, COUNT(*) AS evaluaciones, ROUND(AVG(k.puntaje),2) AS promedio
FROM calificacion k
JOIN viaje j ON j.id_viaje = k.id_viaje
JOIN oferta o ON o.id_oferta = j.id_oferta
JOIN solicitud s ON s.id_solicitud = o.id_solicitud AND s.id_usuario = k.id_usuario
JOIN vehiculo v ON v.placa = o.placa
JOIN conductor d ON d.id_conductor = v.id_conductor
JOIN usuario u ON u.id_usuario = d.id_usuario
GROUP BY d.id_conductor, u.nombres HAVING COUNT(*) >= 3
ORDER BY promedio DESC, evaluaciones DESC LIMIT 10;

-- 8) Integridad: restricciones y triggers existentes (8 tablas)
SELECT TABLE_NAME AS tabla, TABLE_ROWS AS filas_aprox FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'indrive_academico' AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME;
SELECT COUNT(*) AS triggers FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = 'indrive_academico';
SELECT COUNT(*) AS checks FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_SCHEMA = 'indrive_academico';
