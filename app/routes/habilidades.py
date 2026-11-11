from flask import Blueprint, jsonify

from app.repositories import habilidad as repo
from app.routes import cuerpo

bp = Blueprint("habilidades", __name__, url_prefix="/api/habilidades")


@bp.get("")
def listar():
    return jsonify(repo.listar())


@bp.post("")
def crear():
    return jsonify(repo.crear(cuerpo())), 201


@bp.delete("/<clave>")
def eliminar(clave):
    return jsonify(repo.eliminar(clave))
