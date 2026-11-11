from app import db
from app.repositories.comun import Invalido, existe, filtrar, hoy, nuevo_id, requerir

CAMPOS = {"titulo", "descripcion", "modalidad", "nivel", "salario_min", "salario_max", "estado"}
ESTADOS_POSTULACION = {"enviada", "en_revision", "rechazada", "aceptada"}


def _normalizar(datos):
    props = filtrar(datos, CAMPOS)
    for campo in ("salario_min", "salario_max"):
        if campo in props:
            props[campo] = int(props[campo])
    if props.get("estado") not in (None, "abierta", "cerrada"):
        raise Invalido("estado debe ser 'abierta' o 'cerrada'")
    return props


def listar(q="", estado="", empresa_id=""):
    return db.read(
        """
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta)
        WHERE ($estado = '' OR o.estado = $estado)
          AND ($empresa = '' OR e.id = $empresa)
          AND ($q = '' OR toLower(o.titulo) CONTAINS toLower($q) OR toLower(e.nombre) CONTAINS toLower($q))
        RETURN o {.*} AS oferta, e.id AS empresa_id, e.nombre AS empresa,
               [(o)-[r:REQUIERE]->(h) | {nombre: h.nombre, obligatoria: r.obligatoria}] AS requisitos,
               COUNT { (o)<-[:POSTULA_A]-() } AS postulantes
        ORDER BY o.fecha_publicacion DESC
        """,
        q=q.strip(), estado=estado, empresa=empresa_id,
    )


def obtener(oid):
    return existe(db.read_one(
        """
        MATCH (e:Empresa)-[:PUBLICA]->(o:Oferta {id: $id})
        RETURN o {.*} AS oferta, e {.id, .nombre, .sector} AS empresa,
          [(o)-[r:REQUIERE]->(h) | {clave: h.clave, nombre: h.nombre, obligatoria: r.obligatoria,
                                    nivel_minimo: r.nivel_minimo}] AS requisitos,
          [(o)<-[r:POSTULA_A]-(u) | {id: u.id, nombre: u.nombre, titular: u.titular,
                                     estado: r.estado, fecha: r.fecha}] AS postulantes
        """,
        id=oid,
    ), "Oferta")


def crear(datos):
    requerir(datos, "empresa_id", "titulo")
    props = _normalizar(datos)
    props.update(id=nuevo_id(), fecha_publicacion=hoy())
    props.setdefault("estado", "abierta")
    fila = existe(db.write_one(
        """
        MATCH (e:Empresa {id: $empresa})
        CREATE (e)-[:PUBLICA {fecha: $hoy}]->(o:Oferta)
        SET o = $props
        RETURN o {.*} AS oferta
        """,
        empresa=datos["empresa_id"], props=props, hoy=hoy(),
    ), "Empresa")
    for req in datos.get("requisitos") or []:
        agregar_requisito(props["id"], req)
    return fila


def actualizar(oid, datos):
    props = _normalizar(datos)
    if not props:
        raise Invalido("No hay campos para actualizar")
    return existe(db.write_one(
        "MATCH (o:Oferta {id: $id}) SET o += $props RETURN o {.*} AS oferta", id=oid, props=props
    ), "Oferta")


def eliminar(oid):
    return existe(db.write_one(
        "MATCH (o:Oferta {id: $id}) DETACH DELETE o RETURN true AS ok", id=oid
    ), "Oferta")


def agregar_requisito(oid, datos):
    requerir(datos, "nombre")
    return existe(db.write_one(
        """
        MATCH (o:Oferta {id: $id})
        MERGE (h:Habilidad {clave: toLower(trim($nombre))})
          ON CREATE SET h.nombre = trim($nombre), h.categoria = 'otra'
        MERGE (o)-[r:REQUIERE]->(h)
        SET r.obligatoria = $obligatoria, r.nivel_minimo = $nivel
        RETURN h.nombre AS habilidad, r.obligatoria AS obligatoria
        """,
        id=oid, nombre=datos["nombre"], obligatoria=bool(datos.get("obligatoria")),
        nivel=int(datos.get("nivel_minimo") or 1),
    ), "Oferta")


def quitar_requisito(oid, clave):
    return db.write_one(
        "MATCH (:Oferta {id: $id})-[r:REQUIERE]->(:Habilidad {clave: $c}) DELETE r RETURN count(*) AS eliminadas",
        id=oid, c=clave.lower(),
    )


def cambiar_estado_postulacion(oid, uid, estado):
    if estado not in ESTADOS_POSTULACION:
        raise Invalido(f"Estado inválido. Use: {', '.join(sorted(ESTADOS_POSTULACION))}")
    return existe(db.write_one(
        """
        MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o})
        SET r.estado = $estado RETURN r.estado AS estado
        """,
        u=uid, o=oid, estado=estado,
    ), "Postulación")
