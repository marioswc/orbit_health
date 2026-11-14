/**
 * i18n ligero con la misma estructura que Trivo (ES/EN, namespaces, claves planas con punto, `t("ns:clave")`,
 * `useTranslation(ns)`, `useLanguage()`, idioma en localStorage["i18nextLng"] y <html lang>), sin i18next:
 * pesa ~1 KB en vez de ~20 KB, que es lo que cabe en el presupuesto de peso de ORBIT Health.
 * Si algun dia se prefiere i18next, los JSON y las llamadas a `t()` se reutilizan tal cual.
 *
 * Archivos: locales/{ES,EN}/common.json y locales/{ES,EN}/features/<ns>/<ns>.json (namespace = nombre del archivo).
 */
import { useCallback, useSyncExternalStore } from "react";

export const SUPPORTED_LANGUAGES = ["es", "en"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];
export const DEFAULT_LANGUAGE: SupportedLanguage = "es";
export const LANGUAGE_STORAGE_KEY = "i18nextLng";
const LOCALE: Record<SupportedLanguage, string> = { es: "es-MX", en: "en-US" };

type Diccionario = Record<string, string>;
// El espanol (idioma base y de respaldo) viaja en el paquete; el ingles se descarga solo cuando se usa.
const modulosEs = import.meta.glob("./locales/ES/**/*.json", { eager: true, import: "default" }) as Record<string, Diccionario>;
const cargadoresEn = import.meta.glob("./locales/EN/**/*.json", { import: "default" }) as Record<string, () => Promise<Diccionario>>;

const recursos: Record<SupportedLanguage, Record<string, Diccionario>> = { es: {}, en: {} };
function registrar(ruta: string, dic: Diccionario) {
  const m = ruta.match(/\/locales\/(ES|EN)\/(?:.*\/)?([^/]+)\.json$/);
  if (m) recursos[m[1].toLowerCase() as SupportedLanguage][m[2]] = dic;
}
for (const [ruta, dic] of Object.entries(modulosEs)) registrar(ruta, dic);

let promesaEn: Promise<void> | null = null;
/** Descarga los textos del idioma si hace falta (solo el ingles es diferido). Se reintenta si falla. */
export function cargarIdioma(l: SupportedLanguage): Promise<void> {
  if (l !== "en") return Promise.resolve();
  promesaEn ??= Promise.all(Object.entries(cargadoresEn).map(async ([ruta, f]) => registrar(ruta, await f()))).then(() => undefined);
  promesaEn.catch(() => { promesaEn = null; });
  return promesaEn;
}

export const normalizeLanguage = (v?: string | null): SupportedLanguage | null => {
  const s = (v ?? "").toLowerCase();
  return s.startsWith("es") ? "es" : s.startsWith("en") ? "en" : null;
};

function idiomaInicial(): SupportedLanguage {
  try {
    const q = normalizeLanguage(new URLSearchParams(window.location.search).get("lang"));
    if (q) { localStorage.setItem(LANGUAGE_STORAGE_KEY, q); return q; }
    return normalizeLanguage(localStorage.getItem(LANGUAGE_STORAGE_KEY)) ?? DEFAULT_LANGUAGE;
  } catch { return DEFAULT_LANGUAGE; }
}

const inicial = idiomaInicial();
let actual: SupportedLanguage = inicial === "en" ? DEFAULT_LANGUAGE : inicial; // si el guardado es ingles, se muestra en cuanto termina de cargar
const oyentes = new Set<() => void>();
const sincronizarHtml = () => { if (typeof document !== "undefined") document.documentElement.lang = actual; };
sincronizarHtml();

export const getCurrentLanguage = (): SupportedLanguage => actual;
export async function changeLanguage(l: string): Promise<void> {
  const n = normalizeLanguage(l);
  if (!n) return;
  await cargarIdioma(n).catch(() => undefined); // si falla la descarga, se usa el espanol de respaldo
  if (n === actual) return;
  actual = n;
  try { localStorage.setItem(LANGUAGE_STORAGE_KEY, n); } catch { /* sin almacenamiento */ }
  sincronizarHtml();
  oyentes.forEach((f) => f());
}
if (inicial === "en") void changeLanguage("en");

export type Vars = Record<string, string | number | undefined>;

/** Traduce `clave` o `ns:clave`. Plurales con `clave_one` / `clave_other` si se pasa `count`. Cae al espanol y luego a la clave. */
export function translate(lang: SupportedLanguage, ns: string, clave: string, vars?: Vars): string {
  const [espacio, k] = clave.includes(":") ? (clave.split(":") as [string, string]) : [ns, clave];
  const busca = (l: SupportedLanguage, kk: string) => recursos[l][espacio]?.[kk];
  let plantilla: string | undefined;
  if (vars?.count !== undefined) {
    const regla = new Intl.PluralRules(LOCALE[lang]).select(Number(vars.count));
    plantilla = busca(lang, `${k}_${regla}`) ?? busca(DEFAULT_LANGUAGE, `${k}_${regla}`);
  }
  plantilla ??= busca(lang, k) ?? busca(DEFAULT_LANGUAGE, k) ?? k;
  return plantilla.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, n: string) => (vars?.[n] === undefined ? "" : String(vars[n])));
}

const suscribir = (f: () => void) => { oyentes.add(f); return () => { oyentes.delete(f); }; };

/** Como react-i18next: `const { t, i18n } = useTranslation("sistema")`. Re-renderiza al cambiar de idioma. */
export function useTranslation(ns = "common") {
  const language = useSyncExternalStore(suscribir, getCurrentLanguage, getCurrentLanguage);
  const t = useCallback((clave: string, vars?: Vars) => translate(language, ns, clave, vars), [language, ns]);
  return { t, i18n: { language, changeLanguage }, locale: LOCALE[language] };
}

/** Idioma activo y conmutador (misma forma que useLanguage de Trivo). */
export function useLanguage() {
  const { i18n, locale } = useTranslation();
  // El cambio desde la interfaz muestra el modal "Cambiando a…" (i18n/cambio.ts); changeLanguage cambia al instante (pruebas, ?lang=).
  const setLanguage = useCallback((l: string) => import("./cambio").then((m) => m.cambiarConAviso(l)), []);
  const toggleLanguage = useCallback(() => setLanguage(i18n.language === "es" ? "en" : "es"), [i18n.language, setLanguage]);
  return { language: i18n.language as SupportedLanguage, locale, setLanguage, toggleLanguage };
}
