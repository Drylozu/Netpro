const NS = 'http://www.w3.org/2000/svg';
const svgEl = (tag, attrs) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
};

export function dibujarRed({ nodos, aristas }, colorDe, { ancho = 760, alto = 560, alElegir } = {}) {
  const indice = new Map(nodos.map((n, i) => [n.id, i]));
  const enlaces = aristas.map((a) => [indice.get(a.a), indice.get(a.b)]).filter(([a, b]) => a !== undefined && b !== undefined);
  const vecinos = nodos.map(() => new Set());
  enlaces.forEach(([a, b]) => { vecinos[a].add(b); vecinos[b].add(a); });

  const comunidades = [...new Set(nodos.map((n) => n.comunidad))];
  const centros = new Map(comunidades.map((c, i) => {
    const ang = (2 * Math.PI * i) / comunidades.length - Math.PI / 2;
    return [c, [ancho / 2 + Math.cos(ang) * ancho * 0.3, alto / 2 + Math.sin(ang) * alto * 0.31]];
  }));
  const maxPr = Math.max(...nodos.map((n) => n.pagerank));
  const P = nodos.map((n) => {
    const [cx, cy] = centros.get(n.comunidad);
    return { x: cx + (Math.random() - 0.5) * 60, y: cy + (Math.random() - 0.5) * 60, vx: 0, vy: 0, r: 2.6 + 8.5 * Math.sqrt(n.pagerank / maxPr) };
  });

  // Fruchterman–Reingold con atracción extra hacia el centro de cada comunidad
  const k = 0.72 * Math.sqrt((ancho * alto) / nodos.length);
  function paso(alfa) {
    for (const p of P) { p.vx = 0; p.vy = 0; }
    for (let i = 0; i < P.length; i++) {
      for (let j = i + 1; j < P.length; j++) {
        let dx = P[i].x - P[j].x; let dy = P[i].y - P[j].y;
        let d = Math.sqrt(dx * dx + dy * dy);
        if (d < 0.5) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d = 0.5; }
        const f = (k * k) / d;
        P[i].vx += (dx / d) * f; P[i].vy += (dy / d) * f;
        P[j].vx -= (dx / d) * f; P[j].vy -= (dy / d) * f;
      }
    }
    for (const [a, b] of enlaces) {
      const dx = P[a].x - P[b].x; const dy = P[a].y - P[b].y;
      const d = Math.sqrt(dx * dx + dy * dy) || 0.5;
      const f = ((d * d) / k) * (mismaComunidad(a, b) ? 1 : 0.35);
      P[a].vx -= (dx / d) * f; P[a].vy -= (dy / d) * f;
      P[b].vx += (dx / d) * f; P[b].vy += (dy / d) * f;
    }
    const temperatura = 2 + 38 * alfa;
    nodos.forEach((n, i) => {
      const [cx, cy] = centros.get(n.comunidad);
      P[i].vx += (cx - P[i].x) * 1.6; P[i].vy += (cy - P[i].y) * 1.6;
      const d = Math.sqrt(P[i].vx * P[i].vx + P[i].vy * P[i].vy) || 1;
      const mov = Math.min(d, temperatura);
      P[i].x = Math.min(ancho - 16, Math.max(16, P[i].x + (P[i].vx / d) * mov));
      P[i].y = Math.min(alto - 16, Math.max(16, P[i].y + (P[i].vy / d) * mov));
    });
  }
  function mismaComunidad(a, b) { return nodos[a].comunidad === nodos[b].comunidad; }

  const svg = svgEl('svg', { viewBox: `0 0 ${ancho} ${alto}`, class: 'red', role: 'img',
    'aria-label': `Red de ${nodos.length} profesionales y ${enlaces.length} conexiones, coloreada por comunidad` });
  const gLineas = svgEl('g', {}); const gNodos = svgEl('g', {});
  const etiqueta = svgEl('text', { 'text-anchor': 'middle' });
  svg.append(gLineas, gNodos, etiqueta);
  const lineas = enlaces.map(() => gLineas.appendChild(svgEl('line', {})));
  const circulos = nodos.map((n, i) => {
    const c = gNodos.appendChild(svgEl('circle', { r: P[i].r.toFixed(1), fill: colorDe(n.comunidad) }));
    c.addEventListener('mouseenter', () => enfocar(i));
    c.addEventListener('mouseleave', () => enfocar(null));
    c.addEventListener('click', () => alElegir?.(n));
    return c;
  });

  function pintar() {
    enlaces.forEach(([a, b], k) => {
      const l = lineas[k];
      l.setAttribute('x1', P[a].x.toFixed(1)); l.setAttribute('y1', P[a].y.toFixed(1));
      l.setAttribute('x2', P[b].x.toFixed(1)); l.setAttribute('y2', P[b].y.toFixed(1));
    });
    circulos.forEach((c, i) => { c.setAttribute('cx', P[i].x.toFixed(1)); c.setAttribute('cy', P[i].y.toFixed(1)); });
  }

  function enfocar(i) {
    svg.classList.toggle('enfocada', i !== null);
    circulos.forEach((c, k) => c.classList.toggle('vecina', i !== null && (k === i || vecinos[i].has(k))));
    lineas.forEach((l, k) => l.classList.toggle('vecina', i !== null && (enlaces[k][0] === i || enlaces[k][1] === i)));
    if (i === null) { etiqueta.textContent = ''; return; }
    etiqueta.textContent = `${nodos[i].nombre} (${vecinos[i].size} conexiones)`;
    etiqueta.setAttribute('x', Math.min(ancho - 120, Math.max(120, P[i].x)));
    etiqueta.setAttribute('y', P[i].y - P[i].r - 8);
  }

  const TOTAL = 320;
  const reducir = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducir) {
    for (let t = 0; t < TOTAL; t++) paso(1 - t / TOTAL);
    pintar();
  } else {
    let t = 0; let montado = false;
    const cuadro = () => {
      if (svg.isConnected) montado = true;
      else if (montado) return;
      for (let k = 0; k < 3 && t < TOTAL; k++, t++) paso(1 - t / TOTAL);
      pintar();
      if (t < TOTAL) requestAnimationFrame(cuadro);
    };
    pintar();
    requestAnimationFrame(cuadro);
  }
  return svg;
}
