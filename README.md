# DBProyecto · inDrive Lab

Aplicación web académica basada en inDrive, desarrollada con React, Node.js y MySQL. Implementa negociación de viajes, pagos y calificaciones, con integridad referencial, transacciones y un explorador de base de datos con diagrama ER y consultas SQL.

Aplicación académica basada en la sección 7 de `Informe_inDrive.docx`. Implementa personas, conductores, vehículos, solicitudes, ofertas, viajes, pagos y calificaciones. React 18 + Express 4 + MySQL 8, con SQL directo, transacciones y restricciones reales. Es un modelo ilustrativo propio: no representa el sistema interno de inDrive.

## Iniciar localmente

Requisitos: **Docker con Compose v2**, ejecutándose y accesible desde tu terminal. La primera construcción requiere conexión a internet. Node.js 20.19+ permite usar el lanzador:

```bash
npm run local
```

Abre **http://127.0.0.1:3000** cuando el comando termine correctamente. El lanzador crea `.env` solo si no existe; construye el frontend y el backend; inicia MySQL 8.0.44; prepara una base vacía y los datos ficticios de exposición; y deja los contenedores en segundo plano. La salud de MySQL exige una consulta autenticada por TCP, y el inicializador reintenta los fallos temporales de conexión. Si ya hay un esquema válido, conserva el historial y no vuelve a cargar el seed.

La alternativa sin Node instalado en el host es:

```bash
cp -n .env.example .env
docker compose up --build -d --wait
```

En Windows, copia `.env.example` como `.env` desde el explorador y ejecuta el segundo comando en PowerShell. La aplicación y la base solo publican sus puertos en loopback. MySQL se publica en el puerto **3307** del host para evitar conflictos con un motor instalado en 3306. Dentro de Docker conserva el puerto 3306. Para cambiar los puertos del host usa `PORT` y `DB_PORT` en `.env`.

```bash
npm run local:logs
npm run local:stop
```

El primer comando muestra los logs; el segundo detiene app y MySQL sin borrar su volumen. No uses `docker compose down -v` sobre una base que quieras conservar. No se incluye ninguna operación de borrado automático de datos.

Los valores de `.env.example` son claves de demostración local. Cambia `DB_PASSWORD` y `MYSQL_ROOT_PASSWORD` antes de crear una instancia que vaya a usar datos personales. Si el volumen ya existía, usa las claves originales: cambiar `.env` no cambia la contraseña guardada por MySQL.

## Si no arranca

```bash
npm run local:logs
npm run doctor
```

`doctor` requiere las dependencias del host (`npm ci`). Comprueba Docker, configuración, SQL y API sin mostrar contraseñas. [Diagnóstico detallado y cambios aplicados](docs/ARRANQUE.md).

- **Docker no accesible:** inicia Docker Desktop o el servicio Docker y usa una terminal de tu sistema con permisos para el daemon. La sesión restringida del agente no puede abrir sockets.
- **Puerto ocupado:** cambia `PORT=3001` o `DB_PORT=3308` en `.env` y ejecuta de nuevo `npm run local`.
- **Acceso denegado a MySQL:** comprueba las credenciales originales del volumen; no borres los datos para resolverlo.
- **Esquema incompleto:** consulta los logs de `setup`. El inicializador se detiene para que se revise el estado antes de alterar información existente.

## Desarrollo sin contenedor de aplicación

Node.js 20.19+ y MySQL 8.0.16+ o MariaDB 10.6+. El esquema se comprobó en MariaDB 11.8.6; la configuración de Docker usa MySQL 8.0.44.

```bash
cp -n .env.example .env
npm ci
docker compose up -d --wait db
DB_ADMIN_USER=root DB_ADMIN_PASSWORD=cambiar_clave_administrador npm run db:init -- --if-empty --seed
npm run dev
```

La clave del comando debe coincidir con la de tu MySQL. Si usas un motor instalado en el host, omite Docker y ajusta `.env`; se admite `DB_SOCKET` para Unix. `npm run dev` utiliza Vite explícitamente, incluso si existe `dist/`.

Para servir una compilación desde Express:

```bash
npm run build
npm start
```

`npm start` comprueba conexión y esquema antes de escuchar. El puerto por defecto es 3000. No hace falta otro servidor ni configurar CORS.

El inicializador ejecutado sin `--if-empty` rechaza una base con tablas. Con `--if-empty` reutiliza únicamente esquemas con las tablas y triggers esperados. No hace migraciones, no sobrescribe contraseñas ni repite el seed. El DDL no se revierte íntegramente ante un fallo; revisa un esquema parcial antes de reintentar. La carga de datos sí es transaccional.

## Funcionalidades

- CRUD, búsquedas y paginación de maestros, con selección de FK existentes.
- Solicitudes y ofertas; aceptación única dentro de una transacción con bloqueo de la solicitud.
- Inicio y finalización de viajes con fechas y precio pactado derivados de los datos relacionados.
- Registro de cobros por el importe acordado y evaluaciones por los participantes reales.
- Protección del historial mediante FK RESTRICT y triggers. No se eliminan viajes, pagos ni calificaciones desde la app.
- Explorador de Base de Datos: tablas, diccionario, PK/FK, DEFAULT, nulabilidad, CHECK, índices, triggers, reglas referenciales y MER leídos de INFORMATION_SCHEMA.
- Seis consultas académicas controladas con SQL visible, parámetros validados, duración y resultados del motor. Límite de 200 filas.

Solicitudes con ofertas no permiten cambiar ruta/precio; las ofertas cerradas conservan su importe. Los pagos permiten corregir método/comisión y las calificaciones puntaje/comentario. El precio final no se duplica en Viaje y la media del conductor se calcula con AVG.

“Pago” registra un cobro académico, no realiza cargos bancarios. No se añadieron mapas, pasarelas, autenticación ni geolocalización porque no estaban especificados. La demostración es local y no debe exponerse como producto público sin los controles correspondientes. Consulta `database/README.md` para las particularidades del permiso TRIGGER que permite inspeccionar las reglas.

## Validación

```bash
npm test
npm run build
npm run test:sql
```

`npm test`: diez pruebas de validación, separador SQL, diagnóstico de arranque y conexión con reintentos. `test:sql` requiere Python 3 y el servidor MariaDB local: crea una instancia temporal separada en `/tmp`, ejecuta esquema y seed, verifica 23 rechazos de integridad, un flujo positivo con rollback y las seis consultas. Usa InnoDB real en modo bootstrap sin sockets; no toca la conexión de `.env`. Los códigos de error de esa suite son específicos de MariaDB.

Para verificar HTTP contra una instancia de prueba activa:

```bash
ALLOW_INTEGRATION_WRITES=1 npm run test:integration
```

Esa prueba añade historial: verifica CRUD inicial, FK, borrados rechazados, aceptación concurrente, avance de viaje, pago, calificación, metadatos y consultas. Puede usar `TEST_URL` para otro destino. Ejecútala en una instancia de prueba.

Comprobado en esta sesión: dependencias exactas instaladas, lockfile consistente, diez pruebas JavaScript, compilación con Vite 6.4.4 y React 18.3.1, sintaxis de Compose y verificación SQL en MariaDB 11.8.6. **Pendientes:** arranque real de los contenedores, recorrido en navegador y flujo HTTP en MySQL 8. El sandbox bloquea Docker y sockets; no se declara que la aplicación esté ejecutándose aquí. Los jobs de GitHub Actions incluyen MySQL y Docker, y se ejecutarán cuando se publique el repositorio.

## Documentación y GitHub

- [Análisis, alcance y normalización](docs/ANALISIS.md).
- [Informe corregido](docs/Informe_inDrive_corregido.docx) y [registro de cambios](docs/CORRECCIONES.md). Original conservado.
- [Diccionario](docs/DICCIONARIO.md), [MER](docs/MER.svg) y [scripts SQL](database/README.md).
- [Guion para la exposición](docs/EXPOSICION.md) y [validación SQL](docs/VALIDACION-SQL.json).
- [Preparar y publicar la copia en GitHub](docs/GITHUB.md).
- [Evidencia de verificación local y límites del entorno](docs/VERIFICACION-LOCAL.md).

```bash
npm run github:prepare
```

Genera `release/indrive-lab/` y `release/indrive-lab-github.zip`, sin `.env`, dependencias, datos locales ni carpetas privadas. La copia tiene Git inicializado y fuentes preparadas; no se publica nada automáticamente. GitHub Actions usa `npm ci`, pruebas, MySQL 8 y una construcción completa de Docker.
