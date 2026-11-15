-- Verificación del conjunto de demostración de inDrive Lab (solo lectura).
-- Conjunto de demostración = solicitudes cuyo pasajero tiene correo @demo.indrive-lab.test
-- Ejecutar en MySQL Workbench (conexión "inDrive Lab - MySQL 8") o con:
--   docker compose exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -t' < scripts/demo-500/verificar-demo.sql
USE indrive_academico;

-- 1. Totales generales (originales + demostración)
SELECT 'usuarios' AS tabla, COUNT(*) AS filas FROM usuario
UNION ALL SELECT 'conductores', COUNT(*) FROM conductor
UNION ALL SELECT 'vehiculos', COUNT(*) FROM vehiculo
UNION ALL SELECT 'solicitudes', COUNT(*) FROM solicitud
UNION ALL SELECT 'ofertas', COUNT(*) FROM oferta
UNION ALL SELECT 'viajes', COUNT(*) FROM viaje
UNION ALL SELECT 'pagos', COUNT(*) FROM pago
UNION ALL SELECT 'calificaciones', COUNT(*) FROM calificacion;

-- 2. Conjunto de demostración: debe haber EXACTAMENTE 500 solicitudes
SELECT COUNT(*) AS solicitudes_demo,
       IF(COUNT(*)=500,'OK: exactamente 500','FALLA: no son 500') AS resultado
FROM solicitud s JOIN usuario u ON u.id_usuario=s.id_usuario
WHERE u.correo LIKE '%@demo.indrive-lab.test';

-- 3. Solicitudes demo por estado
SELECT s.estado, COUNT(*) AS solicitudes
FROM solicitud s JOIN usuario u ON u.id_usuario=s.id_usuario
WHERE u.correo LIKE '%@demo.indrive-lab.test' GROUP BY s.estado ORDER BY s.estado;

-- 4. Ofertas, viajes, pagos y calificaciones del conjunto demo
SELECT (SELECT COUNT(*) FROM oferta o JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario u ON u.id_usuario=s.id_usuario WHERE u.correo LIKE '%@demo.indrive-lab.test') AS ofertas_demo,
       (SELECT COUNT(*) FROM viaje j JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario u ON u.id_usuario=s.id_usuario WHERE u.correo LIKE '%@demo.indrive-lab.test') AS viajes_demo,
       (SELECT COUNT(*) FROM pago p JOIN viaje j ON j.id_viaje=p.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario u ON u.id_usuario=s.id_usuario WHERE u.correo LIKE '%@demo.indrive-lab.test') AS pagos_demo,
       (SELECT COUNT(*) FROM calificacion c JOIN viaje j ON j.id_viaje=c.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN usuario u ON u.id_usuario=s.id_usuario WHERE u.correo LIKE '%@demo.indrive-lab.test') AS calificaciones_demo;

-- 5. Viajes por estado (todos)
SELECT estado, COUNT(*) AS viajes FROM viaje GROUP BY estado ORDER BY estado;

-- 6. Integridad referencial: cada consulta debe devolver 0 filas huérfanas
SELECT 'conductor sin usuario' AS control, COUNT(*) AS huerfanos FROM conductor c LEFT JOIN usuario u ON u.id_usuario=c.id_usuario WHERE u.id_usuario IS NULL
UNION ALL SELECT 'vehiculo sin conductor', COUNT(*) FROM vehiculo v LEFT JOIN conductor c ON c.id_conductor=v.id_conductor WHERE c.id_conductor IS NULL
UNION ALL SELECT 'solicitud sin usuario', COUNT(*) FROM solicitud s LEFT JOIN usuario u ON u.id_usuario=s.id_usuario WHERE u.id_usuario IS NULL
UNION ALL SELECT 'oferta sin solicitud', COUNT(*) FROM oferta o LEFT JOIN solicitud s ON s.id_solicitud=o.id_solicitud WHERE s.id_solicitud IS NULL
UNION ALL SELECT 'oferta sin vehiculo', COUNT(*) FROM oferta o LEFT JOIN vehiculo v ON v.placa=o.placa WHERE v.placa IS NULL
UNION ALL SELECT 'viaje sin oferta', COUNT(*) FROM viaje j LEFT JOIN oferta o ON o.id_oferta=j.id_oferta WHERE o.id_oferta IS NULL
UNION ALL SELECT 'pago sin viaje', COUNT(*) FROM pago p LEFT JOIN viaje j ON j.id_viaje=p.id_viaje WHERE j.id_viaje IS NULL
UNION ALL SELECT 'calificacion sin viaje', COUNT(*) FROM calificacion c LEFT JOIN viaje j ON j.id_viaje=c.id_viaje WHERE j.id_viaje IS NULL
UNION ALL SELECT 'calificacion sin autor', COUNT(*) FROM calificacion c LEFT JOIN usuario u ON u.id_usuario=c.id_usuario WHERE u.id_usuario IS NULL;

-- 7. Reglas de negocio (0 = correcto)
SELECT 'pago distinto al monto de la oferta' AS control, COUNT(*) AS violaciones FROM pago p JOIN viaje j ON j.id_viaje=p.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta WHERE p.monto<>o.monto
UNION ALL SELECT 'pago de viaje no finalizado', COUNT(*) FROM pago p JOIN viaje j ON j.id_viaje=p.id_viaje WHERE j.estado<>'finalizado'
UNION ALL SELECT 'solicitud aceptada sin viaje', COUNT(*) FROM solicitud s WHERE s.estado='aceptada' AND NOT EXISTS (SELECT 1 FROM viaje j JOIN oferta o ON o.id_oferta=j.id_oferta WHERE o.id_solicitud=s.id_solicitud)
UNION ALL SELECT 'viaje con solicitud no aceptada', COUNT(*) FROM viaje j JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud WHERE s.estado<>'aceptada'
UNION ALL SELECT 'oferta del propio pasajero', COUNT(*) FROM oferta o JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN vehiculo v ON v.placa=o.placa JOIN conductor c ON c.id_conductor=v.id_conductor WHERE c.id_usuario=s.id_usuario
UNION ALL SELECT 'calificacion de no participante', COUNT(*) FROM calificacion k JOIN viaje j ON j.id_viaje=k.id_viaje JOIN oferta o ON o.id_oferta=j.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN vehiculo v ON v.placa=o.placa JOIN conductor c ON c.id_conductor=v.id_conductor WHERE k.id_usuario NOT IN (s.id_usuario,c.id_usuario);

-- 8. Duplicados del conjunto demo (deben ser 0)
SELECT COUNT(*) AS correos_demo_duplicados FROM (SELECT correo FROM usuario WHERE correo LIKE '%@demo.indrive-lab.test' GROUP BY correo HAVING COUNT(*)>1) d;
