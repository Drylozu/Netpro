import { api, qs } from '../api.js';
import { invalidar, lista } from '../store.js';
import {
  aviso, badge, confirmar, datalist, enlace, formulario, h, intentar, nivel, selector, tarjeta, tituloTarjeta, vacio,
} from '../ui.js';

let busqueda = '';

const CAMPOS = [
  { name: 'nombre', label: 'Nombre completo', required: true },
  { name: 'email', label: 'Correo', type: 'email', required: true },
  { name: 'titular', label: 'Titular profesional', placeholder: 'p. ej. Desarrolladora backend' },
  { name: 'ciudad', label: 'Ciudad' },
  { name: 'pais', label: 'País', value: 'Colombia' },
  { name: 'anios_experiencia', label: 'Años de experiencia', type: 'number', min: 0, max: 60 },
  { name: 'bio', label: 'Biografía', type: 'textarea', ancho: true },
];

function panelLista(seleccionado) {
  const contenedor = h('ul', { class: 'lista lista-nav desplazable' });
  const cargar = async () => {
    const filas = await api.get(`/api/usuarios?${qs({ q: busqueda, limite: 200 })}`);
    contenedor.replaceChildren(...(filas.length ? filas.map((u) => h('li', {},
      h('a', { href: `#/usuarios/${u.id}`, class: u.id === seleccionado ? 'activo' : null },
        h('b', {}, u.nombre), h('span', { class: 'sub' }, u.empresa ? `${u.titular ?? 'Sin titular'} en ${u.empresa}` : (u.titular ?? '')),
        h('span', { class: 'sub' }, `${u.conexiones} conexiones`)))) : [vacio()]));
  };
  let temporizador;
  const buscador = h('input', {
    type: 'search', placeholder: 'Buscar por nombre, cargo o correo…', value: busqueda,
    onInput: (e) => { busqueda = e.target.value; clearTimeout(temporizador); temporizador = setTimeout(cargar, 250); },
  });
  cargar();
  return tarjeta(tituloTarjeta('Usuarios', h('a', { class: 'boton', href: '#/usuarios/nuevo' }, '+ Nuevo')),
    buscador, h('div', { style: { marginTop: '.75rem' } }, contenedor));
}

function formularioNuevo() {
  return tarjeta('Nuevo usuario', formulario(CAMPOS, {
    boton: 'Crear usuario',
    alEnviar: async (datos) => {
      const { usuario } = await intentar(() => api.post('/api/usuarios', datos), 'Usuario creado');
      invalidar('usuarios');
      location.hash = `#/usuarios/${usuario.id}`;
    },
  }));
}

/** Lista con botón de quitar por elemento. */
const listaQuitable = (items, contenido, alQuitar, textoVacio) => (items.length
  ? h('ul', { class: 'lista' }, items.map((it) => h('li', {}, h('div', {}, contenido(it)),
    h('button', { class: 'icono', title: 'Quitar', onClick: () => alQuitar(it) }, '✕'))))
  : vacio(textoVacio));

async function detalle(id) {
  const raiz = h('div', { class: 'pila' });
  const [usuarios, empresas, proyectos, ofertas, habilidades] = await Promise.all(
    ['usuarios', 'empresas', 'proyectos', 'ofertas', 'habilidades'].map(lista));

  const recargar = async () => {
    const p = await api.get(`/api/usuarios/${id}`);
    const u = p.usuario;
    const base = `/api/usuarios/${id}`;
    const accion = (fn, msg) => intentar(fn, msg).then(() => { invalidar('usuarios'); return recargar(); });

    // ---- habilidades
    const sugerencias = datalist(habilidades.map((x) => x.nombre));
    const habilidadesCard = tarjeta(`Habilidades (${p.habilidades.length})`,
      p.habilidades.length
        ? h('div', { class: 'chips' }, p.habilidades.sort((a, b) => b.nivel - a.nivel).map((x) => h('span', { class: 'chip', title: `${x.anios ?? 0} años` },
          x.nombre, nivel(x.nivel),
          h('button', { class: 'icono', title: 'Quitar', onClick: () => accion(() => api.del(`${base}/habilidades/${encodeURIComponent(x.clave)}`), 'Habilidad quitada') }, '✕'))))
        : vacio('Aún no tiene habilidades'),
      sugerencias.el,
      formulario([
        { name: 'nombre', label: 'Habilidad', required: true, list: sugerencias.id, placeholder: 'Existente o nueva' },
        { name: 'nivel', label: 'Nivel', type: 'select', value: 3, options: [1, 2, 3, 4, 5].map((n) => [n, `${n} / 5`]) },
        { name: 'anios', label: 'Años', type: 'number', min: 0, value: 1 },
      ], { clase: 'en-linea', boton: 'Agregar', alEnviar: (d) => accion(() => api.post(`${base}/habilidades`, d), 'Habilidad agregada').then(() => invalidar('habilidades')) }));

    // ---- experiencia
    const selEmpresa = selector(empresas, { placeholder: 'Empresa…' });
    const experienciaCard = tarjeta('Experiencia laboral',
      listaQuitable(p.empleos.sort((a, b) => (b.actual - a.actual) || String(b.desde).localeCompare(a.desde)), (e) => [
        h('b', {}, e.cargo), ' en ', enlace(`empresas/${e.empresa_id}`, e.empresa), ' ', e.actual ? badge('actual') : null,
        h('span', { class: 'sub' }, `De ${e.desde ?? '¿?'} a ${e.actual ? 'hoy' : (e.hasta ?? '¿?')}${e.sector ? `, ${e.sector.toLowerCase()}` : ''}`)],
      (e) => confirmar(`¿Quitar el empleo en ${e.empresa}?`) && accion(() => api.del(`${base}/empleos/${e.empresa_id}`), 'Empleo quitado'),
      'Sin experiencia registrada'),
      h('form', { class: 'en-linea', onSubmit: (ev) => {
        ev.preventDefault(); const f = ev.target;
        accion(() => api.post(`${base}/empleos`, { empresa_id: selEmpresa.valor, cargo: f.cargo.value, desde: f.desde.value, actual: f.actual.checked }), 'Empleo registrado');
      } },
      h('label', {}, 'Empresa', selEmpresa.el),
      h('label', {}, 'Cargo', h('input', { name: 'cargo', required: true })),
      h('label', {}, 'Desde', h('input', { name: 'desde', type: 'date' })),
      h('label', { class: 'check' }, h('input', { type: 'checkbox', name: 'actual', checked: true }), 'Actual'),
      h('button', { type: 'submit' }, 'Agregar')));

    // ---- proyectos
    const selProyecto = selector(proyectos, { placeholder: 'Proyecto…' });
    const proyectosCard = tarjeta(`Proyectos (${p.proyectos.length})`,
      listaQuitable(p.proyectos, (x) => [enlace(`proyectos/${x.proyecto_id}`, x.proyecto), ' ', badge(x.estado ?? ''), h('span', { class: 'sub' }, x.rol)],
        (x) => accion(() => api.del(`${base}/proyectos/${x.proyecto_id}`), 'Salió del proyecto'), 'No participa en proyectos'),
      h('form', { class: 'en-linea', onSubmit: (ev) => {
        ev.preventDefault();
        accion(() => api.post(`${base}/proyectos`, { proyecto_id: selProyecto.valor, rol: ev.target.rol.value }), 'Agregado al proyecto');
      } },
      h('label', {}, 'Proyecto', selProyecto.el),
      h('label', {}, 'Rol', h('input', { name: 'rol', placeholder: 'Desarrollador, QA…' })),
      h('button', { type: 'submit' }, 'Unir')));

    // ---- conexiones
    const selUsuario = selector(usuarios.filter((x) => x.id !== id), { placeholder: 'Buscar usuario…' });
    const conexionesCard = tarjeta(`Conexiones (${p.conexiones.length})`,
      h('div', { class: 'desplazable', style: { maxHeight: '320px' } },
        listaQuitable(p.conexiones.sort((a, b) => a.nombre.localeCompare(b.nombre)),
          (c) => [enlace(`usuarios/${c.id}`, c.nombre), h('span', { class: 'sub' }, `${c.titular ?? ''}, conectados desde ${c.desde ?? '¿?'}`)],
          (c) => confirmar(`¿Eliminar la conexión con ${c.nombre}?`) && accion(() => api.del(`${base}/conexiones/${c.id}`), 'Conexión eliminada'),
          'Sin conexiones')),
      h('form', { class: 'en-linea', onSubmit: (ev) => {
        ev.preventDefault();
        accion(() => api.post(`${base}/conexiones`, { usuario_id: selUsuario.valor }), 'Conexión creada');
      } }, h('label', {}, 'Conectar con', selUsuario.el), h('button', { type: 'submit' }, 'Conectar')));

    // ---- postulaciones
    const selOferta = selector(ofertas.filter((o) => o.estado === 'abierta'), { placeholder: 'Oferta abierta…' });
    const postulacionesCard = tarjeta(`Postulaciones (${p.postulaciones.length})`,
      listaQuitable(p.postulaciones, (x) => [enlace(`ofertas/${x.oferta_id}`, x.titulo), ' ', badge(x.estado), h('span', { class: 'sub' }, `${x.empresa}, ${x.fecha}`)],
        (x) => confirmar('¿Retirar la postulación?') && accion(() => api.del(`${base}/postulaciones/${x.oferta_id}`), 'Postulación retirada'),
        'No se ha postulado a ofertas'),
      h('form', { class: 'en-linea', onSubmit: (ev) => {
        ev.preventDefault();
        accion(() => api.post(`${base}/postulaciones`, { oferta_id: selOferta.valor }), 'Postulación enviada');
      } }, h('label', {}, 'Postularse a', selOferta.el), h('button', { type: 'submit' }, 'Postular')));

    // ---- datos
    const datosCard = tarjeta('Datos personales y profesionales', formulario(CAMPOS, {
      valores: u, boton: 'Guardar cambios',
      alEnviar: (d) => accion(() => api.put(base, d), 'Datos actualizados'),
    }));

    const actual = p.empleos.find((e) => e.actual);
    raiz.replaceChildren(
      h('div', { class: 'cabecera' },
        h('div', {}, h('h1', {}, u.nombre),
          h('p', { class: 'suave' }, `${u.titular ?? 'Sin titular'}${actual ? ` en ${actual.empresa}` : ''}${u.ciudad ? `, ${u.ciudad}` : ''}`)),
        h('div', { class: 'fila' },
          h('a', { class: 'boton secundario', href: `#/recomendaciones/${id}` }, 'Recomendaciones'),
          h('a', { class: 'boton secundario', href: `#/consultas/similares/${id}` }, 'Similares'),
          h('button', { class: 'peligro', onClick: async () => {
            if (!confirmar(`¿Eliminar a ${u.nombre} y todas sus relaciones?`)) return;
            const r = await intentar(() => api.del(base));
            invalidar('usuarios');
            location.hash = '#/usuarios';
            aviso(`Usuario eliminado (${r.relaciones} relaciones borradas)`);
          } }, 'Eliminar'))),
      h('div', { class: 'rejilla' }, habilidadesCard, experienciaCard, conexionesCard, proyectosCard, postulacionesCard, datosCard));
  };
  await recargar();
  return raiz;
}

export async function render([id]) {
  const derecha = id === 'nuevo' ? formularioNuevo()
    : id ? await detalle(id)
      : tarjeta('Seleccione un usuario', h('p', { class: 'suave' }, 'Elija un usuario de la lista para ver y editar su perfil, o cree uno nuevo.'));
  return h('div', { class: 'dividido' }, panelLista(id), derecha);
}
