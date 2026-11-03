-- Datos ficticios académicos insertados realmente en el motor. Ejecutar una sola vez.
USE indrive_academico;
START TRANSACTION;
INSERT INTO usuario (nombres,telefono,correo) VALUES
('Ana Torres','+51941000001','ana@example.test'),('Luis Quispe','+51941000002','luis@example.test'),
('Carla Mendoza','+51941000003','carla@example.test'),('Diego Flores','+51941000004','diego@example.test'),
('Sofía Ramos','+51941000005','sofia@example.test');
INSERT INTO conductor (id_usuario,licencia) VALUES (2,'Q12345678'),(3,'M87654321');
INSERT INTO vehiculo VALUES ('ABC-123',1,'Toyota','Yaris','Plata',2022),('BCD-234',2,'Kia','Rio','Azul',2021),('CDE-345',1,'Hyundai','Accent','Blanco',2023);
INSERT INTO solicitud (id_usuario,origen,destino,precio_ofrecido) VALUES
(1,'Universidad Norbert Wiener, Lima','Parque Kennedy, Miraflores',18.00),
(4,'Plaza San Miguel','Centro de Lima',16.00),
(5,'Barranco','San Isidro',20.00),
(1,'Estación Central','Jesús María',12.00);
INSERT INTO oferta (id_solicitud,placa,monto,tiempo_llegada) VALUES (1,'ABC-123',20,4),(1,'BCD-234',19,6),(2,'ABC-123',17,3),(3,'BCD-234',22,5);
INSERT INTO viaje (id_oferta) VALUES (1);
UPDATE viaje SET estado='en_curso',hora_inicio=NOW()-INTERVAL 40 MINUTE WHERE id_viaje=1;
UPDATE viaje SET estado='finalizado',hora_fin=NOW()-INTERVAL 10 MINUTE WHERE id_viaje=1;
INSERT INTO pago (id_viaje,metodo,monto,comision) VALUES (1,'efectivo',20,1.90);
INSERT INTO calificacion (id_viaje,id_usuario,puntaje,comentario) VALUES (1,1,5,'Buen trato y llegada puntual.'),(1,2,5,'Pasajera puntual.');
COMMIT;
