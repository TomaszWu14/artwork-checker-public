# Audyt repozytorium — Artwork Checker (stan na 2026-10-15)

**Zakres:** gałąź `main` (commit `4796e4c`), cały kod aplikacji, testy, CI, dokumentacja.
**Metoda:** przegląd kodu z trzech perspektyw ([BA] analityk, [DEV] developer, [SEC] bezpieczeństwo)
+ uruchomienie narzędzi (wyniki poniżej). Kodu **nie zmieniano** — to wyłącznie analiza.
**Poprzednie audyty w repo:** `AUDIT_2026-06-08.md` (system-matka DocCompare, przed forkiem — duża część
ustaleń dotyczy usuniętych modułów) i `UX_AUDIT.md` (2026-09-04, heurystyki Nielsena). Niniejszy dokument
odnosi się do nich tam, gdzie ustalenia nadal obowiązują.

## Wyniki narzędzi (2026-10-15, lekkie środowisko bez pakietów ML)

| Narzędzie | Wynik |
|---|---|
| `python -m compileall` | ✅ czysto (wszystkie moduły kompilują się) |
| `pytest tests/ -q` | ✅ **408 passed, 35 skipped** w 4,4 s (skipy = brak bibliotek PDF/OCR w środowisku) |
| `ruff check .` | ⚠️ **66 błędów**: F841 (28, nieużywane zmienne), **F601 (17, zduplikowane klucze w słownikach)**, F541 (10), F811 (7), **F821 (4, niezdefiniowane nazwy)** |
| `ruff format --check .` | ⚠️ 108 ze 133 plików nie jest sformatowanych wg konfiguracji |
| `bandit -r . -ll` | ✅ **0 ustaleń ≥ średnie**; 1058 niskich (876 to `assert` w testach, 139 `try/except/pass`, 13 fałszywych B105) |
| `pip-audit -r requirements-prod.txt` | ✅ brak znanych CVE (uwaga: zakresy `>=`, nie lock — wynik dotyczy najnowszych wersji) |
| grep sekretów (klucze API, klucze prywatne) | ✅ nic nie znaleziono w plikach śledzonych |

## Streszczenie (najważniejsze wnioski)

1. **[BA]** Aplikacja jest spójnym narzędziem do kontroli artworków (porównanie, kody GS1, indeks masterów,
   3D), ale **nie ma spisanych wymagań ani kryteriów akceptacji** — wiedza jest w kodzie i w README.
   ~55 tras i ~20 tabel to relikty systemu-matki, które mylą użytkownika i zaciemniają zakres.
2. **[DEV]** Solidne fundamenty (abstrakcja DB, `core/`, 429 szybkich testów z prawdziwym logowaniem i CSRF),
   ale monolit `app.py` (12 791 linii, 272 trasy) i `artwork_comparator.py` (7 559 linii) oraz 124 miejsca
   `except Exception: pass` utrudniają utrzymanie. **4 niezdefiniowane nazwy** (ruff F821) to realne błędy 500.
3. **[SEC]** Podstawy są dobre (CSRF, nagłówki, HSTS, flagi cookie, walidacja magic-bytes, kontrola IDOR,
   ochrona przed path traversal i SSRF, stałoczasowe porównania tokenów, brak SQL przez konkatenację).
   Luki dotyczą **odporności logowania na brute-force**, **prompt injection** przez treść PDF dostawcy,
   **sekretów w bazie**, **CSP z `unsafe-inline`/`unsafe-eval`** i **łańcucha dostaw** (brak pinningu,
   skany tylko raz w miesiącu, kontener jako root).
4. CI pilnuje tylko składni i testów; lint i skany bezpieczeństwa są doradcze — **brak bramki jakości**
   wymaganej przez Definition of Done.
5. Dokumentacja jest obszerna, ale częściowo **nieaktualna** (`docs/architektura.md`, `docs/DOKUMENTACJA_IT.md`,
   `docs/PROCES_*` opisują DocCompare — od US-016 w `docs/archiwum/`; README obiecuje zakładanie kont przez admina, a takiej funkcji nie ma).

---

## [BA] Perspektywa biznesowa

### Co aplikacja robi (stan faktyczny, na podstawie tras i szablonów)

| Obszar | Funkcje | Trasy |
|---|---|---|
| Porównanie artworków | upload pary PDF/obraz (wzorzec ↔ wersja dostawcy) lub wzorzec z biblioteki; porównanie tekstu z pozycjami, obrazu (SSIM/ΔE), stref, pól (profile); raport z listą kontrolną (REF, LOT, EXP, CE…) i eksport HTML/DOCX/PDF; batch do 50 par → ZIP; kolejka pól; komentarze do pól; historia i KPI | 60 |
| Walidacja kodów | EAN-8/13, UPC-A, GTIN-14 (suma kontrolna GS1), GS1-128 (AI 01/10/17/11), odczyt kodów z obrazu, zgodność kod ↔ tekst | w ramach porównania |
| Biblioteka / indeks masterów | indeks ~31 tys. plików z dysku sieciowego (agent `library_sync.py`), aliasy REF, grupy mapowania, potwierdzanie masterów, braki/duplikaty, karta artworku, ranking rewizji po nazwie pliku | 55 |
| 3D / PalViz | model GLB z wykrojnika (dieline), z fotografii, z danych MARM; batch; rejestr renderów; szablony wykrojników; push do PalViz | 39 |
| Master data | materiały (REF, EAN, poziomy opakowań, przeliczniki UOM), dostawcy, baza REF, import CSV/XLSX | 35 |
| Administracja | konta (tylko podgląd), kopia SQLite, status systemu, log aktywności, koszty API, budżet AI, konfiguracja AI/e-mail, webhooki, intake z Power Automate | 29 |
| Relikty DocCompare | checklisty dostaw, typy dokumentów, szablony porównań, kreator dostawców, Incoterms, kraje tranzytu, słownik tłumaczeń, scorecard, wersje, duplikaty | 55 |

Pełna inwentaryzacja: `docs/architektura/API.md`.

### Użytkownicy (zidentyfikowani, do potwierdzenia)

- **Specjalista ds. jakości / opakowań** (rola `user`) — porównuje artworki, czyta raporty, dodaje komentarze.
- **Manager** — potwierdza mastery, zarządza profilami pól, materiałami, biblioteką, wypycha rendery do PalViz.
- **Administrator** — konfiguracja AI/e-mail, kopie, token synchronizacji, webhooki, budżet.
- **Agent synchronizacji** (skrypt on-premise) — wysyła metadane i miniatury plików z dysku `Z:\`.
- **Systemy zewnętrzne** — Power Automate (intake PDF), PalViz (odbiorca renderów), webhooki ERP/WMS.
- **Odbiorcy repozytorium** — rekruter, audytor, nowy członek zespołu (portfolio).

### Czego brakuje w wymaganiach

1. Brak dokumentu wizji, mierników sukcesu i procesu AS-IS/TO-BE — nie wiadomo, *po czym poznać*, że
   narzędzie działa (np. czas kontroli, % wykrytych błędów, liczba reklamacji).
2. Brak wymagań funkcjonalnych z identyfikatorami i kryteriów akceptacji — testy istnieją, ale nie da się
   ich powiązać z wymaganiem (brak macierzy śledzenia).
3. Brak reguł biznesowych na piśmie: progi ΔE (7,0 tekst / 18,0 grafika), ranking rewizji, poziomy
   opakowań, co jest „krytyczne" a co „ostrzeżeniem" — są tylko w kodzie (`constants.py`, `artwork_naming.py`).
4. Niejasny zakres: moduły „szare" (materiały, dostawcy, AI learning) zostały po forku „na wszelki wypadek".
   55 tras reliktowych (checklisty dostaw, Incoterms, kraje tranzytu, słownik tłumaczeń, scorecard) nie ma
   właściciela ani uzasadnienia.
5. Zarządzanie kontami: hierarchia 4 ról istnieje, ale nie ma funkcji tworzenia/dezaktywacji kont ani
   zmiany roli (README twierdzi inaczej). Konta powstają przez edycję bazy.
6. Komunikaty i pomoc: `help.html` odsyła do usuniętych modułów; część ekranów pokazuje surowe kody
   (`active/ignored`, `dieline/marm/photo`) — patrz `UX_AUDIT.md` §1a.
7. Wymagania niefunkcjonalne (RODO, retencja, dostępność, wydajność dla 31 tys. plików, budżet AI)
   nie są spisane — część mechanizmów istnieje (budżet AI, limity), ale bez celów.

---

## [DEV] Perspektywa deweloperska

### Metryki

| Metryka | Wartość |
|---|---|
| `app.py` | 12 791 linii, 272 trasy; + 25 tras w 4 blueprintach (`incoterms`, `translation_dict`, `transit_countries`, `palviz`) |
| `artwork_comparator.py` | 7 559 linii (OCR, CV, modele ML ładowane leniwie, 6 wywołań Claude API) |
| Szablony | 56 (Jinja2 + Alpine.js + Tailwind); 199 użyć `innerHTML`; 0 użyć `\|safe` |
| Tabele DB | 64 `CREATE TABLE` rozsiane po `migrate_db.py` (41) i 9 innych modułach; ~20 to relikty (`kolejka_*`, `zlecenia_*`, `warehouse_*`, `tickets`, `customs_agencies`, `sad_field_mapping`, `po_line_items`, `cn_reference`, `currency_rates`…) |
| Testy | 429 funkcji testowych w 60 plikach; 408 ✅ / 35 ⏭ w 4,4 s; fixtures z prawdziwym logowaniem + CSRF; testy IDOR, uploadu, auth PalViz, walidacji GS1 |
| `except Exception: pass` | 124 (ciche połykanie błędów, w tym DB/IO) |
| Historia git | 3 commity (historia zgnieciona przy anonimizacji) |
| Zależności | 50+ pakietów, zakresy `>=` bez locka; `requirements-prod.txt` (lekki) + `requirements.txt` (ML) |

### Architektura — co działa dobrze

- Kierunek zależności `blueprint → core/db`, nigdy do `app` — wzorzec gotowy do dalszego rozbijania.
- `db.py`: jedna warstwa dla SQLite/PostgreSQL (tłumaczenie `?`→`%s`, `datetime('now')`, `INSERT OR IGNORE`),
  pula połączeń, `escape_like()`; zapytania parametryzowane; nazwy kolumn z białych list (`# nosec B608`).
- Konfiguracja przez env, `.env.example` z placeholderami, `SECRET_KEY` z twardym stopem w produkcji.
- Zadania w tle: tabela `async_jobs` dzielona między workery gunicorna, semafor `_HEAVY_SEM` (3), opcjonalna
  kolejka RQ (`jobs.py`/`worker.py`) z fallbackiem na wątki — udokumentowana w `docs/KOLEJKOWANIE.md`.
- Ciężkie importy (torch, transformers, OCR) są leniwe — CI i boot działają bez nich.
- CI: `compileall` + `pytest` jako bramka (blokująca); `security.yml` (Bandit, gitleaks, Trivy, pip-audit) raz
  w miesiącu, doradczo; obraz bazowy ML w GHCR skraca deploy.

### Dług techniczny (priorytetowo)

1. 🟠 **Niezdefiniowane nazwy (F821)** — `app.py:11247` woła `_resolve_artwork_master_path`, które nie istnieje
   → `NameError`/500 w `/api/artwork/master-files/from-path`; `app.py:2514–2521` woła `_ensure_shipment` /
   `_save_doc_to_shipment` (usunięte z modułem transportu) — gałąź martwa, bo `po_number` nie powstaje
   dla artworków, ale to bomba z opóźnionym zapłonem.
2. 🟠 **Zduplikowane klucze słowników (F601 ×17)** — druga wartość nadpisuje pierwszą po cichu (np. mapy
   tłumaczeń/etykiet). Każdy przypadek wymaga przeglądu, czy nie ginie dana.
3. 🟠 **Monolit** — 272 trasy w jednym pliku; brak modułów domenowych (`auth`, `artwork`, `library`, `admin`).
   Plan istnieje (`docs/PLAN_REFAKTORU.md`), nie jest realizowany.
4. 🟡 **Relikty systemu-matki** — ~55 tras, ~20 tabel, `DocType` z PO/PI/CI/SAD, `TRACKING_PROVIDERS`,
   zmienne tracking w `.env.example`, szablony `checklists/doc_types/templates/versions/scorecard`.
5. 🟡 **Schemat DB w 10 plikach** — `CREATE TABLE IF NOT EXISTS` w `app.py`, `artwork_index.py`,
   `artwork_manage.py`, blueprintach; `schema_migrations` istnieje, ale migracje nie są wersjonowane.
6. 🟡 **Ciche błędy** — 124 `except Exception: pass`, puste `catch(e){}` w JS (UX_AUDIT); utrudniają
   diagnostykę na produkcji.
7. 🟡 **Stan w pamięci procesu** — `_login_attempts`, `_artwork_cache`, `_forgot_attempts` per worker
   gunicorna (2 workery → podwójne limity, utrata przy restarcie).
8. 🟡 **Brak bramek jakości** — lint doradczy (66 błędów), brak pomiaru pokrycia, brak mypy, brak Dependabota,
   brak skanu obrazu Docker, kontener bez `USER`/`HEALTHCHECK`.
9. 🟡 **Testy** — pełny przebieg PDF → raport testowany wąsko (skipy bez PyMuPDF); brak testów „403 dla każdej
   roli" dla większości tras; brak e2e UI.
10. ⚪ **Dokumentacja** — 5 dokumentów w `docs/` opisuje DocCompare; brak CONTRIBUTING/SECURITY/CHANGELOG/ADR;
    `AGENTS.md` twierdzi „brak testów i lintera" (nieaktualne).
11. ⚪ **Frontend** — React/Babel/Chart.js z CDN w raporcie i scorecard (zależność od sieci, CSP), dwa różne
    `esc()` w `artwork.html`, ~700 linii martwego JS (UX_AUDIT).

---

## [SEC] Perspektywa bezpieczeństwa

### Co już jest dobrze (utrzymać)

CSRF na wszystkich mutacjach (`core/security.py`), nagłówki bezpieczeństwa + HSTS w produkcji, cookie
`HttpOnly`/`SameSite=Strict`/`Secure`, `SECRET_KEY` fail-closed w produkcji, hasła przez Werkzeug
(scrypt/pbkdf2) z „dummy hash" przeciw enumeracji, tokeny resetu jednorazowe z atomowym `UPDATE … WHERE used=0`,
kontrola własności zasobów (IDOR) z testami, `realpath`/`safe_join`/`secure_filename` przy serwowaniu plików,
walidacja magic-bytes i odrzucanie PDF z hasłem, ochrona SSRF przy webhookach, stałoczasowe porównania
tokenów (`hmac.compare_digest`), audit log, strony błędów bez tracebacku (PalViz: poprawka RD-1),
`robots.txt` Disallow, `.dockerignore` wykluczający sekrety i bazy, `.gitignore` dla `.env` i hasła admina.

### Top 10 ryzyk

| # | Waga | Ryzyko | Dowód (plik:linia) | Rekomendacja |
|---|---|---|---|---|
| 1 | 🟠 Wysokie | **Brute-force logowania** — limit 5 prób/15 min per IP (*sprostowanie 2026-10-16:* liczony w `audit_log`, pamięć procesu tylko jako fallback), ale **brak blokady konta** — rotacja IP omija limit; polityka haseł: tylko min. 8 znaków przy resecie | `app.py:1238–1262`, `app.py:1437–1440`, `app.py:1685` | blokada per konto w oknie (US-005), polityka haseł, opcjonalnie 2FA dla admina |
| 2 | 🟠 Wysokie | **Prompt injection** — surowy tekst OCR z PDF dostawcy trafia do promptu Claude bez ramki „dane, nie instrukcje"; spreparowany artwork może zasugerować werdykt „zgodny" | `artwork_comparator.py:3504–3530` (`ocr_a[:3000]`, `ocr_b[:3000]`), `:6684–6701` (vision) | system prompt z regułą danych, tagowanie bloków, walidacja JSON odpowiedzi, wynik AI oznaczony jako doradczy, test z „złośliwym" PDF; `ai_validator.py:437–459` ma już wzorzec sanitizacji |
| 3 | 🟡 Średnie | **Klucz Anthropic API w bazie (jawnie) i w `os.environ` z poziomu requestu** — zrzut/backup bazy ujawnia płatny sekret; brak rotacji | `app.py:6647–6665`, `app.py:1225`, `ai_validator.py:125`, `ai_learning.py:41`, `artwork_comparator.py:6568` | sekret tylko z env (usunąć zapis w UI) lub szyfrowanie w bazie; brak mutacji `os.environ` |
| 4 | 🟡 Średnie | **Tokeny resetu hasła jawnie w DB, ważne 24 h**, przekazywane do szablonu `/admin` (obecnie nierenderowane) — odczyt bazy = przejęcie konta | `app.py:1631–1640`, `app.py:2221–2231` | przechowywać hash tokenu, ważność 1 h, nie przekazywać wartości do widoku |
| 5 | 🟡 Średnie | **CSP z `unsafe-inline` i `unsafe-eval`** + 199 `innerHTML` + niespójne `esc()` — każdy XSS w szablonie jest bezpośrednio wykonywalny | `app.py:181–195`, `UX_AUDIT.md`, `AUDIT_2026-06-08.md` #85–87 | nonce dla skryptów inline, usunąć `unsafe-eval` (Alpine CSP build), jeden helper `esc`, lint szablonów |
| 6 | 🟡 Średnie | **Zapis plików do dowolnego katalogu serwera** (`save-copy`): gdy `ARTWORK_COPY_ROOTS` puste (domyślnie), manager może zapisać GLB/PNG w dowolnym istniejącym katalogu i sondować istnienie ścieżek | `app.py:5242–5268`, `_a3d_copy_to_dir` `app.py:5213–5240` | fail-closed: w produkcji wymagać `ARTWORK_COPY_ROOTS`; lista dozwolonych katalogów w UI |
| 7 | 🟡 Średnie | **Brak zarządzania kontami** — konta i role zmieniane w bazie ręcznie (bez audytu, bez wymuszenia polityki haseł, bez dezaktywacji); `superuser` bez przeglądu uprawnień | brak tras `users` w `app.py`; `templates/admin.html` tylko lista | US-009: CRUD kont dla admina z audytem, ochrona „ostatniego admina" |
| 8 | 🟡 Średnie | **Łańcuch dostaw i kontener** — zakresy `>=` bez locka/hashy, brak Dependabota, skany CVE raz w miesiącu i doradcze, obraz uruchamia gunicorn jako **root**, brak `HEALTHCHECK` | `requirements*.txt`, `Dockerfile:75–90`, `.github/workflows/security.yml` | lock (pip-compile/uv) + pip-audit blokujący w CI, Dependabot, `USER app`, skan obrazu Trivy |
| 9 | 🟡 Średnie | **Placeholder z `.env.example` przechodzi walidację** `SECRET_KEY` — `YOUR_SECRET_KEY_HERE` nie jest na liście znanych niebezpiecznych wartości; podobnie `DATABASE_URL=YOUR_DATABASE_URL_HERE` | `app.py:230`, `.env.example:10` | dodać wzorce `YOUR_*_HERE` do `_known_insecure`, puste wartości w `.env.example` |
| 10 | 🟡 Średnie | **RODO / retencja** — `audit_log` z IP i nazwą użytkownika bez retencji, brak eksportu/usuwania danych osoby, brak potwierdzonych umów powierzenia (Anthropic, Mistral, Resend, Sentry, hosting), kopie SQLite nieszyfrowane | `core/audit.py`, `app.py:1390–1403` | `docs/bezpieczenstwo/RODO.md`: podstawy, retencja 12 mies. dla audytu, procedura usunięcia konta, lista procesorów |

Niższe (⚪): `GET /logout` bez CSRF (`app.py:1720`); ręczne sprawdzanie sesji bez kontroli dezaktywacji konta
w `/api/library/search`, `/api/ref-database/*` (`app.py:7887, 8812, 8839`); nagłówek `X-XSS-Protection` przestarzały;
uploady do 200 MB + OCR 220 DPI bez limitu stron — wyczerpanie zasobów przez zalogowanego użytkownika
(łagodzą: limit 30/min i semafor 3); nie wszystkie z ~39 miejsc `request.files` przechodzą przez wspólne
walidatory (`_validate_pdf_upload` ×3, `_validate_upload_magic` ×2) — wymaga przeglądu trasa po trasie.

### Klasyfikacja danych (skrót; pełna: `docs/bezpieczenstwo/KLASYFIKACJA_DANYCH.md`)

Poufne: `SECRET_KEY`, klucze API (Anthropic, Mistral, Resend, PalViz, intake, sync), `DATABASE_URL`, hashe haseł,
tokeny resetu, kopie bazy. Wewnętrzne: artworki i mastery (know-how opakowań, oznaczenia medyczne), raporty,
indeks biblioteki, master data. Dane osobowe: konta (`username`, `email`, `department`, `last_login`),
`audit_log` (nazwa + IP), autorstwo komentarzy, `api_usage.user_id`.

---

## Rekomendowana kolejność prac

1. **Sprint 0 (ten PR):** szkielet procesu — CONTRIBUTING, SECURITY, CHANGELOG, szablony issue/PR, CODEOWNERS,
   Dependabot, CI z lintem/SAST/SCA/sekretami, dokumenty analizy/architektury/bezpieczeństwa v0.1, backlog.
2. **Sprint 1 — pilne poprawki (Must):** US-001 (F821), US-002 (lint jako bramka, F601), US-003 (tokeny resetu),
   US-004 (klucz API poza bazą), US-005 (logowanie: limity w DB + blokada konta), US-018 (`_known_insecure`).
3. **Sprint 2 — Should:** US-006 (save-copy fail-closed), US-007 (prompt hardening), US-008 (CSP), US-009 (konta),
   US-011 (lock + Dependabot), US-012 (Docker non-root + skan obrazu).
4. **Dalej:** usunięcie reliktów (US-010, po decyzji PO), pokrycie testów (US-013), RODO (US-014),
   kolejka RQ (US-015), porządek w dokumentacji (US-016).

Szczegóły i kryteria akceptacji: `docs/analiza/HISTORYJKI.md`. Rejestr ryzyk: `docs/bezpieczenstwo/RYZYKA.md`.

## Decyzje potrzebne od Product Ownera

Patrz lista pytań [BA] w `docs/analiza/ZALOZENIA.md` (Z-01…Z-07) — do czasu odpowiedzi obowiązują zapisane tam
bezpieczne założenia minimalne.
