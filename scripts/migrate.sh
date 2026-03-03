#!/usr/bin/env bash
# SARO v8.0 -- run Alembic migrations against DATABASE_URL
set -euo pipefail
cd "$(dirname "$0")/../backend"
[ -z "${DATABASE_URL:-}" ] && echo "ERROR: DATABASE_URL not set" && exit 1
echo "[migrate] alembic upgrade head -> ${DATABASE_URL%%@*}@..."
alembic upgrade head
echo "[migrate] Done."
