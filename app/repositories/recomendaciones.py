"""Recomendaciones basadas en la estructura del grafo (RF8)."""
from app import db


def contactos(uid, limite=10):
    """Amigos de amigos: más contactos en común, habilidades y empresas compartidas = mejor."""
    return db.read(
        """
        MATCH (u:Usuario {id: $id})-[:CONECTA_CON]-(amigo:Usuario)-[:CONECTA_CON]-(sug:Usuario)
        WHERE sug <> u AND NOT (u)-[:CONECTA_CON]-(sug)
        WITH u, sug, count(DISTINCT amigo) AS en_comun, collect(DISTINCT amigo.nombre)[..3] AS via
        CALL (u, sug) {
          OPTIONAL MATCH (u)-[:TIENE_HABILIDAD]->(h)<-[:TIENE_HABILIDAD]-(sug)
          RETURN collect(h.nombre) AS habilidades
        }
        CALL (u, sug) {
          OPTIONAL MATCH (u)-[:TRABAJA_EN]->(e:Empresa)<-[:TRABAJA_EN]-(sug)
          RETURN collect(DISTINCT e.nombre) AS empresas
        }
        RETURN sug.id AS id, sug.nombre AS nombre, sug.titular AS titular, en_comun, via,
               habilidades, empresas,
               3 * en_comun + size(habilidades) + 2 * size(empresas) AS puntaje
        ORDER BY puntaje DESC
        LIMIT $limite
        """,
        id=uid, limite=limite,
    )


def empleos(uid, limite=10):
    """Ofertas abiertas: 80 % cobertura de habilidades + 20 % contactos dentro de la empresa."""
    return db.read(
        """
        MATCH (u:Usuario {id: $id})
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {estado: 'abierta'})
        WHERE NOT (u)-[:POSTULA_A]->(o) AND NOT (u)-[:TRABAJA_EN {actual: true}]->(e)
        CALL (u, o) {
          MATCH (o)-[:REQUIERE]->(h:Habilidad)
          OPTIONAL MATCH (u)-[t:TIENE_HABILIDAD]->(h)
          RETURN count(h) AS total, count(t) AS tiene,
                 collect(CASE WHEN t IS NOT NULL THEN h.nombre END) AS coinciden,
                 collect(CASE WHEN t IS NULL THEN h.nombre END) AS faltan
        }
        WITH u, e, o, total, tiene, coinciden, faltan WHERE tiene > 0
        CALL (u, e) {
          OPTIONAL MATCH (u)-[:CONECTA_CON]-(c:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
          RETURN collect(DISTINCT c.nombre) AS contactos
        }
        WITH e, o, coinciden, faltan, contactos, toFloat(tiene) / total AS cobertura
        RETURN o.id AS id, o.titulo AS titulo, o.modalidad AS modalidad, e.nombre AS empresa,
               coinciden, faltan, contactos, round(cobertura, 2) AS cobertura,
               round(100 * (0.8 * cobertura + 0.2 * CASE WHEN size(contactos) >= 3 THEN 1.0
                                                         ELSE size(contactos) / 3.0 END)) AS puntaje
        ORDER BY puntaje DESC
        LIMIT $limite
        """,
        id=uid, limite=limite,
    )


def colaboradores(uid, limite=10):
    """Personas a ≤ 3 saltos que aportan tecnologías de los proyectos del usuario que él no domina."""
    return db.read(
        """
        MATCH (u:Usuario {id: $id})-[:PARTICIPA_EN]->(p:Proyecto)-[:USA_TECNOLOGIA]->(h:Habilidad)
        WHERE NOT (u)-[:TIENE_HABILIDAD]->(h)
        WITH u, collect(DISTINCT h) AS faltantes, collect(DISTINCT p) AS proyectos
        MATCH path = SHORTEST 1 (u)-[:CONECTA_CON]-{1,3}(c:Usuario)
        WITH u, faltantes, proyectos, c, length(path) AS distancia
        WHERE c <> u AND NONE(p IN proyectos WHERE (c)-[:PARTICIPA_EN]->(p))
        MATCH (c)-[t:TIENE_HABILIDAD]->(h:Habilidad) WHERE h IN faltantes
        WITH c, distancia, collect(h.nombre) AS aporta, avg(t.nivel) AS nivel_medio
        RETURN c.id AS id, c.nombre AS nombre, c.titular AS titular, aporta, distancia,
               round(nivel_medio, 1) AS nivel_medio,
               round(2 * size(aporta) + nivel_medio - distancia, 1) AS puntaje
        ORDER BY puntaje DESC
        LIMIT $limite
        """,
        id=uid, limite=limite,
    )
