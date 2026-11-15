#!/usr/bin/env python3
"""Genera los iconos de la app instalable (PWA) con un dibujo propio (órbita y planeta), creado para este proyecto.
Uso: python3 scripts/generar_iconos.py     (necesita Pillow; solo hace falta al regenerarlos: los PNG ya están en el repo)"""
from pathlib import Path

from PIL import Image, ImageDraw

SALIDA = Path(__file__).resolve().parents[1] / "frontend" / "public"
FONDO, ANILLO, PUNTO, LUNA = (11, 16, 32), (94, 234, 212), (94, 234, 212), (248, 250, 252)
SS = 4                                                   # supersampling para bordes suaves


def dibujar(lado: int, escala: float = 1.0, redondeado: bool = False) -> Image.Image:
    n = lado * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if redondeado:
        d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * 0.22), fill=FONDO)
    else:
        d.rectangle([0, 0, n, n], fill=FONDO)             # maskable / apple: el sistema recorta las esquinas
    c = n / 2
    r = n * 0.26 * escala
    grosor = max(2, int(n * 0.055 * escala))
    d.ellipse([c - r, c - r, c + r, c + r], outline=ANILLO, width=grosor)
    rp = n * 0.085 * escala
    d.ellipse([c - rp, c - rp, c + rp, c + rp], fill=PUNTO)
    rl = n * 0.045 * escala
    lx, ly = c + r * 0.92, c - r * 0.38
    d.ellipse([lx - rl, ly - rl, lx + rl, ly + rl], fill=LUNA)
    return img.resize((lado, lado), Image.LANCZOS)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    dibujar(192, redondeado=True).save(SALIDA / "icono-192.png")
    dibujar(512, redondeado=True).save(SALIDA / "icono-512.png")
    dibujar(512, escala=0.8).save(SALIDA / "icono-maskable-512.png")      # contenido dentro de la zona segura (80 %)
    dibujar(180, escala=0.9).convert("RGB").save(SALIDA / "apple-touch-icon.png")
    emp = SALIDA.parents[1] / "empaquetado"                           # iconos del ejecutable (Windows y Mac)
    emp.mkdir(exist_ok=True)
    base = dibujar(1024, redondeado=True)
    base.save(emp / "orbit.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    base.save(emp / "orbit.icns")
    print("Iconos generados en", SALIDA, "y", emp)


if __name__ == "__main__":
    main()
