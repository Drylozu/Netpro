from flask import request

from app.repositories.comun import Invalido


def cuerpo():
    return request.get_json(silent=True) or {}


def param(nombre, defecto=""):
    return request.args.get(nombre, defecto).strip()


def entero(nombre, defecto):
    try:
        return int(request.args.get(nombre, defecto))
    except ValueError:
        raise Invalido(f"'{nombre}' debe ser un número")
