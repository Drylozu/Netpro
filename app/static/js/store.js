import { api } from './api.js';

const fuentes = {
  usuarios: async () => (await api.get('/api/usuarios?limite=100000'))
    .map((u) => ({ id: u.id, label: u.titular ? `${u.nombre}, ${u.titular}` : u.nombre })),
  empresas: async () => (await api.get('/api/empresas'))
    .map((e) => ({ id: e.empresa.id, label: e.empresa.nombre, sector: e.empresa.sector })),
  ofertas: async () => (await api.get('/api/ofertas'))
    .map((o) => ({ id: o.oferta.id, label: `${o.oferta.titulo} en ${o.empresa}`, estado: o.oferta.estado })),
  proyectos: async () => (await api.get('/api/proyectos'))
    .map((p) => ({ id: p.proyecto.id, label: p.proyecto.nombre })),
  habilidades: async () => api.get('/api/habilidades'),
};

const cache = {};

export async function lista(nombre) {
  if (!cache[nombre]) cache[nombre] = fuentes[nombre]().catch((e) => { delete cache[nombre]; throw e; });
  return cache[nombre];
}

export function invalidar(...nombres) {
  for (const n of nombres.length ? nombres : Object.keys(cache)) delete cache[n];
}
