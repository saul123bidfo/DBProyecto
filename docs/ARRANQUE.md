# Diagnóstico y cambios de arranque

## Problemas observados en esta sesión

- Las dependencias ya estaban instaladas, incluidas express 4.22.3, mysql2 3.15.3, React 18.3.1 y Vite 6.4.4.
- `npm start` fallaba con `listen EPERM: operation not permitted 127.0.0.1:3000`; el error no estaba capturado.
- Docker fallaba con `dial unix /var/run/docker.sock: connect: operation not permitted`.
- No había conexión disponible con el servidor SQL local desde esta sesión.
- El `.git` de la raíz es una carpeta de solo lectura y no contiene un repositorio Git válido.

EPERM corresponde a restricciones del entorno del agente. No se cambió el puerto para ocultar el error ni se afirma haber iniciado un servicio que el entorno impide abrir.

## Cambios aplicados

1. `npm run local` / `./iniciar.sh` comprueba acceso a Docker, prepara `.env` si falta y ejecuta Compose con construcción y espera de salud. La aplicación queda en segundo plano cuando el comando termina correctamente.
2. Compose coordina MySQL → inicialización → aplicación. El contenedor de aplicación incluye el frontend compilado y depende de que la base y el esquema estén preparados.
3. `db:init --if-empty --seed` inicializa solo bases vacías; reutiliza esquemas existentes con tablas y triggers esperados. No repite el seed, no borra datos y no reemplaza contraseñas. Un esquema parcial detiene el arranque para su revisión.
4. El servidor comprueba conexión y tabla Usuario antes de escuchar. Los errores de puerto, permisos y credenciales muestran instrucciones, sin volcar contraseñas.
5. `npm run dev` usa Vite explícitamente aunque exista dist; `npm start` sirve el frontend compilado.
6. `npm run doctor` revisa configuración, Docker, SQL y API sin mostrar claves.
7. Se completaron 30 entradas sin URL e integridad en el lockfile, verificando los tarballs disponibles en caché; se conservaron las versiones y se fijó Express. Se añadieron CI y paquete fuente seguro para GitHub.

## Uso en una terminal del sistema

Desde `/home/saul-lab/DBCiclo4`:

```bash
npm run local
```

No requiere instalar npm en el host: Node ejecuta el lanzador y Docker construye las dependencias en el contenedor. La primera construcción necesita internet. También puedes usar únicamente Docker:

```bash
cp -n .env.example .env
docker compose up --build -d --wait
```

Abre http://127.0.0.1:3000 cuando el comando termine sin errores. `npm run local:logs` muestra el diagnóstico; `npm run local:stop` detiene app y base, conservando el volumen.

Se observó un conflicto real en el puerto 3306 del host: Docker informó `bind: address already in use`. Se cambió el puerto externo a 3307 en `.env`, el ejemplo y el valor por defecto de Compose, sin tocar el otro servicio ni el volumen. Si 3000 o 3307 están ocupados, define `PORT=3001` o `DB_PORT=3308` en `.env`. Son puertos del host: dentro de Docker MySQL sigue en 3306 y Express en 3000. Si un volumen ya fue creado con otra contraseña administradora, usa esa contraseña en `MYSQL_ROOT_PASSWORD`; no lo elimines para solucionar un problema de acceso.

Si `docker info` falla en la terminal del sistema, inicia Docker Desktop o el servicio Docker y revisa los permisos de tu cuenta con el administrador del equipo. El lanzador no ejecuta sudo ni modifica grupos o permisos.

## Corrección de disponibilidad inicial de MySQL

Los logs de la primera ejecución en Docker mostraron un servidor temporal listo con `port: 0` y, después, el servidor definitivo en 3306. El healthcheck anterior (`mysqladmin ping -h localhost`) usaba el socket Unix y podía aceptar ese servidor temporal. Así se adelantaba setup y fallaba con ECONNREFUSED. Era un error de la configuración de arranque.

Se reemplazó la comprobación por `SELECT 1` autenticado con protocolo TCP en 127.0.0.1:3306. También se añadió espera limitada de conexión en el inicializador, exclusivamente para fallos transitorios; no se reintentan sentencias SQL, credenciales incorrectas o errores de permisos. El helper se incluye tanto en Dockerfile como en el contexto permitido por .dockerignore. Se corrigió también la comprobación TCP del servicio de pruebas de CI.

Las tres pruebas nuevas verifican recuperación después de conexiones rechazadas, fallo inmediato por autenticación/permisos y agotamiento de reintentos. Se aprobaron diez pruebas y la validación sintáctica de Compose; ejecutar los contenedores sigue requiriendo una terminal fuera del sandbox. Para reconstruir y reintentar basta `npm run local`: no es necesario borrar el volumen.

Referencia primaria: el entrypoint de la imagen inicia el servidor temporal con `--skip-networking`: https://github.com/docker-library/mysql/blob/master/docker-entrypoint.sh. `mysqladmin ping` tampoco garantiza autenticación correcta: https://dev.mysql.com/doc/refman/8.0/en/mysqladmin.html.
