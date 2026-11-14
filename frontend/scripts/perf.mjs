// Presupuesto de peso: falla (exit 1) si el build crece mas alla de los limites.
// Uso: pnpm perf   (compila y mide). Se mide lo que descarga la primera carga y cada vista diferida.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const dist = join(dirname(fileURLToPath(import.meta.url)), "..", "dist");
const KB = 1024;
// Limites en KB comprimidos (gzip). Supuesto del equipo: pensados para equipos y enlaces modestos.
const PRESUPUESTO = { jsInicial: 70, cssInicial: 16, vistaDiferida: 15, svgMax: 260 };

const gz = (ruta) => gzipSync(readFileSync(ruta), { level: 9 }).length;
const html = readFileSync(join(dist, "index.html"), "utf8");
const iniciales = [...html.matchAll(/(?:src|href)="\/(assets\/[^"]+\.(?:js|css))"/g)].map((m) => m[1]);
const todos = readdirSync(join(dist, "assets"));

const filas = [];
let fallos = 0;
function medir(nombre, bytesGz, limiteKb) {
  const kb = bytesGz / KB;
  const ok = kb <= limiteKb;
  if (!ok) fallos += 1;
  filas.push(`${ok ? "OK " : "XX "} ${nombre.padEnd(34)} ${kb.toFixed(1).padStart(7)} KB gz   (limite ${limiteKb} KB)`);
}

const js = iniciales.filter((f) => f.endsWith(".js"));
const css = iniciales.filter((f) => f.endsWith(".css"));
medir(`JS inicial (${js.length} archivos)`, js.reduce((t, f) => t + gz(join(dist, f)), 0), PRESUPUESTO.jsInicial);
medir(`CSS inicial (${css.length} archivos)`, css.reduce((t, f) => t + gz(join(dist, f)), 0), PRESUPUESTO.cssInicial);
for (const f of todos.filter((f) => f.endsWith(".js") && !iniciales.includes(`assets/${f}`))) {
  medir(`vista diferida ${f.split("-")[0]}`, gz(join(dist, "assets", f)), PRESUPUESTO.vistaDiferida);
}
for (const f of todos.filter((f) => f.endsWith(".svg"))) medir(`imagen ${f.split("-")[0]}.svg`, gz(join(dist, "assets", f)), PRESUPUESTO.svgMax);

const total = todos.reduce((t, f) => t + statSync(join(dist, "assets", f)).size, 0);
console.log(filas.join("\n"));
console.log(`\nTotal en disco (sin comprimir): ${(total / KB / KB).toFixed(2)} MB en ${todos.length} archivos`);
if (fallos) { console.error(`\n${fallos} limite(s) superado(s). Revisa las dependencias o divide el codigo.`); process.exit(1); }
console.log("Presupuesto cumplido.");
