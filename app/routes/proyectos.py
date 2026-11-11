from flask import Blueprint, jsonify

from app.repositories import proyecto as repo
from app.routes import cuerpo, param

bp = Blueprint("proyectos", __name__, url_prefix="/api/proyectos")


@bp.get("")
def listar():
    return jsonify(repo.listar(param("q")))


@bp.post("")
def crear():
    return jsonify(repo.crear(cuerpo())), 201


@bp.get("/<pid>")
def obtener(pid):
    return jsonify(repo.obtener(pid))


@bp.put("/<pid>")
def actualizar(pid):
    return jsonify(repo.actualizar(pid, cuerpo()))


@bp.delete("/<pid>")
def eliminar(pid):
    return jsonify(repo.eliminar(pid))


@bp.post("/<pid>/tecnologias")
def agregar_tecnologia(pid):
    return jsonify(repo.agregar_tecnologia(pid, cuerpo())), 201


@bp.delete("/<pid>/tecnologias/<clave>")
def quitar_tecnologia(pid, clave):
    return jsonify(repo.quitar_tecnologia(pid, clave))
