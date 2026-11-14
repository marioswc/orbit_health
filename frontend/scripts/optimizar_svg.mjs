// Optimiza los SVG de src/features/monitor/assets (menos bytes = carga y pintado mas rapidos).
// Uso: pnpm optimizar:svg
import { readdirSync, readFileSync, writeFileSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { optimize } from "svgo";

const carpeta = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "features", "monitor", "assets");
const precision = { "astronauta.svg": 1, "esqueleto.svg": 1, "organos.svg": 1, "musculos.svg": 1 };

for (const nombre of readdirSync(carpeta).filter((f) => f.endsWith(".svg"))) {
  const ruta = join(carpeta, nombre);
  const antes = statSync(ruta).size;
  // Limpia restos de Inkscape (elementos/atributos con prefijo sin declarar) antes de optimizar
  const limpio = readFileSync(ruta, "utf8")
    .replace(/<(inkscape|sodipodi):[^>]*\/>/g, "")
    .replace(/\s(inkscape|sodipodi):[\w-]+="[^"]*"/g, "");
  const { data } = optimize(limpio, {
    path: ruta,
    multipass: true,
    floatPrecision: precision[nombre] ?? 2,
    plugins: [{ name: "preset-default", params: { overrides: { removeViewBox: false } } }],
  });
  writeFileSync(ruta, data);
  const despues = statSync(ruta).size;
  console.log(`${nombre}: ${(antes / 1024).toFixed(0)} KB -> ${(despues / 1024).toFixed(0)} KB`);
}
