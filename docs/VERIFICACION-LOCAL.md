# Verificación del arranque y preparación de GitHub

Historia revisada: el usuario inicia la aplicación local, el navegador consulta `/api/health` y los módulos operativos, Express se conecta a MySQL y devuelve registros persistidos.

| Límite del flujo | Estado | Evidencia |
|---|---|---|
| Dependencias | Comprobado | React 18.3.1, Vite 6.4.4, Express 4.22.3 y mysql2 3.15.3 |
| Instalación reproducible | Comprobado sin postinstall | `npm ci --offline --ignore-scripts` instaló 112 paquetes para esta plataforma a partir de un lockfile con 163 entradas resueltas y sus hashes; los restantes son opcionales de otras plataformas |
| Compilación de interfaz | Aprobado | Vite 6.4.4: 26 módulos, generación de dist sin errores |
| Validación JavaScript | Aprobado | Siete pruebas de entradas, separación SQL y errores de arranque |
| Datos y restricciones | Aprobado en MariaDB | `npm run test:sql`: motor 11.8.6, 23 rechazos esperados, flujo positivo, seis consultas y resultados de referencia correctos |
| Configuración Docker | Aprobado sintácticamente | `docker compose config --quiet` |
| Apertura del servidor y conexión SQL | Bloqueado en esta sesión | `listen EPERM: operation not permitted 127.0.0.1:3000` en el arranque original; conexión SQL EPERM tras añadir la comprobación inicial |
| Docker | Bloqueado en esta sesión | `dial unix /var/run/docker.sock: connect: operation not permitted` |
| HTTP y navegador | Pendiente | El bloqueo anterior impide ejecutar el recorrido completo aquí |
| GitHub Actions | Configurado, pendiente de ejecución | Jobs de integración MySQL 8.0.44 y construcción/arranque Docker |
| Paquete fuente | Comprobado | ZIP con lista explícita de fuentes, sin .env, datos locales, node_modules o carpetas privadas |

La comprobación inicial de npm vació node_modules. Se restauró desde caché: antes se completaron 30 entradas de lockfile que carecían de URL e integridad, verificando nombre, versión y SHA-512 de cada tarball. No se cambiaron esas versiones. El postinstall normal de esbuild intentó ejecutar su binario y el sandbox devolvió EPERM; por eso la restauración local se hizo con `--ignore-scripts`. La compilación posterior pasó con el binario distribuido por su paquete de plataforma. En una terminal normal o contenedor se mantiene `npm ci`, sin omitir scripts.

El servidor captura ahora los errores de arranque y muestra instrucciones en vez de una excepción sin manejar. El lanzador también informa cuando Docker no es accesible. Ningún cambio de aplicación puede conceder permisos que la sesión restringida no tiene. Para ejecutar los servicios debe utilizarse `npm run local` desde una terminal del sistema con Docker disponible.

No hay evidencia para declarar que los contenedores estén ejecutándose o que la prueba de aceptación concurrente haya pasado en esta sesión. Esos controles están preparados en CI y en `npm run test:integration`.
