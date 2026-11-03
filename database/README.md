# Orden de ejecución

1. `01-schema.sql`: crea base, tablas, índices y triggers; NO borra tablas existentes.
2. `02-seed.sql`: carga de datos ficticios, opcional, transaccional y de una sola ejecución.
3. `03-consultas.sql`: consultas académicas SELECT del explorador.

Usar MySQL 8.0.16+ o MariaDB 10.6+; la versión realmente comprobada se informa en README. El esquema usa utf8mb4_unicode_ci, CHECK y SIGNAL compatibles, sin collation exclusiva de MySQL ni campos JSON. No ejecutar con CHECK desactivado ni con FOREIGN_KEY_CHECKS=0.

El inicializador usa una cuenta administradora configurada por entorno y crea una cuenta de ejecución con SELECT, INSERT, UPDATE, DELETE, SHOW VIEW y TRIGGER (este último para que el explorador pueda mostrar las definiciones). TRIGGER puede modificar reglas y no es el mínimo privilegio ideal: para un despliegue público se debe servir el catálogo de triggers mediante un procedimiento de lectura con SQL SECURITY DEFINER y retirar ese permiso. Este proyecto es una demostración local. Las operaciones del explorador nunca aceptan SQL escrito por el visitante.
