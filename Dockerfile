# UWAGA: to jest monolityczny obraz (instaluje całe ML przy każdym buildzie →
# deploy 7-8 min). Szybszy wariant „Poziom 0" rozbija to na obraz bazowy z ML
# (Dockerfile.base, publikowany do GHCR) + cienki obraz aplikacji (Dockerfile.slim,
# deploy ~1 min). Jak przełączyć: docs/OBRAZ_BAZOWY_ML.md
FROM python:3.14-slim

WORKDIR /app

# US-021: zależności z locka (wersje + hashe, PyTorch CPU) — nie z zakresów requirements.txt.
COPY requirements-ml.lock .

# All system deps, Python packages, and cleanup in a single layer so that
# build-only tools (git, curl) and bytecode caches never bloat the exported
# image.  Separate layers would embed git+curl permanently even if removed
# later; a single RUN avoids that.
#
# torchaudio removed — not used by any pipeline in this application.
# git/curl are purged after pip finishes; they are only needed for the two
# git+https:// installs (LightGlue, GroundingDINO).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-pol \
    tesseract-ocr-eng \
    tesseract-ocr-ukr \
    tesseract-ocr-rus \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-ita \
    tesseract-ocr-nld \
    tesseract-ocr-por \
    tesseract-ocr-ces \
    tesseract-ocr-slk \
    tesseract-ocr-ron \
    tesseract-ocr-hun \
    tesseract-ocr-hrv \
    tesseract-ocr-slv \
    tesseract-ocr-bul \
    tesseract-ocr-est \
    tesseract-ocr-lav \
    tesseract-ocr-lit \
    tesseract-ocr-fin \
    tesseract-ocr-swe \
    tesseract-ocr-nor \
    tesseract-ocr-dan \
    poppler-utils \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    libzbar0 \
    fonts-dejavu-core \
    fonts-liberation \
    curl \
    git \
    # US-021: wszystko z requirements-ml.lock — przypięte wersje i hashe SHA-256; torch/torchvision
    # w wariancie +cpu (lock zawiera --extra-index-url do indeksu CPU PyTorch, CI odrzuca pakiety CUDA).
    && pip install --no-cache-dir --retries 5 --timeout 120 --require-hashes -r requirements-ml.lock \
    # Remove build-only tools so they don't appear in the exported layer.
    && apt-get purge -y --auto-remove curl git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Strip bytecode caches — saves ~150-200 MB across all ML packages.
    && find /usr/local/lib/python3.11 -name "*.pyc" -delete \
    && find /usr/local/lib/python3.11 -name "__pycache__" -type d \
         -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf /root/.cache /tmp/pip* /tmp/*.whl

COPY . .

# US-012: proces aplikacji działa jako użytkownik bez uprawnień roota (uid 10001).
# Kod (/app) zostaje własnością roota (tylko do odczytu dla aplikacji); zapisywalne
# są wyłącznie katalogi danych. Zamontowany wolumen /data musi być zapisywalny
# dla uid 10001 (patrz docs/operacje/RUNBOOK.md).
RUN (getent group app >/dev/null || groupadd --system --gid 10001 app) \
 && (id -u app >/dev/null 2>&1 || useradd --system --uid 10001 --gid app \
        --home-dir /app --no-create-home --shell /usr/sbin/nologin app) \
 && mkdir -p /app/instance /app/uploads /app/logs /app/library /app/backups /data \
 && chown -R app:app /app/instance /app/uploads /app/logs /app/library /app/backups /data
USER app

EXPOSE 5000

# US-012: sonda zdrowia bez curl (usuniętego z obrazu) — /health zwraca 200 lub 503.
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=4).status == 200 else 1)"


# Migration runs at container start so it targets the runtime DB path
# (which may be on a persistent mounted volume, not available at build time).
# Workers: 2 × 3 threads — each worker loads its own model copy (~2 GB),
# 3 workers exhausted 8 GB RAM and triggered OOM. 2 workers × 3 threads
# serves ~5 concurrent users with overlap during Claude API I/O waits.
CMD python migrate_db.py && \
    gunicorn app:app \
    --workers 2 \
    --worker-class gthread \
    --threads 3 \
    --timeout 300 \
    --bind 0.0.0.0:5000
