from flask import Blueprint, jsonify

from app.services import analitica as servicio

bp = Blueprint("analitica", __name__, url_prefix="/api/analitica")


@bp.get("")
def panel():
    return jsonify(servicio.panel())


@bp.get("/red")
def red():
    return jsonify(servicio.red())


@bp.post("/recalcular")
def recalcular():
    return jsonify(servicio.recalcular())
