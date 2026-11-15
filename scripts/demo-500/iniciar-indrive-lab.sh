#!/usr/bin/env bash
# Inicia SOLO inDrive Lab (proyecto Docker "indrive-lab"). Conserva los datos (volumen mysql_data).
set -euo pipefail
cd "$(dirname "$0")/../.."
docker compose up -d --wait --wait-timeout 180
scripts/demo-500/cargar-demo.sh     # idempotente: no duplica los 500 registros
echo
echo "Aplicación : http://127.0.0.1:3000"
echo "MySQL      : 127.0.0.1:3307  (base indrive_academico)"
