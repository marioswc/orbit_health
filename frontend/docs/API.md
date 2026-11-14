# API consumida por el frontend

Base: `/api` (proxy de Vite a `http://localhost:8000`). Fuente: `backend/app/main.py`. Tipos: `src/api/tipos.ts`.

| Método | Ruta | Feature | Devuelve / uso |
|---|---|---|---|
| GET | `/api/health` | app | Salud del servidor |
| GET | `/api/umbrales` | app | `{version, estado}` — el frontend muestra aviso si no está "validado" |
| GET | `/api/indicadores` | mediciones | Definición de indicadores (`clave`, `etiqueta`, `unidad`, `min`, `max`) |
| GET | `/api/tripulantes` | tripulantes | Lista de tripulantes |
| POST | `/api/lecturas` | mediciones | Registra lectura; devuelve nivel, puntos NEWS2, prioridad |
| GET | `/api/estado/{tid}` | monitor | Estado por indicador, NEWS2 y nivel general |
| POST/GET | `/api/diario`, `/api/diario/{tid}` | bienestar | Diario privado (no entra a la cola a Tierra) |
| POST | `/api/tamizajes` | bienestar | PHQ-2; devuelve total, positivo y cápsulas |
| GET/POST | `/api/enlace` | enlace | Estado/cambio de enlace y entorno (modo Eclipse) |
| GET | `/api/cola` | enlace | Cola hacia la Tierra con resumen por prioridad |
| GET | `/api/cola/verificar` | enlace | Verificación de la cadena de hashes |

## Notas

- El backend **no expone el concepto de "zona corporal"**: el mapeo indicador → zona vive en el frontend (ver [FIGURA_HUMANA.md](./FIGURA_HUMANA.md)).
- No hay WebSocket en el backend actual; el estado se refresca por petición.
- Verificar esta tabla contra `main.py` al cambiar rutas.
