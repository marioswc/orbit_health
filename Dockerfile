# ORBIT Health en un contenedor: interfaz compilada + API en un solo proceso, sin dependencias en la máquina anfitriona.
# Construir:  docker build -t orbit-health .      Correr:  docker run -p 127.0.0.1:3000:3000 -v orbit-data:/app/data orbit-health
# Con docker compose (o ./run.sh --docker): conecta con el Ollama del anfitrión (host.docker.internal) y monta backend/models para voz local.

FROM node:22-slim AS interfaz
WORKDIR /w
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ORBIT_PRECALENTAR=0
WORKDIR /app
COPY backend/requirements.txt backend/requirements-voice.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt && \
    (pip install --no-cache-dir -r backend/requirements-voice.txt || echo "Aviso: librerías opcionales de voz no instaladas")
COPY backend/app backend/app
COPY scripts scripts
COPY docs docs
COPY README.md README.es.md .env.example ./
COPY --from=interfaz /w/dist frontend/dist
RUN useradd --create-home --uid 10001 orbit && mkdir -p /app/data /app/backend/models && chown -R orbit:orbit /app/data /app/backend/models
USER orbit
WORKDIR /app/backend
EXPOSE 3000
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:3000/api/salud', timeout=4)" || exit 1
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
