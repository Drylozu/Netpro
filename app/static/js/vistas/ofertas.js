import { api, qs } from '../api.js';
import { invalidar, lista } from '../store.js';
import {
  aviso, badge, chips, confirmar, datalist, enlace, fmtDinero, formulario, h, intentar, pct, selector, tabla, tarjeta, volver,
} from '../ui.js';

const filtros = { q: '', estado: 'abierta' };
const CAMPOS = [
  { name: 'titulo', label: 'Título', required: true, ancho: true },
  { name: 'nivel', label: 'Nivel', type: 'select', options: ['Junior', 'Semi-senior', 'Senior'].map((n) => [n, n]) },
  { name: 'modalidad', label: 'Modalidad', type: 'select', options: ['Remoto', 'Híbrido', 'Presencial'].map((n) => [n, n]) },
  { name: 'salario_min', label: 'Salario mínimo', type: 'number', min: 0 },
  { name: 'salario_max', label: 'Salario máximo', type: 'number', min: 0 },
  { name: 'descripcion', label: 'Descripción', type: 'textarea', ancho: true },
];

async function listado() {
  const resultados = h('div');
  const cargar = async () => {
    const filas = await api.get(`/api/ofertas?${qs(filtros)}`);
    resultados.replaceChildren(tabla([
      { titulo: 'Oferta', valor: (f) => enlace(`ofertas/${f.oferta.id}`, f.oferta.titulo) },
      { titulo: 'Empresa', valor: (f) => enlace(`empresas/${f.empresa_id}`, f.empresa) },
      { titulo: 'Modalidad', valor: (f) => f.oferta.modalidad ?? '—' },
      { titulo: 'Requisitos', valor: (f) => chips(f.requisitos, (r) => r.nombre + (r.obligatoria ? ' *' : '')) },
      { titulo: 'Estado', valor: (f) => badge(f.oferta.estado) },
      { titulo: 'Postulantes', valor: (f) => f.postulantes, num: true },
    ], filas));
  };
  let t;
  const filtro = h('div', { class: 'fila', style: { marginBottom: '.75rem' } },
    h('input', { type: 'search', placeholder: 'Buscar por título o empresa…', value: filtros.q, style: { flex: '1 1 240px' },
      onInput: (e) => { filtros.q = e.target.value; clearTimeout(t); t = setTimeout(cargar, 250); } }),
    h('select', { style: { width: 'auto' }, onChange: (e) => { filtros.estado = e.target.value; cargar(); } },
      [['abierta', 'Abiertas'], ['cerrada', 'Cerradas'], ['', 'Todas']].map(([v, txt]) => h('option', { value: v, selected: v === filtros.estado }, txt))));
  await cargar();
  return h('div', { class: 'pila' },
    h('div', { class: 'cabecera' }, h('div', {}, h('h1', {}, 'Ofertas laborales'), h('p', { class: 'suave' }, '* = requisito obligatorio')),
      h('a', { class: 'boton', href: '#/ofertas/nuevo' }, '+ Nueva oferta')),
    tarjeta(null, filtro, resultados));
}

async function nueva(empresaId) {
  const empresas = await lista('empresas');
  const habilidades = await lista('habilidades');
  const sel = selector(empresas, { placeholder: 'Empresa que publica…', valorInicial: empresaId });
  const sugerencias = datalist(habilidades.map((x) => x.nombre));
  const form = formulario([
    ...CAMPOS,
    { name: 'obligatorias', label: 'Habilidades obligatorias (separadas por coma)', ancho: true, placeholder: 'Python, SQL' },
    { name: 'deseables', label: 'Habilidades deseables (separadas por coma)', ancho: true, placeholder: 'Docker, Inglés' },
  ], {
    boton: 'Publicar oferta',
    alEnviar: async (d) => {
      const separar = (txt) => txt.split(',').map((s) => s.trim()).filter(Boolean);
      const requisitos = [
        ...separar(d.obligatorias).map((nombre) => ({ nombre, obligatoria: true, nivel_minimo: 3 })),
        ...separar(d.deseables).map((nombre) => ({ nombre, obligatoria: false, nivel_minimo: 1 })),
      ];
      const { oferta } = await intentar(() => api.post('/api/ofertas', { ...d, empresa_id: sel.valor, requisitos }), 'Oferta publicada');
      invalidar('ofertas', 'empresas', 'habilidades');
      location.hash = `#/ofertas/${oferta.id}`;
    },
  });
  form.prepend(h('label', { class: 'ancho' }, 'Empresa', sel.el));
  form.querySelectorAll('input[name=obligatorias], input[name=deseables]').forEach((i) => i.setAttribute('list', sugerencias.id));
  return h('div', { class: 'pila' }, h('div', {}, volver('ofertas', 'Ofertas'), h('div', { class: 'cabecera' }, h('h1', {}, 'Publicar una oferta'))), tarjeta(null, form, sugerencias.el));
}

async function detalle(id) {
  const raiz = h('div', { class: 'pila' });
  const habilidades = await lista('habilidades');
  const recargar = async () => {
    const [d, candidatos] = await Promise.all([api.get(`/api/ofertas/${id}`), api.get(`/api/consultas/candidatos/${id}`)]);
    const o = d.oferta;
    const base = `/api/ofertas/${id}`;
    const accion = (fn, msg) => intentar(fn, msg).then(recargar);
    const sugerencias = datalist(habilidades.map((x) => x.nombre));

    raiz.replaceChildren(
      h('div', { class: 'cabecera' },
        h('div', {}, volver('ofertas', 'Ofertas'), h('h1', {}, o.titulo, badge(o.estado)),
          h('p', { class: 'suave' }, 'Publicada por ', enlace(`empresas/${d.empresa.id}`, d.empresa.nombre), ` el ${o.fecha_publicacion}. `,
            [o.modalidad, o.salario_min ? `${fmtDinero(o.salario_min)} a ${fmtDinero(o.salario_max)}` : null].filter(Boolean).join(', '))),
        h('div', { class: 'fila' },
          h('button', { class: 'secundario', onClick: () => accion(() => api.put(base, { estado: o.estado === 'abierta' ? 'cerrada' : 'abierta' }), 'Estado actualizado').then(() => invalidar('ofertas')) },
            o.estado === 'abierta' ? 'Cerrar oferta' : 'Reabrir oferta'),
          h('button', { class: 'peligro', onClick: async () => {
            if (!confirmar('¿Eliminar esta oferta y sus postulaciones?')) return;
            await intentar(() => api.del(base));
            invalidar('ofertas');
            location.hash = '#/ofertas';
            aviso('Oferta eliminada');
          } }, 'Eliminar'))),
      o.descripcion ? h('p', {}, o.descripcion) : null,
      h('div', { class: 'rejilla' },
        tarjeta(`Habilidades requeridas (${d.requisitos.length})`,
          d.requisitos.length ? h('div', { class: 'chips' }, d.requisitos.map((r) => h('span', { class: `chip ${r.obligatoria ? 'obligatoria' : ''}`, title: `Nivel mínimo ${r.nivel_minimo}` },
            r.nombre, r.obligatoria ? h('b', {}, '*') : null,
            h('button', { class: 'icono', title: 'Quitar', onClick: () => accion(() => api.del(`${base}/requisitos/${encodeURIComponent(r.clave)}`), 'Requisito quitado') }, '✕'))))
            : h('p', { class: 'vacio' }, 'Sin requisitos'),
          sugerencias.el,
          formulario([
            { name: 'nombre', label: 'Habilidad', required: true, list: sugerencias.id },
            { name: 'nivel_minimo', label: 'Nivel mín.', type: 'select', options: [1, 2, 3, 4, 5].map((n) => [n, n]) },
            { name: 'obligatoria', label: 'Obligatoria', type: 'checkbox' },
          ], { clase: 'en-linea', boton: 'Agregar', alEnviar: (r) => accion(() => api.post(`${base}/requisitos`, r), 'Requisito agregado').then(() => invalidar('habilidades')) })),
        tarjeta(`Postulantes (${d.postulantes.length})`, tabla([
          { titulo: 'Candidato', valor: (p) => [enlace(`usuarios/${p.id}`, p.nombre), h('div', { class: 'suave pequeno' }, p.titular)] },
          { titulo: 'Fecha', valor: (p) => p.fecha },
          { titulo: 'Estado', valor: (p) => h('select', { onChange: (e) => accion(() => api.put(`${base}/postulaciones/${p.id}`, { estado: e.target.value }), 'Estado de la postulación actualizado') },
            ['enviada', 'en_revision', 'rechazada', 'aceptada'].map((s) => h('option', { value: s, selected: s === p.estado }, s.replace('_', ' ')))) },
        ], d.postulantes, 'Nadie se ha postulado todavía'))),
      tarjeta('Candidatos recomendados según el grafo',
        h('p', { class: 'suave pequeno' }, 'Puntaje = 70 % cobertura ponderada de habilidades (obligatorias pesan doble) + 30 % cercanía social: contacto directo en la empresa (referido) = 1, a dos saltos = 0,5.'),
        tabla([
          { titulo: 'Candidato', valor: (c) => [enlace(`usuarios/${c.id}`, c.nombre), h('div', { class: 'suave pequeno' }, c.titular), c.ya_postulado ? badge('postulado') : null] },
          { titulo: 'Tiene', valor: (c) => chips(c.coinciden) },
          { titulo: 'Le falta', valor: (c) => chips(c.faltan) },
          { titulo: 'Referidos en la empresa', valor: (c) => (c.referidos.length ? chips(c.referidos, undefined, 'usuario') : (c.segundo_grado ? `${c.segundo_grado} a dos saltos` : '—')) },
          { titulo: 'Cobertura', valor: (c) => pct(c.cobertura), num: true },
          { titulo: 'Puntaje', valor: (c) => h('span', { class: 'puntaje' }, c.puntaje), num: true },
        ], candidatos, 'No hay candidatos con habilidades coincidentes')),
      tarjeta('Editar oferta', formulario(CAMPOS, {
        valores: o, boton: 'Guardar cambios',
        alEnviar: (datos) => accion(() => api.put(base, datos), 'Oferta actualizada').then(() => invalidar('ofertas')),
      })));
  };
  await recargar();
  return raiz;
}

export function render([id, extra]) {
  if (id === 'nuevo') return nueva(extra);
  return id ? detalle(id) : listado();
}
