# Informe: grafo vs relacional en una red profesional

> Componente de investigación de **Netpro**, el proyecto *"Diseño e implementación de una aplicación basada en base de datos de grafos para la gestión y análisis de relaciones en una red profesional"*.
> Tecnologías: Neo4j Community 2026.10 (Cypher 5/25, APOC, Graph Data Science), driver oficial de Python, Flask.

## 1. Objetivo

El enunciado pide explicar **en qué escenarios el modelo de grafos supera al relacional y en cuáles no**. Este informe responde en tres partes:

1. Comparación **conceptual**: cómo se guarda y se recorre una relación en cada modelo.
2. Comparación de **expresividad**: la misma pregunta escrita en SQL y en Cypher.
3. Comparación **empírica**: un experimento reproducible (`scripts/benchmark.py`) que ejecuta las mismas consultas en Neo4j y en SQLite y comprueba que ambos devuelven el mismo resultado.

---

## 2. El mismo dominio en los dos modelos

### 2.1 Modelo de grafo (implementado)

```
(Usuario)-[:CONECTA_CON {desde}]-(Usuario)
(Usuario)-[:TRABAJA_EN {cargo, desde, hasta, actual}]->(Empresa)
(Usuario)-[:TIENE_HABILIDAD {nivel, anios}]->(Habilidad)
(Usuario)-[:PARTICIPA_EN {rol}]->(Proyecto)
(Usuario)-[:POSTULA_A {fecha, estado}]->(Oferta)
(Empresa)-[:PUBLICA {fecha}]->(Oferta)
(Oferta)-[:REQUIERE {obligatoria, nivel_minimo}]->(Habilidad)
(Proyecto)-[:USA_TECNOLOGIA]->(Habilidad)        ← extensión propia
(Proyecto)-[:DESARROLLADO_POR]->(Empresa)        ← extensión propia
```

5 tipos de nodo y 9 tipos de relación. Las relaciones son **ciudadanas de primera clase**: tienen tipo, dirección y propiedades, y se guardan físicamente como punteros entre nodos.

### 2.2 Equivalente relacional

| Tabla | Tipo | Equivale a |
|---|---|---|
| `usuario`, `empresa`, `habilidad`, `proyecto`, `oferta` | entidad | nodos |
| `conexion(usuario_a, usuario_b, desde)` | asociativa N:M | `CONECTA_CON` |
| `empleo(usuario_id, empresa_id, cargo, desde, hasta, actual)` | asociativa N:M | `TRABAJA_EN` |
| `usuario_habilidad(usuario_id, habilidad_id, nivel, anios)` | asociativa N:M | `TIENE_HABILIDAD` |
| `participacion(usuario_id, proyecto_id, rol)` | asociativa N:M | `PARTICIPA_EN` |
| `postulacion(usuario_id, oferta_id, fecha, estado)` | asociativa N:M | `POSTULA_A` |
| `oferta_habilidad(oferta_id, habilidad_id, obligatoria, nivel_minimo)` | asociativa N:M | `REQUIERE` |
| `proyecto_habilidad(proyecto_id, habilidad_id)` | asociativa N:M | `USA_TECNOLOGIA` |
| `oferta.empresa_id`, `proyecto.empresa_id` | clave foránea 1:N | `PUBLICA`, `DESARROLLADO_POR` |

Son **12 tablas**, 7 de ellas solo para representar relaciones. Las dos versiones guardan la misma información. Lo que cambia es **cómo se recorre**.

---

## 3. Diferencia conceptual: cómo se sigue una relación

| | Relacional | Grafo (Neo4j) |
|---|---|---|
| Dónde vive la relación | Como valores repetidos (claves foráneas) en una tabla aparte | Como un registro físico que apunta a sus dos nodos |
| Cómo se sigue un salto | `JOIN`: se busca en un índice B-tree, con costo **O(log n)** por fila según el tamaño de la tabla | El nodo guarda la lista de sus relaciones (*index-free adjacency*): costo **O(1)** por vecino |
| Consulta de profundidad variable | `WITH RECURSIVE`: un `JOIN` por nivel, sin saber qué caminos ya se exploraron | Patrones `-[:R]-{1,6}`, `SHORTEST`, `shortestPath()`; el planificador elige BFS con poda |
| Qué determina el costo | El tamaño **total** de las tablas involucradas | El tamaño del **vecindario recorrido** |
| Esquema | Rígido: una relación nueva implica tabla nueva y migración | Flexible: un tipo de relación nuevo se crea con solo usarlo |

La afirmación "los JOIN son lentos" no es exacta. Con buenos índices, un JOIN de uno o dos niveles es rapidísimo (ver resultados). El problema aparece cuando **la profundidad es variable o grande**:

- Cada nivel multiplica las filas intermedias.
- El motor SQL no sabe que está recorriendo un grafo, así que no puede detenerse al encontrar el destino ni evitar volver a visitar nodos por otros caminos.

En cambio, Neo4j reconoce el patrón. Por ejemplo, para `MATCH (u)-[:CONECTA_CON]-{1,6}(x) RETURN count(DISTINCT x)` el planificador generó este plan (obtenido con `EXPLAIN`):

```
EagerAggregation
  Filter
    VarLengthExpand(Pruning, BFS, All)   ← búsqueda en anchura que descarta nodos ya visitados
      NodeUniqueIndexSeek
```

---

## 4. Diferencia de expresividad: la misma pregunta en SQL y en Cypher

### 4.1 "¿Cuál es la distancia más corta entre dos profesionales?"

**SQL (SQLite / PostgreSQL)**: hay que programar el recorrido a mano.

```sql
WITH RECURSIVE bfs(id, d) AS (
  SELECT :inicio, 0
  UNION
  SELECT c.usuario_b, b.d + 1
  FROM bfs b JOIN conexion c ON c.usuario_a = b.id   -- (con la conexión guardada en ambos sentidos)
  WHERE b.d < 6
)
SELECT min(d) FROM bfs WHERE id = :fin;
```

Este SQL explora **todo** el vecindario de 6 saltos antes de filtrar por el destino. Para devolver *el camino* y no solo su longitud, habría que acumular una cadena con los ids y además evitar ciclos.

**Cypher**:

```cypher
MATCH p = SHORTEST 1 (:Usuario {id: $inicio})-[:CONECTA_CON]-{1,6}(:Usuario {id: $fin})
RETURN length(p), [n IN nodes(p) | n.nombre]
```

El camino completo es el resultado natural de la consulta, y el motor usa una búsqueda bidireccional que se detiene al encontrar el destino.

### 4.2 "Recomiéndame candidatos para esta oferta según habilidades y contactos en la empresa"

En SQL hacen falta al menos 6 JOIN:

`oferta → oferta_habilidad → usuario_habilidad → usuario`, y para medir la cercanía, `usuario → conexion → usuario → empleo → empresa`.

Además, cada parte necesita su propia subconsulta agregada. En Cypher el patrón se escribe tal como se dibujaría en una pizarra:

```cypher
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $id})-[:REQUIERE]->(h)<-[:TIENE_HABILIDAD]-(c:Usuario)
OPTIONAL MATCH (c)-[:CONECTA_CON]-(ref)-[:TRABAJA_EN {actual: true}]->(e)
...
```

La consulta completa está en `app/repositories/consultas.py` (`candidatos_para_oferta`).

---

## 5. Experimento

### 5.1 Método

- **Datos:** red social sintética con comunidades de 50 personas. El 75 % de las conexiones son dentro de la comunidad y el 25 % al azar, con un grado medio cercano a 9, igual que la red real de la aplicación. Se probaron tres tamaños: 2.000, 20.000 y 100.000 usuarios.
- **Relacional:** SQLite en memoria. La tabla `conexion(origen, destino)` guarda cada conexión en ambos sentidos, con clave primaria `(origen, destino)` (índice agrupado). Las consultas de profundidad usan `WITH RECURSIVE ... UNION`.
- **Grafo:** la misma red cargada en Neo4j (`:BenchUsuario`, `:BENCH_CONECTA`), con índice sobre `id`.
- **Medición:**
  - Mediana de 8 ejecuciones, con origen y destino aleatorios (3 ejecuciones en las consultas más pesadas).
  - Para Neo4j se reportan dos tiempos: el **total** (incluye la red Bolt y el driver) y el del **servidor** (`result_available_after + result_consumed_after`).
- **Validación:** en todas las filas ambos motores devolvieron **el mismo resultado** (columna ✓ en `docs/benchmark_resultados.md`).
- **Reproducir:** `.venv/bin/python scripts/benchmark.py`. Los datos de prueba se borran al terminar.

### 5.2 Resultados (red de 100.000 usuarios y 468.814 conexiones)

| Consulta | SQLite | Neo4j (total) | Ganador |
|---|---:|---:|---|
| Búsqueda por clave | 0,00 ms | 1,35 ms | **Relacional** |
| Contactos en común (2 saltos) | 0,01 ms | 1,86 ms | **Relacional** |
| Top 10 por nº de conexiones (agregación global) | 31,0 ms | 48,9 ms | **Relacional** |
| Alcance a 3 saltos | 0,32 ms | 0,91 ms | Relacional |
| Alcance a 4 saltos | 2,81 ms | 2,37 ms | Empate |
| Alcance a 5 saltos | 19,9 ms | 15,2 ms | Grafo (1,3×) |
| Alcance a 6 saltos | 115,1 ms | 31,8 ms | **Grafo (3,6×)** |
| Ruta más corta (≤ 6 saltos) | 80,5 ms | 0,75 ms | **Grafo (107×)** |

Así crece la **ruta más corta** con el tamaño de la red:

| Usuarios | SQLite | Neo4j | Ventaja del grafo |
|---:|---:|---:|---:|
| 2.000 | 8,4 ms | 0,96 ms | 9× |
| 20.000 | 45,1 ms | 1,87 ms | 24× |
| 100.000 | 80,5 ms | 0,75 ms | 107× |

Las tablas completas están en [`benchmark_resultados.md`](benchmark_resultados.md).

### 5.3 Análisis

1. **Consultas puntuales y de 1–2 saltos: gana el relacional.** SQLite responde en microsegundos porque corre dentro del mismo proceso. Neo4j paga cerca de 0,5–1,5 ms solo por la red, aunque su tiempo de servidor es de 0–1 ms. A esa escala ambos motores son instantáneos para un usuario humano.
2. **Agregaciones globales sobre todas las filas** (contar conexiones de todos los usuarios): gana el relacional. Recorrer una tabla compacta y agrupar es justo para lo que está optimizado. El grafo tiene que visitar cada nodo y sus relaciones.
3. **Recorridos profundos: gana el grafo, y la ventaja crece con la profundidad.** A 6 saltos, SQLite pasa de 8,8 ms a 115 ms al crecer la red, mientras que Neo4j se queda en 2–32 ms. El SQL recursivo deduplica pares `(nodo, profundidad)`, no nodos, así que vuelve a expandir nodos ya visitados en cada nivel.
4. **Ruta más corta: es donde el grafo gana con más claridad, y la brecha aumenta con el volumen** (9× → 24× → 107×). Neo4j hace una búsqueda bidireccional que se detiene al encontrar el destino. El SQL recursivo no puede detenerse antes y explora todo el vecindario.
5. **Hallazgo adicional:** la versión con APOC (`apoc.path.subgraphNodes`, BFS explícito) no fue más rápida que el Cypher declarativo. El planificador de Neo4j ya convierte `count(DISTINCT x)` sobre un patrón de longitud variable en un BFS con poda. Escribir la consulta de forma declarativa basta.

### 5.4 Limitaciones del experimento

- SQLite corre dentro del proceso y Neo4j por red. Esto favorece a SQLite en las consultas cortas; por eso se reporta también el tiempo del servidor.
- Es una sola máquina con la caché caliente y volúmenes moderados (≤ 470.000 relaciones). Un PostgreSQL bien configurado tendría números distintos a los de SQLite, aunque la **tendencia** sería la misma: el costo de los recorridos SQL crece con la profundidad y con el tamaño del vecindario.
- No se midieron escrituras concurrentes ni transacciones masivas, que son el terreno natural del modelo relacional.

---

## 6. Respuesta: ¿cuándo gana cada modelo?

### El grafo supera al relacional cuando…

| Escenario | Evidencia en este proyecto |
|---|---|
| **Recorridos de profundidad variable o desconocida**: grados de separación, "¿cómo llego a esta empresa?" | Ruta más corta 107× más rápida con 100.000 usuarios; `SHORTEST` en una línea |
| **Recomendaciones basadas en vecindario**: amigos de amigos, candidatos con referidos | Las consultas de `recomendaciones.py` combinan 3–4 patrones; en SQL serían 6 o más JOIN con subconsultas |
| **Algoritmos de red**: influencia, comunidades, intermediación | PageRank, Louvain y Betweenness con GDS en cerca de 100 ms. Louvain encontró **6 comunidades** (modularidad 0,54) que coinciden con los sectores reales en 84–90 %. En SQL no hay equivalente nativo |
| **Relaciones con atributos propios y muchas N:M** | 9 tipos de relación sin tablas intermedias; `nivel`, `cargo` y `estado` viven en la relación |
| **Esquema que evoluciona** | `USA_TECNOLOGIA` y `DESARROLLADO_POR` se añadieron sin migraciones |
| **Exploración visual y explicable** | Las rutas se devuelven como caminos (`nodos(p)`), listos para mostrar como cadena o en Neo4j Browser |

### El relacional supera al grafo cuando…

| Escenario | Por qué |
|---|---|
| **Búsquedas puntuales y JOIN de 1–2 niveles** | Los índices B-tree son extremadamente eficientes; en el experimento SQLite fue más rápido |
| **Reportes y agregaciones masivas** (sumas, promedios, GROUP BY sobre millones de filas, OLAP) | Almacenamiento compacto por filas o columnas, motores vectorizados; el "Top 10 por grado" fue más rápido en SQL |
| **Datos tabulares homogéneos con pocas relaciones** (facturas, inventario, contabilidad) | Un grafo no aporta nada si no hay recorridos |
| **Integridad estricta y transacciones de alto volumen** | Claves foráneas, `CHECK` y restricciones complejas; décadas de optimización en OLTP |
| **Ecosistema y personal** | SQL es un estándar, con herramientas de BI, ORMs y mucha gente que ya lo conoce |
| **Escalado horizontal de escrituras** | Particionar un grafo es difícil porque las relaciones cruzan particiones |

### Conclusión

No hay un modelo "mejor". **El modelo de grafos rinde más cuando la pregunta se trata de las relaciones**: cuántos saltos hay, por dónde pasa el camino, quién está cerca de quién, qué comunidad se forma. **El relacional rinde más cuando la pregunta se trata de los registros**: buscar uno, filtrar muchos o resumirlos.

Una red profesional está llena de preguntas del primer tipo. Por eso Neo4j es la elección adecuada para su núcleo de conexiones, recomendaciones y analítica. En un sistema real convendría una **arquitectura políglota**: el grafo para la red y las recomendaciones, y una base relacional para facturación, auditoría y reportes masivos.
