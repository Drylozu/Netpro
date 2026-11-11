#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
read -r -p "Esto borra .local/ (incluida la base de datos) y .venv/. ¿Continuar? [s/N] " r
[[ "$r" =~ ^[sS]$ ]] || exit 0
rm -rf .local .venv
find . -name __pycache__ -type d -prune -exec rm -rf {} +
echo "Limpio."
