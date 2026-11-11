from flask import Blueprint, jsonify

from app.repositories import consultas as repo
from app.routes import entero, param

bp = Blueprint("consultas", __name__, url_prefix="/api/consultas")


@bp.get("/similares/<uid>")
def similares(uid):
    return jsonify(repo.usuarios_similares(uid, entero("limite", 10)))


@bp.get("/comunes")
def comunes():
    return jsonify(repo.contactos_en_comun(param("a"), param("b")))


@bp.get("/rutas")
def rutas():
    return jsonify(repo.rutas(param("origen"), param("destino"), param("tipo", "empresa"),
                              param("modo", "contactos"), entero("maximo", 5)))


@bp.get("/candidatos/<oid>")
def candidatos(oid):
    return jsonify(repo.candidatos_para_oferta(oid, entero("limite", 15)))


@bp.get("/proyectos-relacionados")
def proyectos_relacionados():
    return jsonify(repo.proyectos_relacionados(param("proyecto") or None, entero("limite", 15)))


@bp.get("/habilidades-demandadas")
def habilidades_demandadas():
    return jsonify(repo.habilidades_demandadas(entero("limite", 15), param("todas") != "1"))
