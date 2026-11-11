from app import db
from app.repositories.comun import Invalido, existe, filtrar, nuevo_id, requerir

CAMPOS = {"nombre", "sector", "ciudad", "tamano", "descripcion"}


def listar(q=""):
    return db.read(
        """
        MATCH (e:Empresa)
        WHERE $q = '' OR toLower(e.nombre) CONTAINS toLower($q) OR toLower(e.sector) CONTAINS toLower($q)
        RETURN e {.*} AS empresa,
               COUNT { (e)<-[:TRABAJA_EN {actual: true}]-() } AS empleados,
               COUNT { (e)-[:PUBLICA]->(:Oferta {estado: 'abierta'}) } AS ofertas_abiertas
        ORDER BY e.nombre
        """,
        q=q.strip(),
    )


def obtener(eid):
    return existe(db.read_one(
        """
        MATCH (e:Empresa {id: $id})
        RETURN e {.*} AS empresa,
          [(e)<-[t:TRABAJA_EN]-(u) | {id: u.id, nombre: u.nombre, cargo: t.cargo, actual: t.actual}] AS empleados,
          [(e)-[:PUBLICA]->(o) | {id: o.id, titulo: o.titulo, estado: o.estado, nivel: o.nivel,
                                  postulantes: COUNT { (o)<-[:POSTULA_A]-() }}] AS ofertas,
          [(e)<-[:DESARROLLADO_POR]-(p) | {id: p.id, nombre: p.nombre, estado: p.estado}] AS proyectos
        """,
        id=eid,
    ), "Empresa")


def crear(datos):
    requerir(datos, "nombre", "sector")
    props = filtrar(datos, CAMPOS)
    props["id"] = nuevo_id()
    return db.write_one("CREATE (e:Empresa) SET e = $props RETURN e {.*} AS empresa", props=props)


def actualizar(eid, datos):
    props = filtrar(datos, CAMPOS)
    if not props:
        raise Invalido("No hay campos para actualizar")
    return existe(db.write_one(
        "MATCH (e:Empresa {id: $id}) SET e += $props RETURN e {.*} AS empresa", id=eid, props=props
    ), "Empresa")


def eliminar(eid):
    return existe(db.write_one(
        """
        MATCH (e:Empresa {id: $id})
        OPTIONAL MATCH (e)-[:PUBLICA]->(o:Oferta)
        WITH e, collect(o) AS ofertas
        FOREACH (o IN ofertas | DETACH DELETE o)
        DETACH DELETE e
        RETURN size(ofertas) AS ofertas_eliminadas
        """,
        id=eid,
    ), "Empresa")
