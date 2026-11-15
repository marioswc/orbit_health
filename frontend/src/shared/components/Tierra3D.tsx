import { useEffect, useRef, useState } from "react";
import { nivelActual, type Nivel } from "../rendimiento";

interface Props {
  /** Mapa equirectangular de la superficie (2:1). */
  mapa: string;
  /** Imagen plana que se muestra si el equipo no soporta WebGL. */
  respaldo: string;
  className?: string;
  segundosPorVuelta?: number;
}

const VS = `
attribute vec3 aPos; attribute vec2 aUv;
uniform float uAngulo; uniform float uInclina;
varying vec2 vUv; varying vec3 vN;
void main() {
  float c = cos(uAngulo), s = sin(uAngulo);
  vec3 p = vec3(c * aPos.x + s * aPos.z, aPos.y, -s * aPos.x + c * aPos.z);   // giro sobre el eje norte-sur
  float ci = cos(uInclina), si = sin(uInclina);
  p = vec3(p.x, ci * p.y - si * p.z, si * p.y + ci * p.z);                    // inclinacion hacia el espectador
  vN = p; vUv = aUv;
  gl_Position = vec4(p.x * 0.93, p.y * 0.93, -p.z * 0.5, 1.0);
}`;

const FS = `
precision mediump float;
uniform sampler2D uMapa;
varying vec2 vUv; varying vec3 vN;
void main() {
  vec3 n = normalize(vN);
  vec3 luz = normalize(vec3(-0.55, 0.4, 0.75));
  float d = max(dot(n, luz), 0.0);
  vec3 col = texture2D(uMapa, vUv).rgb * (0.3 + 0.95 * d);
  float borde = pow(1.0 - max(n.z, 0.0), 3.0);
  col += vec3(0.22, 0.45, 1.0) * borde * (0.25 + 0.75 * d);                    // atmosfera
  gl_FragColor = vec4(col, 1.0);
}`;

/** Ajustes por nivel de rendimiento: resolucion maxima del lienzo, tope de pixeles y fotogramas por segundo (0 = imagen fija). */
const PERFIL: Record<Nivel, { dpr: number; maxPx: number; fps: number }> = {
  alto: { dpr: 1.5, maxPx: 1100, fps: 60 },
  medio: { dpr: 1, maxPx: 640, fps: 30 },
  bajo: { dpr: 1, maxPx: 480, fps: 0 },
};

function compilar(gl: WebGLRenderingContext, tipo: number, src: string) {
  const sh = gl.createShader(tipo)!;
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh) ?? "shader");
  return sh;
}

function esfera(franjas: number, anillos: number) {
  const pos: number[] = [], uv: number[] = [], idx: number[] = [];
  for (let y = 0; y <= anillos; y++) {
    const v = y / anillos, lat = Math.PI * v;
    for (let x = 0; x <= franjas; x++) {
      const u = x / franjas, lon = 2 * Math.PI * u;
      pos.push(-Math.cos(lon) * Math.sin(lat), Math.cos(lat), Math.sin(lon) * Math.sin(lat));
      uv.push(u, v);
    }
  }
  for (let y = 0; y < anillos; y++) {
    for (let x = 0; x < franjas; x++) {
      const a = y * (franjas + 1) + x, b = a + franjas + 1;
      idx.push(a, b, a + 1, b, b + 1, a + 1);
    }
  }
  return { pos: new Float32Array(pos), uv: new Float32Array(uv), idx: new Uint16Array(idx) };
}

/**
 * Tierra en 3D (esfera con el mapa de la NASA) que gira sola; se puede arrastrar para girarla. Sin dependencias: WebGL directo.
 * Rendimiento: resolucion y fps segun el nivel de la interfaz, se detiene fuera de pantalla o con la pestana oculta,
 * y libera la memoria de la GPU al salir.
 */
export default function Tierra3D({ mapa, respaldo, className, segundosPorVuelta = 60 }: Props) {
  const lienzo = useRef<HTMLCanvasElement>(null);
  const [sinWebgl, setSinWebgl] = useState(false);

  useEffect(() => {
    const canvas = lienzo.current;
    if (!canvas) return;
    const gl = (canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: true, powerPreference: "low-power", depth: true, stencil: false }) ?? null) as WebGLRenderingContext | null;
    if (!gl) { setSinWebgl(true); return; }

    let raf = 0, vivo = true, listo = false, enPantalla = true, angulo = 0.9, previo = 0, ultimoDibujo = 0, sucio = true;
    let arrastre: { x: number; a: number } | null = null;
    const quieto = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
    const recursos: { prog?: WebGLProgram | null; bufs: (WebGLBuffer | null)[]; tex?: WebGLTexture | null } = { bufs: [] };
    try {
      const prog = gl.createProgram()!;
      recursos.prog = prog;
      const vs = compilar(gl, gl.VERTEX_SHADER, VS), fs = compilar(gl, gl.FRAGMENT_SHADER, FS);
      gl.attachShader(prog, vs);
      gl.attachShader(prog, fs);
      gl.linkProgram(prog);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      gl.useProgram(prog);

      const malla = esfera(56, 36);
      const buf = (datos: BufferSource, tipo: number) => {
        const b = gl.createBuffer();
        recursos.bufs.push(b);
        gl.bindBuffer(tipo, b);
        gl.bufferData(tipo, datos, gl.STATIC_DRAW);
        return b;
      };
      buf(malla.pos, gl.ARRAY_BUFFER);
      const aPos = gl.getAttribLocation(prog, "aPos");
      gl.enableVertexAttribArray(aPos);
      gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
      buf(malla.uv, gl.ARRAY_BUFFER);
      const aUv = gl.getAttribLocation(prog, "aUv");
      gl.enableVertexAttribArray(aUv);
      gl.vertexAttribPointer(aUv, 2, gl.FLOAT, false, 0, 0);
      buf(malla.idx, gl.ELEMENT_ARRAY_BUFFER);

      const uAngulo = gl.getUniformLocation(prog, "uAngulo");
      gl.uniform1f(gl.getUniformLocation(prog, "uInclina"), 0.38);
      gl.enable(gl.DEPTH_TEST);
      gl.enable(gl.CULL_FACE);
      gl.cullFace(gl.BACK);

      // Tamano del lienzo: se recalcula solo cuando cambia el contenedor o el nivel (no en cada fotograma)
      const ajustar = () => {
        const perfil = PERFIL[nivelActual()];
        const css = canvas.clientWidth;
        const w = Math.max(1, Math.min(Math.round(css * Math.min(window.devicePixelRatio || 1, perfil.dpr)), perfil.maxPx));
        if (css > 0 && (canvas.width !== w || canvas.height !== w)) {
          canvas.width = w;
          canvas.height = w;
          gl.viewport(0, 0, w, w);
          sucio = true;
        }
      };
      const dibujar = () => {
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        gl.uniform1f(uAngulo, angulo);
        gl.drawElements(gl.TRIANGLES, malla.idx.length, gl.UNSIGNED_SHORT, 0);
        sucio = false;
      };

      const parar = () => { cancelAnimationFrame(raf); raf = 0; previo = 0; };
      const cuadro = (t: number) => {
        raf = 0;
        if (!vivo || !enPantalla || document.hidden) { previo = 0; return; }
        const { fps } = PERFIL[nivelActual()];
        if (fps === 0) { if (sucio) dibujar(); return; }
        if (t - ultimoDibujo >= 1000 / fps - 4) {                                   // tope de fps (el -4 absorbe el jitter de rAF)
          if (previo && !arrastre) angulo += ((t - previo) / 1000) * ((2 * Math.PI) / segundosPorVuelta);
          previo = t;
          ultimoDibujo = t;
          dibujar();
        }
        raf = requestAnimationFrame(cuadro);
      };
      const arrancar = () => {
        if (raf || !vivo || !listo || !enPantalla || document.hidden) return;
        if (quieto || PERFIL[nivelActual()].fps === 0) { if (sucio) dibujar(); return; }   // imagen fija: sin bucle
        raf = requestAnimationFrame(cuadro);
      };

      const tex = gl.createTexture();
      recursos.tex = tex;
      const img = new Image();
      img.decoding = "async";
      img.onload = () => {
        if (!vivo) return;
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, 0);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
        listo = true;
        ajustar();
        dibujar();
        arrancar();
      };
      img.onerror = () => setSinWebgl(true);
      img.src = mapa;

      const redim = new ResizeObserver(() => { ajustar(); if (listo && !raf) { dibujar(); arrancar(); } });
      redim.observe(canvas);
      const visible = new IntersectionObserver(([e]) => { enPantalla = e.isIntersecting; if (enPantalla) arrancar(); else parar(); });
      visible.observe(canvas);
      const alCambiarVisibilidad = () => { if (document.hidden) parar(); else arrancar(); };
      document.addEventListener("visibilitychange", alCambiarVisibilidad);
      // El nivel puede bajar solo por fotogramas lentos: se ajusta la resolucion y el ritmo al vuelo
      const nivel = new MutationObserver(() => { ajustar(); parar(); arrancar(); });
      nivel.observe(document.documentElement, { attributes: true, attributeFilter: ["data-rendimiento"] });

      const bajar = (e: PointerEvent) => { arrastre = { x: e.clientX, a: angulo }; canvas.setPointerCapture(e.pointerId); };
      const mover = (e: PointerEvent) => {
        if (!arrastre) return;
        angulo = arrastre.a + (e.clientX - arrastre.x) * 0.008;
        sucio = true;
        if (!raf && listo) dibujar();                                               // sin bucle activo, redibuja al arrastrar
      };
      const soltar = () => { arrastre = null; };
      canvas.addEventListener("pointerdown", bajar);
      canvas.addEventListener("pointermove", mover);
      canvas.addEventListener("pointerup", soltar);
      canvas.addEventListener("pointercancel", soltar);
      return () => {
        vivo = false;
        parar();
        redim.disconnect();
        visible.disconnect();
        nivel.disconnect();
        document.removeEventListener("visibilitychange", alCambiarVisibilidad);
        canvas.removeEventListener("pointerdown", bajar);
        canvas.removeEventListener("pointermove", mover);
        canvas.removeEventListener("pointerup", soltar);
        canvas.removeEventListener("pointercancel", soltar);
        // Libera la memoria de la GPU sin perder el contexto (StrictMode monta dos veces el mismo lienzo)
        if (recursos.tex) gl.deleteTexture(recursos.tex);
        recursos.bufs.forEach((b) => { if (b) gl.deleteBuffer(b); });
        if (recursos.prog) gl.deleteProgram(recursos.prog);
      };
    } catch {
      setSinWebgl(true);
    }
  }, [mapa, segundosPorVuelta]);

  if (sinWebgl) {
    return <div className={className}><img src={respaldo} alt="" style={{ width: "100%", height: "100%", objectFit: "contain" }} /></div>;
  }
  return <canvas ref={lienzo} className={className} aria-hidden="true" style={{ touchAction: "pan-y", cursor: "grab" }} />;
}
