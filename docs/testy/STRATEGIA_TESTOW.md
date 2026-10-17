# Strategia testów

> [DEV] Stan na 2026-10-17 (US-013): **1195 testów**, w środowisku CI (bez PyMuPDF/Pillow/ML) 1157 ✅ / 38 ⏭
> (skipy = `pytest.importorskip`); pokrycie logiki domenowej 97 %, całego repo 47 %. Uruchomienie: `python -m pytest tests/ -q`.

## Piramida (cel)

| Poziom | Co | Narzędzie | Stan | Cel |
|---|---|---|---|---|
| Jednostkowe | czysta logika: `normalizer`, `barcode_validator`, `artwork_naming`, `uom`, `material_master`, raport | pytest | ✅ większość suite | ✅ pokrycie ≥ 80 % logiki domenowej — bramka CI (US-013) |
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
w CI (NFR-004: tylko SQLite). Pokrycie całego repo (47 %) — głównie `app.py`, `artwork_comparator.py`
i kaskada OCR/ekstrakcji; poza progiem do decyzji PO.

## Próg pokrycia logiki domenowej (US-013, decyzja PO 2026-10-17)

CI (job „Składnia + testy”) **blokuje** merge, gdy łączne pokrycie poniższego zestawu spadnie poniżej **80 %**
(`coverage report --fail-under=80`, lista i próg w `env` pliku `.github/workflows/ci.yml`). Pokrycie mierzone
w lekkim środowisku CI — bez PyMuPDF/Pillow/ML — więc ścieżki wymagające tych pakietów się nie liczą.

| Moduł | Zakres |
|---|---|
| `barcode_validator.py` | EAN/UPC/GS1-128, zgodność kodów A↔B i z tekstem OCR |
| `normalizer.py` | liczby i daty w różnych lokalizacjach |
| `uom.py`, `material_uom.py` | przeliczanie jednostek opakowań |
| `material_master.py`, `supplier_master.py` | dane podstawowe materiałów i dostawców |
| `artwork_naming.py`, `artwork_index.py` | konwencja nazw, wersje, indeks masterów |
| `artwork_report_engine.py` | struktura raportu porównania i eksport HTML |

Zmiana listy lub obniżenie progu = decyzja PO; pilnuje tego `tests/test_us013_coverage_gate.py`.

## Jak uruchomić lokalnie
```bash
pip install -r dev-requirements.txt flask werkzeug "rapidfuzz>=3.0,<4.0" pytest-cov
python -m pytest tests/ -q                      # szybki zestaw
python -m pytest tests/ -q --cov=. --cov-report=term-missing   # z pokryciem
python -m coverage report -m --fail-under=80 --include="artwork_index.py,artwork_naming.py,artwork_report_engine.py,barcode_validator.py,material_master.py,material_uom.py,normalizer.py,supplier_master.py,uom.py"   # bramka US-013
pip install -r requirements-prod.txt && python -m pytest tests/ -q   # bez skipów PDF
```
