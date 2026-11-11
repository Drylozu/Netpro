import { h } from './ui.js';
import * as inicio from './vistas/inicio.js';
import * as usuarios from './vistas/usuarios.js';
import * as empresas from './vistas/empresas.js';
import * as ofertas from './vistas/ofertas.js';
import * as proyectos from './vistas/proyectos.js';
import * as consultas from './vistas/consultas.js';
import * as recomendaciones from './vistas/recomendaciones.js';
import * as analitica from './vistas/analitica.js';

const vistas = { inicio, usuarios, empresas, ofertas, proyectos, consultas, recomendaciones, analitica };
const app = document.getElementById('app');
let ultimaNavegacion = 0;

async function navegar() {
  const turno = ++ultimaNavegacion;
  const [seccion = 'inicio', ...params] = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  const vista = vistas[seccion] || inicio;
  const nombre = vistas[seccion] ? seccion : 'inicio';
  document.body.dataset.seccion = nombre;
  const titulo = document.querySelector(`#menu a[href="#/${nombre}"]`)?.textContent.trim();
  document.title = nombre === 'inicio' ? 'Netpro' : `${titulo} – Netpro`;
  document.querySelectorAll('#menu a').forEach((a) =>
    a.classList.toggle('activo', a.getAttribute('href') === `#/${nombre}`));
  app.replaceChildren(h('p', { class: 'cargando' }, 'Cargando…'));
  let contenido;
  try {
    contenido = await vista.render(params.map(decodeURIComponent));
  } catch (e) {
    console.error(e);
    contenido = h('div', { class: 'error-caja' }, h('b', {}, 'No se pudo cargar la vista. '), e.message);
  }
  if (turno !== ultimaNavegacion) return; // ya se navegó a otra vista
  app.replaceChildren(contenido);
  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', navegar);
navegar();
