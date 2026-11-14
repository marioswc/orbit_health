import { useEffect, useRef } from "react";

interface Estrella { x: number; y: number; r: number; a: number; v: number; fase: number; prof: number }
interface Fugaz { x: number; y: number; vx: number; vy: number; largo: number; vida: number; edad: number }

/** Campo de estrellas fijo detras de toda la app, con estrellas fugaces. Canvas 2D, sin dependencias. */
export default function FondoEstrellas() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let ancho = 0, alto = 0, estrellas: Estrella[] = [], fugaces: Fugaz[] = [], raf = 0, scrollY = window.scrollY;
    let siguiente = 1.2; // segundos hasta la proxima fugaz
    let oscuro = document.documentElement.dataset.theme === "dark";

    const crear = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      ancho = window.innerWidth; alto = window.innerHeight;
      canvas.width = ancho * dpr; canvas.height = alto * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.min(170, Math.round((ancho * alto) / 9000));
      estrellas = Array.from({ length: n }, () => {
        const prof = Math.random(); // 0 lejana, 1 cercana
        return {
          x: Math.random() * ancho, y: Math.random() * alto,
          r: 0.5 + prof * 1.5, a: 0.4 + Math.random() * 0.6,
          v: 0.6 + Math.random() * 1.6, fase: Math.random() * Math.PI * 2, prof,
        };
      });
    };

    const lanzar = () => {
      const ang = (Math.PI / 180) * (25 + Math.random() * 20); // cae en diagonal hacia abajo-izquierda
      const vel = 520 + Math.random() * 380;
      fugaces.push({
        x: ancho * (0.25 + Math.random() * 0.8), y: -20 + Math.random() * alto * 0.3,
        vx: -Math.cos(ang) * vel, vy: Math.sin(ang) * vel,
        largo: 110 + Math.random() * 120, vida: 1.1 + Math.random() * 0.7, edad: 0,
      });
    };

    const pintar = (t: number, dt: number) => {
      ctx.clearRect(0, 0, ancho, alto);
      // Claro: indigo profundo, mas opaco para que se note sobre el crema. Oscuro: blanco.
      const rgb = oscuro ? "253,252,252" : "38,52,140";
      const tope = oscuro ? 1 : 0.9;
      for (const e of estrellas) {
        // parallax con el scroll: las cercanas se mueven mas
        const py = (((e.y - scrollY * e.prof * 0.25) % alto) + alto) % alto;
        const brillo = reducir ? e.a : e.a * (0.5 + 0.5 * Math.sin(t * 0.001 * e.v + e.fase));
        ctx.fillStyle = `rgba(${rgb},${(brillo * tope).toFixed(3)})`;
        ctx.beginPath(); ctx.arc(e.x, py, e.r, 0, Math.PI * 2); ctx.fill();
      }

      if (reducir) return;
      siguiente -= dt;
      if (siguiente <= 0 && fugaces.length < 3) { lanzar(); siguiente = 1.5 + Math.random() * 3.5; }
      const cabeza = oscuro ? "255,255,255" : "4,71,255";
      fugaces = fugaces.filter((f) => f.edad < f.vida && f.x > -300 && f.y < alto + 300);
      for (const f of fugaces) {
        f.edad += dt; f.x += f.vx * dt; f.y += f.vy * dt;
        const k = f.edad / f.vida;
        const op = Math.sin(Math.PI * k); // entra y sale suave
        const m = Math.hypot(f.vx, f.vy);
        const cx = f.x - (f.vx / m) * f.largo, cy = f.y - (f.vy / m) * f.largo;
        const g = ctx.createLinearGradient(f.x, f.y, cx, cy);
        g.addColorStop(0, `rgba(${cabeza},${(op * (oscuro ? 0.95 : 0.9)).toFixed(3)})`);
        g.addColorStop(1, `rgba(${cabeza},0)`);
        ctx.strokeStyle = g; ctx.lineWidth = 1.8; ctx.lineCap = "round";
        ctx.beginPath(); ctx.moveTo(f.x, f.y); ctx.lineTo(cx, cy); ctx.stroke();
        ctx.fillStyle = `rgba(${cabeza},${op.toFixed(3)})`;
        ctx.beginPath(); ctx.arc(f.x, f.y, 2, 0, Math.PI * 2); ctx.fill();
      }
    };

    // Parpadeo a ~30 fps (suficiente y mitad de trabajo); a 60 fps solo mientras cruza una estrella fugaz
    let previo = performance.now();
    const ciclo = (t: number) => {
      raf = requestAnimationFrame(ciclo);
      if (fugaces.length === 0 && t - previo < 33) return;
      const dt = Math.min((t - previo) / 1000, 0.1); previo = t;
      pintar(t, dt);
    };

    const alScroll = () => { scrollY = window.scrollY; if (reducir) pintar(0, 0); };
    const alRedimensionar = () => { crear(); if (reducir) pintar(0, 0); };
    const obs = new MutationObserver(() => { oscuro = document.documentElement.dataset.theme === "dark"; if (reducir) pintar(0, 0); });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

    crear();
    if (reducir) pintar(0, 0); else raf = requestAnimationFrame(ciclo);
    window.addEventListener("resize", alRedimensionar);
    window.addEventListener("scroll", alScroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf); obs.disconnect();
      window.removeEventListener("resize", alRedimensionar);
      window.removeEventListener("scroll", alScroll);
    };
  }, []);

  return <canvas ref={ref} className="fondo-estrellas" aria-hidden="true" />;
}
