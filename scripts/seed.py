"""Genera y carga un grafo de prueba reproducible (semilla fija).

Uso:  .venv/bin/python scripts/seed.py
ATENCIÓN: borra todos los datos existentes antes de cargar.

Las conexiones se generan con sesgo (misma empresa > mismo sector > azar) para
que el grafo tenga comunidades reales que Louvain pueda detectar, y con
algunos "hubs" para que PageRank destaque usuarios influyentes.
"""
import pathlib
import random
import sys
import uuid
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faker import Faker  # noqa: E402

from app import db  # noqa: E402

SEED = 42
rnd = random.Random(SEED)
fake = Faker("es_CO")
Faker.seed(SEED)


def uid():
    return str(uuid.UUID(int=rnd.getrandbits(128), version=4))


def fecha(desde_anios=8, hasta_anios=0):
    dias = rnd.randint(hasta_anios * 365, desde_anios * 365)
    return (date(2026, 11, 1) - timedelta(days=dias)).isoformat()


# ---------------------------------------------------------------- catálogo
HABILIDADES = {
    "lenguaje": ["Python", "Java", "JavaScript", "TypeScript", "C#", "Go", "SQL", "R", "Kotlin", "PHP"],
    "framework": ["Django", "Flask", "Spring Boot", "React", "Angular", "Node.js", ".NET", "Laravel"],
    "datos": ["Machine Learning", "Power BI", "Pandas", "Spark", "Estadística", "Neo4j",
              "PostgreSQL", "MongoDB", "Tableau", "Excel avanzado"],
    "infraestructura": ["AWS", "Azure", "Docker", "Kubernetes", "Linux", "CI/CD", "Ciberseguridad"],
    "negocio": ["Gestión de proyectos", "Scrum", "Contabilidad", "Finanzas corporativas",
                "Análisis de riesgo", "Marketing digital", "Ventas", "Logística", "UX/UI"],
    "blanda": ["Liderazgo", "Comunicación", "Trabajo en equipo", "Negociación", "Inglés"],
    "salud": ["Historia clínica electrónica", "Bioestadística"],
    "educación": ["Diseño instruccional", "E-learning"],
}
CATEGORIA = {h: c for c, hs in HABILIDADES.items() for h in hs}

SECTORES = {
    "Tecnología": {
        "empresas": ["Andina Software", "Nébula Labs", "Cóndor Cloud", "Pixel Forge", "DataRío"],
        "skills": ["Python", "Java", "JavaScript", "TypeScript", "Go", "React", "Node.js", "Docker",
                   "Kubernetes", "AWS", "CI/CD", "Linux", "Spring Boot", "PostgreSQL", "MongoDB", "Scrum"],
        "cargos": ["Desarrollador backend", "Desarrolladora frontend", "Ingeniero DevOps",
                   "Arquitecta de software", "Tech lead", "QA engineer"],
    },
    "Finanzas": {
        "empresas": ["Banco Altiplano", "Fintech Colibrí", "Seguros Pacífico", "Inversiones Ceiba"],
        "skills": ["SQL", "Python", "Java", "Análisis de riesgo", "Finanzas corporativas", "Contabilidad",
                   "Excel avanzado", "Power BI", "Ciberseguridad", ".NET", "C#", "Estadística"],
        "cargos": ["Analista de riesgo", "Analista financiera", "Desarrollador .NET",
                   "Auditor de sistemas", "Gerente de producto"],
    },
    "Salud": {
        "empresas": ["Clínica Horizonte", "BioAndes", "SaludDigital", "Laboratorios Quindío"],
        "skills": ["Historia clínica electrónica", "Bioestadística", "R", "Python", "Estadística",
                   "Machine Learning", "SQL", "Gestión de proyectos", "Comunicación", "Tableau"],
        "cargos": ["Científica de datos clínicos", "Coordinador de sistemas de salud",
                   "Bioestadístico", "Analista de calidad"],
    },
    "Educación": {
        "empresas": ["EduNube", "Academia Volcán", "Universidad Virtual del Sur"],
        "skills": ["Diseño instruccional", "E-learning", "UX/UI", "JavaScript", "PHP", "Laravel",
                   "Comunicación", "Inglés", "Gestión de proyectos", "Marketing digital"],
        "cargos": ["Diseñadora instruccional", "Desarrollador LMS", "Coordinadora académica",
                   "Especialista en contenidos"],
    },
    "Retail y Logística": {
        "empresas": ["Mercado Estrella", "LogiExpress", "Tiendas Arrayán", "Ruta Verde"],
        "skills": ["Logística", "Ventas", "Marketing digital", "Power BI", "Excel avanzado", "SQL",
                   "Python", "Pandas", "Negociación", "Kotlin", "Azure", "Spark"],
        "cargos": ["Analista de demanda", "Jefe de logística", "Ingeniera de datos",
                   "Desarrollador móvil", "Gerente comercial"],
    },
}
GENERALES = ["Liderazgo", "Comunicación", "Trabajo en equipo", "Inglés", "Scrum", "Gestión de proyectos",
             "Neo4j", "Django", "Flask", "Angular", "Tableau", "Pandas", "Machine Learning"]
CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga", "Pereira", "Manizales", "Cartagena"]
TAMANOS = ["Startup (1-50)", "Mediana (51-500)", "Grande (500+)"]


def generar():
    # Habilidades
    habilidades = [{"clave": h.lower(), "nombre": h, "categoria": c} for h, c in CATEGORIA.items()]

    # Empresas
    empresas = []
    for sector, info in SECTORES.items():
        for nombre in info["empresas"]:
            empresas.append({"id": uid(), "nombre": nombre, "sector": sector,
                             "ciudad": rnd.choice(CIUDADES), "tamano": rnd.choice(TAMANOS),
                             "descripcion": f"Empresa del sector {sector.lower()}."})
    emp_por_sector = {s: [e for e in empresas if e["sector"] == s] for s in SECTORES}

    # Usuarios
    usuarios, trabaja, tiene = [], [], []
    sectores = list(SECTORES)
    pesos = [0.32, 0.2, 0.16, 0.12, 0.2]
    for _ in range(200):
        sector = rnd.choices(sectores, pesos)[0]
        info = SECTORES[sector]
        exp = rnd.randint(0, 20)
        nombre = fake.unique.name()
        usuario_ = fake.unique.user_name()
        u = {"id": uid(), "nombre": nombre, "email": f"{usuario_}@correo.co",
             "titular": rnd.choice(info["cargos"]), "ciudad": rnd.choice(CIUDADES), "pais": "Colombia",
             "anios_experiencia": exp, "fecha_registro": fecha(4),
             "bio": f"Profesional con {exp} años de experiencia en {sector.lower()}.",
             "_sector": sector}
        usuarios.append(u)
        # Empleo actual (88 %) y anterior (40 %)
        actual = None
        if rnd.random() < 0.88:
            actual = rnd.choice(emp_por_sector[sector])
            u["_empresa"] = actual["id"]
            trabaja.append({"u": u["id"], "e": actual["id"], "cargo": u["titular"],
                            "desde": fecha(min(exp, 6) or 1), "hasta": None, "actual": True})
        if exp > 3 and rnd.random() < 0.4:
            otro_sector = sector if rnd.random() < 0.7 else rnd.choice(sectores)
            anterior = rnd.choice([e for e in emp_por_sector[otro_sector] if e is not actual])
            trabaja.append({"u": u["id"], "e": anterior["id"], "cargo": rnd.choice(SECTORES[otro_sector]["cargos"]),
                            "desde": fecha(max(exp, 7), 6), "hasta": fecha(5, 2), "actual": False})
        # Habilidades: mayoría del sector + algunas generales
        propias = rnd.sample(info["skills"], rnd.randint(3, 6)) + rnd.sample(GENERALES, rnd.randint(1, 3))
        for h in set(propias):
            tiene.append({"u": u["id"], "h": h.lower(), "nivel": rnd.randint(1, 5),
                          "anios": rnd.randint(0, max(1, exp))})

    # Conexiones con sesgo para formar comunidades
    por_empresa, por_sector = {}, {}
    for u in usuarios:
        por_sector.setdefault(u["_sector"], []).append(u)
        if "_empresa" in u:
            por_empresa.setdefault(u["_empresa"], []).append(u)
    pares = set()

    def conectar(a, b):
        if a["id"] != b["id"]:
            pares.add(tuple(sorted((a["id"], b["id"]))))

    for u in usuarios:
        for _ in range(rnd.randint(2, 6)):
            r = rnd.random()
            if r < 0.55 and "_empresa" in u:
                conectar(u, rnd.choice(por_empresa[u["_empresa"]]))
            elif r < 0.9:
                conectar(u, rnd.choice(por_sector[u["_sector"]]))
            else:
                conectar(u, rnd.choice(usuarios))
    # Hubs: algunos usuarios muy conectados (reclutadores, líderes)
    for hub in rnd.sample(usuarios, 8):
        for otro in rnd.sample(usuarios, rnd.randint(15, 30)):
            conectar(hub, otro)
    conexiones = [{"a": a, "b": b, "desde": fecha(5)} for a, b in pares]

    # Proyectos
    proyectos, participa, usa, desarrolla = [], [], [], []
    temas = ["Plataforma", "Migración", "Portal", "Motor", "App", "Sistema", "Tablero", "API"]
    objetos = ["de pagos", "de inventario", "de analítica", "de citas", "de recomendaciones",
               "de aprendizaje", "de riesgo", "de rutas", "de clientes", "de facturación"]
    for _ in range(40):
        emp = rnd.choice(empresas)
        info = SECTORES[emp["sector"]]
        estado = rnd.choice(["activo", "activo", "finalizado", "planificado"])
        p = {"id": uid(), "nombre": f"{rnd.choice(temas)} {rnd.choice(objetos)} {rnd.randint(1, 99)}",
             "descripcion": f"Proyecto de {emp['nombre']}.", "fecha_inicio": fecha(3, 0), "estado": estado}
        proyectos.append(p)
        desarrolla.append({"p": p["id"], "e": emp["id"]})
        for h in rnd.sample(info["skills"], rnd.randint(3, 5)):
            usa.append({"p": p["id"], "h": h.lower()})
        candidatos = por_empresa.get(emp["id"], []) or por_sector[emp["sector"]]
        miembros = rnd.sample(candidatos, min(len(candidatos), rnd.randint(2, 4)))
        miembros += rnd.sample(por_sector[emp["sector"]], 2)
        roles = ["Líder", "Desarrollador", "Analista", "Diseñador", "QA", "Consultor"]
        for i, m in enumerate({m["id"]: m for m in miembros}.values()):
            participa.append({"u": m["id"], "p": p["id"], "rol": "Líder" if i == 0 else rnd.choice(roles[1:])})

    # Ofertas
    ofertas, publica, requiere = [], [], []
    niveles = ["Junior", "Semi-senior", "Senior"]
    for _ in range(60):
        emp = rnd.choice(empresas)
        info = SECTORES[emp["sector"]]
        nivel = rnd.choice(niveles)
        base = {"Junior": 3, "Semi-senior": 6, "Senior": 10}[nivel]
        o = {"id": uid(), "titulo": f"{rnd.choice(info['cargos'])} {nivel}",
             "descripcion": f"Vacante en {emp['nombre']} ({emp['sector']}).",
             "modalidad": rnd.choice(["Remoto", "Híbrido", "Presencial"]), "nivel": nivel,
             "salario_min": base * 1_000_000, "salario_max": int(base * 1.5) * 1_000_000,
             "estado": "abierta" if rnd.random() < 0.8 else "cerrada", "fecha_publicacion": fecha(1)}
        ofertas.append(o)
        publica.append({"e": emp["id"], "o": o["id"], "fecha": o["fecha_publicacion"]})
        reqs = rnd.sample(info["skills"], rnd.randint(3, 6))
        for i, h in enumerate(reqs):
            requiere.append({"o": o["id"], "h": h.lower(), "obligatoria": i < 2,
                             "nivel_minimo": {"Junior": 2, "Semi-senior": 3, "Senior": 4}[nivel] if i < 2 else 1})

    # Postulaciones (usuarios con alguna habilidad en común con la oferta)
    skills_de = {}
    for t in tiene:
        skills_de.setdefault(t["u"], set()).add(t["h"])
    req_de = {}
    for r in requiere:
        req_de.setdefault(r["o"], set()).add(r["h"])
    postula = set()
    for o in ofertas:
        aptos = [u for u in usuarios if skills_de.get(u["id"], set()) & req_de[o["id"]]]
        for u in rnd.sample(aptos, min(len(aptos), rnd.randint(0, 5))):
            postula.add((u["id"], o["id"]))
    postulaciones = [{"u": u, "o": o, "fecha": fecha(1),
                      "estado": rnd.choice(["enviada", "enviada", "en_revision", "rechazada", "aceptada"])}
                     for u, o in postula]

    for u in usuarios:
        u.pop("_sector"), u.pop("_empresa", None)
    return locals()


def cargar(d):
    print("Borrando datos anteriores…")
    # CALL {...} IN TRANSACTIONS exige una transacción implícita (auto-commit)
    _run_autocommit("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS")
    print("Creando restricciones…")
    for stmt in (ROOT / "cypher" / "00_constraints.cypher").read_text().split(";"):
        lineas = [l for l in stmt.splitlines() if not l.strip().startswith("//")]
        if "".join(lineas).strip():
            db.write("\n".join(lineas))

    pasos = [
        ("habilidades", "UNWIND $rows AS r CREATE (:Habilidad {clave:r.clave, nombre:r.nombre, categoria:r.categoria})"),
        ("empresas", "UNWIND $rows AS r CREATE (e:Empresa) SET e = r"),
        ("usuarios", "UNWIND $rows AS r CREATE (u:Usuario) SET u = r"),
        ("proyectos", "UNWIND $rows AS r CREATE (p:Proyecto) SET p = r"),
        ("ofertas", "UNWIND $rows AS r CREATE (o:Oferta) SET o = r"),
        ("trabaja", """UNWIND $rows AS r MATCH (u:Usuario {id:r.u}), (e:Empresa {id:r.e})
                       CREATE (u)-[:TRABAJA_EN {cargo:r.cargo, desde:r.desde, hasta:r.hasta, actual:r.actual}]->(e)"""),
        ("tiene", """UNWIND $rows AS r MATCH (u:Usuario {id:r.u}), (h:Habilidad {clave:r.h})
                     CREATE (u)-[:TIENE_HABILIDAD {nivel:r.nivel, anios:r.anios}]->(h)"""),
        ("conexiones", """UNWIND $rows AS r MATCH (a:Usuario {id:r.a}), (b:Usuario {id:r.b})
                          CREATE (a)-[:CONECTA_CON {desde:r.desde}]->(b)"""),
        ("participa", """UNWIND $rows AS r MATCH (u:Usuario {id:r.u}), (p:Proyecto {id:r.p})
                         CREATE (u)-[:PARTICIPA_EN {rol:r.rol}]->(p)"""),
        ("usa", """UNWIND $rows AS r MATCH (p:Proyecto {id:r.p}), (h:Habilidad {clave:r.h})
                   CREATE (p)-[:USA_TECNOLOGIA]->(h)"""),
        ("desarrolla", """UNWIND $rows AS r MATCH (p:Proyecto {id:r.p}), (e:Empresa {id:r.e})
                          CREATE (p)-[:DESARROLLADO_POR]->(e)"""),
        ("publica", """UNWIND $rows AS r MATCH (e:Empresa {id:r.e}), (o:Oferta {id:r.o})
                       CREATE (e)-[:PUBLICA {fecha:r.fecha}]->(o)"""),
        ("requiere", """UNWIND $rows AS r MATCH (o:Oferta {id:r.o}), (h:Habilidad {clave:r.h})
                        CREATE (o)-[:REQUIERE {obligatoria:r.obligatoria, nivel_minimo:r.nivel_minimo}]->(h)"""),
        ("postulaciones", """UNWIND $rows AS r MATCH (u:Usuario {id:r.u}), (o:Oferta {id:r.o})
                             CREATE (u)-[:POSTULA_A {fecha:r.fecha, estado:r.estado}]->(o)"""),
    ]
    for nombre, q in pasos:
        db.write(q, rows=d[nombre])
        print(f"  {nombre:<14} {len(d[nombre]):>5}")


def _run_autocommit(query):
    with db.get_driver().session() as s:
        s.run(query).consume()


if __name__ == "__main__":
    datos = generar()
    cargar(datos)
    print(db.read("MATCH (n) RETURN labels(n)[0] AS etiqueta, count(*) AS total ORDER BY total DESC"))
    db.close_driver()
