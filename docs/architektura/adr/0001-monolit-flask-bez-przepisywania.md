# ADR-0001: Monolit Flask rozbijany przyrostowo, bez przepisywania frameworka

- **Status:** zaakceptowany (decyzja historyczna z `docs/PLAN_REFAKTORU.md`, potwierdzona 2026-10-15)
- **Rola:** [DEV]

## Kontekst
`app.py` ma 12 791 linii i 272 trasy; `artwork_comparator.py` 7 559 linii. Wąskie gardła to CPU/RAM
(OCR, modele CV) i latencja API AI, nie I/O. Jeden developer, repo portfolio.

## Rozważane opcje
1. Przepisanie na FastAPI/Django + ORM — duży koszt, ryzyko regresji, nie usuwa wąskich gardeł CPU.
2. Zostawić monolit bez zmian — rosnący koszt utrzymania, trudne przeglądy.
3. **Zostać przy Flask; wydzielać blueprinty domenowe po jednej domenie naraz** (wzorzec już działa:
   `incoterms`, `translation_dict`, `transit_countries`, `palviz`), z bramką testów po każdym kroku.

## Decyzja
Opcja 3. Kolejność: `auth` → `artwork_compare` → `library` → `artwork_3d` → `master_data` → `admin`.
Każde wydzielenie jest mechaniczne (przeniesienie tras), bez zmiany logiki, w osobnym PR.
Nie wprowadzamy ORM: `db.py` z parametryzowanym SQL działa dla obu baz (ADR-0003).

## Konsekwencje
- (+) Niskie ryzyko, każdy krok odwracalny, czytelniejsze PR-y, mniejsze konflikty.
- (−) Przez jakiś czas dwa style (trasy w `app.py` i w blueprintach); wymaga dyscypliny: blueprint → core/db.
- Ciężkie zadania w tle docelowo do RQ (`docs/KOLEJKOWANIE.md`), bez twardej zależności od Redis.
