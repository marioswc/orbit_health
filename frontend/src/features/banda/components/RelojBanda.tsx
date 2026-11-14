import { memo, useEffect, useState } from "react";
import { useTranslation } from "../../../i18n";
import { num } from "../../../shared/formato";

interface Props {
  /** Ultima frecuencia cardiaca registrada (lpm) o undefined. */
  fc?: number;
  /** Ultima saturacion de oxigeno (%) o undefined. */
  spo2?: number;
  /** Puntaje NEWS2 y su nivel (los calcula el backend). */
  news2?: { puntos: number; nivel: string };
  /** Cuantos de los 5 signos del dia ya se registraron (0 a 5). */
  signosHoy: number;
  /** Los datos vienen de la mision simulada. */
  simulada: boolean;
}

const RADIOS = [56, 43, 30];
const ANCHO = 10;
const circ = (r: number) => 2 * Math.PI * r;
const clamp = (x: number) => Math.min(1, Math.max(0, x));

/** Un anillo (pista + progreso); el progreso se llena con una transicion al montar o cambiar. */
function Anillo({ r, frac, color }: { r: number; frac: number; color: string }) {
  const [f, setF] = useState(0);
  useEffect(() => { const id = requestAnimationFrame(() => setF(frac)); return () => cancelAnimationFrame(id); }, [frac]);
  return (
    <g transform="rotate(-90 150 180)">
      <circle cx="150" cy="180" r={r} fill="none" stroke={color} strokeOpacity=".22" strokeWidth={ANCHO} />
      <circle className="reloj-arco" cx="150" cy="180" r={r} fill="none" stroke={color} strokeWidth={ANCHO} strokeLinecap="round" strokeDasharray={circ(r)} strokeDashoffset={circ(r) * (1 - f)} />
    </g>
  );
}

/**
 * Banda inteligente dibujada en SVG, al estilo de un reloj de pulsera: caja de aluminio, corona, correa y una esfera con tres anillos.
 * Todo lo que muestra son lecturas reales del tripulante; los anillos usan una escala de visualizacion (no clinica).
 */
function RelojBanda({ fc, spo2, news2, signosHoy, simulada }: Props) {
  const { t, locale } = useTranslation("banda");
  const [ahora, setAhora] = useState(() => new Date());
  useEffect(() => { const id = setInterval(() => setAhora(new Date()), 15000); return () => clearInterval(id); }, []);
  const hora = ahora.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit", hour12: false });
  const bpm = fc !== undefined ? Math.min(220, Math.max(30, fc)) : null;
  const fracFc = fc !== undefined ? clamp((fc - 40) / 140) : 0;
  const fracO2 = spo2 !== undefined ? clamp((spo2 - 70) / 30) : 0;
  const fracSig = clamp(signosHoy / 5);
  const colorNews = news2?.nivel === "rojo" ? "#ff453a" : news2?.nivel === "amarillo" ? "#ffd60a" : "#30d158";

  return (
    <svg className="reloj" viewBox="0 0 300 380" role="img" aria-label={t("watch.aria", { fc: fc !== undefined ? num(fc) : "—", spo2: spo2 !== undefined ? num(spo2) : "—", hoy: signosHoy })}>
      <defs>
        <linearGradient id="rb-aluminio" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#e6e6ea" /><stop offset=".5" stopColor="#a9a9b0" /><stop offset="1" stopColor="#6e6e75" /></linearGradient>
        <linearGradient id="rb-correa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3d3d42" /><stop offset="1" stopColor="#222226" /></linearGradient>
        <linearGradient id="rb-vidrio" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#fff" stopOpacity=".16" /><stop offset=".35" stopColor="#fff" stopOpacity="0" /></linearGradient>
      </defs>

      {/* correas */}
      <path d="M92 6 Q150 -4 208 6 L226 78 L74 78 Z" fill="url(#rb-correa)" stroke="#55555b" strokeWidth="1.5" />
      <path d="M74 302 L226 302 L208 374 Q150 384 92 374 Z" fill="url(#rb-correa)" stroke="#55555b" strokeWidth="1.5" />
      <g stroke="#5c5c63" strokeWidth="1.5" strokeLinecap="round" opacity=".8">
        {[330, 342, 354].map((y) => <path key={y} d={`M138 ${y}h24`} />)}
      </g>

      {/* caja y botones */}
      <rect x="244" y="132" width="11" height="40" rx="5" fill="url(#rb-aluminio)" stroke="#55555b" />
      <rect x="244" y="190" width="8" height="26" rx="4" fill="url(#rb-aluminio)" stroke="#55555b" />
      <rect x="46" y="62" width="208" height="256" rx="58" fill="url(#rb-aluminio)" stroke="#4a4a50" strokeWidth="1.5" />
      <rect x="54" y="70" width="192" height="240" rx="51" fill="#000" />

      {/* esfera */}
      <text x="224" y="102" textAnchor="end" className="reloj-hora">{hora}</text>
      {news2 && (
        <g>
          <text x="76" y="101" className="reloj-mini" fill={colorNews}>NEWS2 {news2.puntos}</text>
        </g>
      )}
      {simulada && <text x="150" y="302" textAnchor="middle" className="reloj-mini" fill="#ffd60a">{t("watch.sim")}</text>}
      <Anillo r={RADIOS[0]} frac={fracFc} color="#ff375f" />
      <Anillo r={RADIOS[1]} frac={fracO2} color="#32ade6" />
      <Anillo r={RADIOS[2]} frac={fracSig} color="#a4e93a" />
      <g className={bpm ? "reloj-corazon" : ""} style={bpm ? { ["--lat" as string]: `${(60 / bpm).toFixed(2)}s` } : undefined} transform="translate(138 168)">
        <path d="M12 21s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 8.1a4.3 4.3 0 0 1 7.5 2.7C19.5 16.4 12 21 12 21z" fill="#ff375f" />
      </g>

      <g className="reloj-datos">
        <text x="92" y="268" textAnchor="middle" className="reloj-num" fill="#ff375f">{fc !== undefined ? num(fc) : "—"}</text>
        <text x="92" y="283" textAnchor="middle" className="reloj-uni">{t("watch.fc")}</text>
        <text x="150" y="268" textAnchor="middle" className="reloj-num" fill="#32ade6">{spo2 !== undefined ? num(spo2) : "—"}</text>
        <text x="150" y="283" textAnchor="middle" className="reloj-uni">SpO₂ %</text>
        <text x="208" y="268" textAnchor="middle" className="reloj-num" fill="#a4e93a">{signosHoy}/5</text>
        <text x="208" y="283" textAnchor="middle" className="reloj-uni">{t("watch.hoy")}</text>
      </g>
      <rect x="54" y="70" width="192" height="240" rx="51" fill="url(#rb-vidrio)" pointerEvents="none" />
    </svg>
  );
}

export default memo(RelojBanda);
