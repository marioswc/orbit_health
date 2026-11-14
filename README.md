# ORBIT Health

Apoyo a la decisión clínica para tripulaciones con comunicación degradada. Funciona 100 % local.
Plan completo: [PLAN_DE_DESARROLLO.md](PLAN_DE_DESARROLLO.md).

## Producción local (un solo servidor, sin internet)

```bash
cp .env.example .env
cd frontend && npm install && npm run build && cd ..
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
set -a; . ../.env; set +a
uvicorn app.main:app --port 3000      # sirve API y frontend en http://localhost:3000
```

## Desarrollo

```bash
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev            # http://localhost:3000, proxy /api → :8000
cd backend && pytest -q
```

## Prueba offline (checklist manual)

1. Construir el frontend y arrancar el servidor como arriba.
2. Desactivar Wi-Fi y Ethernet.
3. Abrir `http://localhost:3000`; en Monitor registrar SpO₂ 88 (debe salir rojo, prioridad 1).
4. En Enlace activar Modo Eclipse, registrar una lectura normal y otra crítica: quedan retenidas.
5. Escribir una nota en Bienestar y responder el PHQ-2: no aparecen en la cola.
6. Volver a Enlace normal: la prioridad 1 sale primero. Pulsar "Verificar cadena de hash".

Verificado automáticamente: el build no referencia recursos remotos (solo cadenas internas de React),
y el flujo anterior pasa por API contra un servidor único.

## Variables de entorno

Ver `.env.example`. Umbrales marcados como *Supuesto* en el plan requieren validación médica.

## Estructura

| Ruta | Contenido |
|---|---|
| `backend/app/` | API FastAPI, motor clínico, cola, base de datos |
| `backend/tests/` | Pruebas pytest |
| `frontend/src/` | React + TypeScript |
| `data/` | Base local (no se versiona) |
