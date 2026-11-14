"""Prepara la capa de musculos a partir de "Muscles front and back.svg" (OpenStax / Tomas Kebert / umimeto.org, CC BY-SA 4.0).

- Recorta la vista frontal (la espalda queda fuera del viewBox).
- Quita metadatos de Inkscape para aligerar el archivo; no toca la geometria ni los ids.
Uso: python scripts/preparar_musculos.py [entrada.svg]
"""
import os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "Muscles_front_and_back.original.svg")
SALIDA = os.path.join(AQUI, "..", "src", "features", "monitor", "assets", "musculos.svg")

s = open(ENTRADA, encoding="utf-8").read()
s = re.sub(r"<\?xml.*?\?>", "", s)
s = re.sub(r"<metadata.*?</metadata>", "", s, flags=re.S)
s = re.sub(r"<sodipodi:namedview.*?/>", "", s, flags=re.S)
s = re.sub(r"<inkscape:path-effect.*?/>", "", s, flags=re.S)
s = re.sub(r'\s(inkscape|sodipodi):[\w-]+="[^"]*"', "", s)
s = re.sub(r'\sxmlns:(inkscape|sodipodi|dc|cc|rdf)="[^"]*"', "", s)
s = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r"\1", s, count=1)
s = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r"\1", s, count=1)
s = re.sub(r'viewBox="[^"]*"', 'viewBox="8 8 190 340"', s, count=1)  # solo la figura frontal
open(SALIDA, "w", encoding="utf-8").write(s)
print("musculos.svg:", len(s) // 1024, "KB")
