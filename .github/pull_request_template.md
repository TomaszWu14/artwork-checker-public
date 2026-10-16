## Co i dlaczego
<1–3 zdania; link do historyjki: US-… / issue #…; wymagania: FR-… / SEC-…>

## Jak przetestować
```bash
python -m pytest tests/ -q
```
<kroki ręczne w UI, jeśli dotyczy; zrzuty ekranu dla zmian UI>

## Zmiany w dokumentacji
- [ ] `docs/analiza/WYMAGANIA.md` / `HISTORYJKI.md` / `SLEDZENIE.md` zaktualizowane
- [ ] `docs/architektura/API.md` / `MODEL_DANYCH.md` / ADR (jeśli decyzja istotna)
- [ ] `CHANGELOG.md` (sekcja *Unreleased*)

---

## Checklista [BA] — odbiór
- [ ] każde kryterium akceptacji sprawdzone punkt po punkcie (wynik poniżej)
- [ ] komunikaty i UI zrozumiałe po polsku, bez surowych kodów/tracebacków
- [ ] zakres zgodny z historyjką (brak „przy okazji”)
- [ ] macierz śledzenia zaktualizowana

**Wynik odbioru BA:** ✅ / ⚠️ uwagi / ❌ — …

## Checklista [DEV]
- [ ] małe commity Conventional Commits (EN) z ID historyjki
- [ ] testy dla każdego kryterium (w tym bezpieczeństwa); `pytest` zielone; `compileall` czyste
- [ ] `ruff check` bez nowych błędów; ciężkie importy leniwe; `constants.py` zamiast magic strings
- [ ] SQL tylko przez `db.get_db()` z parametrami; `normalizer` do liczb/dat; `core.audit` dla akcji wrażliwych
- [ ] migracja idempotentna (`migrate_db.py`), działa na SQLite i PostgreSQL
- [ ] README / API / runbook zaktualizowane, jeśli dotyczy

## Checklista [SEC] — przegląd (OWASP Top 10 / ASVS L2)
- [ ] **Uwierzytelnianie / sesja:** brak zmian osłabiających logowanie, reset hasła, cookie
- [ ] **Autoryzacja:** każdy nowy endpoint ma `login_required`/`require_role`; test „403 dla roli bez uprawnień”; brak IDOR (kontrola właściciela)
- [ ] **Walidacja wejścia / wstrzyknięcia:** SQL parametryzowany, brak `eval`/`subprocess` z wejściem, `escape_like`
- [ ] **XSS / wyjście:** Jinja autoescape, `innerHTML` tylko z `esc()`, brak `|safe` z danymi użytkownika
- [ ] **CSRF:** `csrf_protect` na POST/PUT/PATCH/DELETE
- [ ] **Upload / pliki:** limit, magic bytes, `secure_filename`, brak traversal (`realpath`/`safe_join`), fail-closed
- [ ] **Sekrety / konfiguracja:** nic w kodzie, testach, logach; env opisane w `.env.example` bez wartości
- [ ] **Logowanie / audyt:** `log_audit` dla operacji wrażliwych; logi bez haseł, tokenów, zbędnych danych osobowych
- [ ] **Nagłówki / transport:** brak osłabienia CSP/HSTS/cookie
- [ ] **Zależności:** nowe pakiety uzasadnione, wersja ograniczona, pip-audit czysty
- [ ] **AI / LLM:** treść użytkownika jako dane, nie instrukcje; brak danych osobowych w promptach; limity kosztów
- [ ] **RODO / dane:** klasa danych określona; retencja; brak danych produkcyjnych
- [ ] wyniki skanerów CI ocenione; fałszywe alarmy oznaczone z uzasadnieniem (`# nosec`, `.gitleaks.toml`), nie wyciszone hurtowo

**Wynik przeglądu SEC:** ✅ / ⚠️ uwagi / ❌ blokada — uzasadnienie: …
**Ryzyka otwarte:** R-… (rejestr) / brak

## Akceptacja PO
- [ ] PO zaakceptował zakres i wynik — **merge dopiero po tej akceptacji**
