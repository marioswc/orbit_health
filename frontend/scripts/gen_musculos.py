"""Genera musculos.svg: ilustracion anatomica frontal, estilo vectorial plano con sombreado cilindrico.
Mitad izquierda: torso con caja toracica expuesta; mitad derecha: musculatura. Coordenadas = px del astronauta."""
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "features", "monitor", "assets", "musculos.svg")
X0 = 239.2
TORSO = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "torso_trazado.txt"), encoding="utf-8").read()  # torso calcado de la referencia (scripts/trace_torso.py)
ESC = 0.392; TX = 169.4; TY = 53.0   # escala y posicion del torso calcado sobre el cuerpo del astronauta

def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def fmt(p):
    return "%.1f %.1f" % p

def cubica(P):
    return "M%s C%s %s %s" % (fmt(P[0]), fmt(P[1]), fmt(P[2]), fmt(P[3]))

def curva_t(A, B, t):
    return [lerp(A[k], B[k], t) for k in range(4)]

def banda(A, B, t0, t1, clase):
    P1, P2 = curva_t(A, B, t0), curva_t(A, B, t1)
    return '<path class="%s" d="%s L%s C%s %s %s Z"/>' % (clase, cubica(P1), fmt(P2[3]), fmt(P2[2]), fmt(P2[1]), fmt(P2[0]))

def musculo(A, B, clase="m", fibras=6):
    """Dos bordes (cubicas) -> forma plana + sombra cilindrica + luz + pocas fibras."""
    forma = cubica(A) + " L%s C%s %s %s Z" % (fmt(B[3]), fmt(B[2]), fmt(B[1]), fmt(B[0]))
    s = '<path class="%s" d="%s"/>' % (clase, forma)
    s += banda(A, B, 0.80, 1.0, "sh")      # sombra en el borde lejano
    s += banda(A, B, 0.00, 0.14, "sh2")    # penumbra en el borde cercano
    s += banda(A, B, 0.28, 0.50, "hl")     # luz principal
    s += banda(A, B, 0.34, 0.40, "sp")     # brillo especular
    n = max(2, round(fibras * 0.5))
    for i in range(1, n + 1):
        t = 0.52 + 0.28 * (i / (n + 1))
        s += '<path class="f" d="%s"/>' % cubica(curva_t(A, B, t))
    return s

def pts(*v):
    return [(v[i], v[i + 1]) for i in range(0, 8, 2)]

SIL = ("M239.2 53 C228 53 219 61 218 74 C217 86 220 95 225 101 L226 108 C218 110 208 112 198 115 "
       "C188 119 182 126 180 138 C179 158 181 178 183 193 C178 210 175 232 176 252 C172 262 171 272 172 282 "
       "C171 290 173 296 176 297 C182 298 188 296 192 291 C194 280 193 266 193 255 C196 236 198 214 199 196 "
       "C201 186 203 176 203 166 C208 182 212 198 214 212 C214 224 208 236 205 244 C199 266 199 304 206 340 "
       "C203 366 204 396 211 430 C209 438 210 446 218 446 L234 446 C236 440 233 436 231 430 "
       "C236 398 238 372 236 346 C238 322 238 286 239.2 250 Z")

# ================= comunes a ambas mitades =================
C = ['<path class="b" d="%s"/>' % SIL]
# cuello
C.append(musculo(pts(239.2, 100, 230, 106, 214, 110, 200, 113), pts(239.2, 119, 230, 118, 216, 119, 204, 123), "m2", 8))      # trapecio
C.append(musculo(pts(221, 88, 225, 98, 232, 108, 239.2, 119), pts(226, 87, 231, 97, 236, 107, 240, 118), "m", 4))            # esternocleidomastoideo
C.append('<path class="d" d="M231 102 C233 106 236 108 239.2 109 M229 98 C232 103 235 106 239.2 107"/>')                      # platisma
# hombro: acromion + deltoides en 3 haces
C.append(musculo(pts(203, 115, 196, 116, 190, 124, 188, 137), pts(207, 127, 204, 139, 198, 152, 192, 162), "m", 8))
C.append(musculo(pts(192, 115, 184, 119, 181, 133, 184, 149), pts(188, 137, 187, 145, 188, 153, 192, 162), "m2", 6))
C.append(musculo(pts(199, 114, 192, 114, 186, 120, 183, 130), pts(204, 120, 197, 120, 192, 126, 189, 136), "m3", 4))
C.append('<path class="hueso" d="M206 113 C199 110.5 190 113 185.5 120 L189 124 C193 118.5 199 116 206 117.5 Z"/>')            # acromion
# dorsal ancho (asoma bajo la axila) y oblicuos
C.append(musculo(pts(203, 168, 206, 178, 208, 190, 211, 200), pts(199, 172, 201, 182, 203, 194, 206, 204), "m3", 3))
C.append(musculo(pts(209, 187, 205, 201, 207, 219, 213, 235), pts(222, 185, 221, 199, 223, 215, 228, 233), "m", 9))
C.append('<path class="d" d="M212 190 C216 202 219 216 224 230 M216 188 C219 200 222 212 226 224"/>')
# recto abdominal (cuatro vientres redondeados + intersecciones tendinosas)
for (y0, y1) in [(165, 180), (182.5, 198), (200.5, 216), (218.5, 234)]:
    C.append('<path class="mv" d="M239.2 %.1f L229.6 %.1f C227.8 %.1f 227.8 %.1f 229.6 %.1f L239.2 %.1f Z"/>' % (y0, y0 + 1.5, y0 + 5, y1 - 5, y1 - 0.5, y1))
    C.append('<path class="hl" d="M236.8 %.1f C234.8 %.1f 234.2 %.1f 234.6 %.1f L236.8 %.1f Z"/>' % (y0 + 2, y0 + 5, y1 - 5, y1 - 2.5, y1 - 2))
    C.append('<path class="sh" d="M229.8 %.1f C228.4 %.1f 228.4 %.1f 229.8 %.1f L231.6 %.1f C230.6 %.1f 230.6 %.1f 231.6 %.1f Z"/>' % (y0 + 2, y0 + 6, y1 - 6, y1 - 1, y1 - 1, y1 - 6, y0 + 6, y0 + 2))
    C.append('<path class="t" d="M229.4 %.1f L239.2 %.1f L239.2 %.1f L229.4 %.1f Z"/>' % (y1, y1 - .3, y1 + 2, y1 + 2.4))
C.append('<path class="d" d="M239.2 164 L239.2 238"/>')
C.append('<path class="o" d="M239.2 207.5 C235.8 207.5 234.8 211 236.8 213 C238 214.2 239.2 214 239.2 214 Z"/>')
# ingle, cresta iliaca y ligamento inguinal
C.append('<path class="hueso" d="M205 236 C207 232 213 231 219 234 L218 238 C213 236 209 237 206 241 Z"/>')
C.append(musculo(pts(224, 230, 228, 238, 233, 243, 239.2, 248), pts(229, 226, 232, 233, 236, 237, 239.2, 241), "m2", 3))
C.append('<path class="t" d="M207 240 C220 242 232 246 239.2 252 L239.2 249 C232 243 220 238 207 236 Z"/>')
# brazo
C.append(musculo(pts(186, 137, 180, 153, 180, 173, 183, 193), pts(192, 141, 189, 157, 188, 175, 189, 193), "m2", 6))          # triceps
C.append(musculo(pts(194, 138, 186, 152, 184, 172, 186, 192), pts(202, 143, 207, 157, 205, 177, 197, 195), "m", 10))         # biceps
C.append(musculo(pts(192, 188, 196, 196, 195, 204, 191, 210), pts(187, 190, 190, 198, 189, 204, 187, 208), "m3", 2))         # braquial
C.append('<path class="t" d="M185 193 C189 199 194 199 198 194 L197 201 C193 205 188 205 184 201 Z"/>')                       # tendon del codo
C.append('<g transform="translate(-7.5 -1)">')
C.append(musculo(pts(184, 199, 177, 210, 174, 228, 176, 250), pts(190, 203, 186, 214, 184, 232, 183, 252), "m", 7))          # braquiorradial
C.append(musculo(pts(192, 199, 199, 213, 198, 235, 191, 255), pts(185, 205, 187, 220, 186, 238, 184, 255), "m2", 7))         # flexores
C.append('<path class="t" d="M181 251 L192 253 L191 260 L180 258 Z"/>')
C.append('<path class="d" d="M183 253 L183 259 M186 253.4 L186 259.4 M189 253.8 L189 259.8"/>')
# mano con huesos: palma, metacarpianos, falanges y pulgar
C.append('<path class="piel" d="M179.4 258 C175 263 173.6 271 176 279 L191 281 C193 273 192.2 265 191 260 Z"/>')
C.append('<path class="d" d="M180 266 L179 279 M184 266 L183.6 280 M188 266 L188 281"/>')
for x0, ln in [(176.2, 15), (180.6, 18), (185, 17), (189.2, 13)]:
    for seg in range(3):
        y = 280 + seg * ln / 3.0
        C.append('<rect class="hueso2" x="%.1f" y="%.1f" width="3.3" height="%.1f" rx="1.5"/>' % (x0, y, ln / 3.0 - .5))
C.append('<path class="hueso2" d="M175.4 268 C172 272 171 278 173 284 L176 283 C175.4 279 176 274 177.4 270 Z"/>')   # pulgar
C.append('</g>')
# muslo
C.append(musculo(pts(212, 232, 207, 246, 207, 258, 211, 269), pts(219, 232, 219, 246, 218, 258, 219, 267), "m3", 4))          # tensor fascia lata
C.append(musculo(pts(214, 245, 203, 273, 202, 309, 208, 339), pts(222, 247, 219, 277, 219, 309, 220, 341), "m2", 10))        # vasto lateral
C.append(musculo(pts(222, 242, 228, 272, 229, 310, 227, 340), pts(214, 245, 214, 277, 215, 309, 217, 341), "m", 10))         # recto femoral
C.append(musculo(pts(228, 296, 236, 316, 236, 334, 230, 349), pts(223, 298, 227, 318, 227, 334, 222, 349), "m", 5))          # vasto medial
C.append(musculo(pts(218, 234, 226, 262, 232, 302, 235, 340), pts(223, 232, 231, 260, 237, 300, 239, 338), "m", 4))          # sartorio
C.append(musculo(pts(230, 243, 236, 265, 238, 297, 236, 325), pts(238, 249, 240, 271, 240, 299, 238, 325), "m3", 4))         # aductores / gracil
C.append(musculo(pts(226, 244, 229, 250, 232, 255, 236, 259), pts(228, 240, 231, 246, 234, 251, 238, 255), "m2", 2))         # pectineo
# rodilla
C.append('<path class="t" d="M221 336 L229 336 L230 344 L220 344 Z"/>')
C.append('<path class="hueso" d="M219 347 C223 341.5 229 341.5 232 347 L231 358 C228 362.5 223 362.5 220 358 Z"/>')           # rotula
C.append('<path class="t" d="M222.5 361 L227.5 361 L226.5 373 L223.5 373 Z"/>')
C.append('<path class="d" d="M213 350 C216 354 219 356 221 357 M236 350 C233 354 230 356 229 357"/>')
# pierna
C.append(musculo(pts(211, 359, 203, 381, 205, 407, 214, 427), pts(220, 361, 218, 383, 218, 407, 218, 427), "m2", 8))          # gemelo lateral
C.append(musculo(pts(234, 359, 241, 381, 239, 407, 230, 427), pts(226, 363, 227, 385, 227, 407, 226, 427), "m2", 8))          # gemelo medial
C.append(musculo(pts(225, 373, 229, 393, 228, 411, 224, 429), pts(218, 373, 217, 393, 218, 411, 219, 429), "m", 8))          # tibial anterior
C.append(musculo(pts(210, 373, 207, 393, 209, 411, 214, 425), pts(217, 374, 215, 394, 216, 411, 217, 425), "m3", 4))         # peroneos
C.append(musculo(pts(227, 380, 231, 396, 230, 412, 227, 428), pts(224, 384, 226, 399, 225, 413, 224, 428), "m3", 2))         # sóleo / extensor largo
# tobillo y pie con huesos
C.append('<path class="t" d="M216 428 L229 428 L230 437 L215 437 Z"/>')
C.append('<path class="piel" d="M213.5 437 C211 443 213.5 446.5 222 446.5 L233 446.5 C236 443 234 439 231 437 Z"/>')
for k in range(5):
    x = 214.5 + k * 3.7
    C.append('<path class="hueso2" d="M%.1f 438 L%.1f 438 L%.1f 446 L%.1f 446 Z"/>' % (x, x + 2.6, x + 2.4, x + 0.2))

# ================= pecho con musculo (mitad derecha del dibujo) =================
PEC = []
PEC.append(musculo(pts(239.2, 132, 228, 133, 216, 137, 207, 144), pts(239.2, 165, 228, 168, 216, 166, 209, 157), "m", 14))   # haz esternocostal
PEC.append(musculo(pts(238.6, 119.5, 226, 118.5, 213, 121.5, 204, 128.5), pts(239.2, 133, 227, 132, 215, 135, 206, 142), "m2", 8)) # haz clavicular
PEC.append(musculo(pts(239.2, 150, 230, 152, 220, 154, 211, 152), pts(239.2, 168, 230, 169, 221, 167, 213, 162), "m3", 4))        # haz abdominal
for k in range(7):                                                                                                             # abanico de fibras
    t = k / 6.0
    PEC.append('<path class="f" d="M238 %.1f C228 %.1f 218 %.1f 208 %.1f"/>' % (126 + t * 36, 127 + t * 36, 131 + t * 30, 137 + t * 22))
PEC.append('<path class="d" d="M239.2 120 L239.2 166 M204 128 C201 138 203 150 209 160"/>')
for k in range(5):
    y = 162 + k * 7.4
    PEC.append(musculo(pts(210, y, 212, y + 1, 215, y + 2, 219, y + 3), pts(209, y + 6, 211, y + 7, 214, y + 8, 218, y + 9), "m3", 2))
PEC.append('<path class="hueso" d="M239.2 116.5 C228 114.5 214 115.5 203 120.5 L204 125.5 C215 121 228 120.5 239.2 123 Z"/>')
PEC.append('<path class="hueso" d="M239.2 123 L236.6 123.6 L237 160 L239.2 167 Z"/>')

# ================= caja toracica expuesta (mitad izquierda) =================
RIB = []
RIB.append('<path class="hueso" d="M239.2 116.5 C230 113 220 111.5 212 113.5 C206 115 202 118 200 121 L202.5 125.5 C206 121 212 119 218 119 C226 119 233 121.5 239.2 123.6 Z"/>')   # clavicula en S
RIB.append('<path class="hueso" d="M239.2 123 L235 124 C234 128 236 134 236 140 L236.6 160 L239.2 170 Z"/>')                                                                          # manubrio + esternon
RIB.append('<path class="hueso" d="M236 160 L239.2 168 L239.2 175 L236.6 168 Z"/>')                                                                                                      # xifoides
for i in range(8):
    y = 126 + i * 8.7
    d1 = "M236.6 %.1f C233 %.1f 230 %.1f 226 %.1f" % (y, y, y, y + 1.6 + i * .15)                       # cartilago costal
    d2 = "M226 %.1f C219 %.1f 211 %.1f 206 %.1f C203.6 %.1f 203.4 %.1f 204.6 %.1f" % (y + 1.6 + i * .15, y + 2, y + 4 + i * .5, y + 9 + i * .9, y + 12 + i * 1.1, y + 16 + i * 1.2, y + 21 + i)
    RIB.append('<path class="costilla-borde" d="%s"/><path class="costilla-borde" d="%s"/>' % (d1, d2))
    RIB.append('<path class="cartilago" d="%s"/><path class="costilla" d="%s"/>' % (d1, d2))
RIB.append(musculo(pts(204, 168, 201, 178, 202, 190, 206, 202), pts(209, 166, 207, 177, 208, 189, 210, 202), "m3", 3))     # restos de serrato

# ================= craneo =================
CRANEO = """
<path class="hueso" d="M239.2 52 C227 52 218 60 217 73 C216 80 217.5 86 220 90 C220.5 93 222 95 224 96 L224.5 100 C227 103 231 105 235 105.5 L239.2 106 Z"/>
<path class="sh" d="M217 73 C216 80 217.5 86 220 90 L222.5 88 C220.5 84 219.6 79 220.4 73 Z"/>
<path class="hl2" d="M226 56 C231 53.5 236 53.5 239.2 54 L239.2 60 C235 58.5 230 59 226 62 Z"/>
<path class="d" d="M221 66 C224 62 229 60 235 60.5 M219 72 C220 68 222 65.6 224 64"/>
<path class="d" d="M220 86 C223 90.4 228 92.2 233 91 M221.5 82 C222.5 85 224 87 226 88.4"/>
<path class="o" d="M224.5 74 C227 71.6 232 71.6 235 74.4 C236 77 235.4 81 233 82.6 C230 84.2 226.4 83.4 224.8 81 C224 78.5 224 76.2 224.5 74 Z"/>
<path class="blanco" d="M226.4 73.6 C228.6 72.6 231.6 72.8 233.4 74 L233 75 C231 74 228.4 73.8 226.6 74.6 Z" opacity=".55"/>
<path class="o" d="M239.2 82 C237 83 235.8 86 236.4 90 C237 92 238.2 92.6 239.2 92.6 Z"/>
<path class="d" d="M239.2 70 C237.6 74 237 78 237.6 82"/>
<path class="blanco" d="M231 96.2 L233.4 96.2 L233.4 100.2 C232.2 100.8 231.6 100.6 231 100 Z M233.8 96.2 L236.2 96.2 L236.2 100.4 C235 101 234.4 100.8 233.8 100.2 Z M236.6 96.2 L239.2 96.2 L239.2 100.6 C238 101.2 237.4 101 236.6 100.4 Z"/>
<path class="blanco" d="M231.6 101 L233.6 101 L233.6 104 L231.6 104 Z M234 101.2 L236.2 101.2 L236.2 104.2 L234 104.2 Z M236.6 101.4 L239.2 101.4 L239.2 104.4 L236.6 104.4 Z"/>
<path class="hueso" d="M221.6 93.6 C222.2 101 226 106.6 232 108.6 C235 109.6 237.4 109.9 239.2 110 L239.2 105 C234 104.8 230.4 102.4 228 99 Z"/>
<path class="d" d="M223 96 C224 101 227 105 232 107"/>
"""

# antebrazo y mano: se dibujan fuera del recorte de la silueta para poder desplazarlos hacia el brazo calcado
i0 = C.index('<g transform="translate(-7.5 -1)">'); i1 = C.index('</g>', i0)
FORE = C[i0:i1 + 1]; del C[i0:i1 + 1]
FORE.insert(1, '<path class="b" d="M184 196 C177 214 175 236 176 252 L192 254 C197 236 198 214 197 194 Z"/>')
FOREJ = ''.join(FORE)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="129.25 21.5 215.25 430.75">
<defs>
  <linearGradient id="gm" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#b1303a"/><stop offset=".5" stop-color="#e5504f"/><stop offset="1" stop-color="#bb363e"/></linearGradient>
  <linearGradient id="gm2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#9d2832"/><stop offset=".55" stop-color="#d04447"/><stop offset="1" stop-color="#aa2f38"/></linearGradient>
  <linearGradient id="gm3" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8e2230"/><stop offset=".5" stop-color="#bb3a42"/><stop offset="1" stop-color="#97262f"/></linearGradient>
  <linearGradient id="gv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b8343c"/><stop offset=".5" stop-color="#e95c56"/><stop offset="1" stop-color="#b8343c"/></linearGradient>
  <filter id="bl" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2"/></filter>
  <clipPath id="inferior"><rect x="129" y="176" width="216" height="282"/></clipPath>
  <clipPath id="sil"><path d="{SIL}"/></clipPath>
  <style>
    .m{{fill:url(#gm);stroke:#821f27;stroke-width:.9;stroke-linejoin:round}}
    .m2{{fill:url(#gm2);stroke:#821f27;stroke-width:.9;stroke-linejoin:round}}
    .m3{{fill:url(#gm3);stroke:#821f27;stroke-width:.9;stroke-linejoin:round}}
    .mv{{fill:url(#gv);stroke:#821f27;stroke-width:.9;stroke-linejoin:round}}
    .hl{{fill:#f89a8e;opacity:.5;stroke:none}}
    .sp{{fill:#fff;opacity:.28;stroke:none}}
    .hl2{{fill:#fff;opacity:.5;stroke:none}}
    .sh{{fill:#4a0c14;opacity:.34;stroke:none}}
    .sh2{{fill:#4a0c14;opacity:.16;stroke:none}}
    .f{{fill:none;stroke:#fdc0b6;stroke-width:.65;opacity:.65;stroke-linecap:round}}
    .f2{{fill:none;stroke:#fff;stroke-width:.8;opacity:.6;stroke-linecap:round}}
    .d{{fill:none;stroke:#6d141b;stroke-width:.6;opacity:.7;stroke-linecap:round}}
    .t{{fill:#f7e9d6;stroke:#b48c70;stroke-width:.7;stroke-linejoin:round}}
    .piel{{fill:#efd5bb;stroke:#b48c70;stroke-width:.7;stroke-linejoin:round}}
    .hueso{{fill:#f7e9d6;stroke:#a97f64;stroke-width:.9;stroke-linejoin:round}}
    .hueso2{{fill:#faf0e1;stroke:#a97f64;stroke-width:.55;stroke-linejoin:round}}
    .blanco{{fill:#fffaf1;stroke:#a97f64;stroke-width:.5}}
    .costilla{{fill:none;stroke:#f7e9d6;stroke-width:3.2;stroke-linecap:round}}
    .cartilago{{fill:none;stroke:#fbf3e6;stroke-width:3.2;stroke-linecap:round}}
    .costilla-borde{{fill:none;stroke:#a97f64;stroke-width:4.7;stroke-linecap:round}}
    .o{{fill:#4f161b;stroke:none}}
    .b{{fill:#8c2229;stroke:#6d141b;stroke-width:.9;stroke-linejoin:round}}
    .sombra{{fill:none;stroke:#4a0c14;stroke-width:6;opacity:.3}}
  </style>
</defs>
<g clip-path="url(#inferior)">
<g id="comun">
  <g clip-path="url(#sil)">{"".join(C)}<path class="sombra" d="{SIL}" filter="url(#bl)"/></g>
  {FOREJ}
  <path d="{SIL}" fill="none" stroke="#6d141b" stroke-width="1.1" stroke-linejoin="round"/>
</g>
<g id="mus"><use href="#comun"/><g clip-path="url(#sil)">{"".join(PEC)}</g></g>
<g id="cos"><use href="#comun"/><g clip-path="url(#sil)">{"".join(RIB)}</g></g>
<use href="#cos"/>
<use href="#mus" transform="matrix(-1 0 0 1 478.4 0)"/>
<g id="craneo-izq">{CRANEO}</g>
<use href="#craneo-izq" transform="matrix(-1 0 0 1 478.4 0)"/>
</g>
<g transform="translate({TX} {TY}) scale({ESC})">{TORSO}</g>
</svg>'''
open(OUT, "w", encoding="utf-8").write(svg)
print(len(svg) // 1024, "KB")
