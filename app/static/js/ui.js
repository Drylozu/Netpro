export function h(tag, attrs = {}, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'class') el.className = v;
    else if (k === 'style' && typeof v === 'object') {
      for (const [prop, val] of Object.entries(v)) {
        if (val === undefined || val === null) continue;
        if (prop.startsWith('--')) el.style.setProperty(prop, val); else el.style[prop] = val;
      }
    }
    else if (k in el && typeof v !== 'string') el[k] = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : String(hijo));
  }
  return el;
}

export function aviso(mensaje, tipo = 'ok') {
  const el = h('div', { class: `aviso ${tipo}` }, mensaje);
  document.getElementById('avisos').append(el);
  setTimeout(() => el.remove(), tipo === 'error' ? 6000 : 3000);
}

export async function intentar(fn, mensajeOk) {
  try {
    const r = await fn();
    if (mensajeOk) aviso(mensajeOk);
    return r;
  } catch (e) {
    aviso(e.message, 'error');
    throw e;
  }
}

export const tarjeta = (titulo, ...contenido) =>
  h('section', { class: 'tarjeta' }, titulo ? (typeof titulo === 'string' ? h('h2', {}, titulo) : titulo) : null, ...contenido);

export const tituloTarjeta = (titulo, ...acciones) =>
  h('div', { class: 'tarjeta-titulo' }, h('h2', {}, titulo), h('div', { class: 'fila' }, ...acciones));

export const vacio = (texto = 'Sin resultados') => h('p', { class: 'vacio' }, texto);

export const badge = (texto) => h('span', { class: `badge ${String(texto).replace(/\s/g, '_')}` }, String(texto).replace('_', ' '));

export const nivel = (n) => h('span', { class: 'nivel', title: `Nivel ${n} de 5`, 'aria-label': `Nivel ${n} de 5` },
  [1, 2, 3, 4, 5].map((i) => h('i', { class: i <= n ? 'lleno' : null })));

export const chips = (items, fn = (x) => x, tipo = 'habilidad') =>
  items?.length ? h('div', { class: 'chips' }, items.map((x) => h('span', { class: `chip ${tipo}` }, fn(x)))) : h('span', { class: 'suave' }, '—');

export const COLORES_COMUNIDAD = ['#7c8bff', '#f2b640', '#35c99e', '#c27bf2', '#f2709d', '#5fd0e8', '#c4cf5a', '#ff9f68', '#a8a6d6'];

export const enlace = (ruta, texto) => h('a', { href: `#/${ruta}` }, texto);

export const volver = (ruta, texto) => h('a', { class: 'volver', href: `#/${ruta}` }, `‹ ${texto}`);

// campo: {name, label, type, options, required, value, placeholder, ancho, list}
export function formulario(campos, { boton = 'Guardar', alEnviar, clase = 'formulario', valores = {} } = {}) {
  const form = h('form', { class: clase });
  for (const c of campos) {
    const valor = valores[c.name] ?? c.value ?? '';
    let control;
    if (c.type === 'select') {
      control = h('select', { name: c.name, required: c.required },
        c.options.map(([v, t]) => h('option', { value: v, selected: String(v) === String(valor) }, t)));
    } else if (c.type === 'textarea') {
      control = h('textarea', { name: c.name, placeholder: c.placeholder, required: c.required }, valor);
    } else if (c.type === 'checkbox') {
      form.append(h('label', { class: 'check' + (c.ancho ? ' ancho' : '') },
        h('input', { type: 'checkbox', name: c.name, checked: Boolean(valor) }), c.label));
      continue;
    } else {
      control = h('input', {
        name: c.name, type: c.type || 'text', value: String(valor), placeholder: c.placeholder,
        required: c.required, min: c.min, max: c.max, list: c.list, autocomplete: 'off',
      });
    }
    form.append(h('label', { class: c.ancho ? 'ancho' : null }, c.label, control));
  }
  const btn = h('button', { type: 'submit' }, boton);
  form.append(h('div', { class: clase === 'formulario' ? 'ancho' : null }, btn));
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const datos = {};
    for (const c of campos) {
      const el = form.elements[c.name];
      datos[c.name] = c.type === 'checkbox' ? el.checked : el.value.trim();
    }
    btn.disabled = true;
    try { await alEnviar(datos, form); } catch { /* el aviso ya se mostró */ } finally { btn.disabled = false; }
  });
  return form;
}

export function tabla(columnas, filas, textoVacio) {
  if (!filas?.length) return vacio(textoVacio);
  return h('div', { class: 'tabla-wrap' }, h('table', {},
    h('thead', {}, h('tr', {}, columnas.map((c) => h('th', { class: c.num ? 'num' : null }, c.titulo)))),
    h('tbody', {}, filas.map((f) => h('tr', {}, columnas.map((c) => h('td', { class: c.num ? 'num' : null }, c.valor(f))))))));
}

export function barras(items, { formato = (v) => v, max, color, color2 } = {}) {
  if (!items?.length) return vacio();
  const tope = max ?? Math.max(...items.map((i) => Math.max(i.valor, i.valor2 ?? 0)), 1);
  return h('div', { class: 'barras', style: { '--barra': color, '--barra2': color2 } }, items.map((i) =>
    h('div', { class: 'barra-fila' },
      h('span', { class: 'etiqueta', title: i.etiqueta }, i.enlace ? enlace(i.enlace, i.etiqueta) : i.etiqueta),
      h('div', { class: 'pista-doble' },
        h('div', { class: 'barra-pista' }, h('div', { class: 'barra-relleno', style: { width: `${(100 * i.valor) / tope}%` } })),
        i.valor2 !== undefined
          ? h('div', { class: 'barra-pista', style: { marginTop: '3px', height: '6px' } },
            h('div', { class: 'barra-relleno b2', style: { width: `${(100 * i.valor2) / tope}%` } }))
          : null),
      h('span', { class: 'valor' }, formato(i.valor, i)))));
}

export function camino(ruta) {
  const partes = [];
  ruta.nodos.forEach((n, i) => {
    const ruta_ = { Usuario: 'usuarios', Empresa: 'empresas', Oferta: 'ofertas', Proyecto: 'proyectos' }[n.tipo];
    partes.push(h('span', { class: `nodo ${n.tipo}` }, h('small', {}, n.tipo), ruta_ ? enlace(`${ruta_}/${n.id}`, n.nombre) : n.nombre));
    if (i < ruta.relaciones.length) partes.push(h('span', { class: 'rel' }, ruta.relaciones[i]));
  });
  return h('div', { class: 'camino' }, ...partes);
}

let contadorListas = 0;
export function selector(items, { placeholder = 'Escriba para buscar…', alCambiar, valorInicial } = {}) {
  const id = `dl-${++contadorListas}`;
  const mapa = new Map(items.map((i) => [i.label, i.id]));
  const input = h('input', { type: 'text', list: id, placeholder, autocomplete: 'off' });
  const inicial = items.find((i) => i.id === valorInicial);
  if (inicial) input.value = inicial.label;
  input.addEventListener('change', () => alCambiar?.(mapa.get(input.value) || null));
  return {
    el: h('span', { class: 'selector' }, input, h('datalist', { id }, items.map((i) => h('option', { value: i.label })))),
    get valor() { return mapa.get(input.value) || null; },
    limpiar() { input.value = ''; },
  };
}

export function datalist(valores) {
  const id = `dl-${++contadorListas}`;
  return { id, el: h('datalist', { id }, valores.map((v) => h('option', { value: v }))) };
}

export const confirmar = (mensaje) => window.confirm(mensaje);

export const fmtDinero = (v) => (v ? `$${Number(v).toLocaleString('es-CO')}` : '—');
export const pct = (v) => `${Math.round(v * 100)} %`;
