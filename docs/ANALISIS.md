# Análisis previo del informe

Fuente: `Informe_inDrive.docx`, leído íntegramente, incluidas sus tablas, referencias y dos imágenes (logotipo universitario y organigrama ejecutivo). No hay anexos SQL ni diagramas de datos. El organigrama es organizacional, no un MER.

## Problema y alcance

La sección 7 describe la necesidad de conservar usuarios, conductores, solicitudes, ofertas, viajes, pagos y calificaciones de forma consistente. La sección 2.3 establece el flujo: pasajero propone precio, conductores ofertan y el pasajero elige. Se implementa exclusivamente ese flujo urbano como ejercicio académico, sin afirmar representar la base real de inDrive. Delivery, inversiones, finanzas, publicidad, organigrama y FODA son contexto empresarial y no módulos de gestión solicitados por el modelo.

## Hallazgos

- El informe es una descripción empresarial con un modelo ilustrativo inicial, no una especificación física. No define motor, SQL, cardinalidades completas, nulabilidad ni políticas de borrado. Se elige MySQL 8.0.16+ con InnoDB; MariaDB 11.8 se admite como compatibilidad verificable, sin presentarlo como MySQL.
- Las ocho entidades se conservan. Faltan los atributos que materializan las relaciones; se añaden las FK mínimas.
- Usuario sirve de pasajero y, opcionalmente, de conductor: no se duplica una entidad Pasajero. Conductor tiene FK UNIQUE a Usuario (0..1 perfil por usuario).
- Vehículo pertenece a exactamente un conductor. Una oferta selecciona un vehículo existente; el conductor se deriva del vehículo, evitando duplicarlo en Oferta. Un vehículo que ya tiene ofertas no se reasigna.
- Oferta relaciona Solicitud y Vehículo. Se permite una oferta por vehículo y solicitud; un conductor con varios vehículos puede proponer alternativas. No puede ofertar sobre su propia solicitud.
- Viaje nace de una oferta seleccionada. UNIQUE(id_oferta), junto con bloqueo de la solicitud al aceptar, impide aceptar dos ofertas de la misma solicitud por la API. Un trigger también verifica esta regla al insertar un viaje directamente.
- No se almacena el estado «aceptada» en Oferta: la existencia de Viaje significa aceptación. Las demás ofertas quedan cerradas al salir Solicitud del estado abierta. Esto evita duplicar hechos entre tablas.
- La calificación promedio del conductor es un agregado derivado, no un atributo almacenado. Se muestra mediante consulta SQL.
- Calificación debe indicar viaje y autor. El destinatario es el otro participante y se deriva del viaje. UNIQUE(viaje, autor); puntaje entero 1..5; solo participantes de viajes finalizados.
- Precio de solicitud y oferta son positivos; el monto final es el precio de la oferta seleccionada. No se vuelve a almacenarlo en Viaje, para evitar una dependencia transitiva. La interfaz y consultas lo exponen como monto_final.
- Se adopta un pago único por viaje finalizado. No se implementan cuotas ni reembolsos, ausentes del informe. Monto del pago debe coincidir con oferta y comisión entre 0 y monto. No se fija 9.5% como regla global: el informe lo atribuye a una entrevista y no define una tarifa contractual.
- Estados definidos para la demostración: solicitud abierta/aceptada/cancelada; viaje pendiente/en_curso/finalizado. Fechas coherentes según estado. La cancelación se permite antes de aceptar. No se inventan cancelaciones de viajes cobrados.
- El borrado de maestros sin referencias está permitido; FK RESTRICT conserva el historial. Solicitudes abiertas sin ofertas, y ofertas sin viaje de solicitudes abiertas, pueden borrarse. Viajes, pagos y calificaciones no se borran por la aplicación. Calificaciones permiten corregir puntaje/comentario sin cambiar autor o viaje; pagos permiten corregir método/comisión sin modificar el importe histórico.
- El índice lista 2.2 antes de 2.3, pero el cuerpo presenta 2.3 antes de 2.2. La versión corregida reordena únicamente esos bloques y amplía la sección 7 para coherencia técnica. Se conservan afirmaciones y referencias empresariales, que no se utilizan como especificación de software ni se certifican como verificación de mercado actual.

## Requerimientos trazables

| Fuente | Funcionalidad |
|---|---|
| Tabla §7 Usuario | CRUD, búsqueda y selección de pasajeros |
| Tabla §7 Conductor/Vehículo | CRUD, licencia/placa únicas, selección de propietarios |
| §2.3 y §7 Solicitud/Oferta | Proponer precio, registrar/editar ofertas válidas, aceptar una transaccionalmente, cancelar solicitud abierta |
| Tabla §7 Viaje | Consultar, iniciar y finalizar con fechas; conservar historial |
| Tabla §7 Pago | Registrar cobro real vinculado al viaje y corregir método/comisión |
| Tabla §7 Calificación | Registrar/corregir evaluación por participante; media calculada |
| Requerimiento del proyecto | Explorador real de metadatos, diccionario, restricciones, MER y consultas predefinidas |

## Modelos y normalización

Conceptual: personas solicitan viajes; personas habilitadas como conductores poseen vehículos; vehículos reciben propuestas asociadas a solicitudes; una propuesta elegida origina un viaje, al que corresponden un pago y las evaluaciones de sus participantes.

Relaciones lógicas: Usuario 1—0..1 Conductor; Conductor 1—0..N Vehículo; Usuario 1—0..N Solicitud; Solicitud 1—0..N Oferta; Vehículo 1—0..N Oferta; Oferta 1—0..1 Viaje; Viaje 1—0..1 Pago; Viaje 1—0..2 Calificación; Usuario 1—0..N Calificación. Cada hijo tiene participación total en sus FK. Los padres pueden existir sin hijos. Un conductor recién registrado puede no tener vehículo todavía.

1FN: valores escalares, sin listas de vehículos/ofertas ni grupos repetidos. 2FN: PK simples; todos los atributos dependen de su PK completa. Calificación también tiene candidata (id_viaje,id_usuario); Oferta candidata (id_solicitud,placa). 3FN: no se repiten nombres de usuario en Conductor, propietario en Oferta, pasajero en Viaje, monto de Oferta en Viaje ni promedio de calificación en Conductor. En Pago, monto es evidencia económica validada contra el precio pactado; comisión es un importe, no una tasa duplicada. Marca/modelo se tratan como descriptores de cada vehículo, sin suponer dependencias funcionales globales no declaradas por el informe.

Dependencias funcionales: id_usuario → nombres,telefono,correo,fecha_registro; id_conductor → id_usuario,licencia; placa → id_conductor,marca,modelo,color,anio; id_solicitud → id_usuario,origen,destino,precio_ofrecido,estado,fecha_solicitud; id_oferta → id_solicitud,placa,monto,tiempo_llegada; id_viaje → id_oferta,estado,hora_inicio,hora_fin; id_pago → id_viaje,metodo,monto,comision,fecha_pago; id_calificacion → id_viaje,id_usuario,puntaje,comentario.

El modelo físico es `database/01-schema.sql`. El diccionario completo se obtiene en vivo de INFORMATION_SCHEMA (tipos, longitudes, PK/FK, valores por defecto, nulabilidad y comentarios). El MER de la interfaz se genera de esas FK, sin mantener una copia manual divergente.

## Estrategia de integridad

PK, FK RESTRICT, UNIQUE, NOT NULL, DEFAULT y CHECK protegen datos locales. Triggers protegen reglas entre filas/tablas (participación, estados, precio de pago, inmutabilidad histórica). Las operaciones API usan transacciones y bloquean solicitudes/viajes para serializar ofertas, aceptación y cobros. Los usuarios de la aplicación no tienen consola SQL libre; solo consultas SELECT del catálogo cerrado con parámetros validados. El usuario SQL de ejecución no debe tener DDL ni permisos administrativos. No se expone el servidor fuera de loopback por defecto: es una demostración local sin autenticación, no un producto público.

## Consultas académicas

El documento original no contiene consultas SQL que corregir. Se añaden consultas identificadas como nuevas: JOIN de viajes; GROUP BY/HAVING de conductores; subconsulta para ofertas bajo el promedio; LEFT JOIN para solicitudes sin ofertas; resumen de cobros y filtros por estado. Cada ejecución devuelve datos del motor, SQL visible y parámetros; no se aceptan sentencias arbitrarias.

## Referencias técnicas de implementación

- https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html
- https://dev.mysql.com/doc/refman/8.0/en/create-table-check-constraints.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html

Estas referencias técnicas complementan el informe y no sustituyen sus referencias empresariales.
