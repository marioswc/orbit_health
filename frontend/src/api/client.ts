export async function api<T>(ruta: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    let detalle = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      if (typeof j.detail === "string") detalle = j.detail;
    } catch { /* sin cuerpo JSON */ }
    throw new Error(detalle);
  }
  return r.json() as Promise<T>;
}

export const post = <T,>(ruta: string, cuerpo: unknown) =>
  api<T>(ruta, { method: "POST", body: JSON.stringify(cuerpo) });
