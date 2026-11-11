import uuid
from datetime import date


class NoEncontrado(Exception):
    """El nodo solicitado no existe (se traduce a HTTP 404)."""


class Invalido(ValueError):
    """Datos inválidos o regla de negocio incumplida (se traduce a HTTP 400)."""


def nuevo_id():
    return str(uuid.uuid4())


def hoy():
    return date.today().isoformat()


def filtrar(datos, permitidos):
    """Devuelve solo las claves permitidas, descartando vacíos."""
    return {k: v for k, v in (datos or {}).items() if k in permitidos and v not in (None, "")}


def requerir(datos, *campos):
    faltan = [c for c in campos if not str((datos or {}).get(c) or "").strip()]
    if faltan:
        raise Invalido(f"Campos obligatorios: {', '.join(faltan)}")


def existe(fila, entidad="Elemento"):
    if not fila:
        raise NoEncontrado(f"{entidad} no encontrado")
    return fila
