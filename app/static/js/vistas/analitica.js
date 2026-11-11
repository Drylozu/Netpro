import { api } from '../api.js';
import { barras, chips, COLORES_COMUNIDAD, enlace, h, intentar, tarjeta } from '../ui.js';

export async function render() {
  const raiz = h('div', { class: 'pila' });
  const cargar = async () => {
    const d = await api.get('/api/analitica');
    const c = d.calculo;
    const totalRel = d.cohesion.internas + d.cohesion.externas;
    const boton = h('button', { class: 'secundario', onClick: async () => {
      boton.disabled = true;
      try { await intentar(() => api.post('/api/analitica/recalcular'), 'Métricas recalculadas'); await cargar(); } finally { boton.disabled = false; }
    } }, '↻ Recalcular');

    raiz.replaceChildren(
      h('div', { class: 'cabecera' },
        h('div', {}, h('h1', {}, 'Panel de analítica'),
          h('p', { class: 'suave' }, c.motor === 'gds'
            ? `Calculado con Neo4j Graph Data Science sobre ${c.nodos} usuarios y ${c.relaciones / 2} conexiones.`
            : 'GDS no disponible: se usa centralidad de grado y el sector como comunidad aproximada.')),
        boton),
      h('div', { class: 'cifras' },
        h('div', { class: 'cifra' }, h('b', {}, c.comunidades), h('span', {}, 'comunidades detectadas')),
        h('div', { class: 'cifra' }, h('b', {}, c.modularidad ?? '—'), h('span', {}, 'modularidad (Louvain)')),
        h('div', { class: 'cifra' }, h('b', {}, totalRel ? `${Math.round((100 * d.cohesion.internas) / totalRel)} %` : '—'), h('span', {}, 'conexiones dentro de su comunidad')),
        h('div', { class: 'cifra' }, h('b', {}, d.resumen.grado_medio), h('span', {}, 'grado medio')),
        h('div', { class: 'cifra' }, h('b', {}, d.resumen.postulaciones), h('span', {}, 'postulaciones'))),
      h('div', { class: 'rejilla-3' },
        tarjeta('Usuarios más influyentes (PageRank)',
          h('p', { class: 'suave pequeno' }, 'Un usuario es influyente si está conectado con otros usuarios influyentes, no solo por su número de contactos.'),
          barras(d.influyentes.map((u) => ({ etiqueta: u.nombre, valor: u.pagerank, enlace: `usuarios/${u.id}`, grado: u.grado })),
            { formato: (v, i) => `${v.toFixed(2)}, ${i.grado} contactos` })),
        tarjeta('Usuarios puente (Betweenness)',
          h('p', { class: 'suave pequeno' }, 'Aparecen en muchos caminos más cortos entre otros usuarios: conectan comunidades distintas.'),
          barras(d.intermediarios.map((u) => ({ etiqueta: u.nombre, valor: u.intermediacion, enlace: `usuarios/${u.id}`, comunidad: u.comunidad })),
            { formato: (v, i) => `${Math.round(v)}` })),
        tarjeta('Habilidades más demandadas',
          h('div', { class: 'leyenda' }, h('span', {}, h('i', { style: { background: 'var(--c-oferta)' } }), 'ofertas abiertas'),
            h('span', {}, h('i', { style: { background: 'var(--c-usuario)', opacity: '.55' } }), 'usuarios con la habilidad')),
          barras(d.habilidades_demandadas.map((f) => ({ etiqueta: f.habilidad, valor: f.demanda, valor2: f.talento })),
            { formato: (v, i) => `${v} / ${i.valor2}`, color: 'var(--c-oferta)', color2: 'var(--c-usuario)' }))),
      h('section', {},
        h('h2', {}, 'Comunidades detectadas (Louvain)'),
        h('p', { class: 'suave pequeno' }, 'Grupos de usuarios más conectados entre sí que con el resto. Louvain no conoce los sectores: los descubre solo a partir de las conexiones.'),
        h('div', { class: 'rejilla' }, d.comunidades.map((com, i) => {
          const repetido = d.comunidades.filter((x) => x.sector_dominante === com.sector_dominante).length > 1;
          return h('div', { class: 'tarjeta comunidad', style: { '--color': COLORES_COMUNIDAD[i % COLORES_COMUNIDAD.length] } },
            h('div', { class: 'tarjeta-titulo' },
              h('h3', {}, repetido && com.empresas[0] ? `${com.sector_dominante}: ${com.empresas[0]}` : com.sector_dominante),
              h('span', { class: 'badge' }, `${com.tamano} usuarios`)),
            h('p', { class: 'pequeno suave' }, `El ${Math.round(com.pureza_sector * 100)} % trabaja en este sector, sobre todo en ${com.empresas.join(', ') || 'empresas variadas'}.`),
            h('div', { class: 'pequeno', style: { marginBottom: '.6rem' } }, chips(com.habilidades)),
            h('p', { class: 'pequeno', style: { margin: 0 } }, 'Más influyentes: ', com.lideres.slice(0, 3).flatMap((l, j) => [j ? ', ' : '', enlace(`usuarios/${l.id}`, l.nombre)])));
        }))));
  };
  await cargar();
  return raiz;
}
