import { api } from '../api.js';
import { invalidar, lista } from '../store.js';
import { chips, enlace, h, intentar, selector, tabla, tarjeta } from '../ui.js';

export async function render([id]) {
  const usuarios = await lista('usuarios');
  const sel = selector(usuarios, { valorInicial: id, alCambiar: (v) => { if (v) location.hash = `#/recomendaciones/${v}`; } });
  const cabecera = h('div', { class: 'cabecera' },
    h('div', {}, h('h1', {}, 'Recomendaciones'),
      h('p', { class: 'suave' }, 'Contactos, empleos y colaboradores sugeridos a partir de la estructura del grafo.')),
    h('label', { style: { minWidth: '320px' } }, 'Usuario', sel.el));
  if (!id) return h('div', { class: 'pila' }, cabecera);

  const raiz = h('div', { class: 'pila' });
  const cargar = async () => {
    const [perfil, contactos, empleos, colaboradores] = await Promise.all([
      api.get(`/api/usuarios/${id}`),
      api.get(`/api/recomendaciones/${id}/contactos`),
      api.get(`/api/recomendaciones/${id}/empleos`),
      api.get(`/api/recomendaciones/${id}/colaboradores`)]);
    const accion = (fn, msg) => intentar(fn, msg).then(() => { invalidar('usuarios'); return cargar(); });
    raiz.replaceChildren(cabecera,
      h('p', {}, enlace(`usuarios/${id}`, perfil.usuario.nombre), ` tiene ${perfil.conexiones.length} conexiones, `,
        `${perfil.habilidades.length} habilidades y participa en ${perfil.proyectos.length} proyectos.`),
      tarjeta('Personas que quizá conozcas',
        h('p', { class: 'suave pequeno' }, 'Amigos de amigos aún no conectados. Puntaje = 3 × contactos en común + habilidades compartidas + 2 × empresas compartidas.'),
        tabla([
          { titulo: 'Persona', valor: (c) => [enlace(`usuarios/${c.id}`, c.nombre), h('div', { class: 'suave pequeno' }, c.titular)] },
          { titulo: 'En común', valor: (c) => h('span', { title: c.via.join(', ') }, `${c.en_comun} (${c.via.join(', ')}${c.en_comun > 3 ? '…' : ''})`) },
          { titulo: 'Habilidades compartidas', valor: (c) => chips(c.habilidades) },
          { titulo: 'Empresas compartidas', valor: (c) => (c.empresas.length ? c.empresas.join(', ') : '—') },
          { titulo: 'Puntaje', valor: (c) => h('span', { class: 'puntaje' }, c.puntaje), num: true },
          { titulo: '', valor: (c) => h('button', { class: 'mini', onClick: () => accion(() => api.post(`/api/usuarios/${id}/conexiones`, { usuario_id: c.id }), `Conectado con ${c.nombre}`) }, 'Conectar') },
        ], contactos, 'Sin sugerencias: el usuario necesita al menos una conexión')),
      tarjeta('Empleos recomendados',
        h('p', { class: 'suave pequeno' }, 'Ofertas abiertas. Puntaje = 80 % habilidades cubiertas + 20 % contactos que trabajan en la empresa.'),
        tabla([
          { titulo: 'Oferta', valor: (o) => [enlace(`ofertas/${o.id}`, o.titulo), h('div', { class: 'suave pequeno' }, [o.empresa, o.modalidad?.toLowerCase()].filter(Boolean).join(', '))] },
          { titulo: 'Tiene', valor: (o) => chips(o.coinciden) },
          { titulo: 'Le falta', valor: (o) => chips(o.faltan) },
          { titulo: 'Contactos dentro', valor: (o) => (o.contactos.length ? o.contactos.join(', ') : '—') },
          { titulo: 'Puntaje', valor: (o) => h('span', { class: 'puntaje' }, o.puntaje), num: true },
          { titulo: '', valor: (o) => h('button', { class: 'mini', onClick: () => accion(() => api.post(`/api/usuarios/${id}/postulaciones`, { oferta_id: o.id }), 'Postulación enviada') }, 'Postular') },
        ], empleos, 'Sin ofertas que coincidan con sus habilidades')),
      tarjeta('Colaboradores para sus proyectos',
        h('p', { class: 'suave pequeno' }, 'Personas a ≤ 3 saltos que dominan tecnologías de los proyectos del usuario que él no tiene. Puntaje = 2 × tecnologías aportadas + nivel medio − distancia.'),
        tabla([
          { titulo: 'Persona', valor: (c) => [enlace(`usuarios/${c.id}`, c.nombre), h('div', { class: 'suave pequeno' }, c.titular)] },
          { titulo: 'Aporta', valor: (c) => chips(c.aporta) },
          { titulo: 'Distancia', valor: (c) => `${c.distancia} salto${c.distancia > 1 ? 's' : ''}`, num: true },
          { titulo: 'Nivel medio', valor: (c) => c.nivel_medio, num: true },
          { titulo: 'Puntaje', valor: (c) => h('span', { class: 'puntaje' }, c.puntaje), num: true },
        ], colaboradores, perfil.proyectos.length ? 'Nadie cercano cubre las tecnologías que le faltan' : 'El usuario no participa en proyectos')));
  };
  await cargar();
  return raiz;
}
