import { api, qs } from '../api.js';
import { lista } from '../store.js';
import { badge, barras, camino, chips, enlace, h, intentar, pct, selector, tabla, tarjeta, vacio } from '../ui.js';
import { tablaRelacionados } from './proyectos.js';

/** Tarjeta de consulta: título, explicación, controles y zona de resultados. */
function consulta(titulo, explicacion, controles, ejecutar, { auto = false } = {}) {
  const resultado = h('div', { style: { marginTop: '.75rem' } });
  const correr = async () => {
    resultado.replaceChildren(h('p', { class: 'cargando' }, 'Consultando…'));
    try { resultado.replaceChildren(await intentar(ejecutar)); } catch { resultado.replaceChildren(); }
  };
  const form = h('form', { class: 'en-linea', onSubmit: (e) => { e.preventDefault(); correr(); } },
    ...controles, h('button', { type: 'submit' }, 'Consultar'));
  if (auto) correr();
  return { el: tarjeta(titulo, h('p', { class: 'suave pequeno' }, explicacion), form, resultado), correr };
}

const exigir = (...valores) => { if (valores.some((v) => !v)) throw new Error('Seleccione un valor de la lista en cada campo'); };

export async function render([accion, param]) {
  const [usuarios, empresas, ofertas, proyectos] = await Promise.all(['usuarios', 'empresas', 'ofertas', 'proyectos'].map(lista));

  // Q1 ---------------------------------------------------------------------
  const q1u = selector(usuarios, { valorInicial: accion === 'similares' ? param : undefined });
  const q1 = consulta('¿Qué usuarios tienen habilidades similares?',
    'Similitud de Jaccard: habilidades en común / habilidades totales de ambos. Se obtiene recorriendo Usuario → Habilidad ← Usuario.',
    [h('label', {}, 'Usuario', q1u.el)],
    async () => {
      exigir(q1u.valor);
      const filas = await api.get(`/api/consultas/similares/${q1u.valor}`);
      return tabla([
        { titulo: 'Usuario', valor: (f) => [enlace(`usuarios/${f.id}`, f.nombre), h('div', { class: 'suave pequeno' }, f.titular), f.ya_conectados ? badge('conectados') : null] },
        { titulo: 'Habilidades en común', valor: (f) => chips(f.comunes) },
        { titulo: 'Jaccard', valor: (f) => f.jaccard.toFixed(2), num: true },
      ], filas);
    }, { auto: accion === 'similares' && param });

  // Q2 ---------------------------------------------------------------------
  const q2a = selector(usuarios); const q2b = selector(usuarios);
  const q2 = consulta('¿Qué contactos en común tienen dos profesionales?',
    'Patrón (a)-[:CONECTA_CON]-(c)-[:CONECTA_CON]-(b), más los grados de separación con SHORTEST.',
    [h('label', {}, 'Profesional A', q2a.el), h('label', {}, 'Profesional B', q2b.el)],
    async () => {
      exigir(q2a.valor, q2b.valor);
      const r = await api.get(`/api/consultas/comunes?${qs({ a: q2a.valor, b: q2b.valor })}`);
      return h('div', {},
        h('p', {}, r.conectados_directamente ? `${r.a} y ${r.b} están conectados directamente. ` : '',
          r.grados_de_separacion ? `Grados de separación: ${r.grados_de_separacion}.` : 'No hay camino entre ellos.'),
        r.comunes.length
          ? h('ul', { class: 'lista' }, r.comunes.map((c) => h('li', {}, h('div', {}, enlace(`usuarios/${c.id}`, c.nombre), h('span', { class: 'sub' }, c.titular)))))
          : vacio('No tienen contactos en común'));
    });

  // Q3 / RF7 -----------------------------------------------------------------
  const q3o = selector(usuarios);
  const destinoCaja = h('label', {}, 'Destino');
  const fuentesDestino = { empresa: empresas, usuario: usuarios, oferta: ofertas.filter((o) => o.estado === 'abierta') };
  let q3d;
  const tipoSel = h('select', { name: 'tipo', onChange: () => cambiarDestino() },
    [['empresa', 'Empresa'], ['usuario', 'Usuario'], ['oferta', 'Oferta abierta']].map(([v, t]) => h('option', { value: v }, t)));
  const modoSel = h('select', { name: 'modo' },
    [['contactos', 'Solo mis contactos'], ['amplio', 'Cualquier vínculo profesional']].map(([v, t]) => h('option', { value: v }, t)));
  const cambiarDestino = () => { q3d = selector(fuentesDestino[tipoSel.value]); destinoCaja.replaceChildren('Destino', q3d.el); };
  cambiarDestino();
  const q3 = consulta('¿Cuál es la ruta más corta entre un usuario y una empresa, persona u oferta?',
    '"Solo mis contactos": avanza por CONECTA_CON y termina en alguien que trabaja actualmente en la empresa (ALL SHORTEST). "Cualquier vínculo": admite empleos pasados, proyectos y publicaciones (allShortestPaths).',
    [h('label', {}, 'Usuario origen', q3o.el), h('label', {}, 'Tipo de destino', tipoSel), destinoCaja, h('label', {}, 'Recorrido', modoSel)],
    async () => {
      exigir(q3o.valor, q3d.valor);
      const rutas = await api.get(`/api/consultas/rutas?${qs({ origen: q3o.valor, destino: q3d.valor, tipo: tipoSel.value, modo: modoSel.value })}`);
      if (!rutas.length) return vacio('No existe un camino con ese tipo de recorrido');
      return h('div', {}, h('p', {}, h('b', {}, `${rutas[0].saltos} saltos`), rutas.length > 1 ? `, con ${rutas.length} rutas posibles de esa longitud.` : '. Es la única ruta de esa longitud.'), rutas.map(camino));
    });

  // Q4 ---------------------------------------------------------------------
  const q4o = selector(ofertas.filter((o) => o.estado === 'abierta'));
  const q4 = consulta('¿Qué candidatos recomendar para una oferta?',
    'Combina competencias (cobertura ponderada de REQUIERE ↔ TIENE_HABILIDAD) y conexiones (contactos que trabajan en la empresa que publica).',
    [h('label', {}, 'Oferta', q4o.el)],
    async () => {
      exigir(q4o.valor);
      const filas = await api.get(`/api/consultas/candidatos/${q4o.valor}`);
      return h('div', {}, h('p', {}, enlace(`ofertas/${q4o.valor}`, 'Abrir la oferta')), tabla([
        { titulo: 'Candidato', valor: (c) => [enlace(`usuarios/${c.id}`, c.nombre), c.ya_postulado ? [' ', badge('postulado')] : null] },
        { titulo: 'Tiene', valor: (c) => chips(c.coinciden) },
        { titulo: 'Referidos', valor: (c) => (c.referidos.length ? chips(c.referidos, undefined, 'usuario') : '—') },
        { titulo: 'Cobertura', valor: (c) => pct(c.cobertura), num: true },
        { titulo: 'Puntaje', valor: (c) => h('span', { class: 'puntaje' }, c.puntaje), num: true },
      ], filas));
    });

  // Q5 ---------------------------------------------------------------------
  const q5p = selector(proyectos, { placeholder: 'Todos (o elija uno)…' });
  const q5 = consulta('¿Qué proyectos comparten tecnologías o miembros relacionados?',
    'Puntaje = tecnologías comunes + 2 × miembros compartidos + 0,5 × pares de miembros conectados entre sí.',
    [h('label', {}, 'Proyecto (opcional)', q5p.el)],
    async () => tablaRelacionados(await api.get(`/api/consultas/proyectos-relacionados?${qs({ proyecto: q5p.valor })}`), q5p.valor),
    { auto: true });

  // Q6 ---------------------------------------------------------------------
  const q6t = h('select', {}, [['', 'Ofertas abiertas'], ['1', 'Todas las ofertas']].map(([v, t]) => h('option', { value: v }, t)));
  const q6 = consulta('¿Qué habilidades son las más demandadas?',
    'Grado entrante de REQUIERE en cada Habilidad, comparado con cuántos usuarios la tienen (talento disponible).',
    [h('label', {}, 'Considerar', q6t)],
    async () => {
      const filas = await api.get(`/api/consultas/habilidades-demandadas?${qs({ todas: q6t.value, limite: 15 })}`);
      return h('div', {},
        h('div', { class: 'leyenda' }, h('span', {}, h('i', { style: { background: 'var(--c-oferta)' } }), 'ofertas que la piden'),
          h('span', {}, h('i', { style: { background: 'var(--c-usuario)', opacity: '.55' } }), 'usuarios que la tienen')),
        barras(filas.map((f) => ({ etiqueta: f.habilidad, valor: f.demanda, valor2: f.talento })),
          { formato: (v, i) => `${v} / ${i.valor2}`, color: 'var(--c-oferta)', color2: 'var(--c-usuario)' }));
    }, { auto: true });

  return h('div', { class: 'pila' },
    h('div', { class: 'cabecera' }, h('div', {}, h('h1', {}, 'Consultas del grafo'),
      h('p', { class: 'suave' }, 'Las preguntas del enunciado resueltas con recorridos Cypher sobre Neo4j.'))),
    h('div', { class: 'rejilla-3' }, q1.el, q2.el),
    q3.el, q4.el,
    h('div', { class: 'rejilla-3' }, q6.el), q5.el);
}
