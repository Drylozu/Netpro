from app import db
from app.repositories.comun import Invalido, existe, filtrar, nuevo_id, requerir

CAMPOS = {"nombre", "descripcion", "fecha_inicio", "fecha_fin", "estado"}


def listar(q=""):
    return db.read(
        """
        MATCH (p:Proyecto)
        WHERE $q = '' OR toLower(p.nombre) CONTAINS toLower($q)
        OPTIONAL MATCH (p)-[:DESARROLLADO_POR]->(e:Empresa)
        RETURN p {.*} AS proyecto, e.nombre AS empresa,
               [(p)-[:USA_TECNOLOGIA]->(h) | h.nombre] AS tecnologias,
               COUNT { (p)<-[:PARTICIPA_EN]-() } AS miembros
        ORDER BY p.nombre
        """,
        q=q.strip(),
    )


def obtener(pid):
    return existe(db.read_one(
        """
        MATCH (p:Proyecto {id: $id})
        OPTIONAL MATCH (p)-[:DESARROLLADO_POR]->(e:Empresa)
        RETURN p {.*} AS proyecto, e {.id, .nombre} AS empresa,
          [(p)-[:USA_TECNOLOGIA]->(h) | {clave: h.clave, nombre: h.nombre}] AS tecnologias,
          [(p)<-[r:PARTICIPA_EN]-(u) | {id: u.id, nombre: u.nombre, titular: u.titular, rol: r.rol}] AS miembros
        """,
        id=pid,
    ), "Proyecto")


def crear(datos):
    requerir(datos, "nombre")
    props = filtrar(datos, CAMPOS)
    props["id"] = nuevo_id()
    props.setdefault("estado", "activo")
    fila = db.write_one(
        """
        CREATE (p:Proyecto) SET p = $props
        WITH p
        OPTIONAL MATCH (e:Empresa {id: $empresa})
        FOREACH (_ IN CASE WHEN e IS NULL THEN [] ELSE [1] END | CREATE (p)-[:DESARROLLADO_POR]->(e))
        RETURN p {.*} AS proyecto
        """,
        props=props, empresa=datos.get("empresa_id") or "",
    )
    for t in datos.get("tecnologias") or []:
        agregar_tecnologia(props["id"], {"nombre": t})
    return fila


def actualizar(pid, datos):
    props = filtrar(datos, CAMPOS)
    if not props:
        raise Invalido("No hay campos para actualizar")
    return existe(db.write_one(
        "MATCH (p:Proyecto {id: $id}) SET p += $props RETURN p {.*} AS proyecto", id=pid, props=props
    ), "Proyecto")


def eliminar(pid):
    return existe(db.write_one(
        "MATCH (p:Proyecto {id: $id}) DETACH DELETE p RETURN true AS ok", id=pid
    ), "Proyecto")


def agregar_tecnologia(pid, datos):
    requerir(datos, "nombre")
    return existe(db.write_one(
        """
        MATCH (p:Proyecto {id: $id})
        MERGE (h:Habilidad {clave: toLower(trim($nombre))})
          ON CREATE SET h.nombre = trim($nombre), h.categoria = 'otra'
        MERGE (p)-[:USA_TECNOLOGIA]->(h)
        RETURN h.nombre AS tecnologia
        """,
        id=pid, nombre=datos["nombre"],
    ), "Proyecto")


def quitar_tecnologia(pid, clave):
    return db.write_one(
        "MATCH (:Proyecto {id: $id})-[r:USA_TECNOLOGIA]->(:Habilidad {clave: $c}) DELETE r RETURN count(*) AS eliminadas",
        id=pid, c=clave.lower(),
    )
