from flask import Blueprint, jsonify

from app.repositories import empresa as repo
from app.routes import cuerpo, param

bp = Blueprint("empresas", __name__, url_prefix="/api/empresas")


@bp.get("")
def listar():
    return jsonify(repo.listar(param("q")))


@bp.post("")
def crear():
    return jsonify(repo.crear(cuerpo())), 201


@bp.get("/<eid>")
def obtener(eid):
    return jsonify(repo.obtener(eid))


@bp.put("/<eid>")
def actualizar(eid):
    return jsonify(repo.actualizar(eid, cuerpo()))


@bp.delete("/<eid>")
def eliminar(eid):
    return jsonify(repo.eliminar(eid))
