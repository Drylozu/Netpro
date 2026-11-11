# Plan del proyecto — Netpro (red profesional sobre Neo4j)

> **Estado (2026-11-10): implementado.** Todas las fases (0–8) están completas: los RF1–RF9 y las preguntas Q1–Q6 funcionan, el informe está escrito y el experimento está medido. Instrucciones de uso en [`README.md`](README.md); investigación en [`docs/informe.md`](docs/informe.md).
> Versiones: Neo4j Community 2026.10.2, APOC 2026.10.2, GDS 2026.10.2, Java (Temurin) 25 del sistema, Python 3.14 en `.venv`.

## 1. Qué pide el enunciado (resumen)

Construir una **aplicación de red profesional** (tipo LinkedIn simplificado) cuyo almacenamiento sea **Neo4j**, accedida desde código mediante el **driver oficial** y consultada con **Cypher**. Tiene dos partes:

| Parte | Qué hay que entregar |
|---|---|
| **Aplicación** | CRUD de usuarios, gestión de relaciones (conexiones, habilidades, empresas, proyectos, ofertas, postulaciones), consultas de caminos, recomendaciones y un panel de analítica. |
| **Investigación** | Explicar, con argumentos y evidencia, en qué escenarios el modelo de grafos supera al relacional y en cuáles no. |

### Requisitos funcionales (checklist)

- [x] **RF1** CRUD de usuarios (datos personales y profesionales).
- [x] **RF2** Conectar usuarios entre sí (`CONECTA_CON`).
- [x] **RF3** Vincular usuarios con habilidades, empresas y proyectos.
- [x] **RF4** Registrar empresas y las ofertas que publican.
- [x] **RF5** Asociar ofertas con habilidades requeridas.
- [x] **RF6** Postular un usuario a una oferta.
- [x] **RF7** Consultar caminos/conexiones entre usuarios, empresas y ofertas.
- [x] **RF8** Recomendar contactos, empleos y colaboradores usando la estructura del grafo.
- [x] **RF9** Panel de analítica: usuarios más influyentes, comunidades detectadas, habilidades más demandadas.

### Preguntas que el sistema debe responder

| # | Pregunta | Técnica en el grafo |
|---|---|---|
| Q1 | ¿Qué usuarios tienen habilidades similares? | Similitud de Jaccard sobre `TIENE_HABILIDAD` |
| Q2 | ¿Qué contactos en común tienen dos profesionales? | Patrón `(a)-[:CONECTA_CON]-(x)-[:CONECTA_CON]-(b)` |
| Q3 | ¿Ruta más corta entre un usuario y una empresa? | `ALL SHORTEST` por `CONECTA_CON` terminando en `TRABAJA_EN {actual}` (solo contactos) o `allShortestPaths` por cualquier vínculo |
| Q4 | ¿Qué candidatos recomendar para una oferta? | Puntaje = cobertura de habilidades + cercanía social a la empresa |
| Q5 | ¿Qué proyectos comparten tecnologías o miembros relacionados? | Habilidades comunes del proyecto + miembros conectados |
| Q6 | ¿Qué habilidades son las más demandadas? | Grado entrante de `REQUIERE` sobre `Habilidad` |

---

## 2. Decisiones de arquitectura

### 2.1 Stack tecnológico

| Capa | Elección | Justificación |
|---|---|---|
| Base de datos | **Neo4j Community (distribución `.tar.gz`) descomprimida dentro del proyecto** | Gratis, local y **portable**: no se instala en el sistema, todo (datos, logs, plugins) vive en `.local/neo4j/`. Incluye **APOC** core; **GDS** se añade copiando un `.jar` a `plugins/`. Se descartan Neo4j Desktop (deja archivos en `~/Library`), Docker (no instalado) y AuraDB Free (no incluye GDS). |
| Lenguaje | **Python del sistema + `venv` en `.venv/`** | Driver oficial `neo4j` maduro, sintaxis simple, buen ecosistema de datos. Las librerías quedan dentro del proyecto. |
| Driver | **`neo4j` (driver oficial de Python)** | Es lo que pide la actividad: uso explícito de un controlador de conexión, sesiones y transacciones. |
| Backend | **Flask** | Micro-framework mínimo: expone una API JSON (`/api/...`) y sirve los archivos estáticos. Es el único framework del proyecto. |
| Frontend | **HTML + CSS + JavaScript puro (vanilla)** | Sin frameworks ni librerías de frontend, sin build, sin npm. El JS usa `fetch()` contra la API de Flask y pinta el resultado en el DOM. |
| Visualización de caminos | HTML/CSS | Un camino más corto es una secuencia lineal de nodos → se dibuja como una cadena de "chips" con flechas (`Ana → Luis → Acme`). |
| Gráficos del panel | Barras horizontales en CSS puro | Rankings (influyentes, habilidades demandadas) = `div` con `width` proporcional. Comunidades = tarjetas agrupadas por color. |
| Datos de prueba | `Faker` (locale `es_CO`/`es_ES`) + listas curadas de habilidades/empresas | Grafo realista y reproducible (semilla fija). |
| Configuración | `.env` + `python-dotenv` | Credenciales fuera del código. |

> Descartados: Streamlit, React/Vue, Bootstrap/Tailwind, Chart.js y similares. El objetivo es que el frontend sea mínimo y que todo el protagonismo lo tengan el modelo de grafo y el Cypher. Si más adelante se quiere ver el grafo completo como red interactiva, la única excepción razonable sería una librería de visualización (p. ej. vis-network) guardada localmente en `static/vendor/`, y solo con aprobación previa.

### 2.2 Entorno portable (sin modificar el sistema)

Requisito: **borrar la carpeta del proyecto debe eliminarlo todo**, sin residuos en el sistema.

| Componente | Dónde vive | Cómo se evita tocar el sistema |
|---|---|---|
| Neo4j | `.local/neo4j/` | Tarball descomprimido; `data/`, `logs/` y `plugins/` quedan dentro. Se ejecuta en primer plano con `neo4j console` (no se registra como servicio). |
| Java | Temurin 25 ya instalado, o un JDK 21 portable en `.local/jdk/` | Si la versión de Neo4j no admite Java 25, se descarga un JDK 21 en `.tar.gz` y se usa solo vía `JAVA_HOME` dentro de los scripts del proyecto. |
| Librerías Python | `.venv/` | Entorno virtual local; `pip install --no-cache-dir` para no dejar caché en `~/Library/Caches/pip`. |
| Flask | `.venv/` | Servidor de desarrollo de Flask (`flask run`), sin instalar servicios ni servidores web en el sistema. |
| Frontend | `app/static/` | Archivos planos; nada se descarga de CDNs ni de npm. |
| Variables / credenciales | `.env` del proyecto | Nada en `~/.zshrc` ni variables globales. |

Scripts de conveniencia: `scripts/setup.sh` (descarga y prepara todo en `.local/`), `scripts/start-db.sh` (arranca Neo4j con el `JAVA_HOME` local) y `scripts/clean.sh` (borra `.local/` y `.venv/`).

**Desinstalación total:** detener Neo4j (Ctrl+C) y borrar la carpeta del proyecto.

### 2.3 Arquitectura en capas

```
┌──────────────────────────────────────────┐
│  Frontend (HTML + CSS + JS vanilla)      │  usuarios, empresas, ofertas, conexiones,
│                                          │  recomendaciones, analítica
└──────────────────┬───────────────────────┘
                   │ fetch() → JSON
┌──────────────────▼───────────────────────┐
│  API Flask (routes/)                     │  /api/usuarios, /api/ofertas, /api/caminos,
│                                          │  /api/recomendaciones, /api/analitica ...
├──────────────────────────────────────────┤
│  Servicios (lógica de negocio)           │  recomendaciones, analítica, validaciones
├──────────────────────────────────────────┤
│  Repositorios (consultas Cypher)         │  un módulo por entidad; SOLO aquí hay Cypher
├──────────────────────────────────────────┤
│  Conexión (driver Neo4j, singleton)      │  db.py: driver, sesiones, execute_read/write
└──────────────────────────────────────────┘
                    │ Bolt (neo4j://localhost:7687)
               ┌────▼────┐
               │  Neo4j  │  + APOC + GDS
               └─────────┘
```

Reglas:
- Un **único driver** por aplicación (es thread-safe y costoso de crear); sesiones cortas por operación.
- Usar **transacciones gestionadas** (`session.execute_read` / `execute_write`) para reintentos automáticos.
- **Siempre parámetros** (`$nombre`) en Cypher, nunca concatenar strings (seguridad y caché de planes).
- Toda consulta Cypher vive en la capa de repositorios → fácil de documentar en el informe.
- Los servicios solo orquestan: deciden si usar GDS o el respaldo en Cypher puro y agregan resultados (p. ej. el resumen por comunidad).
- Errores de dominio → HTTP: `Invalido` 400, `NoEncontrado` 404, `ConstraintError` 409 (email o nombre duplicado), Neo4j caído 503.

### 2.4 Estructura de carpetas

```
bd-investigacion/
├── enunciado.md
├── plan.md
├── README.md                 # cómo instalar y ejecutar
├── requirements.txt
├── .env.example              # NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
├── .local/                   # (ignorado) Neo4j portable, JDK opcional
├── .venv/                    # (ignorado) entorno virtual Python
├── app/
│   ├── __init__.py           # create_app(): crea Flask, registra blueprints, cierra driver
│   ├── db.py                 # conexión / driver
│   ├── routes/               # blueprints: usuarios.py, empresas.py, ofertas.py,
│   │                         #   proyectos.py, caminos.py, recomendaciones.py, analitica.py
│   ├── repositories/         # usuario, empresa, habilidad, proyecto, oferta,
│   │                         #   consultas (Q1–Q6, rutas), recomendaciones, analitica (GDS)
│   ├── services/             # analitica.py (GDS o respaldo, agregación de comunidades)
│   └── static/
│       ├── index.html        # una sola página con pestañas/secciones
│       ├── css/styles.css
│       └── js/               # api.js (fetch), ui.js (helpers DOM), store.js (caché), main.js (router)
│           └── vistas/       #   inicio, usuarios, empresas, ofertas, proyectos, consultas,
│                             #   recomendaciones, analitica
├── run.py                    # punto de entrada: python run.py
├── cypher/
│   ├── 00_constraints.cypher # restricciones e índices
│   └── consultas.cypher      # consultas clave documentadas (para el informe)
├── scripts/
│   ├── seed.py               # genera y carga datos de prueba
│   └── benchmark.py          # (investigación) grafo vs relacional
└── docs/
    └── informe.md            # investigación grafo vs relacional + modelo
```

---

## 3. Modelo de datos (grafo)

### 3.1 Nodos

| Etiqueta | Propiedades principales |
|---|---|
| `Usuario` | `id` (UUID), `nombre`, `email` (único), `titular`, `ciudad`, `pais`, `anios_experiencia`, `fecha_registro` |
| `Empresa` | `id`, `nombre` (único), `sector`, `ciudad`, `tamano` |
| `Habilidad` | `clave` (única: nombre normalizado en minúsculas, evita duplicar "Python" y "python"), `nombre` (para mostrar), `categoria` |
| `Proyecto` | `id`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `estado` |
| `Oferta` | `id`, `titulo`, `descripcion`, `modalidad` (remoto/híbrido/presencial), `salario_min`, `salario_max`, `nivel`, `estado` (abierta/cerrada), `fecha_publicacion` |

### 3.2 Relaciones (con propiedades)

```
(Usuario)-[:CONECTA_CON {desde}]->(Usuario)
(Usuario)-[:TRABAJA_EN {cargo, desde, hasta, actual}]->(Empresa)
(Usuario)-[:TIENE_HABILIDAD {nivel: 1..5, anios}]->(Habilidad)
(Usuario)-[:PARTICIPA_EN {rol}]->(Proyecto)
(Empresa)-[:PUBLICA {fecha}]->(Oferta)
(Oferta)-[:REQUIERE {nivel_minimo, obligatoria: bool}]->(Habilidad)
(Usuario)-[:POSTULA_A {fecha, estado: enviada|en_revision|rechazada|aceptada}]->(Oferta)

-- Extensiones propias (justificadas):
(Proyecto)-[:USA_TECNOLOGIA]->(Habilidad)      // necesaria para Q5 "proyectos que comparten tecnologías"
(Proyecto)-[:DESARROLLADO_POR]->(Empresa)      // opcional: enriquece caminos usuario↔empresa
```

### 3.3 Decisiones de modelado

1. **`CONECTA_CON` se guarda una sola vez y se consulta sin dirección** (`-[:CONECTA_CON]-`). Las conexiones profesionales son simétricas; guardar dos aristas duplica datos y complica la eliminación. Al crear se usa `MERGE` sin dirección para no duplicar.
2. **Habilidad es nodo, no propiedad** (no `usuario.habilidades = [...]`). Es la clave del modelo: permite recorrer usuario → habilidad → oferta y calcular similitudes.
3. **Historial laboral en la relación** `TRABAJA_EN` (`desde`, `hasta`, `actual`) en lugar de un nodo intermedio: suficiente para el alcance y más simple.
4. **Estado de la postulación como propiedad de `POSTULA_A`**: la postulación no tiene identidad propia fuera del par usuario–oferta.
5. **Ids propios (UUID)** en vez de `elementId()` interno de Neo4j, que no es estable entre exportaciones.
6. **Eliminar usuario = `DETACH DELETE`** (borra también sus relaciones).

### 3.4 Restricciones e índices

```cypher
CREATE CONSTRAINT usuario_id    IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT usuario_email IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT empresa_id    IF NOT EXISTS FOR (e:Empresa)   REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT habilidad_clave IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.clave IS UNIQUE;
CREATE CONSTRAINT empresa_nombre IF NOT EXISTS FOR (e:Empresa) REQUIRE e.nombre IS UNIQUE;
CREATE CONSTRAINT proyecto_id   IF NOT EXISTS FOR (p:Proyecto)  REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT oferta_id     IF NOT EXISTS FOR (o:Oferta)    REQUIRE o.id IS UNIQUE;
CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre);
CREATE INDEX oferta_estado  IF NOT EXISTS FOR (o:Oferta)  ON (o.estado);
```

---

## 4. Consultas clave (borrador Cypher)

**Q1 – Usuarios con habilidades similares (Jaccard)**
```cypher
MATCH (u:Usuario {id:$id})-[:TIENE_HABILIDAD]->(h)<-[:TIENE_HABILIDAD]-(otro:Usuario)
WITH u, otro, count(h) AS comunes
MATCH (u)-[:TIENE_HABILIDAD]->(hu) WITH u, otro, comunes, count(hu) AS nu
MATCH (otro)-[:TIENE_HABILIDAD]->(ho) WITH otro, comunes, nu, count(ho) AS no
RETURN otro.nombre, comunes, toFloat(comunes)/(nu+no-comunes) AS jaccard
ORDER BY jaccard DESC LIMIT 10
```

**Q2 – Contactos en común**
```cypher
MATCH (a:Usuario {id:$a})-[:CONECTA_CON]-(c:Usuario)-[:CONECTA_CON]-(b:Usuario {id:$b})
RETURN c
```

**Q3 – Ruta más corta usuario → empresa**
```cypher
MATCH (u:Usuario {id:$u}), (e:Empresa {id:$e})
MATCH p = shortestPath((u)-[:CONECTA_CON|TRABAJA_EN*..6]-(e))
RETURN p
```

**Q4 – Candidatos para una oferta** (puntaje combinado)
- `cobertura` = habilidades requeridas que el candidato tiene / total requeridas (con peso extra a las obligatorias y al nivel).
- `cercania` = bonus si tiene contactos que trabajan actualmente en la empresa que publica (referidos).
- Excluir a quien ya trabaja ahí o ya se postuló.

**Q5 – Proyectos relacionados**: proyectos que comparten `USA_TECNOLOGIA` y/o cuyos miembros están conectados entre sí.

**Q6 – Habilidades más demandadas**
```cypher
MATCH (:Oferta {estado:'abierta'})-[:REQUIERE]->(h:Habilidad)
RETURN h.nombre, count(*) AS demanda ORDER BY demanda DESC LIMIT 10
```

### Recomendaciones (RF8)
| Tipo | Lógica |
|---|---|
| **Contactos** | "Amigos de amigos" no conectados, ordenados por nº de contactos en común + habilidades compartidas + misma empresa. |
| **Empleos** | Ofertas abiertas ordenadas por cobertura de habilidades del usuario + si tiene contactos en la empresa. |
| **Colaboradores** | Usuarios con habilidades complementarias (que el usuario no tiene) requeridas por sus proyectos, a ≤ 3 saltos. |

### Panel de analítica (RF9) con GDS
| Métrica | Algoritmo | Respaldo sin GDS |
|---|---|---|
| Usuarios más influyentes | **PageRank** (`gds.pageRank`) sobre `CONECTA_CON` | Centralidad de grado en Cypher puro |
| Comunidades | **Louvain** (`gds.louvain`) | Componentes conexas / agrupación por empresa |
| Habilidades más demandadas | Agregación Cypher (Q6) | — |

Se proyecta el grafo en memoria con `gds.graph.project('red', 'Usuario', {CONECTA_CON:{orientation:'UNDIRECTED'}})`.

---

## 5. Componente de investigación: grafo vs relacional

Se documentará en `docs/informe.md` con argumentos teóricos **y una pequeña evidencia empírica**:

- **Experimento**: cargar los mismos datos en **SQLite** (no requiere instalación) con tablas `usuario`, `conexion`, `usuario_habilidad`, etc., y comparar la misma consulta en SQL vs Cypher: amigos a 1, 2, 3, 4 saltos y ruta más corta (SQL con `WITH RECURSIVE`). Medir tiempo y complejidad del código.

| El grafo gana cuando… | El relacional gana cuando… |
|---|---|
| Recorridos de profundidad variable/desconocida (caminos, grados de separación) | Agregaciones masivas tabulares (reportes, sumas, OLAP) |
| Muchas relaciones muchos-a-muchos que cambian con frecuencia | Esquema estable y datos homogéneos |
| Recomendaciones y detección de patrones/comunidades | Transacciones ACID de alto volumen con integridad referencial estricta (bancario, inventario) |
| El esquema evoluciona (nuevos tipos de relación sin migraciones) | Ecosistema maduro de BI/reportes, SQL estándar, personal capacitado |
| Consultas "locales" desde un nodo (index-free adjacency) | Escaneos completos de tablas y consultas sobre atributos, no relaciones |

---

## 6. Datos de prueba (seed)

Generación reproducible (semilla fija) con volumen suficiente para que la analítica tenga sentido:

| Entidad | Cantidad |
|---|---|
| Usuarios | ~200 |
| Empresas | ~20 (de 4–5 sectores) |
| Habilidades | ~50 (lista curada y categorizada) |
| Proyectos | ~40 |
| Ofertas | ~60 |
| Conexiones | ~800 (con sesgo por empresa/sector para que Louvain detecte comunidades reales) |

---

## 7. Plan de trabajo por fases

| Fase | Entregable | Criterio de "terminado" |
|---|---|---|
| **0. Entorno** | Neo4j portable en `.local/` + APOC + GDS, `.venv`, `requirements.txt`, `.env`, scripts `setup/start-db/clean` | Script de prueba conecta y ejecuta `RETURN 1` |
| **1. Modelo** | Diagrama del grafo + `00_constraints.cypher` | Restricciones creadas en la BD |
| **2. Datos** | `scripts/seed.py` | Grafo poblado y visible en Neo4j Browser |
| **3. Repositorios** | CRUD y relaciones (RF1–RF6) | Cada función probada desde consola |
| **4. Consultas** | Q1–Q6, caminos y recomendaciones (RF7–RF8) | Resultados coherentes con los datos semilla |
| **5. API** | Endpoints Flask para RF1–RF9, incl. analítica (PageRank, Louvain, demanda) | Todos los endpoints responden JSON correcto (probado con `curl`) |
| **6. Frontend** | `index.html` + CSS + JS vanilla: formularios CRUD, buscador de caminos, recomendaciones y panel de analítica | Flujo completo usable desde el navegador sin tocar código |
| **7. Investigación** | `informe.md` + `benchmark.py` | Tabla comparativa con mediciones |
| **8. Cierre** | README, capturas, presentación | Proyecto reproducible desde cero |

---

## 8. Resultado y decisiones tomadas durante la implementación

- **Analítica:** PageRank, Betweenness y Louvain se escriben como propiedades (`pagerank`, `intermediacion`, `comunidad`) en los nodos `Usuario`. Se recalculan con el botón *Recalcular* o automáticamente si faltan. Con los datos de prueba Louvain detecta 6 comunidades (modularidad 0,54) que coinciden en 84–90 % con los sectores.
- **Seed:** las conexiones se generan con sesgo (misma empresa > mismo sector > azar) y con 8 usuarios muy conectados (*hubs*), para que las comunidades y la influencia tengan sentido.
- **Rutas:** dos modos. *Solo contactos* sigue `CONECTA_CON` y termina en un empleado actual (pregunta "¿a quién le pido que me presente?"). *Cualquier vínculo* admite empleos pasados, proyectos y publicaciones.
- **Borrado:** eliminar una empresa elimina también sus ofertas (y las postulaciones a ellas); eliminar un usuario usa `DETACH DELETE`.
- **Benchmark:** se hizo con SQLite en memoria (incluido en Python, sin instalar nada), con 3 tamaños de red y verificando que ambos motores devuelven el mismo resultado. Ver `docs/benchmark_resultados.md`.
- **Portabilidad:** se comprobó que no se crean archivos fuera del proyecto. El registro de transacciones de Neo4j está limitado a 100 MB.
- **Puerto:** la app usa el 8000, porque en macOS el 5000 lo ocupa AirPlay.

## 9. Diseño visual (Netpro)

Idea central: **la interfaz habla el idioma del grafo**. Cada tipo de nodo tiene un color fijo y siempre significa lo mismo.

| Token | Color (claro / oscuro) | Uso |
|---|---|---|
| Tinta | `#1c1b3a` / `#ecebfa` | Texto y botones principales |
| Niebla | `#e9eaf1` / `#121128` | Fondo |
| Noche | `#17163a` / `#0d0c24` | Portada con la red (oscura en ambos modos) |
| Cobalto | `#3346d3` / `#7c8bff` | Usuario |
| Azafrán | `#c4850a` / `#f2b640` | Empresa |
| Jade | `#0f9372` / `#35c99e` | Oferta |
| Orquídea | `#9b3fd4` / `#c27bf2` | Proyecto |
| Rosa | `#dc3f74` / `#f2709d` | Habilidad |

- **Tipografía:** una sola familia, *Bricolage Grotesque* (variable, guardada en `app/static/fonts/`, sin CDN). Los títulos van condensados y pesados; el logotipo "Netpro" en la portada es el elemento tipográfico principal.
- **Elemento memorable:** la portada dibuja la red real (200 usuarios, 805 conexiones) con una simulación de fuerzas escrita a mano (`js/vistas/red.js`). El tamaño es el PageRank, el color es la comunidad Louvain, y al pasar el cursor se resaltan los vecinos. Es la única animación automática y respeta `prefers-reduced-motion`.
- **Menú:** un camino de nodos unidos por una arista, cada uno con el color de su tipo de nodo. En el móvil se convierte en una barra horizontal.
- **Caminos:** las rutas más cortas se muestran como nodos coloreados unidos por la relación (`TRABAJA_EN`, `PUBLICA`…).
- **Barras:** los colores también tienen significado (demanda = Oferta en jade, talento = Usuario en cobalto).

## 10. Supuestos y puntos a confirmar

- Lenguaje **Python** (cambiable a JavaScript/Node o Java si el curso lo exige; el modelo y el Cypher no cambian).
- Uso **local y portable** (Neo4j dentro del proyecto). Si se prefiere la nube: AuraDB Free, sin instalar nada pero perdiendo GDS → se usan los respaldos en Cypher puro.
- Sin autenticación de usuarios en la app (fuera del alcance del enunciado).
- Frontend sin frameworks: Flask es el único framework (backend); el navegador solo recibe HTML, CSS y JS propios.
- Confirmar con el docente: formato de entrega del informe y fecha límite.
