import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { api } from "../../../shared/api/client";
import { textoTipoT } from "./ConsolaEnlace";

interface MensajeTierra {
  id: number;
  tripulante_id: string;
  tipo_evento: string;
  prioridad: number;
  transmitido_ts?: string;
}

interface RespuestaTierra {
  timestamp_tierra: string;
  recibidos: MensajeTierra[];
}

interface TripulanteInforme {
  id: string;
  nombre: string;
  rol: string;
  nivel_general: string;
  news2: { puntos: number; nivel: string };
}

interface InformeTripulacion {
  generado_ts: string;
  aviso: string;
  tripulacion: TripulanteInforme[];
}

const PRIO_NIVEL: Record<number, string> = { 1: "rojo", 2: "amarillo", 3: "verde" };

/** Vista de solo lectura del centro de control en Tierra e informe exportable. */
export default function VistaTierra() {
  const { t } = useTranslation("enlace");
  const nivel = (n: string) => (["verde", "amarillo", "rojo", "sin_datos"].includes(n) ? t(`common:status.${n}`) : n);
  const [tierra, setTierra] = useState<RespuestaTierra | null>(null);
  const [informe, setInforme] = useState<InformeTripulacion | null>(null);

  const cargar = useCallback(() => {
    api<RespuestaTierra>("/tierra/mensajes?limite=12").then(setTierra).catch(() => {});
    api<InformeTripulacion>("/informe").then(setInforme).catch(() => {});
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  return (
    <section className="tarjeta pieza tierra-bloque" aria-label={t("tierra.aria")}>
      <div className="tierra-cab">
        <div>
          <h2>{t("tierra.title")}</h2>
          <p className="suave">{t("tierra.desc")}</p>
        </div>
        <button type="button" className="ghost" onClick={cargar}>{t("tierra.refresh")}</button>
      </div>

      {tierra && tierra.recibidos.length > 0 ? (
        <ul className="tierra-lista">
          {tierra.recibidos.slice(0, 8).map((m) => (
            <li key={m.id}>
              <span className={`badge ${PRIO_NIVEL[m.prioridad] ?? "sin_datos"}`}>P{m.prioridad}</span>
              <strong>{m.tripulante_id}</strong>
              <span>{textoTipoT(t, m.tipo_evento)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="suave">{t("tierra.empty")}</p>
      )}

      {informe && (
        <div className="informe-bloque">
          <div className="tierra-cab">
            <div>
              <h3>{t("informe.title")}</h3>
              <p className="suave">{informe.aviso}</p>
            </div>
            <a className="ghost informe-btn" href="/api/informe" target="_blank" rel="noreferrer">
              {t("informe.json")}
            </a>
          </div>
          <ul className="informe-lista">
            {informe.tripulacion.map((p) => (
              <li key={p.id}>
                <span>
                  <strong>{p.nombre}</strong> <span className="suave">({p.rol})</span>
                </span>
                <span className="informe-acciones">
                  <span className={`badge ${p.nivel_general}`}>{nivel(p.nivel_general)}</span>
                  <a className="ghost informe-btn" href={`/api/informe/${encodeURIComponent(p.id)}?formato=csv`} download>
                    {t("informe.csv", { id: p.id })}
                  </a>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

