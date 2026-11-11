import threading
from collections import Counter, defaultdict

from app.repositories import analitica as repo
from app.repositories import consultas

_ultimo_calculo = {}
# Evita que dos peticiones proyecten el grafo de GDS al mismo tiempo
_candado = threading.Lock()


def _calcular():
    global _ultimo_calculo
    _ultimo_calculo = repo.calcular_metricas() if repo.gds_disponible() else repo.calcular_metricas_cypher()
    return _ultimo_calculo


def recalcular():
    with _candado:
        return _calcular()


def _asegurar_metricas():
    if _ultimo_calculo and repo.metricas_calculadas():
        return
    with _candado:
        if not (_ultimo_calculo and repo.metricas_calculadas()):
            _calcular()


def comunidades(maximo=10):
    _asegurar_metricas()
    grupos = defaultdict(list)
    for fila in repo.miembros_por_comunidad():
        grupos[fila["comunidad"]].append(fila)
    resultado = []
    for cid, miembros in grupos.items():
        miembros.sort(key=lambda m: m["pagerank"], reverse=True)
        sectores = Counter(m["sector"] for m in miembros if m["sector"])
        empresas = Counter(m["empresa"] for m in miembros if m["empresa"])
        habilidades = Counter(h for m in miembros for h in m["habilidades"])
        sector, n_sector = sectores.most_common(1)[0] if sectores else ("—", 0)
        resultado.append({
            "comunidad": cid,
            "tamano": len(miembros),
            "sector_dominante": sector,
            "pureza_sector": round(n_sector / len(miembros), 2),
            "empresas": [e for e, _ in empresas.most_common(3)],
            "habilidades": [h for h, _ in habilidades.most_common(5)],
            "lideres": [{"id": m["id"], "nombre": m["nombre"]} for m in miembros[:5]],
        })
    resultado.sort(key=lambda c: c["tamano"], reverse=True)
    return resultado[:maximo]


def panel():
    _asegurar_metricas()
    return {
        "calculo": _ultimo_calculo,
        "resumen": repo.resumen(),
        "influyentes": repo.influyentes(10),
        "intermediarios": repo.intermediarios(8),
        "comunidades": comunidades(),
        "cohesion": repo.conexiones_entre_comunidades(),
        "habilidades_demandadas": consultas.habilidades_demandadas(12),
    }


def red():
    _asegurar_metricas()
    nodos, aristas = repo.red()
    return {
        "nodos": nodos,
        "aristas": aristas,
        "comunidades": [{k: c[k] for k in ("comunidad", "tamano", "sector_dominante", "empresas")} for c in comunidades(maximo=50)],
    }
