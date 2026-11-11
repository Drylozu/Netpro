"""Fábrica de la aplicación Flask: API JSON en /api y frontend estático en /."""
import atexit

from flask import Flask, jsonify
from neo4j.exceptions import ConstraintError, Neo4jError, ServiceUnavailable

from app import db
from app.repositories.comun import Invalido, NoEncontrado


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    from app.routes import (analitica, consultas, empresas, habilidades, ofertas, proyectos,
                            recomendaciones, usuarios)
    for modulo in (usuarios, empresas, ofertas, proyectos, habilidades, consultas, recomendaciones, analitica):
        app.register_blueprint(modulo.bp)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(Invalido)
    def invalido(e):
        return jsonify(error=str(e)), 400

    @app.errorhandler(NoEncontrado)
    def no_encontrado(e):
        return jsonify(error=str(e)), 404

    @app.errorhandler(ConstraintError)
    def duplicado(e):
        return jsonify(error="Ya existe un registro con ese valor único (p. ej. email o nombre)."), 409

    @app.errorhandler(ServiceUnavailable)
    def sin_bd(e):
        return jsonify(error="No hay conexión con Neo4j. ¿Está corriendo scripts/start-db.sh?"), 503

    @app.errorhandler(Neo4jError)
    def error_neo4j(e):
        return jsonify(error=f"Error de Neo4j: {e.message}"), 500

    atexit.register(db.close_driver)
    return app
