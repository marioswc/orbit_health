const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function api<T>(ruta: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}
