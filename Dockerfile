# ORBIT Health en un contenedor: interfaz compilada + API en un solo proceso, sin dependencias en la máquina anfitriona.
#
#   Ligera (~180 MB, solo textos escritos):  docker build -t orbit-health .
#   Voz con modelos montados desde tu carpeta:  --build-arg CON_VOZ=libs   (instala las librerías; los modelos van en ./backend/models, que
#                                               docker-compose.yml monta en modo lectura; así es como lo usa `docker compose` y ./run.sh --docker)
#   IA y voz COMPLETAS dentro de la imagen:   docker build -t orbit-health:completa --build-arg CON_IA=1 --build-arg CON_VOZ=1 .   (~2.5 GB, necesita internet al construir)
#   Correr:  docker run -p 127.0.0.1:3000:3000 -v orbit-data:/app/data orbit-health
#
# CON_VOZ: 0 = nada | libs = solo las librerías | 1 = librerías y modelos dentro de la imagen.   CON_IA: 0 | 1 = motor y modelo de IA dentro.
# Con Ollama en tu computadora (no dentro de la imagen): docker-compose.yml añade host.docker.internal y el programa traduce 127.0.0.1 a ese nombre.
# Las variables se pasan con -e, --env-file o env_file (docker-compose.yml): el arranque las normaliza y avisa si alguna está mal escrita.

FROM node:22-slim AS interfaz
WORKDIR /w
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ARG CON_IA=0
ARG CON_VOZ=0
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ORBIT_PUERTO=3000
WORKDIR /app
COPY backend/requirements.txt backend/requirements-ia.txt backend/requirements-voice.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
# Opcionales: el motor de IA incrustado (rueda precompilada de llama.cpp) y las librerías de voz.
RUN if [ "$CON_IA" = "1" ]; then pip install --no-cache-dir -r backend/requirements-ia.txt --only-binary=:all: \
        --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu; fi
RUN if [ "$CON_VOZ" = "libs" ] || [ "$CON_VOZ" = "1" ]; then pip install --no-cache-dir -r backend/requirements-voice.txt; fi
# Modelos (solo si se pidió): quedan en /opt/orbit-modelos, fuera del volumen de datos.
RUN if [ "$CON_IA" = "1" ] || [ "$CON_VOZ" = "1" ]; then pip install --no-cache-dir huggingface_hub && mkdir -p /opt/orbit-modelos; fi
RUN if [ "$CON_IA" = "1" ]; then python -c "from huggingface_hub import hf_hub_download as d; d('Qwen/Qwen2.5-1.5B-Instruct-GGUF','qwen2.5-1.5b-instruct-q4_k_m.gguf',local_dir='/opt/orbit-modelos')"; fi
RUN if [ "$CON_VOZ" = "1" ]; then python -c "\
from huggingface_hub import hf_hub_download as d, snapshot_download as s; \
s('Systran/faster-whisper-small', local_dir='/opt/orbit-modelos/whisper-small'); \
[d('rhasspy/piper-voices', f, local_dir='/tmp/pv') for f in ('es/es_MX/claude/high/es_MX-claude-high.onnx','es/es_MX/claude/high/es_MX-claude-high.onnx.json','en/en_US/lessac/medium/en_US-lessac-medium.onnx','en/en_US/lessac/medium/en_US-lessac-medium.onnx.json')]" \
    && cp /tmp/pv/es/es_MX/claude/high/* /tmp/pv/en/en_US/lessac/medium/* /opt/orbit-modelos/ && rm -rf /tmp/pv /opt/orbit-modelos/whisper-small/.cache; fi
COPY backend/app backend/app
COPY scripts scripts
COPY docs docs
COPY empaquetado/entrypoint.sh /app/entrypoint.sh
COPY README.md README.es.md .env.example ./
COPY --from=interfaz /w/dist frontend/dist
RUN chmod +x /app/entrypoint.sh && useradd --create-home --uid 10001 orbit && mkdir -p /app/data /app/backend/models && chown -R orbit:orbit /app/data /app/backend/models
USER orbit
WORKDIR /app/backend
EXPOSE 3000
VOLUME ["/app/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/api/salud' % os.environ.get('ORBIT_PUERTO','3000').strip('\"\' '), timeout=4)" || exit 1
ENTRYPOINT ["/app/entrypoint.sh"]
