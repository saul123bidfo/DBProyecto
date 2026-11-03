-- MySQL >=8.0.16 / MariaDB >=10.6; InnoDB, utf8mb4, importación sin DROP.
CREATE DATABASE IF NOT EXISTS indrive_academico CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE indrive_academico;
SET NAMES utf8mb4;
CREATE TABLE usuario (
 id_usuario INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Identificador de persona',
 nombres VARCHAR(120) NOT NULL COMMENT 'Nombres y apellidos',
 telefono VARCHAR(20) NOT NULL UNIQUE COMMENT 'Teléfono único con código de país',
 correo VARCHAR(160) NOT NULL UNIQUE COMMENT 'Correo de contacto único',
 fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de alta',
 CONSTRAINT ck_usuario_nombre CHECK (CHAR_LENGTH(TRIM(nombres)) > 0),
 CONSTRAINT ck_usuario_telefono CHECK (CHAR_LENGTH(TRIM(telefono)) >= 7),
 CONSTRAINT ck_usuario_correo CHECK (correo LIKE '%_@_%._%')
) ENGINE=InnoDB COMMENT='Personas; cualquier usuario puede solicitar un viaje';
CREATE TABLE conductor (
 id_conductor INT AUTO_INCREMENT PRIMARY KEY,
 id_usuario INT NOT NULL UNIQUE COMMENT 'Perfil opcional de un usuario',
 licencia VARCHAR(20) NOT NULL UNIQUE COMMENT 'Licencia de conducir',
 CONSTRAINT fk_conductor_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_conductor_licencia CHECK (CHAR_LENGTH(TRIM(licencia)) >= 5)
) ENGINE=InnoDB COMMENT='Habilitación de una persona como conductor';
CREATE TABLE vehiculo (
 placa VARCHAR(10) PRIMARY KEY COMMENT 'Placa única del vehículo',
 id_conductor INT NOT NULL COMMENT 'Propietario del vehículo',
 marca VARCHAR(50) NOT NULL,
 modelo VARCHAR(60) NOT NULL,
 color VARCHAR(30) NOT NULL,
 anio SMALLINT NOT NULL COMMENT 'Año de fabricación',
 CONSTRAINT fk_vehiculo_conductor FOREIGN KEY (id_conductor) REFERENCES conductor(id_conductor) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_vehiculo_anio CHECK (anio BETWEEN 1980 AND 2100),
 CONSTRAINT ck_vehiculo_textos CHECK (CHAR_LENGTH(TRIM(placa)) BETWEEN 5 AND 10 AND CHAR_LENGTH(TRIM(marca))>0 AND CHAR_LENGTH(TRIM(modelo))>0 AND CHAR_LENGTH(TRIM(color))>0)
) ENGINE=InnoDB COMMENT='Vehículos de cada conductor';
CREATE TABLE solicitud (
 id_solicitud INT AUTO_INCREMENT PRIMARY KEY,
 id_usuario INT NOT NULL COMMENT 'Pasajero solicitante',
 origen VARCHAR(200) NOT NULL,
 destino VARCHAR(200) NOT NULL,
 precio_ofrecido DECIMAL(10,2) NOT NULL COMMENT 'Propuesta inicial en soles',
 estado VARCHAR(12) NOT NULL DEFAULT 'abierta',
 fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_solicitud_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_solicitud_precio CHECK (precio_ofrecido > 0),
 CONSTRAINT ck_solicitud_estado CHECK (estado IN ('abierta','aceptada','cancelada')),
 CONSTRAINT ck_solicitud_ruta CHECK (CHAR_LENGTH(TRIM(origen))>0 AND CHAR_LENGTH(TRIM(destino))>0 AND TRIM(origen)<>TRIM(destino)),
 INDEX ix_solicitud_estado_fecha (estado,fecha_solicitud)
) ENGINE=InnoDB COMMENT='Solicitud y propuesta de precio del pasajero';
CREATE TABLE oferta (
 id_oferta INT AUTO_INCREMENT PRIMARY KEY,
 id_solicitud INT NOT NULL,
 placa VARCHAR(10) NOT NULL COMMENT 'Vehículo ofertante; determina al conductor',
 monto DECIMAL(10,2) NOT NULL COMMENT 'Precio propuesto por el conductor, soles',
 tiempo_llegada SMALLINT NOT NULL COMMENT 'Minutos estimados de llegada',
 CONSTRAINT uq_oferta_solicitud_vehiculo UNIQUE (id_solicitud,placa),
 CONSTRAINT fk_oferta_solicitud FOREIGN KEY (id_solicitud) REFERENCES solicitud(id_solicitud) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT fk_oferta_vehiculo FOREIGN KEY (placa) REFERENCES vehiculo(placa) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_oferta_monto CHECK (monto>0),
 CONSTRAINT ck_oferta_tiempo CHECK (tiempo_llegada BETWEEN 1 AND 240)
) ENGINE=InnoDB COMMENT='Ofertas; la aceptación se representa mediante Viaje';
CREATE TABLE viaje (
 id_viaje INT AUTO_INCREMENT PRIMARY KEY,
 id_oferta INT NOT NULL UNIQUE,
 estado VARCHAR(12) NOT NULL DEFAULT 'pendiente',
 hora_inicio DATETIME NULL,
 hora_fin DATETIME NULL,
 CONSTRAINT fk_viaje_oferta FOREIGN KEY (id_oferta) REFERENCES oferta(id_oferta) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_viaje_fechas CHECK (
 (estado='pendiente' AND hora_inicio IS NULL AND hora_fin IS NULL) OR
 (estado='en_curso' AND hora_inicio IS NOT NULL AND hora_fin IS NULL) OR
 (estado='finalizado' AND hora_inicio IS NOT NULL AND hora_fin IS NOT NULL AND hora_fin>=hora_inicio))
) ENGINE=InnoDB COMMENT='Ejecución de una oferta aceptada; monto final derivado de Oferta';
CREATE TABLE pago (
 id_pago INT AUTO_INCREMENT PRIMARY KEY,
 id_viaje INT NOT NULL UNIQUE COMMENT 'Un cobro por viaje',
 metodo VARCHAR(15) NOT NULL,
 monto DECIMAL(10,2) NOT NULL COMMENT 'Importe efectivamente cobrado, soles',
 comision DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT 'Importe de comisión, soles',
 fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_pago_viaje FOREIGN KEY (id_viaje) REFERENCES viaje(id_viaje) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_pago_montos CHECK (monto>0 AND comision>=0 AND comision<=monto),
 CONSTRAINT ck_pago_metodo CHECK (metodo IN ('efectivo','tarjeta','transferencia'))
) ENGINE=InnoDB COMMENT='Evidencia de cobro de un viaje finalizado';
CREATE TABLE calificacion (
 id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
 id_viaje INT NOT NULL,
 id_usuario INT NOT NULL COMMENT 'Autor; el destinatario es el otro participante',
 puntaje TINYINT NOT NULL,
 comentario VARCHAR(500) NOT NULL DEFAULT '',
 CONSTRAINT uq_calificacion_autor UNIQUE (id_viaje,id_usuario),
 CONSTRAINT fk_calificacion_viaje FOREIGN KEY (id_viaje) REFERENCES viaje(id_viaje) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT fk_calificacion_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT,
 CONSTRAINT ck_calificacion_puntaje CHECK (puntaje BETWEEN 1 AND 5)
) ENGINE=InnoDB COMMENT='Evaluación del otro participante después del viaje';

DELIMITER $$
CREATE TRIGGER solicitud_bi BEFORE INSERT ON solicitud FOR EACH ROW
BEGIN
 IF NEW.estado <> 'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Una solicitud debe crearse abierta'; END IF;
END$$
CREATE TRIGGER solicitud_bu BEFORE UPDATE ON solicitud FOR EACH ROW
BEGIN
 IF OLD.estado <> 'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La solicitud cerrada conserva su historial'; END IF;
 IF NEW.id_usuario<>OLD.id_usuario OR NEW.id_solicitud<>OLD.id_solicitud OR NEW.fecha_solicitud<>OLD.fecha_solicitud THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Identidad de solicitud inmutable'; END IF;
 IF EXISTS(SELECT 1 FROM oferta WHERE id_solicitud=OLD.id_solicitud) AND
 (NEW.origen<>OLD.origen OR NEW.destino<>OLD.destino OR NEW.precio_ofrecido<>OLD.precio_ofrecido) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se modifica una solicitud que ya recibió ofertas'; END IF;
 IF NEW.estado='aceptada' AND NOT EXISTS(SELECT 1 FROM viaje v JOIN oferta o ON o.id_oferta=v.id_oferta WHERE o.id_solicitud=OLD.id_solicitud) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Acepte una oferta para generar el viaje'; END IF;
END$$
CREATE TRIGGER solicitud_bd BEFORE DELETE ON solicitud FOR EACH ROW
BEGIN
 IF OLD.estado<>'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se elimina el historial de solicitudes'; END IF;
END$$
CREATE TRIGGER conductor_bu BEFORE UPDATE ON conductor FOR EACH ROW
BEGIN
 IF NEW.id_usuario<>OLD.id_usuario OR NEW.id_conductor<>OLD.id_conductor THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Identidad del conductor inmutable'; END IF;
END$$
CREATE TRIGGER vehiculo_bu BEFORE UPDATE ON vehiculo FOR EACH ROW
BEGIN
 IF NEW.placa<>OLD.placa OR (NEW.id_conductor<>OLD.id_conductor AND EXISTS(SELECT 1 FROM oferta WHERE placa=OLD.placa)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se puede reasignar un vehículo con ofertas'; END IF;
END$$
CREATE TRIGGER oferta_bi BEFORE INSERT ON oferta FOR EACH ROW
BEGIN
 DECLARE s_estado VARCHAR(12); DECLARE pasajero INT; DECLARE chofer INT;
 SELECT estado,id_usuario INTO s_estado,pasajero FROM solicitud WHERE id_solicitud=NEW.id_solicitud FOR UPDATE;
 SELECT c.id_usuario INTO chofer FROM vehiculo v JOIN conductor c ON c.id_conductor=v.id_conductor WHERE v.placa=NEW.placa;
 IF s_estado<>'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La solicitud no está abierta'; END IF;
 IF pasajero=chofer THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se puede ofertar en una solicitud propia'; END IF;
END$$
CREATE TRIGGER oferta_bu BEFORE UPDATE ON oferta FOR EACH ROW
BEGIN
 DECLARE s_estado VARCHAR(12);
 SELECT estado INTO s_estado FROM solicitud WHERE id_solicitud=OLD.id_solicitud FOR UPDATE;
 IF s_estado<>'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Oferta cerrada: conserve el precio acordado'; END IF;
 IF NEW.id_oferta<>OLD.id_oferta OR NEW.id_solicitud<>OLD.id_solicitud OR NEW.placa<>OLD.placa THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Identidad de oferta inmutable'; END IF;
END$$
CREATE TRIGGER oferta_bd BEFORE DELETE ON oferta FOR EACH ROW
BEGIN
 DECLARE s_estado VARCHAR(12);
 SELECT estado INTO s_estado FROM solicitud WHERE id_solicitud=OLD.id_solicitud FOR UPDATE;
 IF s_estado<>'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se elimina una oferta cerrada'; END IF;
END$$
CREATE TRIGGER viaje_bi BEFORE INSERT ON viaje FOR EACH ROW
BEGIN
 DECLARE s_id INT; DECLARE s_estado VARCHAR(12);
 SELECT id_solicitud INTO s_id FROM oferta WHERE id_oferta=NEW.id_oferta;
 SELECT estado INTO s_estado FROM solicitud WHERE id_solicitud=s_id FOR UPDATE;
 IF s_estado<>'abierta' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Esta solicitud ya fue aceptada o cancelada'; END IF;
 IF NEW.estado<>'pendiente' OR NEW.hora_inicio IS NOT NULL OR NEW.hora_fin IS NOT NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='El viaje debe crearse pendiente'; END IF;
END$$
CREATE TRIGGER viaje_ai AFTER INSERT ON viaje FOR EACH ROW
BEGIN
 UPDATE solicitud SET estado='aceptada' WHERE id_solicitud=(SELECT id_solicitud FROM oferta WHERE id_oferta=NEW.id_oferta);
END$$
CREATE TRIGGER viaje_bu BEFORE UPDATE ON viaje FOR EACH ROW
BEGIN
 IF NEW.id_oferta<>OLD.id_oferta OR NEW.id_viaje<>OLD.id_viaje THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Identidad del viaje inmutable'; END IF;
 IF NOT ((OLD.estado='pendiente' AND NEW.estado='en_curso') OR (OLD.estado='en_curso' AND NEW.estado='finalizado' AND NEW.hora_inicio=OLD.hora_inicio)) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Transición de viaje inválida'; END IF;
 IF NEW.hora_inicio>CURRENT_TIMESTAMP OR NEW.hora_fin>CURRENT_TIMESTAMP THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Las fechas no pueden estar en el futuro'; END IF;
END$$
CREATE TRIGGER viaje_bd BEFORE DELETE ON viaje FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Los viajes se conservan como historial'; END$$
CREATE TRIGGER pago_bi BEFORE INSERT ON pago FOR EACH ROW
BEGIN
 DECLARE v_estado VARCHAR(12); DECLARE precio DECIMAL(10,2);
 SELECT v.estado,o.monto INTO v_estado,precio FROM viaje v JOIN oferta o ON o.id_oferta=v.id_oferta WHERE v.id_viaje=NEW.id_viaje FOR UPDATE;
 IF v_estado<>'finalizado' OR NEW.monto<>precio THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Solo se cobra un viaje finalizado por el precio acordado'; END IF;
END$$
CREATE TRIGGER pago_bu BEFORE UPDATE ON pago FOR EACH ROW
BEGIN
 IF NEW.id_pago<>OLD.id_pago OR NEW.id_viaje<>OLD.id_viaje OR NEW.monto<>OLD.monto OR NEW.fecha_pago<>OLD.fecha_pago THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='El importe e identidad del pago son históricos'; END IF;
END$$
CREATE TRIGGER pago_bd BEFORE DELETE ON pago FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se elimina un cobro histórico'; END$$
CREATE TRIGGER calificacion_bi BEFORE INSERT ON calificacion FOR EACH ROW
BEGIN
 DECLARE v_estado VARCHAR(12); DECLARE pasajero INT; DECLARE chofer INT;
 SELECT v.estado,s.id_usuario,c.id_usuario INTO v_estado,pasajero,chofer FROM viaje v JOIN oferta o ON o.id_oferta=v.id_oferta JOIN solicitud s ON s.id_solicitud=o.id_solicitud JOIN vehiculo a ON a.placa=o.placa JOIN conductor c ON c.id_conductor=a.id_conductor WHERE v.id_viaje=NEW.id_viaje FOR UPDATE;
 IF v_estado<>'finalizado' OR NEW.id_usuario NOT IN (pasajero,chofer) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Solo participantes de viajes finalizados pueden calificar'; END IF;
END$$
CREATE TRIGGER calificacion_bu BEFORE UPDATE ON calificacion FOR EACH ROW
BEGIN
 IF NEW.id_calificacion<>OLD.id_calificacion OR NEW.id_viaje<>OLD.id_viaje OR NEW.id_usuario<>OLD.id_usuario THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Autor y viaje de la calificación son inmutables'; END IF;
END$$
CREATE TRIGGER calificacion_bd BEFORE DELETE ON calificacion FOR EACH ROW
BEGIN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Las calificaciones se conservan como historial'; END$$
DELIMITER ;
