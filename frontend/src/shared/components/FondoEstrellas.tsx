import { useEffect, useRef } from "react";
import { FOTOGRAMAS_VENTANA, aplicarNivel, debeDegradar, degradar, nivelActual, type Nivel } from "../rendimiento";

interface Fugaz { x: number; y: number; vx: number; vy: number; largo: number; vida: number; edad: number }

/** Parametros por nivel. fps 0 = estatico (se dibuja una vez y al cambiar tamano o tema). */
const CFG: Record<Nivel, { dpr: number; max: number; fps: number; fugaces: boolean; parallax: boolean }> = {
  alto: { dpr: 1.5, max: 200, fps: 30, fugaces: true, parallax: true },
  medio: { dpr: 1, max: 90, fps: 20, fugaces: false, parallax: true },
  bajo: { dpr: 1, max: 60, fps: 0, fugaces: false, parallax: false },
};
const CUBOS = 6; // estrellas agrupadas por fase de parpadeo: 1 trazo por cubo en vez de 1 por estrella

/**
 * Campo de estrellas fijo detras de la app. Pensado para equipos modestos:
 * - arrays tipados y un solo trazo por cubo (6 llamadas de dibujo por cuadro, no ~200)
 * - tope de fps por nivel, resolucion reducida, parallax calculado solo al hacer scroll
 * - mide los fotogramas reales y baja solo de nivel si el equipo no da; con ?perf=1 muestra fps y nivel
 */
export default function FondoEstrellas() {
  const ref = useRef<HTMLCanvasElement>(null);
  const hud = useRef<HTMLDivElement>(null);
  const verHud = typeof location !== "undefined" && new URLSearchParams(location.search).get("perf") === "1";

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d", { alpha: true });
    if (!canvas || !ctx) return;

    const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let nivel = nivelActual();
    let ancho = 0, alto = 0, n = 0, raf = 0, scrollY = window.scrollY;
    let x = new Float32Array(0), y0 = new Float32Array(0), py = new Float32Array(0), r = new Float32Array(0);
    let prof = new Float32Array(0), cubo = new Uint8Array(0);
    const velCubo = new Float32Array(CUBOS), faseCubo = new Float32Array(CUBOS), baseCubo = new Float32Array(CUBOS);
    let fugaces: Fugaz[] = [], siguienteFugaz = 1.5;
    let oscuro = document.documentElement.dataset.theme === "dark";
    let ultimoDibujo = 0, previoRaf = 0;
    let suma = 0, cuenta = 0, ventanasLentas = 0, fpsMedido = 0;
    let ultimoHud = 0;

    const estatico = () => reducir || CFG[nivel].fps === 0;

    function crear() {
      const c = CFG[nivel];
      const dpr = Math.min(window.devicePixelRatio || 1, c.dpr);
      ancho = window.innerWidth; alto = window.innerHeight;
      canvas!.width = Math.round(ancho * dpr); canvas!.height = Math.round(alto * dpr);
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      n = Math.min(c.max, Math.round((ancho * alto) / 7000));
      x = new Float32Array(n); y0 = new Float32Array(n); py = new Float32Array(n); r = new Float32Array(n);
      prof = new Float32Array(n); cubo = new Uint8Array(n);
      for (let i = 0; i < n; i++) {
        const p = Math.random();
        x[i] = Math.random() * ancho; y0[i] = Math.random() * alto; prof[i] = p;
        r[i] = 0.5 + p * 1.4; cubo[i] = (Math.random() * CUBOS) | 0;
      }
      for (let b = 0; b < CUBOS; b++) { velCubo[b] = 0.6 + Math.random() * 1.6; faseCubo[b] = Math.random() * 6.283; baseCubo[b] = 0.4 + Math.random() * 0.6; }
      posiciones();
    }

    /** Parallax: solo se recalcula al hacer scroll o cambiar tamano. */
    function posiciones() {
      const k = CFG[nivel].parallax ? scrollY * 0.25 : 0;
      for (let i = 0; i < n; i++) py[i] = (((y0[i] - k * prof[i]) % alto) + alto) % alto;
    }

    function pintar(t: number, dt: number) {
      ctx!.clearRect(0, 0, ancho, alto);
      const rgb = oscuro ? "253,252,252" : "38,52,140";
      const tope = oscuro ? 1 : 0.9;
      const parpadea = !estatico();
      for (let b = 0; b < CUBOS; b++) {
        const a = parpadea ? baseCubo[b] * (0.5 + 0.5 * Math.sin(t * 0.001 * velCubo[b] + faseCubo[b])) : baseCubo[b];
        ctx!.fillStyle = `rgba(${rgb},${(a * tope).toFixed(2)})`;
        ctx!.beginPath();
        for (let i = 0; i < n; i++) {
          if (cubo[i] !== b) continue;
          const d = r[i] * 2;
          if (r[i] > 1.3) { ctx!.moveTo(x[i] + r[i], py[i]); ctx!.arc(x[i], py[i], r[i], 0, 6.283); } else ctx!.rect(x[i] - r[i], py[i] - r[i], d, d);
        }
        ctx!.fill();
      }
      if (!CFG[nivel].fugaces || reducir) return;
      siguienteFugaz -= dt;
      if (siguienteFugaz <= 0 && fugaces.length < 3) { lanzar(); siguienteFugaz = 1.5 + Math.random() * 3.5; }
      const cabeza = oscuro ? "255,255,255" : "4,71,255";
      fugaces = fugaces.filter((f) => f.edad < f.vida && f.x > -300 && f.y < alto + 300);
      for (const f of fugaces) {
        f.edad += dt; f.x += f.vx * dt; f.y += f.vy * dt;
        const op = Math.sin(Math.PI * (f.edad / f.vida));
        const m = Math.hypot(f.vx, f.vy);
        const cx = f.x - (f.vx / m) * f.largo, cy = f.y - (f.vy / m) * f.largo;
        const g = ctx!.createLinearGradient(f.x, f.y, cx, cy);
        g.addColorStop(0, `rgba(${cabeza},${(op * 0.9).toFixed(2)})`);
        g.addColorStop(1, `rgba(${cabeza},0)`);
        ctx!.strokeStyle = g; ctx!.lineWidth = 1.8; ctx!.lineCap = "round";
        ctx!.beginPath(); ctx!.moveTo(f.x, f.y); ctx!.lineTo(cx, cy); ctx!.stroke();
        ctx!.fillStyle = `rgba(${cabeza},${op.toFixed(2)})`;
        ctx!.beginPath(); ctx!.arc(f.x, f.y, 2, 0, 6.283); ctx!.fill();
      }
    }

    function lanzar() {
      const ang = (Math.PI / 180) * (25 + Math.random() * 20);
      const vel = 520 + Math.random() * 380;
      fugaces.push({ x: ancho * (0.25 + Math.random() * 0.8), y: -20 + Math.random() * alto * 0.3, vx: -Math.cos(ang) * vel, vy: Math.sin(ang) * vel, largo: 110 + Math.random() * 120, vida: 1.1 + Math.random() * 0.7, edad: 0 });
    }

    /** Fotogramas reales (rAF crudo): si dos ventanas seguidas van lentas, baja un nivel. */
    function medir(delta: number) {
      if (delta > 250) return; // pausa de pestana, no cuenta
      suma += delta; cuenta += 1;
      if (cuenta < FOTOGRAMAS_VENTANA) return;
      const prom = suma / cuenta;
      fpsMedido = 1000 / prom;
      suma = 0; cuenta = 0;
      ventanasLentas = debeDegradar(nivel, prom) ? ventanasLentas + 1 : 0;
      if (ventanasLentas >= 2) { ventanasLentas = 0; aplicarNivel(degradar(nivel), true); }
    }

    function ciclo(t: number) {
      raf = requestAnimationFrame(ciclo);
      if (previoRaf) medir(t - previoRaf);
      previoRaf = t;
      const fps = CFG[nivel].fps;
      if (verHud && hud.current && t - ultimoHud > 500) {
        ultimoHud = t;
        hud.current.textContent = `${nivel} · ${fpsMedido ? fpsMedido.toFixed(0) : "…"} fps · ${n} estrellas`;
      }
      if (t - ultimoDibujo < 1000 / fps - 2) return;
      const dt = Math.min((t - ultimoDibujo) / 1000, 0.1);
      ultimoDibujo = t;
      pintar(t, dt);
    }

    function arrancar() {
      cancelAnimationFrame(raf); raf = 0; previoRaf = 0; suma = 0; cuenta = 0;
      crear();
      if (estatico()) pintar(0, 0); else raf = requestAnimationFrame(ciclo);
    }

    const alScroll = () => { scrollY = window.scrollY; if (!CFG[nivel].parallax) return; posiciones(); if (estatico()) pintar(0, 0); };
    const alRedimensionar = () => { crear(); if (estatico()) pintar(0, 0); };
    const obs = new MutationObserver((m) => {
      for (const c of m) {
        if (c.attributeName === "data-theme") { oscuro = document.documentElement.dataset.theme === "dark"; if (estatico()) pintar(0, 0); }
        if (c.attributeName === "data-rendimiento") { const nuevo = nivelActual(); if (nuevo !== nivel) { nivel = nuevo; arrancar(); } }
      }
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme", "data-rendimiento"] });

    arrancar();
    window.addEventListener("resize", alRedimensionar);
    window.addEventListener("scroll", alScroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf); obs.disconnect();
      window.removeEventListener("resize", alRedimensionar);
      window.removeEventListener("scroll", alScroll);
    };
  }, [verHud]);

  return (
    <>
      <canvas ref={ref} className="fondo-estrellas" aria-hidden="true" />
      {verHud && <div ref={hud} className="perf-hud" aria-hidden="true" />}
    </>
  );
}
