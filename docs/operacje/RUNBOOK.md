# Runbook — wdrożenie, kopie, odtworzenie, incydenty

> [DEV]/[SEC] Repo nie ma dziś celu produkcyjnego (CLAUDE.md). Poniżej procedury dla wariantu
> Docker/Coolify oraz Render (`render.yaml`). Sekrety wyłącznie w env hostingu.

## 1. Wdrożenie

### Docker / Coolify
1. Zbuduj obraz: `docker build -t artwork:$(git rev-parse --short HEAD) .` (pełny, ~8 min) lub
   `Dockerfile.slim` na bazie `ghcr.io/<owner>/doccompare-ml-base` (`docs/OBRAZ_BAZOWY_ML.md`).
2. Ustaw env (minimum): `SECRET_KEY` (`python -c "import secrets;print(secrets.token_hex(32))"`),
   `DATABASE_URL` **lub** `SQLITE_PATH=/data/doccompare.db`, `DATA_DIR=/data`, `UPLOAD_FOLDER=/data/uploads`,
   `APP_BASE_URL`, `LOG_DIR`, `WEB_CONCURRENCY=2`, `THREADS_PER_WORKER=3`, `DISABLE_QWEN=1`.
   Opcjonalnie: `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `RESEND_API_KEY`+`EMAIL_FROM`, `SENTRY_DSN`,
   `INTAKE_TOKEN`, `PALVIZ_PUSH_URL`+`PALVIZ_API_KEY`, `ARTWORK_COPY_ROOTS`, `REDIS_URL`.
3. Zamontuj trwały wolumen `/data` (bez niego uploady i SQLite giną przy redeployu — R-14).
4. Start: `python migrate_db.py && gunicorn app:app -c gunicorn.conf.py` (CMD w Dockerfile). Migracja jest idempotentna.
5. Pierwsze uruchomienie tworzy konto `admin` z losowym hasłem: w logach i w `INITIAL_ADMIN_PASSWORD.txt`
   (katalog aplikacji, `chmod 600`). Zaloguj się, zmień hasło (`/profile`), usuń plik.
6. Sonda: `GET /health` → `{"status":"ok","db":"ok"}` (503 gdy baza/dysk degraded). Render używa `/login`.

### Render
`render.yaml`: `buildCommand` instaluje `requirements-prod.txt` i uruchamia migrację; `SECRET_KEY` generowany;
dysk `doccompare-data` 1 GB pod `/data`.

## 2. Kopie zapasowe
| Co | Jak | Częstotliwość | Przechowywanie |
|---|---|---|---|
| PostgreSQL | snapshot/PITR dostawcy (Supabase/Neon/Coolify) lub `pg_dump -Fc "$DATABASE_URL" > backup_$(date +%F).dump` | codziennie | 30 dni, szyfrowane, poza hostem |
| SQLite | `POST /api/admin/backup` (admin) → `backups/` lub `sqlite3 /data/doccompare.db ".backup /backups/db_$(date +%F).sqlite"` | codziennie (cron hosta) | 7 dni lokalnie + kopia poza hostem |
| Wolumen `/data` (mastery, GLB, uploads) | snapshot wolumenu / `rsync` | codziennie | 30 dni |
| Sekrety | menedżer sekretów hostingu | przy zmianie | — |

**Test odtworzenia** (raz na kwartał, zapisz wynik tutaj): przywróć dump do pustej bazy, uruchom aplikację,
zaloguj się, otwórz historię porównań i kartę artworku. Ostatni test: **brak** (do zaplanowania).

## 3. Odtworzenie
1. Nowy kontener z tym samym obrazem i env. 2. Przywróć bazę (`pg_restore -d "$DATABASE_URL" backup.dump`
   lub skopiuj plik SQLite na `/data`). 3. Przywróć `/data`. 4. `python migrate_db.py`. 5. Sprawdź `/health`
   i logowanie. 6. Zrotuj sekrety, jeśli odtwarzanie wynika z incydentu.

## 4. Operacje rutynowe
- **Rotacja tokenu agenta:** admin → `/library` → „Resetuj token" (`POST /api/library/token-reset`); nowy token w
  `LIBRARY_SYNC_TOKEN` agenta.
- **Rotacja kluczy API:** zmień w env hostingu, restart; usuń stary klucz u dostawcy.
- **Budżet AI:** `/api/ai/budget` (admin) — limit USD/miesiąc; przekroczenie blokuje wywołania.
- **Logi:** stdout (gunicorn) + `LOG_DIR/app.log` (5×10 MB); poziom `LOG_LEVEL`.
- **Miejsce na dysku:** `/admin` pokazuje użycie; `/health` ostrzega < 200 MB; `uploads/` czyszczone po porównaniu,
  `artwork3d/` i `glb_cache/` można usunąć (odtwarzalne).

## 5. Incydenty

| Objaw | Diagnoza | Działanie |
|---|---|---|
| 500 na wielu stronach | logi: `OperationalError` → baza | sprawdź `DATABASE_URL`/pulę (`DB_POOL_SIZE`); `check_session_active` działa fail-open przy awarii DB |
| 502/timeout przy porównaniu | gunicorn timeout 300 s, OOM (2 workery × ~2 GB) | zmniejsz DPI/strony, `DISABLE_QWEN=1`, więcej RAM, kolejka RQ |
| „Zbyt wiele prób" dla legalnego użytkownika | limit 5/15 min per IP (NAT firmowy) | odczekać 15 min; restart workerów zeruje licznik; docelowo US-005 |
| Podejrzenie wycieku sekretu | gitleaks w CI / zgłoszenie | **natychmiast**: zrotuj sekret u dostawcy i w env, unieważnij sesje (zmiana `SECRET_KEY`), przejrzyj `audit_log` i logi dostawcy, wpis w rejestrze incydentów, ocena RODO (72 h) |
| Nieautoryzowany dostęp do konta | `audit_log` login z obcego IP | dezaktywuj konto (`UPDATE users SET is_active=0`), zresetuj hasło, przejrzyj działania, zgłoś PO |
| Agent sync odrzucany (401) | token zrotowany | ustaw nowy `LIBRARY_SYNC_TOKEN` |
| Push do PalViz `failed` | `/admin/palviz-push`, `push_error` | sprawdź `PALVIZ_PUSH_URL`/klucz; ponów (`push-retry`, min. 30 s odstępu) |
| Brak e-maili resetu | `RESEND_API_KEY`/`EMAIL_FROM` | test: `POST /api/email/test` (admin) |

Rejestr incydentów: prowadzić jako issues z etykietą `incident` (szablon `security_issue`, bez szczegółów exploitu
w publicznym repo — szczegóły prywatnym kanałem, patrz `SECURITY.md`).
