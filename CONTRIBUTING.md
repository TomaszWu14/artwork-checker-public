# CONTRIBUTING — jak pracujemy

Repozytorium jest prowadzone tak, jakby pracował nad nim trzyosobowy zespół: **[BA]** analityk biznesowy,
**[DEV]** developer, **[SEC]** specjalista ds. bezpieczeństwa, a **Product Owner (PO)** podejmuje decyzje
biznesowe i akceptuje wyniki. Każda zmiana przechodzi przez trzy perspektywy, a ślad pracy jest w repo
(dokumenty w `docs/`, issues, commity, PR-y).

## Role

| Rola | Odpowiada za | Nie robi |
|---|---|---|
| [BA] | pytania do PO, wymagania (FR/NFR/BR), historyjki z kryteriami Given/When/Then, MoSCoW, słownik, macierz śledzenia, odbiór z perspektywy użytkownika | nie pisze kodu; nie zgaduje — pyta (`docs/analiza/ZALOZENIA.md`) |
| [DEV] | projekt (ADR), implementacja w małych krokach, testy, lint/typy, Docker/CI/migracje, README/API/CHANGELOG | nie zmienia zakresu bez BA/PO; nie wyłącza testów ani kontroli bezpieczeństwa |
| [SEC] | klasyfikacja danych, threat model (STRIDE), przegląd PR wg OWASP Top 10/ASVS, SECURITY.md, rejestr ryzyk i wyjątków | — ma **prawo weta**: PR z ryzykiem wysokim/krytycznym nie przechodzi bez poprawki albo akceptacji PO zapisanej w `docs/bezpieczenstwo/RYZYKA.md` |
| PO | odpowiedzi, zakres, priorytety, ryzyka, wydania | — |

W issue, PR i commitach oznaczamy rolę: `[BA]`, `[DEV]`, `[SEC]`.

## Proces dla każdej funkcji (nie przeskakujemy kroków)

1. **[BA] Analiza** — pytania do PO (max 5), historyjka „Jako… chcę… aby…”, kryteria akceptacji Given/When/Then,
   NFR, priorytet; sprawdzenie Definition of Ready. Issue z szablonu *User story*.
2. **[SEC] Wymagania bezpieczeństwa** — klasa danych, mini-STRIDE dla nowego przepływu, zabezpieczenia jako
   dodatkowe kryteria akceptacji, wpis do rejestru ryzyk, jeśli coś zostaje otwarte.
3. **[DEV] Projekt** — opis rozwiązania; ADR dla decyzji istotnych lub trudno odwracalnych
   (`docs/architektura/adr/NNNN-nazwa.md`); zmiany modelu danych/API w dokumentacji **przed** kodem.
4. **[DEV] Implementacja** — gałąź `feature/<US-id>-<nazwa>` (lub `fix/`, `security/`), małe commity
   (Conventional Commits, EN), testy dla każdego kryterium, w tym bezpieczeństwa („użytkownik bez roli X dostaje 403”).
5. **[SEC] Przegląd** — diff wg checklisty w szablonie PR; wynik ✅ / ⚠️ uwagi / ❌ blokada z uzasadnieniem;
   wyniki narzędzi CI ocenione; fałszywe alarmy oznaczone (`# nosec Bxxx — powód`, `.gitleaks.toml`), nie wyciszane hurtowo.
6. **[BA] Odbiór** — kryteria punkt po punkcie, komunikaty i UX, aktualizacja `docs/analiza/SLEDZENIE.md`.
7. **PR i podsumowanie** — opis wg szablonu, wpis w `CHANGELOG.md`, **merge tylko po akceptacji PO**.

Po każdym etapie: podsumowanie 5–8 punktów z podziałem na role + lista decyzji potrzebnych od PO.

## Definition of Ready
- cel i korzyść jasne; kryteria akceptacji testowalne; zależności znane; dane (klasa) i uprawnienia (role) określone;
  priorytet MoSCoW nadany; brak otwartych pytań blokujących (lub założenie zapisane w `ZALOZENIA.md`).

## Definition of Done
Funkcja jest skończona, gdy:
- wszystkie kryteria akceptacji (funkcjonalne i bezpieczeństwa) są spełnione i pokryte testami,
- CI jest zielone: lint, testy, skany bezpieczeństwa bez nowych ustaleń wysokich/krytycznych,
- dokumentacja zaktualizowana (wymagania, API, model danych, ADR jeśli dotyczy, CHANGELOG),
- przegląd SEC i odbiór BA zapisane w PR,
- brak sekretów, danych osobowych i danych produkcyjnych w repo, testach i logach,
- PO zaakceptował.

## Konwencje
- **Język:** dokumentacja PL; kod, nazwy, commity EN (założenie T-01 — do potwierdzenia).
- **Commity:** `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `security:`, `ci:` + odwołanie do ID
  (`feat: add account lockout (US-005)`).
- **Gałęzie:** `feature/US-009-user-management`, `security/US-003-reset-token-hash`; do `main` tylko przez PR.
- **Kod:** `constants.py` zamiast magic strings; `db.get_db()` + parametryzacja; `normalizer` do liczb/dat; ciężkie
  importy leniwe; `core.security` do ról; `core.audit.log_audit` dla akcji wrażliwych (pełna lista: `CLAUDE.md`).
- **Testy:** nazwa cytuje ID historyjki; bez sieci i sekretów; `importorskip` dla ciężkich zależności.
- **Diagramy:** Mermaid w Markdown.

## Narzędzia (uzasadnienie: ADR-0002)

| Narzędzie | Lokalnie | W CI |
|---|---|---|
| ruff | `ruff check . && ruff format --check .` | doradczo do US-002, potem blokująco |
| pytest | `python -m pytest tests/ -q` | blokująco |
| bandit | `bandit -r . -ll -x ./tests` | blokująco (≥ średnie) |
| semgrep | `pip install semgrep && semgrep scan --config p/python --config p/flask --config p/owasp-top-ten` | doradczo |
| pip-audit | `pip-audit -r requirements-prod.txt` | blokująco |
| gitleaks | `gitleaks git --redact` (lub pre-commit) | blokująco |
| trivy | `trivy fs --scanners vuln,secret,misconfig .` | doradczo (do US-012) |
| pre-commit | `pip install pre-commit && pre-commit install` | — |

Instalacja środowiska testowego: `pip install -r dev-requirements.txt flask werkzeug "rapidfuzz>=3.0,<4.0"`.

## Zasady ogólne
- Nie wymyślamy wymagań biznesowych — pytamy. Nie obniżamy wymagań bezpieczeństwa — eskalujemy do PO.
- Przy sprzecznych rekomendacjach ról przedstawiamy obie opcje z konsekwencjami i prosimy PO o decyzję
  (zapis w ADR lub rejestrze ryzyk).
- Dokumenty mają być zwięzłe i aktualne — lepiej krótko i prawdziwie niż długo i nieaktualnie.
- Bez pushu do innych gałęzi, wdrożeń i migracji na danych produkcyjnych bez zgody PO.
