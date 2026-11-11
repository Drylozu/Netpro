from flask import Blueprint, jsonify

from app.repositories import oferta as repo
from app.routes import cuerpo, param

bp = Blueprint("ofertas", __name__, url_prefix="/api/ofertas")


@bp.get("")
def listar():
    return jsonify(repo.listar(param("q"), param("estado"), param("empresa_id")))


@bp.post("")
def crear():
    return jsonify(repo.crear(cuerpo())), 201


@bp.get("/<oid>")
def obtener(oid):
    return jsonify(repo.obtener(oid))


@bp.put("/<oid>")
def actualizar(oid):
    return jsonify(repo.actualizar(oid, cuerpo()))


@bp.delete("/<oid>")
def eliminar(oid):
    return jsonify(repo.eliminar(oid))


@bp.post("/<oid>/requisitos")
def agregar_requisito(oid):
    return jsonify(repo.agregar_requisito(oid, cuerpo())), 201


@bp.delete("/<oid>/requisitos/<clave>")
def quitar_requisito(oid, clave):
    return jsonify(repo.quitar_requisito(oid, clave))


@bp.put("/<oid>/postulaciones/<uid>")
def cambiar_estado(oid, uid):
    return jsonify(repo.cambiar_estado_postulacion(oid, uid, cuerpo().get("estado", "")))
