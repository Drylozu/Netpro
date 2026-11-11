import argparse
import pathlib
import random
import sqlite3
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.db import close_driver, get_driver  # noqa: E402

rnd = random.Random(7)

def generar_red(n, tam_comunidad=50, grado_medio=10):
    aristas = set()
    for u in range(n):
        base = (u // tam_comunidad) * tam_comunidad
        for _ in range(grado_medio // 2):
            if rnd.random() < 0.75:
                v = rnd.randrange(base, min(base + tam_comunidad, n))
            else:
                v = rnd.randrange(n)
            if u != v:
                aristas.add((min(u, v), max(u, v)))
    return sorted(aristas)

def cargar_neo4j(n, aristas):
    with get_driver().session() as s:
        limpiar_neo4j(s)
        s.run("CREATE INDEX bench_id IF NOT EXISTS FOR (u:BenchUsuario) ON (u.id)").consume()
        s.run("CALL db.awaitIndexes()").consume()
        for i in range(0, n, 10000):
            s.run("UNWIND range($a, $b) AS i CREATE (:BenchUsuario {id: i})", a=i, b=min(i + 9999, n - 1)).consume()
        for i in range(0, len(aristas), 10000):
            lote = [{"a": a, "b": b} for a, b in aristas[i:i + 10000]]
            s.run("""UNWIND $rows AS r MATCH (a:BenchUsuario {id: r.a}), (b:BenchUsuario {id: r.b})
                     CREATE (a)-[:BENCH_CONECTA]->(b)""", rows=lote).consume()

def limpiar_neo4j(s):
    s.run("MATCH (u:BenchUsuario) CALL (u) { DETACH DELETE u } IN TRANSACTIONS OF 5000 ROWS").consume()
    s.run("DROP INDEX bench_id IF EXISTS").consume()

def cargar_sqlite(n, aristas):
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE usuario (id INTEGER PRIMARY KEY);
        CREATE TABLE conexion (origen INTEGER, destino INTEGER, PRIMARY KEY (origen, destino)) WITHOUT ROWID;
    """)
    con.executemany("INSERT INTO usuario VALUES (?)", ((i,) for i in range(n)))
    con.executemany("INSERT INTO conexion VALUES (?, ?)", aristas)
    con.executemany("INSERT INTO conexion VALUES (?, ?)", ((b, a) for a, b in aristas))
    con.execute("ANALYZE")
    return con

SQL = {
    "alcance": """
        WITH RECURSIVE alcance(id, d) AS (
          SELECT :inicio, 0
          UNION
          SELECT c.destino, a.d + 1 FROM alcance a JOIN conexion c ON c.origen = a.id WHERE a.d < :k
        )
        SELECT count(DISTINCT id) - 1 FROM alcance""",
    "ruta": """
        WITH RECURSIVE bfs(id, d) AS (
          SELECT :inicio, 0
          UNION
          SELECT c.destino, b.d + 1 FROM bfs b JOIN conexion c ON c.origen = b.id WHERE b.d < :max
        )
        SELECT min(d) FROM bfs WHERE id = :fin""",
    "comunes": """
        SELECT count(*) FROM conexion x JOIN conexion y ON x.destino = y.destino
        WHERE x.origen = :inicio AND y.origen = :fin""",
    "top_grado": """
        SELECT origen, count(*) AS g FROM conexion GROUP BY origen ORDER BY g DESC LIMIT 10""",
    "busqueda": "SELECT id FROM usuario WHERE id = :inicio",
}
CYPHER = {
    "alcance": """MATCH (u:BenchUsuario {id: $inicio})
                  MATCH (u)-[:BENCH_CONECTA]-{1,%d}(x) WHERE x <> u
                  RETURN count(DISTINCT x)""",
    "alcance_bfs": """MATCH (u:BenchUsuario {id: $inicio})
                      CALL apoc.path.subgraphNodes(u, {relationshipFilter: 'BENCH_CONECTA', maxLevel: $k})
                      YIELD node RETURN count(node) - 1""",
    "ruta": """MATCH (a:BenchUsuario {id: $inicio}), (b:BenchUsuario {id: $fin})
               OPTIONAL MATCH p = SHORTEST 1 (a)-[:BENCH_CONECTA]-{1,%d}(b)
               RETURN length(p)""",
    "comunes": """MATCH (:BenchUsuario {id: $inicio})-[:BENCH_CONECTA]-(c)-[:BENCH_CONECTA]-(:BenchUsuario {id: $fin})
                  RETURN count(DISTINCT c)""",
    "top_grado": """MATCH (u:BenchUsuario)
                    RETURN u.id, COUNT { (u)-[:BENCH_CONECTA]-() } AS g ORDER BY g DESC LIMIT 10""",
    "busqueda": "MATCH (u:BenchUsuario {id: $inicio}) RETURN u.id",
}

def medir_sqlite(con, sql, params_lista):
    tiempos, res = [], None
    for p in params_lista:
        t = time.perf_counter()
        res = con.execute(sql, p).fetchall()
        tiempos.append((time.perf_counter() - t) * 1000)
    return statistics.median(tiempos), res

def medir_neo4j(cypher, params_lista):
    total, servidor, res = [], [], None
    with get_driver().session() as s:
        s.run(cypher, **params_lista[0]).consume()  # calentamiento
        for p in params_lista:
            t = time.perf_counter()
            r = s.run(cypher, **p)
            res = r.values()
            resumen = r.consume()
            total.append((time.perf_counter() - t) * 1000)
            servidor.append(resumen.result_available_after + resumen.result_consumed_after)
    return statistics.median(total), statistics.median(servidor), res

def experimento(n, repeticiones):
    print(f"\n== Red de {n} usuarios ==")
    aristas = generar_red(n)
    print(f"  {len(aristas)} conexiones. Cargando Neo4j y SQLite…")
    cargar_neo4j(n, aristas)
    con = cargar_sqlite(n, aristas)
    pares = [{"inicio": rnd.randrange(n), "fin": rnd.randrange(n)} for _ in range(repeticiones)]

    casos = [("busqueda", "Búsqueda por clave", SQL["busqueda"], CYPHER["busqueda"], {}),
             ("comunes", "Contactos en común (2 saltos)", SQL["comunes"], CYPHER["comunes"], {}),
             ("top_grado", "Top 10 por nº de conexiones (agregación global)", SQL["top_grado"], CYPHER["top_grado"], {})]
    for k in (2, 3, 4, 5, 6):
        casos.append((f"alcance{k}", f"Alcance a {k} saltos (Cypher, enumera caminos)", SQL["alcance"], CYPHER["alcance"] % k, {"k": k}))
        casos.append((f"bfs{k}", f"Alcance a {k} saltos (APOC, BFS por nodos)", SQL["alcance"], CYPHER["alcance_bfs"], {"k": k}))
    casos.append(("ruta", "Ruta más corta (máx. 6 saltos)", SQL["ruta"], CYPHER["ruta"] % 6, {"max": 6}))

    filas = []
    for clave, nombre, sql, cypher, extra in casos:
        params = [{**p, **extra} for p in pares]
        reps = params[:3] if clave in ("top_grado", "alcance5", "alcance6") else params
        t_sql, r_sql = medir_sqlite(con, sql, reps)
        t_neo, t_srv, r_neo = medir_neo4j(cypher, reps)
        norm = (lambda r: [x[-1] for x in r]) if clave == "top_grado" else (lambda r: [tuple(x) for x in r])
        iguales = norm(r_sql) == norm(r_neo)
        filas.append((nombre, t_sql, t_neo, t_srv, iguales))
        print(f"  {nombre:<52} SQLite {t_sql:9.2f} ms | Neo4j {t_neo:8.2f} ms (servidor {t_srv:6.0f} ms)"
              f" {'✓' if iguales else '✗ RESULTADOS DISTINTOS'}")
    con.close()
    return len(aristas), filas

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tamanos", type=int, nargs="+", default=[2000, 20000, 100000])
    ap.add_argument("--repeticiones", type=int, default=15)
    args = ap.parse_args()

    md = ["# Resultados del benchmark grafo vs relacional", "",
          "Generado por `scripts/benchmark.py`. Mediana de varias ejecuciones con origen/destino aleatorios.",
          "SQLite corre en memoria dentro del proceso; Neo4j se consulta por Bolt (localhost).", ""]
    try:
        for n in args.tamanos:
            m, filas = experimento(n, args.repeticiones)
            md += [f"## Red de {n:,} usuarios y {m:,} conexiones".replace(",", "."), "",
                   "| Consulta | SQLite (ms) | Neo4j total (ms) | Neo4j servidor (ms) | Mismo resultado |",
                   "|---|---:|---:|---:|:---:|"]
            md += [f"| {nombre} | {a:.2f} | {b:.2f} | {c:.0f} | {'✓' if ok else '✗'} |" for nombre, a, b, c, ok in filas]
            md.append("")
    finally:
        with get_driver().session() as s:
            limpiar_neo4j(s)
        close_driver()
    salida = ROOT / "docs" / "benchmark_resultados.md"
    salida.write_text("\n".join(md), encoding="utf-8")
    print(f"\nResultados guardados en {salida.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
