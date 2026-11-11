"""CRUD de usuarios y sus relaciones (conexiones, habilidades, empleos, proyectos, postulaciones)."""
from app import db
from app.repositories.comun import Invalido, existe, filtrar, hoy, nuevo_id, requerir

CAMPOS = {"nombre", "email", "titular", "ciudad", "pais", "anios_experiencia", "bio"}


def _normalizar(datos):
    props = filtrar(datos, CAMPOS)
    if "anios_experiencia" in props:
        try:
            props["anios_experiencia"] = int(props["anios_experiencia"])
        except (TypeError, ValueError):
            raise Invalido("anios_experiencia debe ser un número entero")
    if "email" in props:
        props["email"] = props["email"].strip().lower()
    return props


# ------------------------------------------------------------------ CRUD
def listar(q="", limite=50):
    return db.read(
        """
        MATCH (u:Usuario)
        WHERE $q = '' OR toLower(u.nombre) CONTAINS toLower($q)
              OR toLower(coalesce(u.titular, '')) CONTAINS toLower($q)
              OR toLower(u.email) CONTAINS toLower($q)
        OPTIONAL MATCH (u)-[:TRABAJA_EN {actual: true}]->(e:Empresa)
        RETURN u.id AS id, u.nombre AS nombre, u.email AS email, u.titular AS titular,
               u.ciudad AS ciudad, head(collect(e.nombre)) AS empresa,
               COUNT { (u)-[:CONECTA_CON]-() } AS conexiones
        ORDER BY nombre
        LIMIT $limite
        """,
        q=q.strip(), limite=int(limite),
    )


def obtener(uid):
    return existe(db.read_one(
        """
        MATCH (u:Usuario {id: $id})
        RETURN u {.*} AS usuario,
          [(u)-[t:TIENE_HABILIDAD]->(h) | {clave: h.clave, nombre: h.nombre, categoria: h.categoria,
                                            nivel: t.nivel, anios: t.anios}] AS habilidades,
          [(u)-[t:TRABAJA_EN]->(e) | {empresa_id: e.id, empresa: e.nombre, sector: e.sector, cargo: t.cargo,
                                      desde: t.desde, hasta: t.hasta, actual: t.actual}] AS empleos,
          [(u)-[r:PARTICIPA_EN]->(p) | {proyecto_id: p.id, proyecto: p.nombre, rol: r.rol, estado: p.estado}] AS proyectos,
          [(u)-[r:CONECTA_CON]-(c) | {id: c.id, nombre: c.nombre, titular: c.titular, desde: r.desde}] AS conexiones,
          [(u)-[r:POSTULA_A]->(o)<-[:PUBLICA]-(e) | {oferta_id: o.id, titulo: o.titulo, empresa: e.nombre,
                                                     estado: r.estado, fecha: r.fecha}] AS postulaciones
        """,
        id=uid,
    ), "Usuario")


def crear(datos):
    requerir(datos, "nombre", "email")
    props = _normalizar(datos)
    props.update(id=nuevo_id(), fecha_registro=hoy())
    props.setdefault("pais", "Colombia")
    return db.write_one("CREATE (u:Usuario) SET u = $props RETURN u {.*} AS usuario", props=props)


def actualizar(uid, datos):
    props = _normalizar(datos)
    if not props:
        raise Invalido("No hay campos para actualizar")
    return existe(db.write_one(
        "MATCH (u:Usuario {id: $id}) SET u += $props RETURN u {.*} AS usuario", id=uid, props=props
    ), "Usuario")


def eliminar(uid):
    # DETACH DELETE elimina el nodo y todas sus relaciones
    return existe(db.write_one(
        """
        MATCH (u:Usuario {id: $id})
        WITH u, COUNT { (u)--() } AS relaciones
        DETACH DELETE u
        RETURN relaciones
        """,
        id=uid,
    ), "Usuario")


# ------------------------------------------------------------ Conexiones
def conectar(uid, otro_id):
    if uid == otro_id:
        raise Invalido("Un usuario no puede conectarse consigo mismo")
    # MERGE sin dirección: si ya existen conectados (en cualquier sentido) no duplica
    return existe(db.write_one(
        """
        MATCH (a:Usuario {id: $a}), (b:Usuario {id: $b})
        MERGE (a)-[r:CONECTA_CON]-(b)
        ON CREATE SET r.desde = $hoy
        RETURN a.nombre AS de, b.nombre AS con, r.desde AS desde
        """,
        a=uid, b=otro_id, hoy=hoy(),
    ), "Usuario")


def desconectar(uid, otro_id):
    return db.write_one(
        """
        MATCH (:Usuario {id: $a})-[r:CONECTA_CON]-(:Usuario {id: $b})
        DELETE r RETURN count(*) AS eliminadas
        """,
        a=uid, b=otro_id,
    )


# ----------------------------------------------------------- Habilidades
def agregar_habilidad(uid, datos):
    requerir(datos, "nombre")
    nivel = int(datos.get("nivel") or 3)
    if not 1 <= nivel <= 5:
        raise Invalido("El nivel debe estar entre 1 y 5")
    return existe(db.write_one(
        """
        MATCH (u:Usuario {id: $id})
        MERGE (h:Habilidad {clave: toLower(trim($nombre))})
          ON CREATE SET h.nombre = trim($nombre), h.categoria = coalesce($categoria, 'otra')
        MERGE (u)-[t:TIENE_HABILIDAD]->(h)
        SET t.nivel = $nivel, t.anios = $anios
        RETURN h.nombre AS habilidad, t.nivel AS nivel
        """,
        id=uid, nombre=datos["nombre"], categoria=datos.get("categoria"),
        nivel=nivel, anios=int(datos.get("anios") or 0),
    ), "Usuario")


def quitar_habilidad(uid, clave):
    return db.write_one(
        "MATCH (:Usuario {id: $id})-[t:TIENE_HABILIDAD]->(:Habilidad {clave: $clave}) "
        "DELETE t RETURN count(*) AS eliminadas",
        id=uid, clave=clave.lower(),
    )


# --------------------------------------------------------------- Empleos
def agregar_empleo(uid, datos):
    requerir(datos, "empresa_id", "cargo")
    actual = bool(datos.get("actual", True))
    return existe(db.write_one(
        """
        MATCH (u:Usuario {id: $id}), (e:Empresa {id: $empresa})
        // Si es el empleo actual, los demás empleos dejan de serlo
        CALL (u, e) {
          MATCH (u)-[otro:TRABAJA_EN {actual: true}]->(x) WHERE $actual AND x <> e
          SET otro.actual = false, otro.hasta = coalesce(otro.hasta, $hoy)
        }
        MERGE (u)-[t:TRABAJA_EN]->(e)
        SET t.cargo = $cargo, t.desde = coalesce($desde, t.desde, $hoy), t.hasta = $hasta, t.actual = $actual
        RETURN e.nombre AS empresa, t.cargo AS cargo, t.actual AS actual
        """,
        id=uid, empresa=datos["empresa_id"], cargo=datos["cargo"], desde=datos.get("desde") or None,
        hasta=None if actual else (datos.get("hasta") or hoy()), actual=actual, hoy=hoy(),
    ), "Usuario o empresa")


def quitar_empleo(uid, empresa_id):
    return db.write_one(
        "MATCH (:Usuario {id: $id})-[t:TRABAJA_EN]->(:Empresa {id: $e}) DELETE t RETURN count(*) AS eliminadas",
        id=uid, e=empresa_id,
    )


# ------------------------------------------------------------- Proyectos
def unir_a_proyecto(uid, datos):
    requerir(datos, "proyecto_id")
    return existe(db.write_one(
        """
        MATCH (u:Usuario {id: $id}), (p:Proyecto {id: $p})
        MERGE (u)-[r:PARTICIPA_EN]->(p)
        SET r.rol = coalesce($rol, r.rol, 'Miembro')
        RETURN p.nombre AS proyecto, r.rol AS rol
        """,
        id=uid, p=datos["proyecto_id"], rol=datos.get("rol") or None,
    ), "Usuario o proyecto")


def salir_de_proyecto(uid, proyecto_id):
    return db.write_one(
        "MATCH (:Usuario {id: $id})-[r:PARTICIPA_EN]->(:Proyecto {id: $p}) DELETE r RETURN count(*) AS eliminadas",
        id=uid, p=proyecto_id,
    )


# --------------------------------------------------------- Postulaciones
def postular(uid, oferta_id):
    fila = existe(db.read_one(
        "MATCH (u:Usuario {id: $u}), (o:Oferta {id: $o}) RETURN o.estado AS estado",
        u=uid, o=oferta_id,
    ), "Usuario u oferta")
    if fila["estado"] != "abierta":
        raise Invalido("La oferta está cerrada")
    return db.write_one(
        """
        MATCH (u:Usuario {id: $u}), (o:Oferta {id: $o})
        MERGE (u)-[r:POSTULA_A]->(o)
        ON CREATE SET r.fecha = $hoy, r.estado = 'enviada'
        RETURN o.titulo AS oferta, r.estado AS estado, r.fecha AS fecha
        """,
        u=uid, o=oferta_id, hoy=hoy(),
    )


def retirar_postulacion(uid, oferta_id):
    return db.write_one(
        "MATCH (:Usuario {id: $u})-[r:POSTULA_A]->(:Oferta {id: $o}) DELETE r RETURN count(*) AS eliminadas",
        u=uid, o=oferta_id,
    )
