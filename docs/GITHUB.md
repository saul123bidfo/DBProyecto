# Preparación para GitHub

La carpeta de trabajo expone `.git` como solo lectura en el sandbox y no es actualmente un repositorio Git válido. Por eso el empaquetador prepara una copia limpia, con repositorio local propio, en `release/indrive-lab` y un ZIP portable. No modifica ese `.git` ni publica nada.

```bash
npm run github:prepare
cd release/indrive-lab
git status
```

Se incluyen fuente, scripts, package-lock.json, configuración de Docker, CI, documentación e informe. Se excluyen `.env`, contraseñas locales, datos de MySQL, dependencias, compilados y carpetas privadas de herramientas. `.env.example` contiene solo valores de demostración.

Para publicar con Git, crea un repositorio vacío en tu cuenta de GitHub y ejecuta desde `release/indrive-lab`:

```bash
git commit -m "Implementa laboratorio académico de base de datos"
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Si Git pide tu identidad, configura tu nombre y correo de GitHub antes del commit. Si `origin` ya existe, consulta `git remote -v` y usa el remoto correcto; no vuelvas a añadirlo. La autenticación la administra tu cliente Git. También puedes descargar `release/indrive-lab-github.zip`, extraerlo y subir los archivos mediante la web de GitHub.

GitHub Actions está configurado para instalar con `npm ci`, compilar, probar el arranque y comprobar el flujo HTTP contra MySQL 8.0.44, incluida la aceptación concurrente. Otro trabajo construye Docker y comprueba `/api/health`. Las claves `ci_root_only` y `ci_app_only` solo sirven a instancias efímeras del runner; no son credenciales personales ni se utilizan en producción. Los jobs quedan pendientes de ejecución hasta que se publique la copia.

La publicación del código en GitHub no ejecuta ni aloja la aplicación. GitHub Pages tampoco ejecuta Express o MySQL. Para usarla localmente tras clonar, se ejecuta `npm run local` (Node + Docker) o `docker compose up --build -d --wait` (solo Docker).

No se añadió una licencia de distribución: el proyecto contiene un informe universitario de sus autores. Elige una licencia con ellos si desean autorizar reutilización pública.
