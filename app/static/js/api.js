// Envoltorio mínimo de fetch() para la API JSON de Flask.
async function peticion(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== undefined) {
    opciones.headers['Content-Type'] = 'application/json';
    opciones.body = JSON.stringify(cuerpo);
  }
  const resp = await fetch(url, opciones);
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(datos.error || `Error ${resp.status}`);
  return datos;
}

export const api = {
  get: (url) => peticion('GET', url),
  post: (url, cuerpo = {}) => peticion('POST', url, cuerpo),
  put: (url, cuerpo = {}) => peticion('PUT', url, cuerpo),
  del: (url) => peticion('DELETE', url),
};

export const qs = (params) =>
  new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString();
