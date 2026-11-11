"""Prueba mínima de conexión: python scripts/test_connection.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app import db

print(db.read_one("RETURN 1 AS ok"))
print(db.read("CALL dbms.components() YIELD name, versions RETURN name, versions"))
print(db.read_one("RETURN gds.version() AS gds, apoc.version() AS apoc"))
db.close_driver()
