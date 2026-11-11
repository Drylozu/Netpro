import { api } from '../api.js';
import { barras, COLORES_COMUNIDAD, enlace, h, tarjeta } from '../ui.js';
import { dibujarRed } from './red.js';

const NODOS = {
  Usuario: [380, 190, '--c-usuario'], Empresa: [110, 65, '--c-empresa'], Oferta: [650, 65, '--c-oferta'],
  Proyecto: [110, 285, '--c-proyecto'], Habilidad: [650, 285, '--c-habilidad'],
};
const RELS = [
  ['Usuario', 'Empresa', 'TRABAJA_EN'], ['Usuario', 'Proyecto', 'PARTICIPA_EN'],
  ['Usuario', 'Habilidad', 'TIENE_HABILIDAD'], ['Usuario', 'Oferta', 'POSTULA_A'],
  ['Empresa', 'Oferta', 'PUBLICA'], ['Oferta', 'Habilidad', 'REQUIERE'],
  ['Proyecto', 'Habilidad', 'USA_TECNOLOGIA'], ['Proyecto', 'Empresa', 'DESARROLLADO_POR'],
];
const R = 44;

// Diagrama del modelo como SVG generado (contenido fijo, sin datos del usuario).
function esquema() {
  const lineas = RELS.map(([a, b, tipo]) => {
    const [x1, y1] = NODOS[a]; const [x2, y2] = NODOS[b];
    const d = Math.hypot(x2 - x1, y2 - y1); const ux = (x2 - x1) / d; const uy = (y2 - y1) / d;
    const mx = (x1 + x2) / 2; const my = (y1 + y2) / 2;
    const dy = y1 === y2 && y1 > 200 ? 16 : -6;
    return `<line x1="${x1 + ux * R}" y1="${y1 + uy * R}" x2="${x2 - ux * (R + 4)}" y2="${y2 - uy * (R + 4)}" marker-end="url(#flecha)"/>
            <text class="r" x="${mx}" y="${my + dy}" text-anchor="middle">${tipo}</text>`;
  }).join('');
  const nodos = Object.entries(NODOS).map(([n, [x, y, c]]) =>
    `<circle cx="${x}" cy="${y}" r="${R}" style="fill:color-mix(in srgb, var(${c}) 14%, var(--superficie));stroke:var(${c});stroke-width:2.5"/>
     <text x="${x}" y="${y + 4}" text-anchor="middle">${n}</text>`).join('');
  const [ux, uy] = NODOS.Usuario;
  const bucle = `<path d="M ${ux - 20} ${uy - 39} C ${ux - 55} ${uy - 110}, ${ux + 55} ${uy - 110}, ${ux + 22} ${uy - 41}" marker-end="url(#flecha)"/>
                 <text class="r" x="${ux}" y="${uy - 92}" text-anchor="middle">CONECTA_CON</text>`;
  const svg = h('div', { class: 'esquema' });
  svg.innerHTML = `<svg viewBox="0 0 760 340" role="img" aria-label="Modelo del grafo: nodos y relaciones">
    <defs><marker id="flecha" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" style="fill:var(--texto-suave);stroke:none"/></marker></defs>
    ${lineas}${bucle}${nodos}</svg>`;
  return svg;
}

export async function render() {
  const [{ resumen }, red] = await Promise.all([api.get('/api/analitica'), api.get('/api/analitica/red')]);
  const total = (tipo) => resumen.nodos.find((n) => n.etiqueta === tipo)?.total ?? 0;
  const rango = new Map(red.comunidades.map((c, i) => [c.comunidad, i]));
  const colorDe = (c) => COLORES_COMUNIDAD[(rango.get(c) ?? 8) % COLORES_COMUNIDAD.length];

  const portada = h('section', { class: 'portada' },
    h('div', { class: 'portada-texto' },
      h('h1', { class: 'wordmark' }, 'Netpro'),
      h('p', {}, `${total('Usuario')} profesionales y ${red.aristas.length} conexiones guardadas como un grafo. `,
        'Cada punto es una persona; su tamaño es su influencia y su color, la comunidad a la que pertenece.'),
      h('div', { class: 'leyenda' }, red.comunidades.slice(0, 8).map((c) => {
        // Si dos comunidades comparten sector, se distinguen por su empresa principal
        const repetido = red.comunidades.filter((x) => x.sector_dominante === c.sector_dominante).length > 1;
        const nombre = repetido && c.empresas[0] ? `${c.sector_dominante}: ${c.empresas[0]}` : c.sector_dominante;
        return h('span', {}, h('i', { style: { background: colorDe(c.comunidad) } }), `${nombre} (${c.tamano})`);
      }))),
    h('div', { class: 'portada-red' },
      dibujarRed(red, colorDe, { alElegir: (n) => { location.hash = `#/usuarios/${n.id}`; } })),
    h('p', { class: 'portada-pista' }, 'Pase el cursor por un punto para ver sus conexiones; haga clic para abrir el perfil.'));

  const cifra = (valor, texto, ruta) => h('a', { class: 'cifra', href: `#/${ruta}` }, h('b', {}, valor), h('span', {}, texto));

  return h('div', { class: 'pila' },
    portada,
    h('div', { class: 'cifras' },
      cifra(total('Empresa'), 'empresas', 'empresas'),
      cifra(resumen.ofertas_abiertas, 'ofertas abiertas', 'ofertas'),
      cifra(total('Proyecto'), 'proyectos', 'proyectos'),
      cifra(total('Habilidad'), 'habilidades', 'consultas'),
      cifra(resumen.postulaciones, 'postulaciones', 'ofertas')),
    h('div', { class: 'rejilla-3' },
      tarjeta('Cómo está guardada la información', esquema(),
        h('p', { class: 'suave pequeno' }, 'Cinco tipos de nodo y nueve tipos de relación. CONECTA_CON se guarda una sola vez y se recorre en ambos sentidos.')),
      tarjeta('Relaciones almacenadas',
        barras(resumen.relaciones.map((r) => ({ etiqueta: r.tipo, valor: r.total })), { color: 'var(--texto-suave)' }),
        h('p', { class: 'suave pequeno', style: { marginTop: '1.1rem' } },
          'Siga explorando en ', enlace('consultas', 'consultas'), ', ', enlace('recomendaciones', 'recomendaciones'),
          ' o la ', enlace('analitica', 'analítica'), ' de la red.'))));
}
