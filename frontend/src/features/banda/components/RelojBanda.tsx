import { memo, useCallback, useEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
import { nivelActual } from "../../../shared/rendimiento";
import { useTranslation } from "../../../i18n";
import { num } from "../../../shared/formato";
import type { PuntoHistorial } from "../../monitor/types/estado";

interface Props {
  /** Ultima frecuencia cardiaca registrada (lpm) o undefined. */
  fc?: number;
  /** Ultima saturacion de oxigeno (%) o undefined. */
  spo2?: number;
  /** Puntaje NEWS2 y su nivel (los calcula el backend). */
  news2?: { puntos: number; nivel: string };
  ventana?: number;
  /** Cuantos de los 5 signos del dia ya se registraron (0 a 5). */
  signosHoy: number;
  /** Los datos vienen de la mision simulada. */
  simulada: boolean;
  /** Series reales de 14 dias (las dibujan las pantallas de pulso y oxigeno). */
  fcSerie?: PuntoHistorial[];
  spo2Serie?: PuntoHistorial[];
  mision?: { progreso: number; minuto: number; duracion: number; evento?: string; activa: boolean };
}

const PAGINAS = ["anillos", "pulso", "oxigeno", "news2", "mision"] as const;
type Pagina = (typeof PAGINAS)[number];
const RADIOS = [56, 43, 30];
const ANCHO = 10;
const CY = 180;
const circ = (r: number) => 2 * Math.PI * r;
const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const PROF_CORREA = 6;
const PERIMETRO_CORREA_ARRIBA: Pt[] = [[96, 30], [150, 26], [204, 30], [226, 78], [74, 78]];
const PERIMETRO_CORREA_ABAJO: Pt[] = [[74, 302], [226, 302], [212, 352], [150, 362], [88, 352]];
const PROF = 20;            // grosor de la caja en unidades del lienzo (300 de ancho)
const CENTRO = { x: -4, y: 0 };   // de frente y centrado; solo una ligera inclinacion para que se note el volumen
type Pt = [number, number];
interface Pared { cx: number; cy: number; l: number; a: number; luz: number }

/** Perimetro del rectangulo redondeado de la caja (x 46..254, y 62..318, radio 26) en sentido horario, con `n` tramos por esquina. */
function perimetroCaja(n: number): Pt[] {
  const R = 26;
  const esquinas: [number, number, number][] = [[72, 88, 180], [228, 88, 270], [228, 292, 0], [72, 292, 90]];
  const pts: Pt[] = [];
  for (const [cx, cy, a0] of esquinas) for (let i = 0; i <= n; i++) { const a = ((a0 + (90 * i) / n) * Math.PI) / 180; pts.push([cx + R * Math.cos(a), cy + R * Math.sin(a)]); }
  return pts;
}

/** Paredes (una por tramo) de un perimetro: cada una es un rectangulo vertical al plano de la cara, asi el canto es continuo desde cualquier angulo. */
function paredes(pts: Pt[]): Pared[] {
  const out: Pared[] = [];
  for (let i = 0; i < pts.length; i++) {
    const [px, py] = pts[i], [qx, qy] = pts[(i + 1) % pts.length];
    const dx = qx - px, dy = qy - py, l = Math.hypot(dx, dy);
    if (l < 0.01) continue;
    const nx = dy / l, ny = -dx / l;                       // normal hacia afuera (sentido horario, y hacia abajo)
    const luz = clamp(0.5 + 0.5 * (nx * -0.51 + ny * -0.86)); // luz desde arriba a la izquierda
    out.push({ cx: (px + qx) / 2, cy: (py + qy) / 2, l: l + 0.8, a: (Math.atan2(dy, dx) * 180) / Math.PI, luz });
  }
  return out;
}
const estiloPared = (p: Pared, prof: number, l0: number, l1: number) => ({
  width: `calc(var(--u) * ${p.l.toFixed(2)})`,
  height: `calc(var(--u) * ${prof})`,
  transform: `translate3d(calc(var(--u) * ${p.cx.toFixed(2)}), calc(var(--u) * ${p.cy.toFixed(2)}), 0) translate(-50%, -50%) rotateZ(${p.a.toFixed(2)}deg) rotateX(90deg)`,
  background: `linear-gradient(180deg, rgba(255,255,255,.34), rgba(255,255,255,0) 30%, rgba(0,0,0,.22)), hsl(240 4% ${(l0 + (l1 - l0) * p.luz).toFixed(1)}%)`,
});

const COLOR_NIVEL: Record<string, string> = { rojo: "#ff453a", amarillo: "#ffd60a", verde: "#30d158" };

/** Un anillo (pista + progreso); el progreso se llena con una transicion al montar o cambiar. */
function Anillo({ r, frac, color, cy = CY, ancho = ANCHO }: { r: number; frac: number; color: string; cy?: number; ancho?: number }) {
  const [f, setF] = useState(0);
  useEffect(() => { const id = requestAnimationFrame(() => setF(frac)); return () => cancelAnimationFrame(id); }, [frac]);
  return (
    <g transform={`rotate(-90 150 ${cy})`}>
      <circle cx="150" cy={cy} r={r} fill="none" stroke={color} strokeOpacity=".22" strokeWidth={ancho} />
      <circle className="reloj-arco" cx="150" cy={cy} r={r} fill="none" stroke={color} strokeWidth={ancho} strokeLinecap="round" strokeDasharray={circ(r)} strokeDashoffset={circ(r) * (1 - f)} />
    </g>
  );
}

/** Linea de la serie real dentro de un recuadro (x 66..234, y 218..278). */
function Linea({ puntos, color }: { puntos?: PuntoHistorial[]; color: string }) {
  if (!puntos || puntos.length < 2) return <line x1="66" x2="234" y1="248" y2="248" stroke="#2c2c30" strokeWidth="2" strokeDasharray="3 5" />;
  const v = puntos.map((p) => p.valor);
  const min = Math.min(...v), max = Math.max(...v), rango = max - min || 1;
  const xs = (i: number) => 66 + (i / (puntos.length - 1)) * 168;
  const ys = (x: number) => 276 - ((x - min) / rango) * 56;
  const d = puntos.map((p, i) => `${i ? "L" : "M"}${xs(i).toFixed(1)} ${ys(p.valor).toFixed(1)}`).join(" ");
  const ult = puntos[puntos.length - 1];
  return (
    <g>
      <path d={`${d} L234 280 L66 280 Z`} fill={color} opacity=".14" />
      <path className="reloj-linea" d={d} fill="none" stroke={color} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={xs(puntos.length - 1)} cy={ys(ult.valor)} r="3.6" fill={color} />
    </g>
  );
}

/** Texto en hasta dos lineas (SVG no envuelve solo). */
function Parrafo({ texto, x, y, max = 24 }: { texto: string; x: number; y: number; max?: number }) {
  const palabras = texto.split(" ");
  const lineas: string[] = [""];
  for (const w of palabras) {
    const ult = lineas[lineas.length - 1];
    if ((ult + " " + w).trim().length <= max || lineas.length >= 3) lineas[lineas.length - 1] = (ult + " " + w).trim();
    else lineas.push(w);
  }
  return <>{lineas.slice(0, 3).map((l, i) => <text key={i} x={x} y={y + i * 13} className="reloj-uni" style={{ textTransform: "none", fontSize: 10.5 }} fill="#d1d1d6">{l}{i === 2 && lineas.length > 3 ? "…" : ""}</text>)}</>;
}

/**
 * Banda inteligente en 3D: caja de aluminio con grosor, correas, corona y vidrio en capas con profundidad; se gira arrastrando
 * y sus pantallas se cambian deslizando, tocando la pantalla, con la corona, los puntos o las flechas del teclado.
 * Todo lo que muestra son lecturas reales del tripulante; los anillos usan una escala de visualizacion (no clinica).
 */
function RelojBanda({ fc, spo2, news2, ventana, signosHoy, simulada, fcSerie, spo2Serie, mision }: Props) {
  const { t, locale } = useTranslation("banda");
  const [ahora, setAhora] = useState(() => new Date());
  useEffect(() => { const id = setInterval(() => setAhora(new Date()), 15000); return () => clearInterval(id); }, []);
  const hora = ahora.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit", hour12: false });

  // Rendimiento: menos tramos en las esquinas (menos elementos) segun el nivel; la geometria se calcula una sola vez
  const [{ cajaP, arribaP, abajoP }] = useState(() => {
    const n = { alto: 4, medio: 3, bajo: 2 }[nivelActual()];
    return { cajaP: paredes(perimetroCaja(n)), arribaP: paredes(PERIMETRO_CORREA_ARRIBA), abajoP: paredes(PERIMETRO_CORREA_ABAJO) };
  });
  // Pausa las animaciones cuando el reloj no se ve
  const escena = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);
  const [unidad, setUnidad] = useState(1.4667); // px por unidad del lienzo (300 de ancho); se mide, no se usan unidades de contenedor
  useEffect(() => {
    const el = escena.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([en]) => setVisible(en.isIntersecting), { threshold: 0.05 });
    io.observe(el);
    const medir = () => setUnidad(el.clientWidth / 300);
    medir();
    const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(medir) : null;
    ro?.observe(el);
    return () => { io.disconnect(); ro?.disconnect(); };
  }, []);

  const [pag, setPag] = useState(0);
  const [saliente, setSaliente] = useState<{ i: number; dir: 1 | -1 } | null>(null);
  const [dir, setDir] = useState<1 | -1>(1);
  const ir = useCallback((destino: number) => {
    const n = ((destino % PAGINAS.length) + PAGINAS.length) % PAGINAS.length;
    if (n === pag) return;
    const d: 1 | -1 = destino > pag ? 1 : -1;
    setDir(d); setSaliente({ i: pag, dir: d }); setPag(n);
    window.setTimeout(() => setSaliente(null), 380);
  }, [pag]);

  // Rotacion 3D con el puntero (clamp para que nunca se vea el reverso plano)
  const [rot, setRot] = useState(() => {
    // ?giro=Y,X fija la pose inicial (capturas y ensayos de la demo)
    const q = new URLSearchParams(window.location.search).get("giro")?.split(",").map(Number);
    return q && q.length === 2 && q.every(Number.isFinite) ? { y: q[0], x: clamp(q[1], -75, 75) } : CENTRO;
  });
  const rotRef = useRef(rot);
  rotRef.current = rot;
  const inercia = useRef(0);
  const vel = useRef({ vx: 0, vy: 0, t: 0 });
  useEffect(() => () => cancelAnimationFrame(inercia.current), []);
  const [arrastrando, setArrastrando] = useState(false);
  const [tocado, setTocado] = useState(false);
  const gesto = useRef<{ modo: "rotar" | "pantalla"; x: number; y: number; rx: number; ry: number; movio: boolean; tol: number } | null>(null);

  function abajo(e: PointerEvent<HTMLDivElement>) {
    if ((e.target as HTMLElement).closest("button")) return;
    const enPantalla = Boolean((e.target as HTMLElement).closest("[data-pantalla]"));
    cancelAnimationFrame(inercia.current);
    vel.current = { vx: 0, vy: 0, t: performance.now() };
    gesto.current = { modo: enPantalla ? "pantalla" : "rotar", x: e.clientX, y: e.clientY, rx: rot.x, ry: rot.y, movio: false, tol: e.pointerType === "mouse" ? 6 : 12 };   // el dedo tiembla mas que el raton
    e.currentTarget.setPointerCapture(e.pointerId);
    setArrastrando(true); setTocado(true);
  }
  function mover(e: PointerEvent<HTMLDivElement>) {
    const g = gesto.current; if (!g) return;
    const dx = e.clientX - g.x, dy = e.clientY - g.y;
    if (Math.abs(dx) + Math.abs(dy) > g.tol) g.movio = true;
    if (g.modo === "rotar" || (g.modo === "pantalla" && g.movio && Math.abs(dy) > Math.abs(dx) * 1.2)) {
      g.modo = "rotar";
      const nuevo = { y: g.ry + dx * 0.5, x: clamp(g.rx - dy * 0.4, -75, 75) };
      const ahora = performance.now(), dt = Math.max(1, ahora - vel.current.t);
      vel.current = { vx: (nuevo.y - rotRef.current.y) / dt, vy: (nuevo.x - rotRef.current.x) / dt, t: ahora };
      setRot(nuevo);
    }
  }
  function arriba(e: PointerEvent<HTMLDivElement>) {
    const g = gesto.current; gesto.current = null; setArrastrando(false);
    if (g && g.modo === "rotar" && g.movio) soltarConInercia();
    if (!g || g.modo !== "pantalla") return;
    const dx = e.clientX - g.x;
    const dy = e.clientY - g.y;
    if (!g.movio) ir(pag + 1);           // un toque avanza de pantalla
    else if (Math.abs(dx) > 30 && Math.abs(dx) > Math.abs(dy)) ir(pag + (dx < 0 ? 1 : -1));
  }
  /** El navegador se quedo con el gesto (por ejemplo, para desplazar la pagina): no es un toque, no cambia de pantalla. */
  function cancelar() {
    const g = gesto.current; gesto.current = null; setArrastrando(false);
    if (g && g.modo === "rotar" && g.movio) soltarConInercia();
  }
  /** Al soltar, el reloj sigue girando y se frena solo (se omite con "reducir movimiento" y en rendimiento bajo). */
  function soltarConInercia() {
    const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches || nivelActual() === "bajo";
    if (reducir || performance.now() - vel.current.t > 90) return;
    let { vx, vy } = vel.current;
    let previo = performance.now();
    const paso = (t: number) => {
      const dt = Math.min(40, t - previo); previo = t;
      vx *= Math.pow(0.0035, dt / 1000); vy *= Math.pow(0.0035, dt / 1000);   // friccion
      setRot((r) => ({ y: r.y + vx * dt, x: clamp(r.x + vy * dt, -75, 75) }));
      if (Math.abs(vx) > 0.004 || Math.abs(vy) > 0.004) inercia.current = requestAnimationFrame(paso);
    };
    inercia.current = requestAnimationFrame(paso);
  }
  function teclas(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowRight") { e.preventDefault(); ir(pag + 1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); ir(pag - 1); }
    else if (e.key === "Home" || e.key === "Escape") { e.preventDefault(); centrar(); }
    else if (e.key === "ArrowUp" || e.key === "ArrowDown") { e.preventDefault(); setRot((r) => ({ ...r, x: clamp(r.x + (e.key === "ArrowUp" ? -12 : 12), -75, 75) })); }
  }

  /** Vuelve a la pose inicial por el camino mas corto (sin dar vueltas de mas). */
  const centrar = () => {
    cancelAnimationFrame(inercia.current);
    setRot((r) => ({ x: CENTRO.x, y: CENTRO.y + Math.round((r.y - CENTRO.y) / 360) * 360 }));
  };

  const bpm = fc !== undefined ? clamp(fc, 30, 220) : null;
  const fracFc = fc !== undefined ? clamp((fc - 40) / 140) : 0;
  const fracO2 = spo2 !== undefined ? clamp((spo2 - 70) / 30) : 0;
  const fracSig = clamp(signosHoy / 5);
  const colorNews = COLOR_NIVEL[news2?.nivel ?? ""] ?? "#30d158";

  const corazon = (x: number, y: number, esc = 1) => (
    <g className={bpm ? "reloj-corazon" : ""} style={bpm ? { ["--lat" as string]: `${(60 / bpm).toFixed(2)}s` } : undefined} transform={`translate(${x} ${y}) scale(${esc})`}>
      <path d="M12 21s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 8.1a4.3 4.3 0 0 1 7.5 2.7C19.5 16.4 12 21 12 21z" fill="#ff375f" />
    </g>
  );

  const pagina = (p: Pagina): ReactNode => {
    switch (p) {
      case "anillos": return (
        <g>
          <text x="224" y="102" textAnchor="end" className="reloj-hora">{hora}</text>
          {news2 && <text x="76" y="101" className="reloj-mini" fill={colorNews}>NEWS2 {news2.puntos}</text>}
          {simulada && <text x="150" y="302" textAnchor="middle" className="reloj-mini" fill="#ffd60a">{t("watch.sim")}</text>}
          <Anillo r={RADIOS[0]} frac={fracFc} color="#ff375f" />
          <Anillo r={RADIOS[1]} frac={fracO2} color="#32ade6" />
          <Anillo r={RADIOS[2]} frac={fracSig} color="#a4e93a" />
          {corazon(138, 168)}
          <text x="92" y="268" textAnchor="middle" className="reloj-num" fill="#ff375f">{fc !== undefined ? num(fc) : "—"}</text>
          <text x="92" y="283" textAnchor="middle" className="reloj-uni">{t("watch.fc")}</text>
          <text x="150" y="268" textAnchor="middle" className="reloj-num" fill="#32ade6">{spo2 !== undefined ? num(spo2) : "—"}</text>
          <text x="150" y="283" textAnchor="middle" className="reloj-uni">SpO₂ %</text>
          <text x="208" y="268" textAnchor="middle" className="reloj-num" fill="#a4e93a">{signosHoy}/5</text>
          <text x="208" y="283" textAnchor="middle" className="reloj-uni">{t("watch.hoy")}</text>
        </g>
      );
      case "pulso": return (
        <g>
          <text x="72" y="104" className="reloj-mini" fill="#ff375f">{t("watch.p.pulso")}</text>
          {corazon(206, 88, 1.1)}
          <text x="150" y="176" textAnchor="middle" className="reloj-grande" fill="#ff375f">{fc !== undefined ? num(fc) : "—"}</text>
          <text x="150" y="196" textAnchor="middle" className="reloj-uni">{t("watch.fc")}</text>
          <Linea puntos={fcSerie} color="#ff375f" />
        </g>
      );
      case "oxigeno": return (
        <g>
          <text x="72" y="104" className="reloj-mini" fill="#32ade6">{t("watch.p.oxigeno")}</text>
          <text x="150" y="176" textAnchor="middle" className="reloj-grande" fill="#32ade6">{spo2 !== undefined ? num(spo2) : "—"}</text>
          <text x="150" y="196" textAnchor="middle" className="reloj-uni">SpO₂ %</text>
          <Linea puntos={spo2Serie} color="#32ade6" />
        </g>
      );
      case "news2": return (
        <g>
          <text x="72" y="104" className="reloj-mini" fill={colorNews}>NEWS2</text>
          <Anillo r={52} frac={news2 ? clamp(news2.puntos / 20) : 0} color={colorNews} cy={180} ancho={12} />
          <text x="150" y="190" textAnchor="middle" className="reloj-grande" fill="#fff">{news2 ? news2.puntos : "—"}</text>
          <text x="150" y="212" textAnchor="middle" className="reloj-uni">{t("watch.p.deveinte")}</text>
          <text x="150" y="282" textAnchor="middle" className="reloj-uni">{ventana ? t("watch.p.ventana", { min: ventana }) : ""}</text>
        </g>
      );
      default: return (
        <g>
          <text x="72" y="104" className="reloj-mini" fill="#ffd60a">{t("watch.p.mision")}</text>
          {mision?.activa ? (
            <>
              <text x="150" y="160" textAnchor="middle" className="reloj-grande" fill="#fff">{Math.round(mision.progreso)}%</text>
              <rect x="70" y="176" width="160" height="8" rx="4" fill="#2c2c30" />
              <rect x="70" y="176" width={160 * clamp(mision.progreso / 100)} height="8" rx="4" fill="#ffd60a" />
              <text x="150" y="204" textAnchor="middle" className="reloj-uni">{t("watch.p.minuto", { min: Math.floor(mision.minuto), total: mision.duracion })}</text>
              {mision.evento && <Parrafo texto={mision.evento} x={70} y={232} />}
            </>
          ) : (
            <Parrafo texto={t("watch.p.detenida")} x={70} y={170} />
          )}
        </g>
      );
    }
  };

  const nombrePag = t(`watch.p.${PAGINAS[pag]}`);
  return (
    <div className="reloj-caja">
      <div
        ref={escena} className={`reloj-escena${arrastrando ? " arrastrando" : ""}${tocado ? " tocado" : ""}${visible ? "" : " pausado"}`}
        tabIndex={0} role="group" aria-roledescription={t("watch.role")} aria-label={t("watch.group", { pantalla: nombrePag, n: pag + 1, total: PAGINAS.length })}
        onPointerDown={abajo} onPointerMove={mover} onPointerUp={arriba} onPointerCancel={cancelar} onKeyDown={teclas}
      >
        <div className="reloj-pose" style={{ transform: `rotateX(${rot.x}deg) rotateY(${rot.y}deg)` }}>
          <div className="reloj-idle">
            <div className="reloj-3d" style={{ ["--u" as string]: `${unidad}px` }}>
              {/* caja: paredes continuas que forman el canto de aluminio */}
              {cajaP.map((p, k) => <span key={`k${k}`} className="rl-pared" style={estiloPared(p, PROF, 42, 86)} />)}
              {/* correas: cara delantera, cara trasera y paredes (espesor) */}
              <svg className="rl-capa rl-correas" style={{ transform: `translateZ(calc(var(--u) * ${PROF_CORREA / 2}))` }} viewBox="0 0 300 380" aria-hidden="true">
                <defs>
                  <linearGradient id="rb-correa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#3d3d42" /><stop offset="1" stopColor="#222226" /></linearGradient>
                </defs>
                <path d="M96 30 L204 30 L226 78 L74 78 Z" fill="url(#rb-correa)" stroke="#55555b" strokeWidth="1.5" />
                <g stroke="#5c5c63" strokeWidth="1.2" strokeDasharray="3 4" opacity=".7"><path d="M92 46h116M88 62h124" /></g>
                <path d="M74 302 L226 302 L212 346 Q210 362 150 364 Q90 362 88 346 Z" fill="url(#rb-correa)" stroke="#55555b" strokeWidth="1.5" />
                <g fill="#101012" stroke="#55555b" strokeWidth="1">{[318, 331, 344].map((y) => <circle key={y} cx="150" cy={y} r="4.2" />)}</g>
              </svg>
              <svg className="rl-capa rl-correas" style={{ transform: `translateZ(calc(var(--u) * ${-PROF_CORREA / 2})) rotateY(180deg)` }} viewBox="0 0 300 380" aria-hidden="true">
                <path d="M96 30 L204 30 L226 78 L74 78 Z" fill="#2a2a2e" stroke="#4a4a50" strokeWidth="1.5" />
                <path d="M74 302 L226 302 L212 346 Q210 362 150 364 Q90 362 88 346 Z" fill="#2a2a2e" stroke="#4a4a50" strokeWidth="1.5" />
              </svg>
              {[...arribaP, ...abajoP].map((p, k) => <span key={`c${k}`} className="rl-pared" style={estiloPared(p, PROF_CORREA, 12, 30)} />)}
              <svg className="rl-capa rl-dorso" viewBox="0 0 300 380" aria-hidden="true" style={{ transform: `translateZ(calc(var(--u) * ${-PROF / 2})) rotateY(180deg)` }}>
                <rect x="46" y="62" width="208" height="256" rx="26" fill="#3a3a40" stroke="#4a4a50" strokeWidth="1.5" />
                <rect x="62" y="78" width="176" height="224" rx="16" fill="#1d1d21" />
                <circle cx="150" cy="190" r="56" fill="#0c0c0e" stroke="#55555b" strokeWidth="2" />
                <g fill="#30d158" opacity=".9">{[0, 1, 2, 3].map((k) => <circle key={k} cx={150 + 26 * Math.cos((k * Math.PI) / 2 + Math.PI / 4)} cy={190 + 26 * Math.sin((k * Math.PI) / 2 + Math.PI / 4)} r="6" />)}</g>
                <circle cx="150" cy="190" r="12" fill="#222" stroke="#55555b" />
                <text x="150" y="280" textAnchor="middle" className="reloj-uni" fill="#8e8e96">ORBIT HEALTH · BANDA</text>
              </svg>
              <svg className="rl-capa rl-cara" style={{ transform: `translateZ(calc(var(--u) * ${PROF / 2}))` }} viewBox="0 0 300 380" role="img" aria-label={t("watch.aria", { fc: fc !== undefined ? num(fc) : "—", spo2: spo2 !== undefined ? num(spo2) : "—", hoy: signosHoy })}>
                <defs>
                  <linearGradient id="rb-aluminio" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#e6e6ea" /><stop offset=".5" stopColor="#a9a9b0" /><stop offset="1" stopColor="#6e6e75" /></linearGradient>
                  <clipPath id="rb-pantalla"><rect x="54" y="70" width="192" height="240" rx="20" /></clipPath>
                </defs>
                <rect x="244" y="190" width="8" height="26" rx="4" fill="url(#rb-aluminio)" stroke="#55555b" />
                <rect x="46" y="62" width="208" height="256" rx="26" fill="url(#rb-aluminio)" stroke="#4a4a50" strokeWidth="1.5" />
                <rect x="54" y="70" width="192" height="240" rx="20" fill="#000" />
                <g clipPath="url(#rb-pantalla)">
                  {saliente && <g key={`s${saliente.i}-${pag}`} className={`rl-pg rl-sale-${saliente.dir > 0 ? "izq" : "der"}`}>{pagina(PAGINAS[saliente.i])}</g>}
                  <g key={`e${pag}`} className={saliente ? `rl-pg rl-entra-${dir > 0 ? "der" : "izq"}` : "rl-pg"}>{pagina(PAGINAS[pag])}</g>
                  <g aria-hidden="true">{PAGINAS.map((_, i) => <circle key={i} cx={150 + (i - (PAGINAS.length - 1) / 2) * 11} cy="299" r={i === pag ? 2.6 : 1.9} fill={i === pag ? "#fff" : "#55555b"} />)}</g>
                </g>
              </svg>
              <div className="rl-vidrio" aria-hidden="true" />
              <button type="button" className="rl-corona" onClick={() => { setTocado(true); ir(pag + 1); }} aria-label={t("watch.crown")} title={t("watch.crown")} />
              <div className="rl-pantalla" data-pantalla aria-hidden="true" />
            </div>
          </div>
        </div>
      </div>

      <div className="reloj-controles">
        <button type="button" className="ghost icono" onClick={() => ir(pag - 1)} aria-label={t("watch.prev")}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m15 6-6 6 6 6" /></svg></button>
        <div className="reloj-puntos" role="tablist" aria-label={t("watch.screens")}>
          {PAGINAS.map((p, i) => <button key={p} type="button" role="tab" aria-selected={i === pag} className={i === pag ? "activo" : ""} onClick={() => ir(i)}>{t(`watch.p.${p}`)}</button>)}
        </div>
        <button type="button" className="ghost icono" onClick={() => ir(pag + 1)} aria-label={t("watch.next")}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></button>
        <button type="button" onClick={centrar}>{t("watch.center")}</button>
      </div>
      <p className="suave banda-nota">{t("watch.hint")}</p>
    </div>
  );
}

export default memo(RelojBanda);
