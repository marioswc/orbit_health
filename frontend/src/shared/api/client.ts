const CLAVE_TOKEN = "orbit-token";
let listener401: (() => void) | null = null;

export function getToken(): string | null {
  try { return sessionStorage.getItem(CLAVE_TOKEN); } catch { return null; }
}

export function setToken(token: string | null) {
  try {
    if (token) sessionStorage.setItem(CLAVE_TOKEN, token);
    else sessionStorage.removeItem(CLAVE_TOKEN);
  } catch { /* almacenamiento no disponible */ }
}

export function onNoAutorizado(fn: (() => void) | null) {
  listener401 = fn;
}

const enVuelo = new Map<string, Promise<unknown>>();

/**
 * GET identicos que coinciden en el tiempo (varios componentes pidiendo lo mismo) comparten una sola peticion.
 * Solo agrupa mientras la peticion esta en curso: no guarda respuestas, asi que nunca devuelve datos viejos.
 */
export function api<T>(ruta: string, init?: RequestInit): Promise<T> {
  if (init?.method && init.method !== "GET") return pedir<T>(ruta, init);
  const clave = `${getToken() ?? ""}|${ruta}`;
  const previa = enVuelo.get(clave);
  if (previa) return previa as Promise<T>;
  const p = pedir<T>(ruta, init).finally(() => enVuelo.delete(clave));
  enVuelo.set(clave, p);
  return p;
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const r = await fetch(`/api${ruta}`, {
    headers,
    ...init,
  });
  if (!r.ok) {
    if (r.status === 401 && listener401) listener401();
    let detalle = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      if (typeof j.detail === "string") detalle = j.detail;
      else if (j.detail && typeof j.detail.mensaje === "string") detalle = j.detail.mensaje;
    } catch { /* sin cuerpo JSON */ }
    throw new Error(detalle);
  }
  return r.json() as Promise<T>;
}

export const post = <T,>(ruta: string, cuerpo: unknown) =>
  api<T>(ruta, { method: "POST", body: JSON.stringify(cuerpo) });
