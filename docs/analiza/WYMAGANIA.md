# Wymagania — wersja 0.1 (odtworzone z kodu; do potwierdzenia przez PO)

> [BA] Identyfikatory: **FR** funkcjonalne, **NFR** niefunkcjonalne, **BR** reguły biznesowe,
> **SEC** bezpieczeństwo (dostarcza [SEC]). Status: ✅ zaimplementowane, ⚠️ częściowo, ❌ brak.
> Priorytet MoSCoW dotyczy *utrzymania/rozwoju*, nie tego, czy funkcja już istnieje.

## Wymagania funkcjonalne

| ID | Wymaganie | Status | MoSCoW | Źródło w kodzie |
|---|---|---|---|---|
| FR-001 | Użytkownik loguje się nazwą lub e-mailem i hasłem; sesja wygasa po 8 h | ✅ | M | `app.py:/login` |
| FR-002 | Użytkownik resetuje hasło linkiem e-mail (jednorazowy token) | ✅ | M | `/forgot-password`, `/reset-password` |
| FR-003 | Porównanie pary plików (PDF/JPG/PNG/TIFF): wzorzec (upload lub master z biblioteki) ↔ wersja dostawcy | ✅ | M | `/api/artwork/compare` |
| FR-004 | Raport różnic: tekst (z pozycją), obraz (strefy czerwone/żółte/niebieskie), pola strukturalne (EAN, REF, rewizja, data, gramatura, kolor, format) | ✅ | M | `artwork_report_engine.py` |
| FR-005 | Lista kontrolna elementów obowiązkowych (REF, LOT, EXP, CE, EAN…) z oceną per element | ✅ | M | `artwork_report_engine.py`, `test_checklist_ean_checksum.py` |
| FR-006 | Walidacja kodów: EAN-8/13, UPC-A, GTIN-14 (suma kontrolna), GS1-128 (AI 01/10/17/11), zgodność A↔B i kod↔tekst | ✅ | M | `barcode_validator.py` |
| FR-007 | Porównanie stref zaznaczonych przez użytkownika i szablony stref | ✅ | S | `/api/artwork/zone-compare` |
| FR-008 | Porównanie wsadowe do 50 par z automatycznym parowaniem i wynikiem ZIP | ✅ | S | `artwork_batch_processor.py` |
| FR-009 | Eksport raportu do HTML, DOCX, PDF | ✅ | S | `/artwork/report/export-*` |
| FR-010 | Historia porównań per użytkownik (manager+ widzi wszystkie), komentarze do pól, widoczność raportu | ✅ | M | `/api/artwork/history`, `/api/artwork/report/<id>/*` |
| FR-011 | Indeks masterów z dysku sieciowego: synchronizacja metadanych i miniatur przez agenta z tokenem | ✅ | M | `/api/library/sync`, `library_sync.py` |
| FR-012 | Rozpoznawanie REF, typu opakowania i rewizji z nazwy pliku; ranking „najnowsza rewizja" | ✅ | M | `artwork_naming.py` |
| FR-013 | Aliasy REF, grupy mapowania, potwierdzanie masterów, wykrywanie braków i duplikatów | ✅ | S | `artwork_index.py`, `artwork_manage.py` |
| FR-014 | Karta artworku (REF): mastery, rewizje, poziomy opakowań, powiązania MARM | ✅ | S | `/artwork/card/<ref>` |
| FR-015 | Profile pól (szablony pól artworku) z historią zmian, wykrywaniem pól przez AI, słownikiem pól | ✅ | S | `/api/artwork/profiles*` |
| FR-016 | Model 3D z wykrojnika (W×H×D z tabeli metadanych, panele z linii bigowania), z fotografii i z danych MARM; podgląd w przeglądarce; akceptacja układu; batch | ✅ | S | `artwork_3d.py`, `/api/artwork/3d*` |
| FR-017 | Rejestr renderów, grupy renderów, push do PalViz z kluczem idempotencji i ponowieniem | ✅ | S | `artwork_render_registry.py`, `palviz_push.py` |
| FR-018 | Master data materiałów (REF, EAN, poziomy opakowań, przeliczniki UOM) i dostawców; import CSV/XLSX | ✅ | S | `material_master.py`, `supplier_master.py` |
| FR-019 | Przyjmowanie PDF z Power Automate (intake) tokenem | ✅ | C | `/api/intake/artwork` |
| FR-020 | Webhooki wychodzące (ERP/WMS) z podpisem HMAC | ✅ | C | `/api/webhooks*` |
| FR-021 | Budżet miesięczny AI z ostrzeżeniem/blokadą; koszty per model/typ | ✅ | S | `api_usage_tracker.py` |
| FR-022 | Administrator tworzy, dezaktywuje konta i zmienia role w aplikacji (z audytem) | ⚠️ (PR US-009) | S | `blueprints/users.py` |
| FR-023 | Interfejs PL z przełączeniem na EN | ⚠️ (EN przez post-processing HTML) | C | `translation_en.py` |
| FR-024 | Pomoc w aplikacji opisuje aktualne funkcje | ⚠️ | C | `help.html` (nieaktualna) |

## Reguły biznesowe

| ID | Reguła | Źródło |
|---|---|---|
| BR-001 | Suma kontrolna EAN/GTIN wg algorytmu GS1 (wagi 1/3); kod z błędną sumą = błąd krytyczny | `barcode_validator.py:validate_ean13` |
| BR-002 | GS1-128: AI 01 = GTIN (14), 10 = LOT (zmienna, FNC1), 17 = EXP (YYMMDD), 11 = data produkcji | `parse_gs1_128` |
| BR-003 | Różnica koloru: ΔE > 7,0 (tekst) / > 18,0 (grafika) = różnica | `constants.ARTWORK_DE_THRESH*` |
| BR-004 | Rewizja z nazwy pliku: wyższa rewizja (liczba/rzymska/litera) = nowsza; master potwierdzony ma pierwszeństwo | `artwork_naming.py` |
| BR-005 | Poziomy opakowania: SZT/OP/OPZ/KAR/PAZ/PPA z własnym EAN i wymiarami; konwersja przez `uom.py` | `material_master.py`, `uom.py` |
| BR-006 | Wynik AI jest doradczy; status końcowy ustala użytkownik | README, `artwork_report.html` |
| BR-007 | Pliki masterów nie opuszczają dysku `Z:\` poza miniaturami i potwierdzonymi masterami | `library_sync.py`, `/api/library/needed-masters` |
| BR-008 | Role: `user` widzi tylko swoje porównania; `superuser`/`admin` wszystkie; `manager` zarządza biblioteką | `core/security.py` |

## Wymagania niefunkcjonalne

| ID | Wymaganie | Status | Miara / cel |
|---|---|---|---|
| NFR-001 | Wydajność: porównanie pary PDF (2 strony, 150/220 DPI) ≤ 60 s bez AI, ≤ 180 s z AI | ⚠️ niemierzone | timeout gunicorn 300 s; semafor 3 |
| NFR-002 | Pojemność: indeks ≥ 31 000 plików; wyszukiwanie ≤ 1 s | ⚠️ | `tools/bench_artwork_browse.py` |
| NFR-003 | Dostępność: narzędzie wewnętrzne w godzinach pracy; `/health` dla sondy | ✅ | — |
| NFR-004 | Przenośność: SQLite (dev) i PostgreSQL (prod) z jednego kodu | ✅ | `db.py` |
| NFR-005 | Użyteczność: desktop Chrome, język PL, komunikaty błędów po polsku bez tracebacków | ⚠️ | `UX_AUDIT.md` |
| NFR-006 | Obserwowalność: logi rotowane, Sentry opcjonalny, audit log działań | ✅ | `core/audit.py` |
| NFR-007 | Koszty: AI w budżecie miesięcznym; limit 30 wywołań/min/użytkownika | ✅ | `api_usage_tracker.py` |
| NFR-008 | Jakość: CI blokuje merge przy błędzie testów, lintu (po US-002), SAST ≥ średnie, CVE ≥ wysokie, sekretach | ⚠️ (ten PR) | `.github/workflows/ci.yml` |
| NFR-009 | Pokrycie testami logiki domenowej ≥ 80 % (łącznie, 9 modułów — decyzja PO 2026-10-17) | ✅ bramka blokująca w CI | US-013, `tests/test_us013_*.py` |
| NFR-010 | RODO: minimalizacja, retencja, prawa osób — patrz `docs/bezpieczenstwo/RODO.md` | ✅ (DPA/szyfrowanie kopii — Z-04) | US-014 |
| NFR-011 | Zasoby: produkcja na 8 GB RAM, 2 workery × 3 wątki; ciężkie modele opcjonalne | ✅ | `gunicorn.conf.py` |

## Wymagania bezpieczeństwa (SEC-*)

Pełna lista w `docs/bezpieczenstwo/THREAT_MODEL.md` (§ zabezpieczenia) i `CHECKLISTA_ASVS.md`.
Najważniejsze jako kryteria akceptacji dla historyjek: SEC-001 limity logowania w DB + blokada konta;
SEC-002 tokeny resetu jako hash, ważność 1 h; SEC-003 sekrety tylko z env; SEC-004 „dane, nie instrukcje"
w promptach; SEC-005 CSP bez `unsafe-eval`; SEC-006 operacje na plikach fail-closed; SEC-007 test 403
dla każdej roli na każdym nowym endpointcie; SEC-008 zależności z lockiem i skanem w CI.
