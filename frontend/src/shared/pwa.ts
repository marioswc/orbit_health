/** Registro de la app instalable (PWA): service worker, aviso de nueva versión y botón de instalar.
 *  Solo actúa en producción y en un contexto seguro (localhost o HTTPS); en otro caso la web funciona igual, sin instalarse. */
export interface EventoInstalar extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

type Oyente = () => void;
let instalador: EventoInstalar | null = null;
let hayActualizacion: ServiceWorkerRegistration | null = null;
const oyentes = new Set<Oyente>();
const avisar = () => oyentes.forEach((f) => f());

export const suscribir = (f: Oyente) => { oyentes.add(f); return () => { oyentes.delete(f); }; };
export const puedeInstalar = () => instalador !== null;
export const actualizacionLista = () => hayActualizacion !== null;
export const yaInstalada = () =>
  typeof window !== "undefined" && (window.matchMedia?.("(display-mode: standalone)").matches || (navigator as { standalone?: boolean }).standalone === true);

export async function instalar(): Promise<"accepted" | "dismissed" | "no-disponible"> {
  if (!instalador) return "no-disponible";
  await instalador.prompt();
  const r = await instalador.userChoice;
  instalador = null;
  avisar();
  return r.outcome;
}

/** Activa la versión nueva y recarga cuando el service worker nuevo toma el control. */
export function aplicarActualizacion() {
  hayActualizacion?.waiting?.postMessage("activar");
}

export function iniciarPwa() {
  if (typeof window === "undefined") return;
  window.addEventListener("beforeinstallprompt", (e) => { e.preventDefault(); instalador = e as EventoInstalar; avisar(); });
  window.addEventListener("appinstalled", () => { instalador = null; avisar(); });
  if (!import.meta.env.PROD || !("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").then((reg) => {
      const revisar = () => {
        const nuevo = reg.installing;
        nuevo?.addEventListener("statechange", () => {
          if (nuevo.state === "installed" && navigator.serviceWorker.controller) { hayActualizacion = reg; avisar(); }
        });
      };
      if (reg.waiting && navigator.serviceWorker.controller) { hayActualizacion = reg; avisar(); }
      reg.addEventListener("updatefound", revisar);
      setInterval(() => reg.update().catch(() => undefined), 60 * 60 * 1000);   // busca versión nueva cada hora
    }).catch(() => undefined);
    let recargado = false;
    navigator.serviceWorker.addEventListener("controllerchange", () => { if (!recargado) { recargado = true; window.location.reload(); } });
  });
}
