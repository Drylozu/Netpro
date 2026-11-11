"""Catálogo de habilidades."""
from app import db
from app.repositories.comun import existe, requerir


def listar():
    return db.read(
        """
        MATCH (h:Habilidad)
        RETURN h.clave AS clave, h.nombre AS nombre, h.categoria AS categoria,
               COUNT { (h)<-[:TIENE_HABILIDAD]-() } AS usuarios,
               COUNT { (h)<-[:REQUIERE]-() } AS ofertas
        ORDER BY h.nombre
        """
    )


def crear(datos):
    requerir(datos, "nombre")
    return db.write_one(
        """
        MERGE (h:Habilidad {clave: toLower(trim($nombre))})
          ON CREATE SET h.nombre = trim($nombre), h.categoria = coalesce($categoria, 'otra')
        RETURN h {.*} AS habilidad
        """,
        nombre=datos["nombre"], categoria=datos.get("categoria") or None,
    )


def eliminar(clave):
    return existe(db.write_one(
        "MATCH (h:Habilidad {clave: $c}) DETACH DELETE h RETURN true AS ok", c=clave.lower()
    ), "Habilidad")
