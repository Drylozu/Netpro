// =====================================================================
//  Consultas clave del proyecto (para ejecutar en Neo4j Browser:
//  http://localhost:7474  usuario neo4j / contraseña del .env)
//  Son las mismas que usa la aplicación en app/repositories/.
//  Primero defina los parámetros, p. ej.:
//    :param usuario => 'ID-DE-UN-USUARIO'
//    :param otro    => 'ID-DE-OTRO-USUARIO'
//    :param empresa => 'ID-DE-UNA-EMPRESA'
//    :param oferta  => 'ID-DE-UNA-OFERTA'
//  Para obtener ids:  MATCH (u:Usuario) RETURN u.id, u.nombre LIMIT 5;
// =====================================================================

// ---------------------------------------------------------------------
// Q1. ¿Qué usuarios tienen habilidades similares?  (similitud de Jaccard)
// ---------------------------------------------------------------------
MATCH (u:Usuario {id: $usuario})-[:TIENE_HABILIDAD]->(h:Habilidad)<-[:TIENE_HABILIDAD]-(otro:Usuario)
WITH u, otro, collect(h.nombre) AS comunes
WITH u, otro, comunes,
     COUNT { (u)-[:TIENE_HABILIDAD]->() }    AS nu,
     COUNT { (otro)-[:TIENE_HABILIDAD]->() } AS no
RETURN otro.nombre, comunes,
       round(toFloat(size(comunes)) / (nu + no - size(comunes)), 3) AS jaccard
ORDER BY jaccard DESC LIMIT 10;

// ---------------------------------------------------------------------
// Q2. ¿Qué contactos en común existen entre dos profesionales?
// ---------------------------------------------------------------------
MATCH (a:Usuario {id: $usuario})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b:Usuario {id: $otro})
RETURN c.nombre AS contacto_en_comun;

// Grados de separación entre ambos
MATCH p = SHORTEST 1 (:Usuario {id: $usuario})-[:CONECTA_CON]-+(:Usuario {id: $otro})
RETURN length(p) AS grados, [n IN nodes(p) | n.nombre] AS camino;

// ---------------------------------------------------------------------
// Q3. ¿Cuál es la ruta más corta entre un usuario y una empresa?
// ---------------------------------------------------------------------
// a) Solo por contactos, terminando en alguien que trabaja ACTUALMENTE allí
MATCH p = ALL SHORTEST (:Usuario {id: $usuario})-[:CONECTA_CON]-{0,7}(:Usuario)
                       -[:TRABAJA_EN {actual: true}]->(:Empresa {id: $empresa})
RETURN [n IN nodes(p) | coalesce(n.nombre, n.titulo)] AS ruta, length(p) AS saltos
LIMIT 5;

// b) Por cualquier vínculo profesional (excompañeros, proyectos...)
MATCH (a:Usuario {id: $usuario}), (e:Empresa {id: $empresa})
MATCH p = shortestPath((a)-[:CONECTA_CON|TRABAJA_EN|PARTICIPA_EN|DESARROLLADO_POR*..10]-(e))
RETURN p;   // en Neo4j Browser se dibuja como grafo

// ---------------------------------------------------------------------
// Q4. ¿Qué candidatos recomendar para una oferta según conexiones y competencias?
//     puntaje = 70 % cobertura ponderada + 30 % cercanía social a la empresa
// ---------------------------------------------------------------------
MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $oferta})
MATCH (o)-[:REQUIERE]->(:Habilidad)<-[:TIENE_HABILIDAD]-(c:Usuario)
WHERE NOT (c)-[:TRABAJA_EN {actual: true}]->(e)
WITH DISTINCT e, o, c
CALL (o, c) {
  MATCH (o)-[r:REQUIERE]->(h:Habilidad)
  OPTIONAL MATCH (c)-[t:TIENE_HABILIDAD]->(h)
  WITH r, t, CASE WHEN r.obligatoria THEN 2.0 ELSE 1.0 END AS peso
  RETURN sum(peso) AS total,
         sum(CASE WHEN t IS NULL THEN 0.0
                  WHEN t.nivel >= coalesce(r.nivel_minimo, 1) THEN peso
                  ELSE peso * 0.5 END) AS cubierto
}
CALL (c, e) {
  OPTIONAL MATCH (c)-[:CONECTA_CON]-(ref:Usuario)-[:TRABAJA_EN {actual: true}]->(e)
  RETURN collect(DISTINCT ref.nombre) AS referidos
}
WITH c, cubierto / total AS cobertura, referidos
RETURN c.nombre, round(cobertura, 2) AS cobertura, referidos,
       round(100 * (0.7 * cobertura + 0.3 * CASE WHEN size(referidos) > 0 THEN 1 ELSE 0 END)) AS puntaje
ORDER BY puntaje DESC LIMIT 10;

// ---------------------------------------------------------------------
// Q5. ¿Qué proyectos comparten tecnologías o miembros relacionados?
// ---------------------------------------------------------------------
MATCH (p1:Proyecto), (p2:Proyecto) WHERE p1.id < p2.id
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
  RETURN count(DISTINCT [m1, m2]) AS pares_conectados
}
WITH p1, p2, tecnologias, miembros_compartidos, pares_conectados,
     size(tecnologias) + 2 * size(miembros_compartidos) + 0.5 * pares_conectados AS puntaje
WHERE puntaje > 0
RETURN p1.nombre, p2.nombre, tecnologias, miembros_compartidos, pares_conectados, puntaje
ORDER BY puntaje DESC LIMIT 10;

// ---------------------------------------------------------------------
// Q6. ¿Qué habilidades son las más demandadas en las ofertas?
// ---------------------------------------------------------------------
MATCH (o:Oferta {estado: 'abierta'})-[:REQUIERE]->(h:Habilidad)
RETURN h.nombre AS habilidad, count(o) AS demanda,
       COUNT { (h)<-[:TIENE_HABILIDAD]-() } AS usuarios_que_la_tienen
ORDER BY demanda DESC LIMIT 10;

// =====================================================================
//  Recomendaciones
// =====================================================================
// Contactos: amigos de amigos aún no conectados
MATCH (u:Usuario {id: $usuario})-[:CONECTA_CON]-(amigo)-[:CONECTA_CON]-(sug:Usuario)
WHERE sug <> u AND NOT (u)-[:CONECTA_CON]-(sug)
RETURN sug.nombre, count(DISTINCT amigo) AS en_comun
ORDER BY en_comun DESC LIMIT 10;

// =====================================================================
//  Analítica con Graph Data Science
// =====================================================================
CALL gds.graph.project('red-usuarios', 'Usuario', {CONECTA_CON: {orientation: 'UNDIRECTED'}});

CALL gds.pageRank.stream('red-usuarios') YIELD nodeId, score
RETURN gds.util.asNode(nodeId).nombre AS usuario, round(score, 3) AS pagerank
ORDER BY pagerank DESC LIMIT 10;

CALL gds.louvain.stats('red-usuarios') YIELD communityCount, modularity
RETURN communityCount, modularity;

CALL gds.graph.drop('red-usuarios') YIELD graphName;
