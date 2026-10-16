# Rejestr ryzyk

> [SEC] Skala: wpływ (1–3) × prawdopodobieństwo (1–3) = ocena (≥6 wysokie, 3–4 średnie, ≤2 niskie).
> Decyzje: **mitygować** (historyjka), **akceptować** (PO podpisuje, data przeglądu), **przenieść**, **unikać**.
> Właściciel domyślny: PO (decyzja) / DEV (wdrożenie) / SEC (weryfikacja).

| ID | Ryzyko | Wpływ | Prawd. | Ocena | Decyzja | Historyjka | Właściciel | Przegląd |
|---|---|---|---|---|---|---|---|---|
| R-01 | Przejęcie konta przez brute-force (limit tylko per IP — rotacja IP go omija; brak blokady konta; słaba polityka haseł) | 3 | 2 | 6 🟠 | **zamknięte** (Sprint 1, 2026-10-16) | US-005 | DEV | 2026-11-15 |
| R-02 | Fałszywy werdykt AI przez prompt injection w PDF dostawcy → wadliwe opakowanie w druku | 3 | 2 | 6 🟠 | **zamknięte** (Sprint 2, #24; szczątkowe: AI tylko doradcze, werdykt deterministyczny) | US-007 | DEV | 2026-11-15 |
| R-03 | Wyciek klucza Anthropic z bazy/backupu (jawny zapis z UI) | 2 | 2 | 4 🟡 | **zamknięte** (Sprint 1, 2026-10-16) | US-004 | DEV | 2026-11-15 |
| R-04 | Przejęcie konta przez jawny token resetu z bazy (24 h) | 3 | 1 | 3 🟡 | **zamknięte** (Sprint 1, 2026-10-16) | US-003 | DEV | 2026-11-15 |
| R-05 | XSS wykonywalny przez CSP `unsafe-inline`/`unsafe-eval` + `innerHTML` | 2 | 2 | 4 🟡 | mitygować (etap 1 #28; etap 2a #33 — bez CDN i Babel; US-024 Alpine CSP odłożone decyzją PO 2026-10-16 — `unsafe-eval` zostaje, ryzyko średnie akceptowane do czasu wznowienia; dalej US-023) | US-008 | DEV | 2026-12-15 |
| R-06 | Zapis plików w dowolnym katalogu serwera przez managera (`save-copy` bez `ARTWORK_COPY_ROOTS`) | 2 | 2 | 4 🟡 | **zamknięte** (Sprint 2, #23) | US-006 | DEV | 2026-11-30 |
| R-07 | Konta zarządzane ręcznie w bazie — brak audytu i polityki haseł | 2 | 2 | 4 🟡 | mitygować | US-009 | DEV | 2026-12-15 |
| R-08 | Podatność w zależności niewykryta (zakresy bez locka, skan miesięczny), kontener jako root | 2 | 2 | 4 🟡 | obniżone (#25 non-root, #26 lock z hashami, #32 aktualizacje, #33 biblioteki JS przypięte w repo); otwarte do US-021 i weryfikacji obrazu | US-011, US-012 | DEV | 2026-11-30 |
| R-09 | Placeholder `SECRET_KEY` z `.env.example` w produkcji | 3 | 1 | 3 🟡 | **zamknięte** (Sprint 1, 2026-10-16) | US-018 | DEV | 2026-11-15 |
| R-10 | RODO: brak retencji audit logu, brak procedur praw osób, nieszyfrowane kopie, DPA z procesorami niepotwierdzone | 2 | 2 | 4 🟡 | mitygować | US-014 + Z-04 | PO | 2026-12-15 |
| R-11 | Błąd 500 przez niezdefiniowane nazwy (F821) w trasie managera | 2 | 3 | 6 🟠 (dostępność) | **zamknięte** (Sprint 1, 2026-10-16) | US-001 | DEV | 2026-11-01 |
| R-12 | DNS rebinding omija SSRF guard webhooków (sprawdzenie ≠ wysyłka) | 2 | 1 | 2 ⚪ | **akceptować** (admin konfiguruje webhooki; koszt obejścia wysoki) | — | PO | 2027-04-15 |
| R-13 | Wyczerpanie zasobów przez duże PDF (200 MB, 220 DPI, brak limitu stron) przez zalogowanego użytkownika | 2 | 1 | 2 ⚪ | **zamknięte** (Sprint 3, #31; szczątkowe: limit uploadu 200 MB bez zmian) | US-019 | PO | 2027-01-15 |
| R-14 | Utrata plików tymczasowych/masterów przy redeployu bez wolumenu `/data` | 2 | 2 | 4 🟡 | mitygować konfiguracją (RUNBOOK) | — | admin | 2026-11-15 |
| R-15 | Dług dokumentacyjny: 5 dokumentów opisuje DocCompare, README obiecuje nieistniejącą funkcję | 1 | 3 | 3 🟡 | mitygować | US-016 | BA | 2026-12-15 |

## Wyjątki (świadoma akceptacja ryzyka)

| ID | Wyjątek | Uzasadnienie | Zaakceptował | Data | Przegląd |
|---|---|---|---|---|---|
| W-01 | `# nosec B608` w 6 miejscach (interpolacja nazw kolumn/placeholderów) | nazwy z białych list w kodzie, wartości parametryzowane; każde miejsce ma komentarz | SEC (propozycja) — **do potwierdzenia PO** | 2026-10-15 | 2027-04-15 |
| W-02 | `.gitleaks.toml` allowlista: `itpass-*-123`, `test-csrf-token-deadbeef`, `test-*-secret`, `YOUR_*_HERE`, syntetyczne hasła/tokeny z testów US-003/US-005 (wymienione z nazwy w pliku) | syntetyczne dane testowe i placeholdery szablonów env; gitleaks skanuje historię commitów, więc wpisy są po wartości, nie po ścieżce | SEC (propozycja) — **do potwierdzenia PO** | 2026-10-15 | 2027-04-15 |
| W-03 | Semgrep i `ruff format` doradcze w CI do triage / decyzji PO (US-020); `ruff check` blokuje od US-002 (2026-10-16) | 66 błędów legacy usunięte; formatowanie = wielki diff bez wartości; Semgrep wymaga triage szumu | SEC+DEV — **do potwierdzenia PO** | 2026-10-16 | 2026-11-15 |
| W-04 | Podatności (5 high, 2 moderate) w narzędziach budowania Tailwind 3 (`braces`, `micromatch`, `chokidar`, `postcss-selector-parser`) — devDependencies w `package-lock.json` | tylko czas budowy (`npm run build`), wzorce glob kontrolowane w repo; do przeglądarki i na serwer trafiają wyłącznie zbudowane pliki; poprawka wymaga Tailwind 4 (inna konfiguracja i wygląd) | PO (akceptacja #33) | 2026-10-16 | 2027-01-15 |
