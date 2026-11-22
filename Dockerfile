# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS web
WORKDIR /app
COPY package.json package-lock.json ./
COPY scripts/localize-mediapipe.mjs ./scripts/localize-mediapipe.mjs
RUN npm ci
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/cache \
    FACESIGNUP_ENV=production

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 facesignup

WORKDIR /app
RUN mkdir -p /app/scripts
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY --from=web /app/dist ./dist
COPY MODEL_MANIFEST.md THIRD_PARTY_NOTICES.md ./
COPY scripts/backup_database.py scripts/check_production.py ./scripts/

RUN mkdir -p /app/data && chown -R facesignup:facesignup /app
USER facesignup

EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; host=os.environ['FACESIGNUP_ALLOWED_HOSTS'].split(',')[0]; req=urllib.request.Request('http://127.0.0.1:8100/api/ready', headers={'Host': host}); urllib.request.urlopen(req, timeout=3)"

CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8100", "--proxy-headers", "--forwarded-allow-ips=*"]
