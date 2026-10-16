#!/usr/bin/env bash
# tools/regen_ml_lock.sh — regeneracja requirements-ml.lock (US-021, ADR-0002).
#
# Lock pełnego obrazu ML (Dockerfile, Dockerfile.base): wersje + hashe SHA-256 dla
# Python 3.11 / Linux x86_64. PyTorch i torchvision w wariancie CPU z indeksu PyTorch
# (wersje „+cpu” wygrywają z wariantami CUDA z PyPI); CI odrzuca lock z pakietami CUDA.
#
# Istniejący lock jest preferencją: bez zmian w requirements.txt piny się nie zmieniają.
# Uruchamia go workflow .github/workflows/ml-lock.yml (sieć do download.pytorch.org);
# lokalnie: pip install "uv==0.13.1" && tools/regen_ml_lock.sh
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=requirements-ml.lock
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
# Zachowaj dotychczasowe piny (bez nagłówka) jako preferencje rozwiązywania.
if [[ -f "$OUT" ]]; then grep -v '^#' "$OUT" > "$TMP" || true; fi

uv pip compile requirements.txt \
  --python-version 3.11 \
  --python-platform x86_64-manylinux_2_28 \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --index-strategy unsafe-best-match \
  --emit-index-url \
  --generate-hashes --no-header --quiet \
  -o "$TMP"

{
  echo "# requirements-ml.lock — pełny obraz ML: wersje + hashe SHA-256 (US-021, ADR-0002)."
  echo "# Źródło: requirements.txt. Cel: Python 3.11, Linux x86_64, PyTorch CPU."
  echo "# NIE edytuj ręcznie — regeneracja: tools/regen_ml_lock.sh (CI: .github/workflows/ml-lock.yml)."
  echo "# Instalacja: pip install --require-hashes -r requirements-ml.lock"
  cat "$TMP"
} > "$OUT"
echo "requirements-ml.lock: $(grep -cE '^[A-Za-z0-9_.-]+==' "$OUT") pakietów"
