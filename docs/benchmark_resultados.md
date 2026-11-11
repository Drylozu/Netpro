# Resultados del benchmark grafo vs relacional

Generado por `scripts/benchmark.py`. Mediana de varias ejecuciones con origen/destino aleatorios.
SQLite corre en memoria dentro del proceso; Neo4j se consulta por Bolt (localhost).

## Red de 2.000 usuarios y 9.304 conexiones

| Consulta | SQLite (ms) | Neo4j total (ms) | Neo4j servidor (ms) | Mismo resultado |
|---|---:|---:|---:|:---:|
| Búsqueda por clave | 0.00 | 0.45 | 0 | ✓ |
| Contactos en común (2 saltos) | 0.01 | 0.72 | 1 | ✓ |
| Top 10 por nº de conexiones (agregación global) | 0.50 | 1.96 | 2 | ✓ |
| Alcance a 2 saltos (Cypher, enumera caminos) | 0.03 | 0.75 | 0 | ✓ |
| Alcance a 2 saltos (APOC, BFS por nodos) | 0.04 | 1.09 | 1 | ✓ |
| Alcance a 3 saltos (Cypher, enumera caminos) | 0.21 | 0.98 | 1 | ✓ |
| Alcance a 3 saltos (APOC, BFS por nodos) | 0.27 | 1.21 | 1 | ✓ |
| Alcance a 4 saltos (Cypher, enumera caminos) | 1.55 | 1.53 | 1 | ✓ |
| Alcance a 4 saltos (APOC, BFS por nodos) | 1.40 | 1.99 | 1 | ✓ |
| Alcance a 5 saltos (Cypher, enumera caminos) | 4.78 | 2.13 | 1 | ✓ |
| Alcance a 5 saltos (APOC, BFS por nodos) | 4.87 | 3.44 | 3 | ✓ |
| Alcance a 6 saltos (Cypher, enumera caminos) | 8.83 | 2.28 | 1 | ✓ |
| Alcance a 6 saltos (APOC, BFS por nodos) | 8.51 | 3.13 | 3 | ✓ |
| Ruta más corta (máx. 6 saltos) | 8.37 | 0.96 | 0 | ✓ |

## Red de 20.000 usuarios y 93.624 conexiones

| Consulta | SQLite (ms) | Neo4j total (ms) | Neo4j servidor (ms) | Mismo resultado |
|---|---:|---:|---:|:---:|
| Búsqueda por clave | 0.00 | 0.44 | 0 | ✓ |
| Contactos en común (2 saltos) | 0.01 | 0.51 | 0 | ✓ |
| Top 10 por nº de conexiones (agregación global) | 4.79 | 7.11 | 7 | ✓ |
| Alcance a 2 saltos (Cypher, enumera caminos) | 0.03 | 0.55 | 0 | ✓ |
| Alcance a 2 saltos (APOC, BFS por nodos) | 0.05 | 0.98 | 1 | ✓ |
| Alcance a 3 saltos (Cypher, enumera caminos) | 0.28 | 0.85 | 1 | ✓ |
| Alcance a 3 saltos (APOC, BFS por nodos) | 0.26 | 0.81 | 1 | ✓ |
| Alcance a 4 saltos (Cypher, enumera caminos) | 2.21 | 1.39 | 1 | ✓ |
| Alcance a 4 saltos (APOC, BFS por nodos) | 2.20 | 1.31 | 1 | ✓ |
| Alcance a 5 saltos (Cypher, enumera caminos) | 14.98 | 4.49 | 4 | ✓ |
| Alcance a 5 saltos (APOC, BFS por nodos) | 13.02 | 5.21 | 4 | ✓ |
| Alcance a 6 saltos (Cypher, enumera caminos) | 55.33 | 12.08 | 11 | ✓ |
| Alcance a 6 saltos (APOC, BFS por nodos) | 50.19 | 17.51 | 16 | ✓ |
| Ruta más corta (máx. 6 saltos) | 45.05 | 1.87 | 1 | ✓ |

## Red de 100.000 usuarios y 468.814 conexiones

| Consulta | SQLite (ms) | Neo4j total (ms) | Neo4j servidor (ms) | Mismo resultado |
|---|---:|---:|---:|:---:|
| Búsqueda por clave | 0.00 | 1.35 | 0 | ✓ |
| Contactos en común (2 saltos) | 0.01 | 1.86 | 1 | ✓ |
| Top 10 por nº de conexiones (agregación global) | 31.00 | 48.88 | 48 | ✓ |
| Alcance a 2 saltos (Cypher, enumera caminos) | 0.04 | 2.92 | 2 | ✓ |
| Alcance a 2 saltos (APOC, BFS por nodos) | 0.04 | 1.32 | 1 | ✓ |
| Alcance a 3 saltos (Cypher, enumera caminos) | 0.32 | 0.91 | 1 | ✓ |
| Alcance a 3 saltos (APOC, BFS por nodos) | 0.31 | 1.88 | 1 | ✓ |
| Alcance a 4 saltos (Cypher, enumera caminos) | 2.81 | 2.37 | 2 | ✓ |
| Alcance a 4 saltos (APOC, BFS por nodos) | 2.68 | 5.44 | 5 | ✓ |
| Alcance a 5 saltos (Cypher, enumera caminos) | 19.95 | 15.20 | 14 | ✓ |
| Alcance a 5 saltos (APOC, BFS por nodos) | 23.31 | 21.27 | 19 | ✓ |
| Alcance a 6 saltos (Cypher, enumera caminos) | 115.13 | 31.79 | 30 | ✓ |
| Alcance a 6 saltos (APOC, BFS por nodos) | 108.17 | 43.41 | 42 | ✓ |
| Ruta más corta (máx. 6 saltos) | 80.46 | 0.75 | 0 | ✓ |
