# Netpro

**Netpro** es una aplicación de gestión y análisis de una red profesional (usuarios, empresas, habilidades, proyectos y ofertas) construida sobre una **base de datos de grafos (Neo4j)**. Usa el **driver oficial de Python** y **Cypher**, un backend **Flask** y un frontend en **HTML, CSS y JavaScript puro**.

- El enunciado está en [`enunciado.md`](enunciado.md).
- El plan y las decisiones de diseño están en [`plan.md`](plan.md).
- El informe de investigación (grafo vs relacional) está en [`docs/informe.md`](docs/informe.md).

## Requisitos

- macOS o Linux con `bash`, `curl` y **Python 3.10+**.
- **Java 21 o superior**, que Neo4j necesita (probado con Temurin 25).

No se instala nada en el sistema. Todo queda dentro de esta carpeta.

## Puesta en marcha

```bash
# 1. Descargar Neo4j + plugins en .local/ y crear el entorno Python en .venv/  (una sola vez)
scripts/setup.sh

# 2. Arrancar la base de datos (terminal 1, se detiene con Ctrl+C)
scripts/start-db.sh

# 3. Cargar los datos de prueba (200 usuarios, 20 empresas, 60 ofertas…) — borra lo que haya
.venv/bin/python scripts/seed.py

# 4. Arrancar la aplicación (terminal 2)
scripts/start-app.sh
```

| Qué | Dónde |
|---|---|
| Aplicación web | http://localhost:8000 |
| Neo4j Browser (consultas manuales) | http://localhost:7474 · usuario `neo4j` · contraseña la del `.env` (por defecto `redprofesional`) |
| Consultas Cypher para copiar en el Browser | [`cypher/consultas.cypher`](cypher/consultas.cypher) |

Otros scripts:

```bash
.venv/bin/python scripts/test_connection.py   # comprueba conexión, versión de Neo4j, GDS y APOC
.venv/bin/python scripts/benchmark.py         # experimento grafo vs relacional → docs/benchmark_resultados.md
```

## Qué incluye

| Requisito del enunciado | Dónde verlo en la app |
|---|---|
| CRUD de usuarios | **Usuarios**: lista, búsqueda, crear, editar y eliminar |
| Conexiones entre usuarios | **Usuarios → Conexiones**; botón *Conectar* en **Recomendaciones** |
| Vincular usuarios con habilidades, empresas y proyectos | **Usuarios**: tarjetas Habilidades, Experiencia y Proyectos |
| Empresas y sus ofertas | **Empresas** y **Ofertas** (*+ Publicar oferta*) |
| Habilidades requeridas por oferta | **Ofertas → Habilidades requeridas** (obligatorias o deseables, con nivel mínimo) |
| Postulación | **Usuarios → Postulaciones**, o *Postular* en **Recomendaciones**; el estado se gestiona en la oferta |
| Caminos entre usuarios, empresas y ofertas | **Consultas → Ruta más corta** (solo contactos o cualquier vínculo) |
| Recomendaciones | **Recomendaciones**: contactos, empleos y colaboradores; candidatos en cada oferta |
| Panel de analítica | **Analítica**: PageRank, Betweenness, comunidades con Louvain y habilidades demandadas |
| Preguntas Q1–Q6 | **Consultas** (una tarjeta por pregunta) |

## Arquitectura

```
Navegador (HTML + CSS + JS vanilla)  ──fetch/JSON──►  Flask (app/routes)
                                                         │
                                       app/services (orquestación de la analítica)
                                                         │
                                       app/repositories (TODO el Cypher)
                                                         │
                                       app/db.py (driver oficial, transacciones gestionadas)
                                                         │ Bolt
                                                   Neo4j + APOC + GDS (.local/neo4j)
```

```
app/
├── __init__.py          create_app(): blueprints y manejo de errores (400/404/409/503)
├── db.py                driver único, read()/write() con execute_read/execute_write
├── repositories/        usuario, empresa, oferta, proyecto, habilidad, consultas, recomendaciones, analitica
├── services/            analitica.py (GDS o respaldo en Cypher puro, agregación de comunidades)
├── routes/              un blueprint por recurso (API JSON en /api/...)
└── static/              index.html, css/styles.css, fonts/, js/ (api, ui, store, main, vistas/ incl. red.js)
cypher/                  restricciones e índices + consultas documentadas
scripts/                 setup, start-db, start-app, clean, seed, benchmark, test_connection
docs/                    informe.md, benchmark_resultados.md
```

### API

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `/api/usuarios` | Listar (`?q=&limite=`) / crear |
| GET/PUT/DELETE | `/api/usuarios/<id>` | Perfil completo / actualizar / eliminar (`DETACH DELETE`) |
| POST, DELETE | `/api/usuarios/<id>/conexiones[/<otro>]` | Conectar / desconectar |
| POST, DELETE | `/api/usuarios/<id>/habilidades[/<clave>]` | Agregar (nivel 1–5) / quitar habilidad |
| POST, DELETE | `/api/usuarios/<id>/empleos[/<empresa>]` | Registrar / quitar empleo |
| POST, DELETE | `/api/usuarios/<id>/proyectos[/<proyecto>]` | Unirse / salir de un proyecto |
| POST, DELETE | `/api/usuarios/<id>/postulaciones[/<oferta>]` | Postularse / retirar postulación |
| GET/POST, GET/PUT/DELETE | `/api/empresas[/<id>]` | CRUD de empresas (al borrar, también sus ofertas) |
| GET/POST, GET/PUT/DELETE | `/api/ofertas[/<id>]` | CRUD de ofertas (`?estado=&q=&empresa_id=`) |
| POST, DELETE | `/api/ofertas/<id>/requisitos[/<clave>]` | Requisitos de la oferta |
| PUT | `/api/ofertas/<id>/postulaciones/<usuario>` | Cambiar el estado de una postulación |
| GET/POST, GET/PUT/DELETE | `/api/proyectos[/<id>]` (+ `/tecnologias`) | CRUD de proyectos y sus tecnologías |
| GET/POST/DELETE | `/api/habilidades[/<clave>]` | Catálogo de habilidades |
| GET | `/api/consultas/similares/<usuario>` | Q1: Jaccard |
| GET | `/api/consultas/comunes?a=&b=` | Q2: contactos en común y grados de separación |
| GET | `/api/consultas/rutas?origen=&destino=&tipo=usuario\|empresa\|oferta&modo=contactos\|amplio` | Q3: rutas más cortas |
| GET | `/api/consultas/candidatos/<oferta>` | Q4: candidatos recomendados |
| GET | `/api/consultas/proyectos-relacionados[?proyecto=]` | Q5 |
| GET | `/api/consultas/habilidades-demandadas[?todas=1]` | Q6 |
| GET | `/api/recomendaciones/<usuario>/contactos\|empleos\|colaboradores` | Recomendaciones |
| GET, POST | `/api/analitica`, `/api/analitica/recalcular` | Panel y recálculo con GDS |

Ejemplo: `curl -s localhost:8000/api/consultas/habilidades-demandadas | python3 -m json.tool`

## Desinstalar

1. Detener Neo4j (Ctrl+C en su terminal) y Flask.
2. `scripts/clean.sh` borra `.local/` (Neo4j y la base de datos) y `.venv/`, sin tocar el código.
3. Si se borra la carpeta del proyecto, no queda nada en el sistema.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| La app muestra "No hay conexión con Neo4j" | Arrancar `scripts/start-db.sh` y esperar a que imprima `Started.` |
| `Unsupported Java version` | Neo4j 2026.x necesita Java 21+. Se puede descomprimir un JDK en `.local/jdk/`; `start-db.sh` lo usa automáticamente |
| La contraseña no funciona | La contraseña inicial solo se aplica antes del primer arranque. Para reiniciar desde cero: `scripts/clean.sh` y luego `scripts/setup.sh` |
| El puerto está ocupado (en macOS, AirPlay usa el 5000) | Cambiar `FLASK_PORT` en `.env` (por defecto 8000) |
