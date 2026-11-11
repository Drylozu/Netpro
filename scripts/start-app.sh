#!/usr/bin/env bash
# Arranca la aplicación web (Flask) en http://localhost:8000. Requiere Neo4j corriendo.
set -euo pipefail
cd "$(dirname "$0")/.."
exec .venv/bin/python run.py
