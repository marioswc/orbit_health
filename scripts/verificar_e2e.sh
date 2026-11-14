#!/usr/bin/env bash
# Verificación E2E automática contra una base temporal. Uso: scripts/verificar_e2e.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TMP="$(mktemp -d)"; PUERTO=3917; B="http://127.0.0.1:$PUERTO"
trap 'kill "$PID" 2>/dev/null || true; rm -rf "$TMP"' EXIT
ORBIT_DB_PATH="$TMP/e2e.db" ORBIT_DIR_RESPALDOS="$TMP/resp" backend/.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $PUERTO >"$TMP/log" 2>&1 &
PID=$!
for _ in $(seq 30); do curl -sf "$B/api/health" >/dev/null && break; sleep 0.3; done
j() { curl -sf -XPOST "$B$1" -H 'content-type: application/json' -d "$2"; }
fallo() { echo "FALLO: $1"; exit 1; }
curl -sf "$B/" | grep -q "ORBIT Health" || fallo "frontend no servido"
j /api/enlace '{"activo":false,"entorno":"marte"}' >/dev/null
j /api/lecturas '{"tripulante_id":"T1","indicador":"temperatura","valor":36.8}' >/dev/null
j /api/lecturas '{"tripulante_id":"T1","indicador":"spo2","valor":88}' | grep -q '"prioridad":1' || fallo "hipoxia no es prioridad 1"
j /api/diario '{"tripulante_id":"T1","contenido":"x"}' | grep -q '"transmitido_tierra":false' || fallo "diario"
[ "$(curl -sf $B/api/cola | grep -o '"estado":"retenido"' | wc -l)" -eq 2 ] || fallo "eclipse no retuvo (o diario entró a cola)"
j /api/enlace '{"activo":true,"entorno":"marte"}' | grep -Eq '"prioridad":1.*"prioridad":3' || fallo "orden de despacho"
curl -sf "$B/api/cola/verificar" | grep -q '"valida":true' || fallo "cadena de hash"
curl -sf "$B/api/salud" | grep -q '"base_ok":true' || fallo "salud de la base"
[ -n "$(ls "$TMP"/resp/orbit_health_*.db 2>/dev/null)" ] || fallo "no se hizo el respaldo inicial"
echo "E2E OK"
