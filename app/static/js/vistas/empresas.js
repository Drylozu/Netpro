import { api } from '../api.js';
import { invalidar } from '../store.js';
import { aviso, badge, confirmar, enlace, formulario, h, intentar, tabla, tarjeta, volver } from '../ui.js';

const SECTORES = ['Tecnología', 'Finanzas', 'Salud', 'Educación', 'Retail y Logística', 'Otro'];
const CAMPOS = [
  { name: 'nombre', label: 'Nombre', required: true },
  { name: 'sector', label: 'Sector', type: 'select', options: SECTORES.map((s) => [s, s]) },
  { name: 'ciudad', label: 'Ciudad' },
  { name: 'tamano', label: 'Tamaño', type: 'select', options: ['Startup (1-50)', 'Mediana (51-500)', 'Grande (500+)'].map((t) => [t, t]) },
  { name: 'descripcion', label: 'Descripción', type: 'textarea', ancho: true },
];

async function listado() {
  const filas = await api.get('/api/empresas');
  return h('div', { class: 'pila' },
    h('div', { class: 'cabecera' }, h('div', {}, h('h1', {}, 'Empresas'), h('p', { class: 'suave' }, `${filas.length} organizaciones registradas`))),
    tarjeta(null, tabla([
      { titulo: 'Empresa', valor: (f) => enlace(`empresas/${f.empresa.id}`, f.empresa.nombre) },
      { titulo: 'Sector', valor: (f) => f.empresa.sector },
      { titulo: 'Ciudad', valor: (f) => f.empresa.ciudad ?? '—' },
      { titulo: 'Tamaño', valor: (f) => f.empresa.tamano ?? '—' },
      { titulo: 'Empleados', valor: (f) => f.empleados, num: true },
      { titulo: 'Ofertas abiertas', valor: (f) => f.ofertas_abiertas, num: true },
    ], filas)),
    tarjeta('Registrar empresa', formulario(CAMPOS, {
      boton: 'Crear empresa',
      alEnviar: async (d) => {
        const { empresa } = await intentar(() => api.post('/api/empresas', d), 'Empresa creada');
        invalidar('empresas');
        location.hash = `#/empresas/${empresa.id}`;
      },
    })));
}

async function detalle(id) {
  const raiz = h('div', { class: 'pila' });
  const recargar = async () => {
    const d = await api.get(`/api/empresas/${id}`);
    const e = d.empresa;
    const actuales = d.empleados.filter((x) => x.actual);
    raiz.replaceChildren(
      h('div', { class: 'cabecera' },
        h('div', {}, volver('empresas', 'Empresas'), h('h1', {}, e.nombre),
          h('p', { class: 'suave' }, `${e.sector}${e.ciudad ? `, con sede en ${e.ciudad}` : ''}${e.tamano ? `. ${e.tamano}` : ''}`)),
        h('div', { class: 'fila' },
          h('a', { class: 'boton', href: `#/ofertas/nuevo/${id}` }, '+ Publicar oferta'),
          h('button', { class: 'peligro', onClick: async () => {
            if (!confirmar(`¿Eliminar ${e.nombre}? También se eliminarán sus ofertas.`)) return;
            const r = await intentar(() => api.del(`/api/empresas/${id}`));
            invalidar('empresas', 'ofertas');
            location.hash = '#/empresas';
            aviso(`Empresa eliminada (${r.ofertas_eliminadas} ofertas)`);
          } }, 'Eliminar'))),
      h('div', { class: 'rejilla' },
        tarjeta(`Ofertas publicadas (${d.ofertas.length})`, tabla([
          { titulo: 'Oferta', valor: (o) => enlace(`ofertas/${o.id}`, o.titulo) },
          { titulo: 'Estado', valor: (o) => badge(o.estado) },
          { titulo: 'Postulantes', valor: (o) => o.postulantes, num: true },
        ], d.ofertas, 'Sin ofertas publicadas')),
        tarjeta(`Empleados actuales (${actuales.length})`, h('div', { class: 'desplazable', style: { maxHeight: '340px' } }, tabla([
          { titulo: 'Nombre', valor: (u) => enlace(`usuarios/${u.id}`, u.nombre) },
          { titulo: 'Cargo', valor: (u) => u.cargo },
        ], actuales, 'Sin empleados registrados'))),
        tarjeta(`Exempleados (${d.empleados.length - actuales.length})`, tabla([
          { titulo: 'Nombre', valor: (u) => enlace(`usuarios/${u.id}`, u.nombre) },
          { titulo: 'Cargo', valor: (u) => u.cargo },
        ], d.empleados.filter((x) => !x.actual), '—')),
        tarjeta(`Proyectos (${d.proyectos.length})`, tabla([
          { titulo: 'Proyecto', valor: (p) => enlace(`proyectos/${p.id}`, p.nombre) },
          { titulo: 'Estado', valor: (p) => badge(p.estado) },
        ], d.proyectos, 'Sin proyectos')),
        tarjeta('Editar empresa', formulario(CAMPOS, {
          valores: e, boton: 'Guardar cambios',
          alEnviar: async (datos) => { await intentar(() => api.put(`/api/empresas/${id}`, datos), 'Empresa actualizada'); invalidar('empresas'); await recargar(); },
        }))));
  };
  await recargar();
  return raiz;
}

export const render = ([id]) => (id ? detalle(id) : listado());
