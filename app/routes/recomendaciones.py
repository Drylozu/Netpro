from flask import Blueprint, jsonify

from app.repositories import recomendaciones as repo
from app.routes import entero

bp = Blueprint("recomendaciones", __name__, url_prefix="/api/recomendaciones")


@bp.get("/<uid>/contactos")
def contactos(uid):
    return jsonify(repo.contactos(uid, entero("limite", 10)))


@bp.get("/<uid>/empleos")
def empleos(uid):
    return jsonify(repo.empleos(uid, entero("limite", 10)))


@bp.get("/<uid>/colaboradores")
def colaboradores(uid):
    return jsonify(repo.colaboradores(uid, entero("limite", 10)))
