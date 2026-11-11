#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"

NEO4J_VERSION="${NEO4J_VERSION:-2026.10.2}"
GDS_VERSION="${GDS_VERSION:-2026.10.2}"
LOCAL="$ROOT/.local"
NEO4J_HOME="$LOCAL/neo4j"
DL="$LOCAL/downloads"
mkdir -p "$DL"

[ -f .env ] || cp .env.example .env
set -a; source .env; set +a

if [ ! -d "$NEO4J_HOME" ]; then
  echo ">> Descargando Neo4j Community $NEO4J_VERSION"
  curl -fL --progress-bar -o "$DL/neo4j.tar.gz" \
    "https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
  tar -xzf "$DL/neo4j.tar.gz" -C "$LOCAL"
  mv "$LOCAL/neo4j-community-${NEO4J_VERSION}" "$NEO4J_HOME"
fi

cp -n "$NEO4J_HOME"/labs/apoc-*-core.jar "$NEO4J_HOME/plugins/" 2>/dev/null || true
GDS_JAR="$NEO4J_HOME/plugins/neo4j-graph-data-science-${GDS_VERSION}.jar"
if [ ! -f "$GDS_JAR" ]; then
  echo ">> Descargando Graph Data Science $GDS_VERSION"
  curl -fL --progress-bar -o "$GDS_JAR" \
    "https://github.com/neo4j/graph-data-science/releases/download/${GDS_VERSION}/neo4j-graph-data-science-${GDS_VERSION}.jar"
fi

CONF="$NEO4J_HOME/conf/neo4j.conf"
if ! grep -q "# red-profesional" "$CONF"; then
  cat >> "$CONF" <<CONF

# red-profesional
dbms.security.procedures.unrestricted=gds.*,apoc.*
dbms.security.procedures.allowlist=gds.*,apoc.*
server.memory.heap.initial_size=512m
server.memory.heap.max_size=1g
server.memory.pagecache.size=512m
db.tx_log.rotation.retention_policy=100M size
CONF
fi

if [ ! -d "$NEO4J_HOME/data/databases/neo4j" ]; then
  "$NEO4J_HOME/bin/neo4j-admin" dbms set-initial-password "$NEO4J_PASSWORD" || true
fi

if [ ! -d .venv ]; then
  echo ">> Creando .venv"
  python3 -m venv .venv
fi
.venv/bin/pip install --no-cache-dir -q --upgrade pip
.venv/bin/pip install --no-cache-dir -q -r requirements.txt

rm -rf "$DL"
echo ">> Listo. Arranca la BD con: scripts/start-db.sh"
