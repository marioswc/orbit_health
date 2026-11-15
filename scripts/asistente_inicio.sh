#!/usr/bin/env bash
# Asistente de inicio, para quien no sabe nada: te explica, te pregunta y lo deja funcionando. Responde con Enter para
# aceptar lo recomendado. Necesita internet SOLO para instalar; después ORBIT Health funciona sin red.
# Uso: scripts/asistente_inicio.sh [--en] [--sin-preguntas] [--simular]
#   --en              mensajes en inglés          --sin-preguntas  acepta lo recomendado (prepara y no arranca)
#   --simular         muestra qué haría, sin instalar ni cambiar nada
set -uo pipefail
cd "$(dirname "$0")/.."
EN=0; AUTO=0; SIM=0
for a in "$@"; do case "$a" in --en) EN=1;; --sin-preguntas) AUTO=1;; --simular) SIM=1;; esac; done
m() { if [ "$EN" = 1 ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }
pregunta() {  # pregunta "texto es" "text en" defecto(s|n)  -> código 0 si sí
  local def="${3:-n}" r
  if [ "$AUTO" = 1 ]; then r="$def"; else
    printf '%s ' "$( [ "$EN" = 1 ] && echo "$2" || echo "$1" ) [$( [ "$def" = s ] && echo 'S/n' || echo 's/N' )]"; read -r r || r=""
    [ -z "$r" ] && r="$def"; fi
  case "$r" in s|S|y|Y|si|sí|yes) return 0;; *) return 1;; esac
}
hacer() { if [ "$SIM" = 1 ]; then echo "   (simulación) $*"; else "$@"; fi; }

echo; m "=== ORBIT Health: asistente de inicio ===" "=== ORBIT Health: setup assistant ==="
m "ORBIT Health es un apoyo para la salud y el bienestar de una tripulación lejos de la Tierra, sin internet y sin médico a bordo." \
  "ORBIT Health supports the health and wellbeing of a crew far from Earth, with no internet and no doctor on board."
m "Todo en esta demostración es SIMULADO y es un prototipo: no sustituye a un médico." "Everything in this demo is SIMULATED and a prototype: it does not replace a doctor."
echo

echo "1) $( [ "$EN" = 1 ] && echo 'Checking your computer' || echo 'Revisando tu computadora' )"
faltan=0
for c in python3 node npm; do
  if command -v "$c" >/dev/null; then echo "   ✔ $c"; else echo "   ✘ $c"; faltan=1; fi
done
if [ "$faltan" = 1 ]; then
  m "   Falta algo. En Ubuntu/Debian:  sudo apt install python3 python3-venv nodejs npm   (en Mac: brew install python node)" \
    "   Something is missing. On Ubuntu/Debian:  sudo apt install python3 python3-venv nodejs npm   (Mac: brew install python node)"
  [ "$SIM" = 1 ] || exit 1
fi

echo; echo "2) $( [ "$EN" = 1 ] && echo 'Preparing ORBIT Health (needs internet once)' || echo 'Preparando ORBIT Health (necesita internet una vez)' )"
if [ -x backend/.venv/bin/python ] && [ -f frontend/dist/index.html ]; then
  m "   Ya estaba preparado." "   Already prepared."
elif pregunta "   ¿Lo preparo ahora? (tarda unos minutos)" "   Prepare it now? (takes a few minutes)" s; then
  hacer scripts/preparar.sh || { m "   No se pudo preparar. Revisa el mensaje de arriba." "   Setup failed. Check the message above."; exit 1; }
else
  m "   Entendido. Luego puedes correr scripts/preparar.sh." "   OK. You can run scripts/preparar.sh later."; exit 0
fi
[ -f .env ] || [ "$SIM" = 1 ] || cp .env.example .env

echo; echo "3) $( [ "$EN" = 1 ] && echo 'Login with PIN' || echo 'Acceso con PIN' )"
if pregunta "   ¿Quieres entrar con cuentas de ejemplo y PIN (como en una nave real)?" "   Do you want accounts with PINs (like a real ship)?" n; then
  hacer backend/.venv/bin/python scripts/poner_env.py ORBIT_AUTH 1
  hacer scripts/cuentas_demo.sh
  m "   Entra como T3 con el PIN 333333 (comandante: T1 con 111111). Son cuentas DE DEMOSTRACIÓN." \
    "   Sign in as T3 with PIN 333333 (commander: T1 with 111111). These are DEMO accounts."
else
  hacer backend/.venv/bin/python scripts/poner_env.py ORBIT_AUTH 0
  m "   Sin PIN: entras directo (solo para probar en tu equipo)." "   No PIN: you go straight in (only for testing on your own computer)."
fi

echo; echo "4) $( [ "$EN" = 1 ] && echo 'AI assistant "Nova"' || echo 'Asistente con IA "Nova"' )"
m "   Sin IA generativa, Nova igual te saluda y te guía con textos escritos. Puedes añadir IA así:" \
  "   Without generative AI, Nova still greets you and guides you with written texts. You can add AI like this:"
m "     1) Local, sin internet (privada; descarga ~2.5 GB; modelo pequeño)   2) En la nube con DeepSeek (tu clave; los textos SALEN de tu equipo)   3) Ninguna" \
  "     1) Local, no internet (private; ~2.5 GB download; small model)   2) Cloud with DeepSeek (your key; text LEAVES your computer)   3) None"
if [ "$AUTO" = 1 ]; then op=3; else printf '   [1/2/3, Enter=3] '; read -r op || op=3; fi
case "${op:-3}" in
  1) hacer scripts/instalar_ia_local.sh
     hacer backend/.venv/bin/python scripts/poner_env.py ORBIT_IA_PROVEEDOR local
     hacer backend/.venv/bin/python scripts/poner_env.py ORBIT_IA_LOCAL_MODELO qwen2.5:1.5b
     m "   Falta bajar el modelo: ~/.local/ollama/bin/ollama pull qwen2.5:1.5b  (con 'ollama serve' corriendo). Detalle en docs/IA_LOCAL.md." \
       "   Still to do: ~/.local/ollama/bin/ollama pull qwen2.5:1.5b  (with 'ollama serve' running). Details in docs/IA_LOCAL.md.";;
  2) m "   Pega tu clave de DeepSeek (no se verá al escribir ni se guarda en el historial):" "   Paste your DeepSeek key (hidden while typing, kept out of shell history):"
     if [ "$SIM" = 1 ]; then echo "   (simulación) se guardaría en .env con permisos 600"; else
       read -rs clave; echo
       if [ -n "$clave" ]; then printf '%s\n' "$clave" | backend/.venv/bin/python scripts/poner_env.py ORBIT_DEEPSEEK_API_KEY - && backend/.venv/bin/python scripts/poner_env.py ORBIT_IA_PROVEEDOR automatico
       else m "   Sin clave: se queda sin IA en la nube." "   No key: staying without cloud AI."; fi; fi
     m "   Ojo: con la nube, tu pregunta sale de la estación (Nova lo avisa en cada respuesta). Tu perfil nunca sale." \
       "   Note: with the cloud, your question leaves the station (Nova says so on every reply). Your profile never leaves.";;
  *) m "   Sin IA generativa: perfecto para empezar." "   No generative AI: perfect to start.";;
esac

echo; echo "5) $( [ "$EN" = 1 ] && echo 'Voice' || echo 'Voz' )"
if pregunta "   ¿Quieres hablar con Nova por voz, sin internet? (descarga ~0.6 GB)" "   Do you want to talk to Nova by voice, offline? (~0.6 GB download)" n; then
  hacer scripts/instalar_voz_local.sh
  for kv in "ORBIT_VOZ_ACTIVA 1" "ORBIT_VOZ_STT_MODELO ./models/whisper-small" "ORBIT_VOZ_PIPER_BIN ./.venv/bin/piper" \
            "ORBIT_VOZ_PIPER_MODELO ./models/es_MX-claude-high.onnx" "ORBIT_VOZ_PIPER_MODELO_EN ./models/en_US-lessac-medium.onnx"; do
    # shellcheck disable=SC2086
    hacer backend/.venv/bin/python scripts/poner_env.py $kv
  done
else
  m "   Sin voz: Nova funciona por texto." "   No voice: Nova works by text."
fi

echo; echo "6) $( [ "$EN" = 1 ] && echo 'Start' || echo 'Arrancar' )"
if pregunta "   ¿Arranco ORBIT Health ahora y abro el navegador?" "   Start ORBIT Health now and open the browser?" "$( [ "$AUTO" = 1 ] && echo n || echo s )"; then
  url="http://127.0.0.1:3000"
  m "   Abriendo $url  (para detenerlo, pulsa Ctrl+C aquí)." "   Opening $url  (press Ctrl+C here to stop it)."
  if [ "$SIM" = 1 ]; then echo "   (simulación) ./run.sh"; exit 0; fi
  ( sleep 4; command -v xdg-open >/dev/null && xdg-open "$url" >/dev/null 2>&1 || command -v open >/dev/null && open "$url" >/dev/null 2>&1 || true ) &
  exec ./run.sh
fi
echo; m "Listo. Cuando quieras arrancar:  ./run.sh   y abre  http://127.0.0.1:3000" "Done. To start any time:  ./run.sh   and open  http://127.0.0.1:3000"
