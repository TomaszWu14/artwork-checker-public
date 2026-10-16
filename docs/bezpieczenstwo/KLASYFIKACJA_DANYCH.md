# Klasyfikacja danych

> [SEC] Klasy: **P** publiczne · **W** wewnętrzne · **PF** poufne · **DO** dane osobowe (RODO).
> Zasada: dane PF nigdy w repo, logach, odpowiedziach błędów ani w promptach do AI; DO — minimalizacja i retencja.

| Dane | Klasa | Gdzie | Kto ma dostęp | Retencja (propozycja) | Uwagi |
|---|---|---|---|---|---|
| `SECRET_KEY`, `DATABASE_URL`, klucze API (Anthropic, Mistral, Resend, PalViz, GLM), `INTAKE_TOKEN`, `SENTRY_DSN` | PF | env hostingu, `.env` (gitignored) | admin hostingu | rotacja ≥ raz/rok i po incydencie | klucz AI obecnie także w `settings` (US-004) |
| Token synchronizacji biblioteki | PF | `settings` (category=library) | admin (reset), agent | rotacja przez `/api/library/token-reset` | |
| Hashe haseł | PF | `users.password_hash` | aplikacja | do usunięcia konta | Werkzeug scrypt/pbkdf2 |
| Tokeny resetu hasła | PF | `password_reset_tokens` | aplikacja | 24 h → 1 h (US-003) | jawne → hash (US-003) |
| Sekrety webhooków | PF | `webhooks.secret` | admin | — | HMAC-SHA256 podpisu |
| Kopie bazy SQLite (`backups/`) | PF | dysk serwera | admin | 7 dni rotacji (RUNBOOK) | nieszyfrowane — R-10 |
| Konta: `username`, `email`, `department`, `language`, `last_login` | DO | `users` | admin; użytkownik swoje | okres zatrudnienia + 30 dni | FR-022 |
| `audit_log` (nazwa użytkownika, IP, akcja) | DO | `audit_log` | manager+ (`/api/admin/activity-log`) | 12 miesięcy (US-014) | podstawa: prawnie uzasadniony interes (bezpieczeństwo) |
| Komentarze do pól, autorstwo porównań | DO (pośrednio) | `artwork_field_comments`, `comparisons.user_id` | właściciel, manager+ | jak porównania | |
| `api_usage.user_id`, `api_rate_events` | DO (pośrednio) | DB | admin/manager | 12 miesięcy | rozliczenie kosztów |
| Artworki dostawców, mastery, miniatury, raporty, GLB | W | `uploads/`, `/data`, `library_files.thumb_data`, `artwork_master_file.data`, `Z:\` | zalogowani wg roli | tymczasowe: usuwane po porównaniu; mastery: bezterminowo | know-how opakowań, oznaczenia medyczne; fragmenty mogą trafiać do AI/OCR API (Z-04) |
| Indeks biblioteki (nazwy plików, REF, ścieżki `Z:\`) | W | `library_files`, `artwork_index` | zalogowani | bezterminowo | ścieżki ujawniają strukturę dysku — tylko dla zalogowanych |
| Master data (REF, EAN, wymiary, dostawcy) | W | `material_master`, `suppliers`, `ref_database` | zalogowani | bezterminowo | |
| Koszty API, KPI | W | `api_usage`, widoki KPI | manager+ | | |
| Logi aplikacji (`logs/app.log`) | W (+DO: IP w audycie CSRF) | dysk | admin | 5 plików × 10 MB (rotacja) | bez haseł/tokenów — sprawdzone grep |
| Strona logowania, `/health`, `robots.txt` | P | — | wszyscy | | `/health` bez metryk biznesowych |
| Kod źródłowy, dokumentacja | P (portfolio) | GitHub | wszyscy | | dane demo syntetyczne; LICENSE: wszystkie prawa zastrzeżone |

## Przepływy danych do podmiotów zewnętrznych

| Odbiorca | Co wysyłamy | Klasa | Warunek |
|---|---|---|---|
| Anthropic (Claude) | tekst OCR (do 3000 znaków/plik), obrazy stron artworku, nazwy plików | W | zgoda PO (Z-04), DPA, `use_ai` włączone przez użytkownika |
| Mistral OCR | obrazy stron | W | jak wyżej; klucz opcjonalny |
| Resend | adres e-mail, nazwa użytkownika, link resetu | DO + PF (token) | tylko reset hasła |
| Sentry | stack trace, ścieżka żądania, IP (domyślnie) | W/DO | opcjonalny; wyłączyć `send_default_pii` |
| PalViz | metadane renderu (REF, wariant, hash, nazwa pliku) | W | `PALVIZ_PUSH_URL` ustawione |
| Webhooki ERP/WMS | zdarzenia porównań (nazwy plików, status) | W | tylko adresy publiczne (SSRF guard), HMAC |
