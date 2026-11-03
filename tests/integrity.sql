USE indrive_academico;
DELIMITER $$
CREATE PROCEDURE esperar_error(IN sentencia TEXT, IN esperado INT)
BEGIN
 DECLARE codigo INT DEFAULT 0;
 BEGIN
  DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN GET DIAGNOSTICS CONDITION 1 codigo=MYSQL_ERRNO; END;
  SET @sentencia=sentencia;
  PREPARE caso FROM @sentencia;
  EXECUTE caso;
  DEALLOCATE PREPARE caso;
 END;
 IF codigo<>esperado THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='La restricción no rechazó el caso con el error esperado'; END IF;
END$$
CREATE PROCEDURE verificar()
BEGIN
 -- Errores MariaDB: 1062 UNIQUE; 1452 FK; 4025 CHECK; 1644 SIGNAL; 1451 RESTRICT.
 CALL esperar_error('INSERT INTO usuario(nombres,telefono,correo) VALUES (''Otro'',''+51941000001'',''otro@example.test'')',1062);
 CALL esperar_error('INSERT INTO conductor(id_usuario,licencia) VALUES(9999,''Z00000999'')',1452);
 CALL esperar_error('INSERT INTO oferta(id_solicitud,placa,monto,tiempo_llegada) VALUES(2,''BCD-234'',-1,5)',4025);
 CALL esperar_error('INSERT INTO oferta(id_solicitud,placa,monto,tiempo_llegada) VALUES(1,''CDE-345'',20,5)',1644);
 CALL esperar_error('INSERT INTO viaje(id_oferta) VALUES(2)',1644);
 CALL esperar_error('UPDATE oferta SET monto=25 WHERE id_oferta=1',1644);
 CALL esperar_error('UPDATE solicitud SET origen=''Otro origen'' WHERE id_solicitud=2',1644);
 CALL esperar_error('DELETE FROM usuario WHERE id_usuario=1',1451);
 CALL esperar_error('DELETE FROM viaje WHERE id_viaje=1',1644);
 CALL esperar_error('DELETE FROM pago WHERE id_pago=1',1644);
 CALL esperar_error('UPDATE vehiculo SET id_conductor=2 WHERE placa=''ABC-123''',1644);
 CALL esperar_error('INSERT INTO calificacion(id_viaje,id_usuario,puntaje) VALUES(1,4,5)',1644);
 CALL esperar_error('INSERT INTO calificacion(id_viaje,id_usuario,puntaje) VALUES(1,1,5)',1062);
 CALL esperar_error('INSERT INTO pago(id_viaje,metodo,monto,comision) VALUES(1,''efectivo'',21,0)',1644);
 CALL esperar_error('INSERT INTO pago(id_viaje,metodo,monto,comision) VALUES(1,''efectivo'',20,0)',1062);
 CALL esperar_error('UPDATE pago SET monto=19 WHERE id_pago=1',1644);
 CALL esperar_error('UPDATE calificacion SET id_usuario=4 WHERE id_calificacion=1',1644);
 CALL esperar_error('UPDATE calificacion SET puntaje=6 WHERE id_calificacion=1',4025);
 CALL esperar_error('UPDATE viaje SET estado=''pendiente'',hora_inicio=NULL,hora_fin=NULL WHERE id_viaje=1',1644);
 START TRANSACTION;
 INSERT INTO solicitud(id_usuario,origen,destino,precio_ofrecido) VALUES(2,'Punto A','Punto B',10);
 SET @propia=LAST_INSERT_ID();
 SET @sql_propia=CONCAT('INSERT INTO oferta(id_solicitud,placa,monto,tiempo_llegada) VALUES(',@propia,',''ABC-123'',10,5)');
 CALL esperar_error(@sql_propia,1644);
 ROLLBACK;
 -- Flujo positivo completo en transacción; ROLLBACK conserva el dataset inicial.
 START TRANSACTION;
 INSERT INTO viaje(id_oferta) VALUES(3);
 SET @viaje=LAST_INSERT_ID();
 IF (SELECT estado FROM solicitud WHERE id_solicitud=2)<>'aceptada' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='No se cerró la solicitud'; END IF;
 SET @pago_temprano=CONCAT('INSERT INTO pago(id_viaje,metodo,monto,comision) VALUES(',@viaje,',''efectivo'',17,0)');
 CALL esperar_error(@pago_temprano,1644);
 SET @fin_temprano=CONCAT('UPDATE viaje SET estado=''finalizado'',hora_inicio=NOW(),hora_fin=NOW() WHERE id_viaje=',@viaje);
 CALL esperar_error(@fin_temprano,1644);
 UPDATE viaje SET estado='en_curso',hora_inicio=NOW() WHERE id_viaje=@viaje;
 UPDATE viaje SET estado='finalizado',hora_fin=NOW() WHERE id_viaje=@viaje;
 INSERT INTO pago(id_viaje,metodo,monto,comision) VALUES(@viaje,'tarjeta',17,1);
 INSERT INTO calificacion(id_viaje,id_usuario,puntaje,comentario) VALUES(@viaje,4,4,'Correcto');
 UPDATE calificacion SET puntaje=5 WHERE id_viaje=@viaje AND id_usuario=4;
 UPDATE pago SET metodo='transferencia',comision=1.50 WHERE id_viaje=@viaje;
 ROLLBACK;
 START TRANSACTION;
 UPDATE solicitud SET estado='cancelada' WHERE id_solicitud=3;
 CALL esperar_error('INSERT INTO viaje(id_oferta) VALUES(4)',1644);
 ROLLBACK;
END$$
DELIMITER ;
CALL verificar();
DROP PROCEDURE verificar;
DROP PROCEDURE esperar_error;
