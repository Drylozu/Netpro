"""Analítica del grafo con Graph Data Science (GDS) y respaldos en Cypher puro."""
from app import db

GRAFO = "red-usuarios"


def gds_disponible():
    try:
        db.read("RETURN gds.version() AS v")
        return True
    except Exception:
        return False


def calcular_metricas():
    """Proyecta la red de usuarios en memoria, ejecuta PageRank, Betweenness y Louvain,
    escribe los resultados como propiedades de los nodos y libera la proyección."""
    db.write("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAFO)
    proy = db.write_one(
        """
        CALL gds.graph.project($g, 'Usuario', {CONECTA_CON: {orientation: 'UNDIRECTED'}})
        YIELD nodeCount, relationshipCount
        RETURN nodeCount AS nodos, relationshipCount AS relaciones
        """,
        g=GRAFO,
    )
    pr = db.write_one(
        "CALL gds.pageRank.write($g, {writeProperty: 'pagerank'}) YIELD ranIterations "
        "RETURN ranIterations AS iteraciones", g=GRAFO)
    db.write("CALL gds.betweenness.write($g, {writeProperty: 'intermediacion'}) "
             "YIELD nodePropertiesWritten RETURN nodePropertiesWritten", g=GRAFO)
    lv = db.write_one(
        """
        CALL gds.louvain.write($g, {writeProperty: 'comunidad'})
        YIELD communityCount, modularity
        RETURN communityCount AS comunidades, round(modularity, 3) AS modularidad
        """,
        g=GRAFO,
    )
    db.write("CALL gds.graph.drop($g, false) YIELD graphName RETURN graphName", g=GRAFO)
    return {**proy, **pr, **lv, "motor": "gds"}


def calcular_metricas_cypher():
    """Respaldo sin GDS: centralidad de grado como 'influencia' y sector de la empresa
    actual como 'comunidad' aproximada."""
    db.write(
        """
        MATCH (u:Usuario)
        OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
        WITH u, head(collect(e.sector)) AS sector
        SET u.pagerank = toFloat(COUNT { (u)-[:CONECTA_CON]-() }),
            u.intermediacion = 0.0,
            u.comunidad = coalesce(sector, 'Sin empresa')
        """
    )
    fila = db.read_one("MATCH (u:Usuario) RETURN count(DISTINCT u.comunidad) AS comunidades")
    return {**fila, "modularidad": None, "motor": "cypher"}


def metricas_calculadas():
    return db.read_one("MATCH (u:Usuario) WHERE u.pagerank IS NOT NULL RETURN count(u) > 0 AS ok")["ok"]


def influyentes(limite=10):
    return db.read(
        """
        MATCH (u:Usuario) WHERE u.pagerank IS NOT NULL
        OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
        WITH u, head(collect(e.nombre)) AS empresa
        RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular, empresa,
               round(u.pagerank, 3) AS pagerank, round(u.intermediacion, 1) AS intermediacion,
               COUNT { (u)-[:CONECTA_CON]-() } AS grado, u.comunidad AS comunidad
        ORDER BY u.pagerank DESC
        LIMIT $limite
        """,
        limite=limite,
    )


def intermediarios(limite=10):
    """Usuarios 'puente' entre comunidades (alta centralidad de intermediación)."""
    return db.read(
        """
        MATCH (u:Usuario) WHERE u.intermediacion > 0
        RETURN u.id AS id, u.nombre AS nombre, u.titular AS titular,
               round(u.intermediacion, 1) AS intermediacion, u.comunidad AS comunidad
        ORDER BY u.intermediacion DESC
        LIMIT $limite
        """,
        limite=limite,
    )


def miembros_por_comunidad():
    return db.read(
        """
        MATCH (u:Usuario) WHERE u.comunidad IS NOT NULL
        OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
        WITH u, head(collect(e)) AS e
        RETURN toString(u.comunidad) AS comunidad, u.id AS id, u.nombre AS nombre,
               coalesce(u.pagerank, 0) AS pagerank, e.nombre AS empresa, e.sector AS sector,
               [(u)-[:TIENE_HABILIDAD]->(h) | h.nombre] AS habilidades
        """
    )


def conexiones_entre_comunidades():
    return db.read(
        """
        MATCH (a:Usuario)-[:CONECTA_CON]->(b:Usuario)
        WHERE a.comunidad IS NOT NULL AND b.comunidad IS NOT NULL
        RETURN sum(CASE WHEN a.comunidad = b.comunidad THEN 1 ELSE 0 END) AS internas,
               sum(CASE WHEN a.comunidad <> b.comunidad THEN 1 ELSE 0 END) AS externas
        """
    )[0]


def red():
    """Toda la red de usuarios (nodos y conexiones) para dibujarla en el navegador."""
    nodos = db.read(
        """
        MATCH (u:Usuario)
        RETURN u.id AS id, u.nombre AS nombre, toString(u.comunidad) AS comunidad,
               coalesce(u.pagerank, 1.0) AS pagerank
        """
    )
    aristas = db.read("MATCH (a:Usuario)-[:CONECTA_CON]->(b:Usuario) RETURN a.id AS a, b.id AS b")
    return nodos, aristas


def resumen():
    nodos = db.read("MATCH (n) RETURN labels(n)[0] AS etiqueta, count(*) AS total ORDER BY total DESC")
    rels = db.read("MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY total DESC")
    extra = db.read_one(
        """
        MATCH (u:Usuario)
        WITH count(u) AS usuarios, avg(toFloat(COUNT { (u)-[:CONECTA_CON]-() })) AS grado_medio
        RETURN usuarios, round(grado_medio, 2) AS grado_medio,
               COUNT { (o:Oferta {estado: 'abierta'}) } AS ofertas_abiertas,
               COUNT { ()-[:POSTULA_A]->() } AS postulaciones
        """
    )
    return {"nodos": nodos, "relaciones": rels, **extra}
