from flask import Blueprint, jsonify

from app.repositories import usuario as repo
from app.routes import cuerpo, entero, param

bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")


@bp.get("")
def listar():
    return jsonify(repo.listar(param("q"), entero("limite", 50)))


@bp.post("")
def crear():
    return jsonify(repo.crear(cuerpo())), 201


@bp.get("/<uid>")
def obtener(uid):
    return jsonify(repo.obtener(uid))


@bp.put("/<uid>")
def actualizar(uid):
    return jsonify(repo.actualizar(uid, cuerpo()))


@bp.delete("/<uid>")
def eliminar(uid):
    return jsonify(repo.eliminar(uid))


@bp.post("/<uid>/conexiones")
def conectar(uid):
    return jsonify(repo.conectar(uid, cuerpo().get("usuario_id", ""))), 201


@bp.delete("/<uid>/conexiones/<otro>")
def desconectar(uid, otro):
    return jsonify(repo.desconectar(uid, otro))


@bp.post("/<uid>/habilidades")
def agregar_habilidad(uid):
    return jsonify(repo.agregar_habilidad(uid, cuerpo())), 201


@bp.delete("/<uid>/habilidades/<clave>")
def quitar_habilidad(uid, clave):
    return jsonify(repo.quitar_habilidad(uid, clave))


@bp.post("/<uid>/empleos")
def agregar_empleo(uid):
    return jsonify(repo.agregar_empleo(uid, cuerpo())), 201


@bp.delete("/<uid>/empleos/<eid>")
def quitar_empleo(uid, eid):
    return jsonify(repo.quitar_empleo(uid, eid))


@bp.post("/<uid>/proyectos")
def unir_a_proyecto(uid):
    return jsonify(repo.unir_a_proyecto(uid, cuerpo())), 201


@bp.delete("/<uid>/proyectos/<pid>")
def salir_de_proyecto(uid, pid):
    return jsonify(repo.salir_de_proyecto(uid, pid))


@bp.post("/<uid>/postulaciones")
def postular(uid):
    return jsonify(repo.postular(uid, cuerpo().get("oferta_id", ""))), 201


@bp.delete("/<uid>/postulaciones/<oid>")
def retirar_postulacion(uid, oid):
    return jsonify(repo.retirar_postulacion(uid, oid))
