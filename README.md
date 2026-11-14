# ORBIT Health

Apoyo a la decisión clínica para tripulaciones con comunicación degradada. Funciona 100 % local.
Plan completo: [PLAN_DE_DESARROLLO.md](PLAN_DE_DESARROLLO.md).

## Arranque rápido

```bash
cp .env.example .env

# Backend
cd backend && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q

# Frontend (otra terminal)
cd frontend && npm install && npm run dev
```

## Estructura

| Ruta | Contenido |
|---|---|
| `backend/app/` | API FastAPI, motor clínico, cola, base de datos |
| `backend/tests/` | Pruebas pytest |
| `frontend/src/` | React + TypeScript |
| `data/` | Series de calibración y base local (no se versiona) |
| `docs/` | Documentación adicional |
