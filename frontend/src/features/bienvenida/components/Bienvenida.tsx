import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "../../../i18n";
import "./bienvenida.css";

const PASOS = 5;
const CLAVE = "orbit-bienvenida-vista";

function yaVista(): boolean {
  try { return localStorage.getItem(CLAVE) === "1"; } catch { return false; }
}
function marcarVista() {
  try { localStorage.setItem(CLAVE, "1"); } catch { /* sin almacenamiento: se mostrará de nuevo */ }
}

/** Guía de bienvenida para quien no sabe nada: se abre sola la primera vez, se puede omitir y se reabre con el botón "?". */
export default function Bienvenida() {
  const { t } = useTranslation("bienvenida");
  const [abierta, setAbierta] = useState(() => !yaVista());
  const [paso, setPaso] = useState(1);
  const principal = useRef<HTMLButtonElement | null>(null);
  const ayuda = useRef<HTMLButtonElement | null>(null);

  const cerrar = useCallback(() => {
    marcarVista();
    setAbierta(false);
    setPaso(1);
    setTimeout(() => ayuda.current?.focus?.(), 0);
  }, []);

  useEffect(() => { if (abierta) principal.current?.focus(); }, [abierta, paso]);
  useEffect(() => {
    if (!abierta) return;
    const alTeclear = (e: KeyboardEvent) => { if (e.key === "Escape") cerrar(); };
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [abierta, cerrar]);

  const ultimo = paso === PASOS;
  return (
    <>
      <button ref={ayuda} type="button" className="bienvenida-ayuda" aria-label={t("ayuda")} title={t("ayuda")} onClick={() => setAbierta(true)}>?</button>
      {abierta && (
        <div className="bienvenida-fondo" onMouseDown={(e) => { if (e.target === e.currentTarget) cerrar(); }}>
          <div className="bienvenida" role="dialog" aria-modal="true" aria-labelledby="bienvenida-titulo" aria-label={t("titulo.aria")}>
            <div className="bienvenida-paso">{t("paso").replace("{n}", String(paso)).replace("{total}", String(PASOS))}</div>
            <div className="bienvenida-puntos" aria-hidden="true">
              {Array.from({ length: PASOS }, (_, i) => <i key={i} className={i + 1 === paso ? "activo" : undefined} />)}
            </div>
            <h2 id="bienvenida-titulo">{t(`p${paso}.titulo`)}</h2>
            <p>{t(`p${paso}.texto`)}</p>
            <div className="bienvenida-acciones">
              <button type="button" className="boton" onClick={cerrar}>{ultimo ? t("cerrar") : t("omitir")}</button>
              <div>
                {paso > 1 && <button type="button" className="boton" onClick={() => setPaso((p) => p - 1)}>{t("atras")}</button>}
                <button ref={principal} type="button" className="boton" onClick={() => (ultimo ? cerrar() : setPaso((p) => p + 1))}>
                  {ultimo ? t("empezar") : t("siguiente")}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
