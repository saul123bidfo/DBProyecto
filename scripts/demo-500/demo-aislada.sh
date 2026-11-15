#!/usr/bin/env bash
# Instancia DESECHABLE de inDrive Lab para probar escrituras (crear, aceptar ofertas, pagar…) sin tocar los 500 registros.
#   start : MySQL 8.0.44 en memoria (sin volumen) + la app en http://127.0.0.1:3100 con el esquema y el seed original.
#   test  : ejecuta las pruebas de integración completas contra esa instancia (arrancarla antes con "start").
#   stop  : elimina contenedores y red. Al estar en memoria, los datos desaparecen; la base de demostración no se toca.
# Requiere la imagen indrive-lab:local (se construye con docker compose build app) y mysql:8.0.44 ya descargada.
set -euo pipefail
cd "$(dirname "$0")/../.."
NET=indrive-aislada-net; DB=indrive-aislada-db; APP=indrive-aislada-app
# Claves desechables: se generan al arrancar, no están escritas en el repositorio y viven solo en los contenedores.
secreto() { docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1" | sed -n "s/^$2=//p"; }
case "${1:-}" in
  start)
    ROOT_PW=$(od -An -N12 -tx1 /dev/urandom | tr -d ' \n'); APP_PW=$(od -An -N12 -tx1 /dev/urandom | tr -d ' \n')
    ENVS=(-e DB_HOST=$DB -e DB_PORT=3306 -e DB_USER=indrive_app -e DB_PASSWORD=$APP_PW)
    docker network create $NET >/dev/null
    docker run -d --name $DB --network $NET --tmpfs /var/lib/mysql:rw,size=512m -e MYSQL_ROOT_PASSWORD=$ROOT_PW \
      mysql:8.0.44 --innodb-buffer-pool-size=64M --performance-schema=OFF >/dev/null
    echo "Esperando a MySQL…"
    for _ in $(seq 1 60); do docker exec $DB mysqladmin ping -uroot -p$ROOT_PW --silent 2>/dev/null && break; sleep 2; done
    sleep 3
    docker run --rm --network $NET "${ENVS[@]}" -e DB_ADMIN_USER=root -e DB_ADMIN_PASSWORD=$ROOT_PW indrive-lab:local node scripts/init-db.js --seed | tail -2
    docker run -d --name $APP --network $NET -p 127.0.0.1:3100:3000 "${ENVS[@]}" -e HOST=0.0.0.0 indrive-lab:local >/dev/null
    sleep 4; echo "Instancia aislada lista: http://127.0.0.1:3100 (la demostración real sigue en :3000)";;
  test)
    ENVS=(-e DB_HOST=$DB -e DB_PORT=3306 -e DB_USER=indrive_app -e DB_PASSWORD="$(secreto $APP DB_PASSWORD)")
    docker run --rm --network $NET "${ENVS[@]}" -e ALLOW_INTEGRATION_WRITES=1 -e TEST_URL=http://$APP:3000 \
      -v "$PWD/tests:/app/tests:ro" indrive-lab:local node tests/api.integration.js;;
  stop)
    docker rm -f $APP $DB >/dev/null 2>&1 || true; docker network rm $NET >/dev/null 2>&1 || true
    echo "Instancia aislada eliminada.";;
  *) echo "Uso: $0 start|test|stop" >&2; exit 1;;
esac
