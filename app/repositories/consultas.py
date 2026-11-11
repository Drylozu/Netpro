"""Consultas de análisis del grafo: las preguntas Q1–Q6 del enunciado y búsqueda de caminos."""
from app import db
from app.repositories.comun import Invalido

# Proyección común de un camino a JSON: lista de nodos (tipo, id, nombre) y tipos de relación.
_CAMINO = """
  [n IN nodes(p) | {tipo: labels(n)[0], id: coalesce(n.id, n.clave),
                    nombre: coalesce(n.nombre, n.titulo)}] AS nodos,
  [r IN relationships(p) | type(r)] AS relaciones,
  length(p) AS saltos
"""


# Q1 ------------------------------------------------------------------------
def usuarios_similares(uid, limite=10):
    """Similitud de Jaccard: |A∩B| / |A∪B| sobre los conjuntos de habilidades."""
    return db.read(
        """
        MATCH (u:Usuario {id: $id})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(otro:Usuario)
        WITH u, otro, collect(h.nombre) AS comunes
        WITH u, otro, comunes,
             COUNT { (u)-[:TIENE_HABILIDAD]->() } AS nu,
             COUNT { (otro)-[:TIENE_HABILIDAD]->() } AS no
        RETURN otro.id AS id, otro.nombre AS nombre, otro.titular AS titular, comunes,
               round(toFloat(size(comunes)) / (nu + no - size(comunes)), 3) AS jaccard,
               EXISTS { (u)-[:CONECTA_CON]-(otro) } AS ya_conectados
        ORDER BY jaccard DESC, size(comunes) DESC
        LIMIT $limite
        """,
        id=uid, limite=limite,
    )


# Q2 ------------------------------------------------------------------------
def contactos_en_comun(a, b):
    if a == b:
        raise Invalido("Elija dos usuarios distintos")
    fila = db.read_one(
        """
        MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
        OPTIONAL MATCH (a)-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b)
        WITH a, b, collect(DISTINCT c {.id, .nombre, .titular}) AS comunes
        OPTIONAL MATCH p = SHORTEST 1 (a)-[:CONECTA_CON]-+(b)
        RETURN a.nombre AS a, b.nombre AS b, comunes,
               EXISTS { (a)-[:CONECTA_CON]-(b) } AS conectados_directamente,
               length(p) AS grados_de_separacion
        """,
        a=a, b=b,
    )
    if not fila:
        raise Invalido("Usuario no encontrado")
    return fila


# Q3 / RF7 ------------------------------------------------------------------
# Modo 'contactos': solo se avanza por CONECTA_CON y el último salto es un
# empleo actual (¿a quién le pido que me presente?).
# Modo 'amplio': cualquier vínculo profesional (excompañeros, proyectos, etc.).
_DESTINOS = {
    "usuario": ("Usuario", "(:Usuario {id: $origen})-[:CONECTA_CON]-{1,8}(:Usuario {id: $destino})"),
    "empresa": ("Empresa", "(:Usuario {id: $origen})-[:CONECTA_CON]-{0,7}(:Usuario)"
                           "-[:TRABAJA_EN {actual: true}]->(:Empresa {id: $destino})"),
    "oferta": ("Oferta", "(:Usuario {id: $origen})-[:CONECTA_CON]-{0,6}(:Usuario)"
                         "-[:TRABAJA_EN {actual: true}]->(:Empresa)-[:PUBLICA]->(:Oferta {id: $destino})"),
}
_AMPLIO = "CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|DESARROLLADO_POR|PUBLICA"


def rutas(origen, destino, tipo="empresa", modo="contactos", maximo=5):
    if tipo not in _DESTINOS:
        raise Invalido("tipo debe ser usuario, empresa u oferta")
    etiqueta, patron = _DESTINOS[tipo]
    if modo == "contactos":
        query = f"MATCH p = ALL SHORTEST {patron} RETURN {_CAMINO} LIMIT $maximo"
    else:
        query = f"""
        MATCH (a:Usuario {{id: $origen}}), (b:{etiqueta} {{id: $destino}})
        MATCH p = allShortestPaths((a)-[:{_AMPLIO}*..10]-(b))
        RETURN {_CAMINO} LIMIT $maximo
        """
    return db.read(query, origen=origen, destino=destino, maximo=maximo)


# Q4 ------------------------------------------------------------------------
def candidatos_para_oferta(oid, limite=15):
    """Puntaje = 70 % cobertura ponderada de habilidades + 30 % cercanía social a la empresa.

    - Cobertura: requisito obligatorio pesa 2, opcional 1; si el nivel del candidato
      es menor al mínimo, cuenta a la mitad.
    - Cercanía: 1.0 si tiene un contacto directo trabajando en la empresa (referido),
      0.5 si lo tiene a 2 saltos, 0 en otro caso.
    """
    return db.read(
        """
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $id})
        MATCH (o)-[:REQUIERE]->(:Habilidad)<-[:TIENE_HABILIDAD]-(c:Usuario)
        WHERE NOT (c)-[:TRABAJA_EN {actual: true}]->(e)
        WITH DISTINCT e, o, c
        CALL (o, c) {
          MATCH (o)-[r:REQUIERE]->(h:Habilidad)
          OPTIONAL MATCH (c)-[t:TIENE_HABILIDAD]->(h)
          WITH r, h, t, CASE WHEN r.obligatoria THEN 2.0 ELSE 1.0 END AS peso
          RETURN sum(peso) AS peso_total,
                 sum(CASE WHEN t IS NULL THEN 0.0
                          WHEN t.nivel >= coalesce(r.nivel_minimo, 1) THEN peso
                          ELSE peso * 0.5 END) AS peso_cubierto,
                 collect(CASE WHEN t IS NOT NULL THEN h.nombre END) AS coinciden,
                 collect(CASE WHEN t IS NULL THEN h.nombre END) AS faltan
        }
        CALL (c, e) {
          OPTIONAL MATCH (c)-[:CONECTA_CON]-(ref:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
          RETURN collect(DISTINCT ref.nombre) AS referidos
        }
        CALL (c, e) {
          OPTIONAL MATCH (c)-[:CONECTA_CON]-(:Usuario)-[:CONECTA_CON]-(r2:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
          WHERE r2 <> c
          RETURN count(DISTINCT r2) AS segundo_grado
        }
        WITH c, o, peso_cubierto / peso_total AS cobertura, coinciden, faltan, referidos, segundo_grado,
             CASE WHEN size(referidos) > 0 THEN 1.0 WHEN segundo_grado > 0 THEN 0.5 ELSE 0.0 END AS cercania
        RETURN c.id AS id, c.nombre AS nombre, c.titular AS titular, coinciden, faltan, referidos,
               segundo_grado, round(cobertura, 2) AS cobertura, cercania,
               EXISTS { (c)-[:POSTULA_A]->(o) } AS ya_postulado,
               round(100 * (0.7 * cobertura + 0.3 * cercania)) AS puntaje
        ORDER BY puntaje DESC, cobertura DESC
        LIMIT $limite
        """,
        id=oid, limite=limite,
    )


# Q5 ------------------------------------------------------------------------
def proyectos_relacionados(pid=None, limite=15):
    """Pares de proyectos que comparten tecnologías, miembros o miembros conectados entre sí.

    Puntaje = 1·tecnologías comunes + 2·miembros compartidos + 0.5·pares de miembros conectados.
    """
    return db.read(
        """
        MATCH (p1:Proyecto), (p2:Proyecto)
        WHERE ($pid IS NULL AND p1.id < p2.id) OR ($pid IS NOT NULL AND p1.id = $pid AND p2 <> p1)
        CALL (p1, p2) {
          OPTIONAL MATCH (p1)-[:USA_TECNOLOGIA]->(h)<-[:USA_TECNOLOGIA]-(p2)
          RETURN collect(h.nombre) AS tecnologias
        }
        CALL (p1, p2) {
          OPTIONAL MATCH (p1)<-[:PARTICIPA_EN]-(m:Usuario)-[:PARTICIPA_EN]->(p2)
          RETURN collect(m.nombre) AS miembros_compartidos
        }
        CALL (p1, p2) {
          OPTIONAL MATCH (p1)<-[:PARTICIPA_EN]-(m1:Usuario)-[:CONECTA_CON]-(m2:Usuario)-[:PARTICIPA_EN]->(p2)
          WHERE NOT (m1)-[:PARTICIPA_EN]->(p2) AND NOT (m2)-[:PARTICIPA_EN]->(p1)
          RETURN collect(DISTINCT m1.nombre + ' ↔ ' + m2.nombre) AS miembros_conectados
        }
        WITH p1, p2, tecnologias, miembros_compartidos, miembros_conectados,
             size(tecnologias) + 2 * size(miembros_compartidos) + 0.5 * size(miembros_conectados) AS puntaje
        WHERE puntaje > 0
        RETURN p1 {.id, .nombre} AS proyecto_a, p2 {.id, .nombre} AS proyecto_b,
               tecnologias, miembros_compartidos, miembros_conectados, puntaje
        ORDER BY puntaje DESC
        LIMIT $limite
        """,
        pid=pid, limite=limite,
    )


# Q6 ------------------------------------------------------------------------
def habilidades_demandadas(limite=15, solo_abiertas=True):
    """Demanda (ofertas que la requieren) frente a oferta de talento (usuarios que la tienen)."""
    return db.read(
        """
        MATCH (o:Oferta)-[r:REQUIERE]->(h:Habilidad)
        WHERE NOT $solo_abiertas OR o.estado = 'abierta'
        WITH h, count(o) AS demanda, sum(CASE WHEN r.obligatoria THEN 1 ELSE 0 END) AS obligatoria
        WITH h, demanda, obligatoria, COUNT { (h)<-[:TIENE_HABILIDAD]-() } AS talento
        RETURN h.nombre AS habilidad, h.categoria AS categoria, demanda, obligatoria, talento,
               round(toFloat(demanda) / CASE WHEN talento = 0 THEN 1 ELSE talento END, 2) AS escasez
        ORDER BY demanda DESC, escasez DESC
        LIMIT $limite
        """,
        limite=limite, solo_abiertas=solo_abiertas,
    )
