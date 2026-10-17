"""
migrate_db.py — migracja bazy danych doccompare.

Działa zarówno z SQLite (lokalnie) jak i PostgreSQL (Coolify/Render).
Uruchom po każdej aktualizacji kodu:
    python migrate_db.py

Bezpieczny: każda migracja jest w try/except, nie uszkodzi danych.
"""

import os
import sys

from db import get_db, DATABASE_URL

IS_PG = bool(DATABASE_URL)

_schema_cache: dict[tuple, bool] = {}


def _col_exists(db, table: str, col: str) -> bool:
    """Sprawdza czy kolumna istnieje — obsługa SQLite i PostgreSQL."""
    key = ("col", table, col)
    if key in _schema_cache:
        return _schema_cache[key]
    if IS_PG:
        row = db.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = ?",
            (table, col),
        ).fetchone()
    else:
        row = None
        for r in db.execute(f"PRAGMA table_info({table})").fetchall():
            if r[1] == col:
                row = r
                break
    result = row is not None
    _schema_cache[key] = result
    return result


def _table_exists(db, table: str) -> bool:
    key = ("tbl", table)
    if key in _schema_cache:
        return _schema_cache[key]
    if IS_PG:
        row = db.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = ?",
            (table,),
        ).fetchone()
    else:
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
    result = row is not None
    _schema_cache[key] = result
    return result


def add_column(db, table: str, col: str, definition: str):
    if not _table_exists(db, table):
        print(
            f"  ⏭   {table}.{col} — tabela nie istnieje (powstanie przy starcie aplikacji); pomijam"
        )
        return
    if _col_exists(db, table, col):
        print(f"  ⏭   {table}.{col} — już istnieje")
        return
    try:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
        db.commit()
        # Uniewa­żnij cache: _col_exists zapisał False przy pre-checku; bez tego
        # późniejsza weryfikacja widzi stare False i zgłasza fałszywy brak kolumny.
        _schema_cache[("col", table, col)] = True
        print(f"  ✅  {table}.{col} — dodano")
    except Exception as e:
        print(f"  ⚠   {table}.{col} — błąd: {e}")


def create_table(db, ddl: str, table_name: str):
    try:
        db.execute(ddl)
        db.commit()
        # Uniewa­żnij/ustaw cache istnienia tabeli: bez tego pre-check w
        # _table_exists mógł zapisać False przed utworzeniem, przez co późniejsze
        # add_column/create_index dla świeżo utworzonej tabeli byłyby pomijane.
        _schema_cache[("tbl", table_name)] = True
        print(f"  ✅  Tabela {table_name} — gotowa")
    except Exception as e:
        print(f"  ⚠   Tabela {table_name} — błąd: {e}")


def create_index(db, name: str, table: str, cols: str):
    if not _table_exists(db, table):
        print(
            f"  ⏭   Indeks {name} — tabela {table} nie istnieje (powstanie przy starcie aplikacji); pomijam"
        )
        return
    try:
        db.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table}({cols})")
        db.commit()
        print(f"  ✅  Indeks {name}")
    except Exception as e:
        print(f"  ⚠   Indeks {name} — błąd: {e}")


def _backfill_library_ref(db):
    """Uzupełnia ref/packaging_type w library_files dla wierszy, które ich nie mają
    (zsyncowane przed dodaniem kolumn). Parsuje z nazwy pliku. Idempotentne."""
    if not _table_exists(db, "library_files"):
        return
    try:
        from artwork_naming import parse_master_filename
    except Exception as e:
        print(f"  ⏭   Backfill ref — brak artwork_naming ({e}); pomijam")
        return
    rows = db.execute(
        "SELECT id, filename FROM library_files WHERE COALESCE(ref,'')='' "
        "AND lower(filename) LIKE '%.pdf'"
    ).fetchall()
    n = 0
    for r in rows:
        p = parse_master_filename(r["filename"])
        if p["ref"]:
            db.execute(
                "UPDATE library_files SET ref=?, packaging_type=? WHERE id=?",
                (p["ref"], p["packaging_type"], r["id"]),
            )
            n += 1
    db.commit()
    print(f"  ✅  Backfill ref/packaging: {n} wierszy")


def _record_migration(db, version: int, description: str):
    """Record a successfully applied migration version."""
    try:
        db.execute(
            "INSERT INTO schema_migrations(version, description) VALUES(?, ?) "
            "ON CONFLICT(version) DO NOTHING",
            (str(version), description),
        )
        db.commit()
    except Exception:
        pass


def run():
    db_label = (
        DATABASE_URL.split("@")[-1]
        if IS_PG
        else os.environ.get("SQLITE_PATH", "instance/doccompare.db")
    )
    print(f"\n{'═' * 60}")
    print(f"  Migracja: {'PostgreSQL' if IS_PG else 'SQLite'} — {db_label}")
    print(f"{'═' * 60}\n")

    db = get_db()

    # ── Tabele wersji migracji ────────────────────────────────────
    # Schemat zgodny z app.py (_db_track_schema_version): version jako TEXT, aby
    # pomieścić zarówno numery rund (2,3) jak i hash wersji schematu z aplikacji.
    create_table(
        db,
        """CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TEXT DEFAULT (datetime('now')),
        description TEXT DEFAULT ''
    )""",
        "schema_migrations",
    )

    # ── Tabele bazowe ─────────────────────────────────────────────
    print("── Tabele bazowe ──")

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        )
    """,
        "users",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doc_type TEXT,
            file_a TEXT,
            file_b TEXT,
            result_json TEXT,
            status TEXT DEFAULT 'ok',
            diff_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """,
        "comparisons",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            country TEXT DEFAULT 'XX',
            currency TEXT DEFAULT 'USD',
            language TEXT DEFAULT 'EN',
            price_rounding INTEGER DEFAULT 4,
            po_rounding INTEGER DEFAULT 2,
            payment_terms_json TEXT DEFAULT '{}',
            date_format TEXT DEFAULT '%Y/%m/%d',
            known_issues_json TEXT DEFAULT '[]',
            price_tolerance_pct REAL DEFAULT 0.5,
            qty_tolerance_pct REAL DEFAULT 0.0,
            detect_keywords_json TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "suppliers",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE(category, key)
        )
    """,
        "settings",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS comparison_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comparison_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            comment_type TEXT DEFAULT 'note',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "comparison_comments",
    )

    # Składnica bajtów masterów artworków (agent dosyła pliki potwierdzonych/grupowych).
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_master_file (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rel_path TEXT UNIQUE NOT NULL,
            stored_name TEXT NOT NULL,
            content_type TEXT DEFAULT 'application/pdf',
            size INTEGER DEFAULT 0,
            data BLOB,
            uploaded_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_master_file",
    )

    # Grupy mapowań artworków (grupa → lista REF + jeden master).
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_mapping_group (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            master_rel_path TEXT DEFAULT '',
            refs_json TEXT DEFAULT '[]',
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_mapping_group",
    )

    # Akceptacja układu modelu 3D + baza uczenia orientacji. Jeden wiersz = jeden
    # zatwierdzony przez człowieka model; ten sam wiersz jest źródłem podpowiedzi dla
    # kolejnych artworków o tym samym REF/typie opakowania (patrz _a3d_learned w app.py).
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_3d_orientation (
            glb_name TEXT PRIMARY KEY,
            ref TEXT DEFAULT '',
            packaging_type TEXT DEFAULT '',
            package_type TEXT DEFAULT '',
            grupa TEXT DEFAULT '',
            podgrupa TEXT DEFAULT '',
            roll INTEGER DEFAULT 0,
            pitch INTEGER DEFAULT 0,
            yaw INTEGER DEFAULT 0,
            accepted_by TEXT,
            accepted_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_3d_orientation",
    )
    create_index(db, "idx_a3d_orient_key", "artwork_3d_orientation", "ref, packaging_type")
    create_index(db, "idx_a3d_orient_grupa", "artwork_3d_orientation", "grupa, podgrupa")
    add_column(db, "artwork_3d_orientation", "grupa", "TEXT DEFAULT ''")
    add_column(db, "artwork_3d_orientation", "podgrupa", "TEXT DEFAULT ''")

    # MARM-01/02 (Faza 3): trwałe powiązanie artwork (REF) → wiersz MARM (ref, unit).
    # Ustawiane ręcznie przy generowaniu 3D z MARM, czytane jako domyślne przy
    # ponownym otwarciu generatora dla tego artworku (propose/correct/remember).
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_marm_link (
            art_ref_norm TEXT PRIMARY KEY,
            marm_ref     TEXT DEFAULT '',
            marm_unit    TEXT DEFAULT '',
            updated_by   TEXT,
            updated_at   TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_marm_link",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS supplier_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER,
            supplier_code TEXT,
            action TEXT,
            changed_by TEXT,
            changed_at TEXT DEFAULT (datetime('now')),
            diff_json TEXT
        )
    """,
        "supplier_audit_log",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS library_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rel_path TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            size_bytes INTEGER DEFAULT 0,
            modified_at TEXT,
            synced_at TEXT DEFAULT (datetime('now')),
            checksum TEXT,
            lvl1 TEXT DEFAULT '',
            lvl2 TEXT DEFAULT '',
            lvl3 TEXT DEFAULT '',
            lvl4 TEXT DEFAULT '',
            lvl5 TEXT DEFAULT '',
            file_path TEXT DEFAULT ''
        )
    """,
        "library_files",
    )

    # Cache modeli 3D (GLB) generowanych leniwie z plików biblioteki. Klucz = fid
    # pliku; checksum pilnuje świeżości (zmiana pliku na Z:\ → re-render). Plik GLB
    # leży na dysku (DATA_DIR/glb_cache), tu tylko wskaźnik + wymiary użyte do renderu.
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_glb_cache (
            fid INTEGER PRIMARY KEY,
            checksum TEXT DEFAULT '',
            glb_path TEXT NOT NULL,
            w_mm REAL DEFAULT 0,
            h_mm REAL DEFAULT 0,
            d_mm REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_glb_cache",
    )

    # Nazwane grupy produktowe do renderu 3D (np. „Rękawice" spinające kilka folderów
    # biblioteki). members_json = {"folders": [rel_path-prefix...], "file_ids": [...]}.
    # Render grupy: rozwiń członków → wybierz aktualne rewizje → GLB do cache w tle.
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS render_group (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            members_json TEXT DEFAULT '{}',
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "render_group",
    )

    # Rejestr renderów 3D (Faza 1) — append-only log „co i kiedy wyrenderowano".
    # Klucz tożsamości: fid (rendery z biblioteki) gdy dostępny, inaczej ref_norm
    # (accept path: manual/photo/MARM — D-04). Ten sam source_hash dla (klucz,
    # variant) bumpuje last_confirmed_at zamiast tworzyć nowy wiersz; zmiana
    # source_hash dopisuje nowy wiersz (append-only, D-02) — brak is_current/
    # superseded_at, „aktualny" = MAX(created_at). Patrz artwork_render_registry.py.
    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_render_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fid INTEGER,
            ref_norm TEXT DEFAULT '',
            variant TEXT NOT NULL,
            source_hash TEXT DEFAULT '',
            glb_path TEXT NOT NULL,
            created_by INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            last_confirmed_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_render_registry",
    )
    create_index(db, "idx_arr_fid_variant", "artwork_render_registry", "fid, variant")
    create_index(db, "idx_arr_refnorm_variant", "artwork_render_registry", "ref_norm, variant")
    # PUSH-02 (Faza 4): status wypchnięcia wiersza rejestru do PalViz.
    add_column(db, "artwork_render_registry", "push_status", "TEXT DEFAULT 'pending'")
    add_column(db, "artwork_render_registry", "push_at", "TEXT")
    add_column(db, "artwork_render_registry", "push_error", "TEXT DEFAULT ''")
    add_column(db, "artwork_render_registry", "push_attempts", "INTEGER DEFAULT 0")

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            total INTEGER DEFAULT 0,
            done INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0,
            pairs_json TEXT DEFAULT '[]',
            results_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_batch_jobs",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            user_id INTEGER,
            model TEXT,
            call_type TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0.0
        )
    """,
        "api_usage",
    )

    # ── Migracje — brakujące kolumny ─────────────────────────────

    print("\n── Kolumny tabeli: comparisons ──")
    add_column(db, "comparisons", "po_number", "TEXT DEFAULT ''")
    add_column(db, "comparisons", "supplier_code", "TEXT DEFAULT ''")
    add_column(db, "comparisons", "total_a", "TEXT DEFAULT ''")
    add_column(db, "comparisons", "total_b", "TEXT DEFAULT ''")
    add_column(db, "comparisons", "comment", "TEXT DEFAULT ''")
    add_column(db, "comparisons", "approval_status", "TEXT DEFAULT 'pending'")
    add_column(db, "comparisons", "approved_by", "INTEGER")
    add_column(db, "comparisons", "approved_at", "TEXT")
    add_column(db, "comparisons", "file_hash_a", "TEXT")
    add_column(db, "comparisons", "file_hash_b", "TEXT")
    add_column(db, "comparisons", "is_deleted", "INTEGER DEFAULT 0")

    print("\n── Kolumny tabeli: users ──")
    add_column(db, "users", "last_login", "TEXT")
    add_column(db, "users", "email", "TEXT")
    add_column(db, "users", "is_active", "INTEGER DEFAULT 1")
    add_column(db, "users", "forwarder_id", "INTEGER")  # spedytor zewnętrzny → firma spedycyjna
    add_column(db, "users", "customs_agency_id", "INTEGER")  # agent celny → agencja celna

    print("\n── Kolumny tabeli: library_files ──")
    add_column(db, "library_files", "file_path", "TEXT DEFAULT ''")
    add_column(db, "library_files", "thumb_data", "BLOB")
    add_column(db, "library_files", "z_path", "TEXT DEFAULT ''")
    # REF + typ opakowania sparsowane z nazwy — szybki lookup po REF (render z listy REF)
    add_column(db, "library_files", "ref", "TEXT DEFAULT ''")
    add_column(db, "library_files", "packaging_type", "TEXT DEFAULT ''")
    create_index(db, "idx_library_files_ref", "library_files", "ref")
    # Backfill: uzupełnij ref/packaging dla już zsyncowanych wierszy (jednorazowo).
    _backfill_library_ref(db)

    print("\n── Kolumny tabeli: suppliers ──")
    add_column(db, "suppliers", "column_mapping_json", "TEXT DEFAULT '{}'")
    add_column(db, "suppliers", "synonyms_json", "TEXT DEFAULT '[]'")
    add_column(db, "suppliers", "pi_column_mapping_json", "TEXT DEFAULT '{}'")
    add_column(db, "suppliers", "po_column_mapping_json", "TEXT DEFAULT '{}'")
    add_column(db, "suppliers", "ref_format_pi", "TEXT DEFAULT 'standard'")
    add_column(db, "suppliers", "ref_format_po", "TEXT DEFAULT 'standard'")
    add_column(db, "suppliers", "wizard_completed", "INTEGER DEFAULT 0")
    add_column(db, "suppliers", "profile_updated_at", "TEXT")
    add_column(db, "suppliers", "profile_updated_by", "TEXT")
    add_column(db, "suppliers", "profile_version", "INTEGER DEFAULT 1")
    add_column(db, "suppliers", "header_patterns_json", "TEXT DEFAULT '{}'")
    add_column(db, "suppliers", "ignore_fields_json", "TEXT DEFAULT '[]'")
    add_column(db, "suppliers", "custom_rules_json", "TEXT DEFAULT '[]'")
    add_column(db, "suppliers", "sad_column_mapping_json", "TEXT DEFAULT '{}'")

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS ref_database (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            uploaded_by INTEGER,
            uploaded_at TEXT DEFAULT (datetime('now')),
            UNIQUE(ref_code)
        )
    """,
        "ref_database",
    )

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_profiles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            description     TEXT DEFAULT '',
            ean             TEXT DEFAULT '',
            ref_code        TEXT DEFAULT '',
            ref_list_json   TEXT DEFAULT '[]',
            master_pdf_path TEXT DEFAULT '',
            thumb_b64       TEXT DEFAULT '',
            page_width_mm   REAL DEFAULT 0,
            page_height_mm  REAL DEFAULT 0,
            is_active       INTEGER DEFAULT 1,
            created_by      INTEGER,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now'))
        )
    """,
        "artwork_profiles",
    )
    add_column(db, "artwork_profiles", "ref_list_json", "TEXT DEFAULT '[]'")
    add_column(db, "artwork_profiles", "master_pdf_path", "TEXT DEFAULT ''")
    add_column(db, "artwork_profiles", "thumb_b64", "TEXT DEFAULT ''")
    add_column(db, "artwork_profiles", "use_count", "INTEGER DEFAULT 0")
    add_column(db, "artwork_profiles", "folder_path", "TEXT DEFAULT ''")
    # Kolumny mastera niezależnego (upload z dysku do mapowania pól) — bez nich
    # INSERT/SELECT do artwork_profiles padał: „column packaging_type does not exist".
    add_column(db, "artwork_profiles", "packaging_type", "TEXT DEFAULT ''")
    add_column(db, "artwork_profiles", "revision", "TEXT DEFAULT ''")
    add_column(db, "artwork_profiles", "revision_rank", "INTEGER DEFAULT 0")
    add_column(db, "artwork_profiles", "source_path", "TEXT DEFAULT ''")
    add_column(db, "artwork_profiles", "is_current_revision", "INTEGER DEFAULT 1")
    # master_pdf_path jest warunkiem JOIN-a przy przeglądaniu i wyszukiwaniu biblioteki
    # (library_files.file_path = artwork_profiles.master_pdf_path) — bez indeksu każde
    # otwarcie biblioteki skanowało całą tabelę profili dla każdego wiersza strony.
    create_index(db, "idx_artwork_profiles_master_path", "artwork_profiles", "master_pdf_path")

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS artwork_profile_fields (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id   INTEGER NOT NULL,
            field_name   TEXT NOT NULL,
            display_name TEXT NOT NULL,
            x1_pct       REAL NOT NULL,
            y1_pct       REAL NOT NULL,
            x2_pct       REAL NOT NULL,
            y2_pct       REAL NOT NULL,
            severity     TEXT DEFAULT 'critical',
            notes        TEXT DEFAULT '',
            sort_order   INTEGER DEFAULT 0,
            size_label   TEXT DEFAULT '',
            skip_analysis INTEGER DEFAULT 0
        )
    """,
        "artwork_profile_fields",
    )
    add_column(db, "artwork_profile_fields", "size_label", "TEXT DEFAULT ''")
    add_column(db, "artwork_profile_fields", "skip_analysis", "INTEGER DEFAULT 0")
    add_column(db, "artwork_profile_fields", "display_layout", "TEXT DEFAULT 'side_by_side'")

    create_table(
        db,
        """
        CREATE TABLE IF NOT EXISTS intake_queue (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            filename   TEXT NOT NULL,
            path       TEXT NOT NULL,
            sender     TEXT DEFAULT '',
            subject    TEXT DEFAULT '',
            status     TEXT DEFAULT 'new',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """,
        "intake_queue",
    )

    # ── Indeksy ───────────────────────────────────────────────────
    print("\n── Indeksy ──")
    create_index(db, "idx_comparisons_user", "comparisons", "user_id")
    create_index(db, "idx_comparisons_created", "comparisons", "created_at DESC")
    create_index(db, "idx_comparisons_po", "comparisons", "po_number")
    create_index(db, "idx_comparisons_supplier", "comparisons", "supplier_code")
    create_index(db, "idx_comparisons_status", "comparisons", "status")
    create_index(db, "idx_comparisons_hashes", "comparisons", "file_hash_a, file_hash_b")
    create_index(db, "idx_comparisons_user_status", "comparisons", "user_id, status")
    create_index(db, "idx_comparisons_user_created", "comparisons", "user_id, created_at DESC")
    create_index(db, "idx_comparisons_approval", "comparisons", "approval_status, is_deleted")
    create_index(
        db, "idx_comparisons_user_del_date", "comparisons", "user_id, is_deleted, created_at"
    )
    create_index(db, "idx_audit_log_user_date", "audit_log", "username, created_at DESC")
    create_index(db, "idx_audit_log_event", "audit_log", "event, created_at DESC")
    create_index(db, "idx_suppliers_code", "suppliers", "code")
    create_index(db, "idx_settings_cat", "settings", "category, key")
    create_index(db, "idx_ref_database_code", "ref_database", "ref_code")
    create_index(db, "idx_users_created_at", "users", "created_at")

    # Missing indexes discovered in audit
    create_index(db, "idx_comparisons_doc_type", "comparisons", "doc_type")
    create_index(db, "idx_audit_log_username", "audit_log", "username")
    create_index(db, "idx_users_email", "users", "email")
    create_index(db, "idx_comparisons_approval_status", "comparisons", "approval_status")
    create_index(db, "idx_notifications_user_read", "notifications", "user_id, is_read")

    print("\n── Kolumny tabeli: settings ──")
    # Wyrażeniowy DEFAULT (datetime('now')) jest castowany na ::TEXT tylko w gałęzi
    # CREATE TABLE w db._pg_sql; w ALTER ADD COLUMN na PG zostaje DEFAULT (NOW())
    # → przypisanie timestamptz do kolumny TEXT → błąd i kolumna nie powstaje
    # (ten sam problem co artwork_batch_jobs.expires_at). Pusty default jest bezpieczny.
    add_column(db, "settings", "updated_at", "TEXT DEFAULT ''")

    print("\n── Kolumny tabeli: artwork_batch_jobs ──")
    # Bez wyrażeniowego DEFAULT-u: `datetime('now','+7 days')` po translacji na PG daje
    # timestamptz przypisywany do kolumny TEXT (cast TEXT robimy tylko w CREATE, nie w
    # ALTER) → błąd i kolumna nie powstaje. Datę wygaśnięcia ustawiamy przy INSERT.
    add_column(db, "artwork_batch_jobs", "expires_at", "TEXT DEFAULT ''")

    # ── Weryfikacja ───────────────────────────────────────────────
    print("\n── Weryfikacja ──")
    required = {
        "comparisons": [
            "id",
            "user_id",
            "doc_type",
            "file_a",
            "file_b",
            "result_json",
            "status",
            "diff_count",
            "created_at",
            "po_number",
            "supplier_code",
            "total_a",
            "total_b",
            "approval_status",
        ],
        "suppliers": [
            "id",
            "code",
            "name",
            "column_mapping_json",
            "synonyms_json",
            "profile_version",
        ],
        "users": ["id", "username", "role", "last_login"],
    }
    all_ok = True
    for table, cols in required.items():
        missing = [c for c in cols if not _col_exists(db, table, c)]
        if missing:
            print(f"  ❌  {table}: brakuje kolumn: {missing}")
            all_ok = False
        else:
            print(f"  ✅  {table}: wszystkie wymagane kolumny istnieją")

    # Round 3: additional indexes, constraints, pool sizing
    create_index(db, "idx_comparisons_supplier_code_nn", "comparisons", "supplier_code")
    create_index(db, "idx_comparisons_doc_type_deleted", "comparisons", "doc_type, is_deleted")
    create_index(db, "idx_suppliers_active", "suppliers", "active")
    create_index(db, "idx_notifications_user_created", "notifications", "user_id, created_at DESC")
    create_index(db, "idx_password_reset_expires", "password_reset_tokens", "expires_at")
    create_index(db, "idx_audit_log_created", "audit_log", "created_at DESC")
    # Koszty AI: dashboard filtruje po modelu / typie wywołania / dacie.
    create_index(db, "idx_api_usage_model_date", "api_usage", "model, created_at DESC")
    create_index(db, "idx_api_usage_type_date", "api_usage", "call_type, created_at DESC")
    create_index(db, "idx_api_usage_created", "api_usage", "created_at DESC")

    if IS_PG:
        # Unique partial index on users.email (NULL-safe)
        try:
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email) WHERE email IS NOT NULL"
            )
            db.commit()
        except Exception:
            db.rollback()
        # Update query planner statistics
        try:
            for tbl in ("comparisons", "users", "notifications", "audit_log", "suppliers"):
                db.execute(f"ANALYZE {tbl}")
            db.commit()
            print("  ✅  ANALYZE completed")
        except Exception as e:
            db.rollback()
            print(f"  ⚠   ANALYZE failed: {e}")

    # Record migration versions
    _record_migration(db, 2, "Round 2: indexes, constraints, columns")
    _record_migration(db, 3, "Round 3: additional indexes, constraints, pool sizing")

    db.close()
    print(f"\n{'═' * 60}")
    if all_ok:
        print("  ✅  Migracja zakończona pomyślnie")
    else:
        print("  ❌  Migracja zakończona z błędami — sprawdź logi powyżej")
    print(f"{'═' * 60}\n")
    return all_ok


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
