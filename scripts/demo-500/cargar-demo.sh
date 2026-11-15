#!/usr/bin/env bash
# Carga el conjunto de demostración (500 solicitudes ficticias) en el MySQL de Docker de inDrive Lab.
# Seguro y repetible: si el conjunto ya existe (500 solicitudes) no vuelve a insertar nada.
# No borra tablas ni registros. Uso: scripts/demo-500/cargar-demo.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

mysql_root() {  # la clave se lee DENTRO del contenedor; nunca se imprime
  docker compose exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --protocol=TCP -h127.0.0.1 -uroot --default-character-set=utf8mb4 --batch --skip-column-names "$@"' sh "$@"
}

CONTEO_SQL="SELECT COUNT(*) FROM indrive_academico.solicitud s JOIN indrive_academico.usuario u ON u.id_usuario=s.id_usuario WHERE u.correo LIKE '%@demo.indrive-lab.test'"
actual=$(mysql_root -e "$CONTEO_SQL")

if [ "$actual" = "500" ]; then
  echo "Conjunto de demostración ya cargado (500 solicitudes). No se insertó nada."
  exit 0
elif [ "$actual" != "0" ]; then
  echo "ERROR: hay $actual solicitudes de demostración (se esperaban 0 o 500). No se modificó nada; revise manualmente." >&2
  exit 2
fi

echo "Cargando conjunto de demostración (una sola transacción)…"
python3 scripts/demo-500/generar_demo_sql.py | mysql_root

final=$(mysql_root -e "$CONTEO_SQL")
echo "Solicitudes de demostración presentes: $final"
[ "$final" = "500" ] || { echo "ERROR: el conteo final no es 500" >&2; exit 3; }
