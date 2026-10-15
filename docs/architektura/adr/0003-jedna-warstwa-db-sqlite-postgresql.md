# ADR-0003: Jedna warstwa dostępu do danych dla SQLite i PostgreSQL (translacja SQL w `db.py`)

- **Status:** zaakceptowany (decyzja historyczna, udokumentowana 2026-10-15)
- **Rola:** [DEV]

## Kontekst
Dev i testy działają na SQLite (zero infrastruktury, 4 s testów); produkcja na PostgreSQL (Supabase/Neon/Coolify).
Kod używa surowego SQL w dialekcie SQLite.

## Opcje
1. ORM (SQLAlchemy) — przepisanie ~setek zapytań, duży diff, nowe ryzyko.
2. Tylko PostgreSQL (także w dev/CI przez kontener) — wolniejsze CI, trudniejszy onboarding.
3. **Cienka warstwa `db.py`**: `get_db()` zwraca połączenie z puli; dla PG tłumaczy `?`→`%s`,
   `datetime('now')`→`NOW()`, `INSERT OR IGNORE`→`ON CONFLICT DO NOTHING`, `AUTOINCREMENT`→`SERIAL`,
   `BLOB`→`BYTEA`; `_PGRow` imituje `sqlite3.Row`.

## Decyzja
Opcja 3 (istniejąca). Zasady: zawsze `db.get_db()`, zawsze parametryzacja, nazwy kolumn/tabel tylko z białych
list (komentarz `# nosec B608` z uzasadnieniem), `escape_like()` dla LIKE, porównania dat w Pythonie przy
kolumnach TEXT.

## Konsekwencje
- (+) Szybkie testy i dev bez infrastruktury; jeden kod dla obu baz.
- (−) Translacja regexowa jest krucha (`INSERT OR REPLACE`, `ADD CONSTRAINT IF NOT EXISTS`, typy dat) —
  każda nowa konstrukcja SQL wymaga testu na obu bazach; CI testuje dziś tylko SQLite (luka: NFR-004).
- (−) Brak wersjonowanych migracji — `schema_migrations` istnieje, ale schemat jest rozsiany po 10 plikach;
  kandydat na kolejny ADR (narzędzie migracji) po US-010.
