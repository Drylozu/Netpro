import { api } from '../api.js';
import { invalidar, lista } from '../store.js';
import {
  aviso, badge, chips, confirmar, datalist, enlace, formulario, h, intentar, selector, tabla, tarjeta, volver,
} from '../ui.js';

const CAMPOS = [
  { name: 'nombre', label: 'Nombre', required: true, ancho: true },
  { name: 'estado', label: 'Estado', type: 'select', options: ['planificado', 'activo', 'finalizado'].map((e) => [e, e]) },
  { name: 'fecha_inicio', label: 'Inicio', type: 'date' },
  { name: 'fecha_fin', label: 'Fin', type: 'date' },
  { name: 'descripcion', label: 'Descripción', type: 'textarea', ancho: true },
];

export function tablaRelacionados(filas, idActual) {
  return tabla([
    { titulo: 'Proyectos', valor: (r) => (idActual
      ? enlace(`proyectos/${r.proyecto_b.id}`, r.proyecto_b.nombre)
      : [enlace(`proyectos/${r.proyecto_a.id}`, r.proyecto_a.nombre), ' ↔ ', enlace(`proyectos/${r.proyecto_b.id}`, r.proyecto_b.nombre)]) },
    { titulo: 'Tecnologías comunes', valor: (r) => chips(r.tecnologias) },
    { titulo: 'Miembros compartidos', valor: (r) => chips(r.miembros_compartidos, undefined, 'usuario') },
    { titulo: 'Miembros conectados', valor: (r) => (r.miembros_conectados.length ? h('span', { title: r.miembros_conectados.join('\n') }, `${r.miembros_conectados.length} pares`) : '—') },
    { titulo: 'Puntaje', valor: (r) => h('span', { class: 'puntaje' }, r.puntaje), num: true },
  ], filas, 'No hay proyectos relacionados');
}

async function listado() {
  const [filas, empresas, habilidades] = await Promise.all([api.get('/api/proyectos'), lista('empresas'), lista('habilidades')]);
  const sel = selector(empresas, { placeholder: 'Empresa (opcional)…' });
  const sugerencias = datalist(habilidades.map((x) => x.nombre));
  const form = formulario([...CAMPOS, { name: 'tecnologias', label: 'Tecnologías (separadas por coma)', ancho: true, list: sugerencias.id }], {
    boton: 'Crear proyecto',
    alEnviar: async (d) => {
      const tecnologias = d.tecnologias.split(',').map((s) => s.trim()).filter(Boolean);
      const { proyecto } = await intentar(() => api.post('/api/proyectos', { ...d, tecnologias, empresa_id: sel.valor }), 'Proyecto creado');
      invalidar('proyectos', 'habilidades');
      location.hash = `#/proyectos/${proyecto.id}`;
    },
  });
  form.prepend(h('label', { class: 'ancho' }, 'Empresa', sel.el));
  return h('div', { class: 'pila' },
    h('div', { class: 'cabecera' }, h('div', {}, h('h1', {}, 'Proyectos'), h('p', { class: 'suave' }, `${filas.length} proyectos`))),
    tarjeta(null, tabla([
      { titulo: 'Proyecto', valor: (f) => enlace(`proyectos/${f.proyecto.id}`, f.proyecto.nombre) },
      { titulo: 'Empresa', valor: (f) => f.empresa ?? '—' },
      { titulo: 'Tecnologías', valor: (f) => chips(f.tecnologias) },
      { titulo: 'Estado', valor: (f) => badge(f.proyecto.estado ?? '') },
      { titulo: 'Miembros', valor: (f) => f.miembros, num: true },
    ], filas)),
    tarjeta('Nuevo proyecto', form, sugerencias.el));
}

async function detalle(id) {
  const raiz = h('div', { class: 'pila' });
  const [usuarios, habilidades] = await Promise.all([lista('usuarios'), lista('habilidades')]);
  const recargar = async () => {
    const [d, relacionados] = await Promise.all([api.get(`/api/proyectos/${id}`), api.get(`/api/consultas/proyectos-relacionados?proyecto=${id}&limite=8`)]);
    const p = d.proyecto;
    const base = `/api/proyectos/${id}`;
    const accion = (fn, msg) => intentar(fn, msg).then(recargar);
    const selUsuario = selector(usuarios, { placeholder: 'Agregar miembro…' });
    const sugerencias = datalist(habilidades.map((x) => x.nombre));

    raiz.replaceChildren(
      h('div', { class: 'cabecera' },
        h('div', {}, volver('proyectos', 'Proyectos'), h('h1', {}, p.nombre, badge(p.estado ?? '')),
          h('p', { class: 'suave' }, d.empresa ? ['Desarrollado por ', enlace(`empresas/${d.empresa.id}`, d.empresa.nombre)] : 'Sin empresa asociada')),
        h('button', { class: 'peligro', onClick: async () => {
          if (!confirmar(`¿Eliminar el proyecto ${p.nombre}?`)) return;
          await intentar(() => api.del(base));
          invalidar('proyectos');
          location.hash = '#/proyectos';
          aviso('Proyecto eliminado');
        } }, 'Eliminar')),
      p.descripcion ? h('p', {}, p.descripcion) : null,
      h('div', { class: 'rejilla' },
        tarjeta(`Tecnologías (${d.tecnologias.length})`,
          d.tecnologias.length ? h('div', { class: 'chips' }, d.tecnologias.map((t) => h('span', { class: 'chip' }, t.nombre,
            h('button', { class: 'icono', title: 'Quitar', onClick: () => accion(() => api.del(`${base}/tecnologias/${encodeURIComponent(t.clave)}`), 'Tecnología quitada') }, '✕'))))
            : h('p', { class: 'vacio' }, 'Sin tecnologías'),
          sugerencias.el,
          formulario([{ name: 'nombre', label: 'Tecnología', required: true, list: sugerencias.id }],
            { clase: 'en-linea', boton: 'Agregar', alEnviar: (t) => accion(() => api.post(`${base}/tecnologias`, t), 'Tecnología agregada').then(() => invalidar('habilidades')) })),
        tarjeta(`Miembros (${d.miembros.length})`,
          d.miembros.length ? h('ul', { class: 'lista' }, d.miembros.map((m) => h('li', {},
            h('div', {}, enlace(`usuarios/${m.id}`, m.nombre), h('span', { class: 'sub' }, [m.rol, m.titular].filter(Boolean).join(', '))),
            h('button', { class: 'icono', title: 'Quitar', onClick: () => accion(() => api.del(`/api/usuarios/${m.id}/proyectos/${id}`), 'Miembro quitado') }, '✕'))))
            : h('p', { class: 'vacio' }, 'Sin miembros'),
          h('form', { class: 'en-linea', onSubmit: (ev) => {
            ev.preventDefault();
            accion(() => api.post(`/api/usuarios/${selUsuario.valor}/proyectos`, { proyecto_id: id, rol: ev.target.rol.value }), 'Miembro agregado');
          } }, h('label', {}, 'Usuario', selUsuario.el), h('label', {}, 'Rol', h('input', { name: 'rol' })), h('button', { type: 'submit' }, 'Agregar'))),
        tarjeta('Editar proyecto', formulario(CAMPOS, {
          valores: p, boton: 'Guardar cambios',
          alEnviar: (datos) => accion(() => api.put(base, datos), 'Proyecto actualizado').then(() => invalidar('proyectos')),
        }))),
      tarjeta('Proyectos relacionados (comparten tecnologías o miembros relacionados)', tablaRelacionados(relacionados, id)));
  };
  await recargar();
  return raiz;
}

export const render = ([id]) => (id ? detalle(id) : listado());
