#!/usr/bin/env bash
# Detiene SOLO inDrive Lab. Usa "stop" (no "down"): contenedores y volumen de datos se conservan.
# NUNCA use "docker compose down -v": borraría el volumen con los 500 registros.
set -euo pipefail
cd "$(dirname "$0")/../.."
docker compose stop
docker compose ps -a
