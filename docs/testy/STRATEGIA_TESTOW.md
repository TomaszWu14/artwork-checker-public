# Strategia testów

> [DEV] Stan na 2026-10-15: **429 testów w 60 plikach**, 408 ✅ / 35 ⏭ w 4,4 s w środowisku bez pakietów
> PDF/OCR/ML (skipy = `pytest.importorskip`). Uruchomienie: `python -m pytest tests/ -q`.

## Piramida (cel)

| Poziom | Co | Narzędzie | Stan | Cel |
|---|---|---|---|---|
| Jednostkowe | czysta logika: `normalizer`, `barcode_validator`, `artwork_naming`, `uom`, `material_master`, raport | pytest | ✅ większość suite | pokrycie ≥ 80 % logiki domenowej (Z-05) |
| Integracyjne HTTP | trasy przez `app.test_client()` z prawdziwym logowaniem i CSRF (`tests/conftest.py`: `client`, `admin_client`, `manager_client`, `user_client`) | pytest | ✅ auth, IDOR, upload, PalViz, manage | **test 403 dla każdej roli** na każdej nowej trasie (SEC-007) |
| Bezpieczeństwa | regresje: IDOR cache/3D, magic bytes, CSRF, tokeny, path traversal, prompt injection (mock API) | pytest | ⚠️ częściowo | każde kryterium SEC-* w historyjce ma test |
| Kontraktowe | `palviz_push` (seam `_http_post`), webhooki (SSRF guard), sync agent | pytest z atrapami | ⚠️ | bez sieci w CI |
| E2E (pełny przebieg) | PDF → OCR → raport na próbkach syntetycznych | pytest z PyMuPDF (job opcjonalny) | ❌ wąsko (skipy) | osobny job CI „heavy" na żądanie |
| Statyczne | `compileall`, ruff, bandit, semgrep, pip-audit, gitleaks, trivy | CI | ✅ (ten PR) | ADR-0002 |

## Zasady
1. Test pisze się do **kryterium akceptacji** (Given/When/Then) — nazwa testu cytuje ID historyjki (`test_us005_lockout_after_10_failures`).
2. Brak sieci i sekretów w testach: AI/OCR/HTTP przez atrapy (`monkeypatch`), klucze = puste.
3. Baza: SQLite w `tempfile` per sesja (`conftest.py`); testy nie zależą od kolejności (rate-limit czyszczony w fixture).
4. Ciężkie zależności: `pytest.importorskip` — test pomijany, nie czerwony; raz w tygodniu job „heavy" z pełnym `requirements.txt` (do uruchomienia ręcznie).
5. Regresje bezpieczeństwa nigdy nie są usuwane ani oznaczane `skip`, by „przeszło" (CONTRIBUTING).
6. Dane testowe: syntetyczne; hasła testowe allowlistowane w `.gitleaks.toml` (W-02).

## Luki (z macierzy `docs/analiza/SLEDZENIE.md`)
Strefy (FR-007), eksport (FR-009), intake (FR-019), webhooki (FR-020), reset hasła (FR-002), PostgreSQL
w CI (NFR-004: tylko SQLite), pomiar pokrycia (NFR-009).

## Jak uruchomić lokalnie
```bash
pip install -r dev-requirements.txt flask werkzeug "rapidfuzz>=3.0,<4.0" pytest-cov
python -m pytest tests/ -q                      # szybki zestaw
python -m pytest tests/ -q --cov=. --cov-report=term-missing   # z pokryciem
pip install -r requirements-prod.txt && python -m pytest tests/ -q   # bez skipów PDF
```
