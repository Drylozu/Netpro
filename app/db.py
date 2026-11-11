import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "")),
        )
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _run(tx, query, params):
    return [record.data() for record in tx.run(query, params)]


def read(query, **params):
    with get_driver().session() as session:
        return session.execute_read(_run, query, params)


def write(query, **params):
    with get_driver().session() as session:
        return session.execute_write(_run, query, params)


def read_one(query, **params):
    rows = read(query, **params)
    return rows[0] if rows else None


def write_one(query, **params):
    rows = write(query, **params)
    return rows[0] if rows else None
