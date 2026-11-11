#!/usr/bin/env bash
# Arranca Neo4j en primer plano (Ctrl+C para detenerlo). No se registra como servicio.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .local/jdk ] && export JAVA_HOME="$(pwd)/.local/jdk"
exec .local/neo4j/bin/neo4j console
