#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .local/jdk ] && export JAVA_HOME="$(pwd)/.local/jdk"
exec .local/neo4j/bin/neo4j console
