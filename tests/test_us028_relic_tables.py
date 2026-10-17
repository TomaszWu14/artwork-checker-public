"""US-028 (decyzja PO 2026-10-17: „usuń”): tabele-relikty DocCompare.

- aplikacja (`init_db` w app.py) i `migrate_db.py` już ich nie tworzą,
- `tools/drop_relic_tables.py` kasuje je z istniejącej bazy tylko na żądanie (--apply), po kopii.
"""

import os
import pathlib
import re
import sqlite3
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import drop_relic_tables as drt  # noqa: E402

# Tabele, które zostają mimo pochodzenia z DocCompare (używane przez zachowane funkcje).
KEPT = {
    "comparisons",
    "comparison_comments",
    "suppliers",
    "supplier_audit_log",
    "webhooks",
    "products",
    "intake_queue",
}


def test_us028_relic_list_does_not_touch_kept_tables():
    assert not KEPT & set(drt.RELIC_TABLES)
    assert len(drt.RELIC_TABLES) == len(set(drt.RELIC_TABLES)) == 25


def test_us028_code_no_longer_creates_relics():
    sources = {p: (ROOT / p).read_text(encoding="utf-8") for p in ["app.py", "migrate_db.py"]}
    for t in drt.RELIC_TABLES:
        for name, src in sources.items():
            assert not re.search(rf"CREATE TABLE IF NOT EXISTS {t}\b", src), (name, t)
            assert not re.search(rf"(INSERT|UPDATE|DELETE)\b[^\n]*\b{t}\b", src), (name, t)


def test_us028_fresh_install_has_no_relic_tables(tmp_path, monkeypatch):
    """Świeża baza po migrate_db.run() nie ma żadnego reliktu."""
    import db
    import migrate_db

    path = str(tmp_path / "fresh.db")
    monkeypatch.setattr(db, "SQLITE_PATH", path)
    # migrate_db pamięta schemat poprzedniej bazy (inne testy) — świeża baza = pusta pamięć.
    monkeypatch.setattr(migrate_db, "_schema_cache", {})
    monkeypatch.setenv("SQLITE_PATH", path)
    migrate_db.run()
    names = {
        r[0]
        for r in sqlite3.connect(path).execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert names, "migracja nie utworzyła żadnych tabel"
    assert "users" in names and "artwork_index" not in drt.RELIC_TABLES
    assert not names & set(drt.RELIC_TABLES)


def _db_with_relics(path):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
    c.execute("INSERT INTO users(username) VALUES ('admin')")
    c.execute("CREATE TABLE doc_types (id INTEGER PRIMARY KEY, code TEXT)")
    c.executemany("INSERT INTO doc_types(code) VALUES (?)", [("PO",), ("CI",)])
    c.execute("CREATE TABLE kolejka_zlecenia (id INTEGER PRIMARY KEY)")
    c.commit()
    c.close()


def test_us028_dry_run_deletes_nothing(tmp_path, monkeypatch, capsys):
    import db

    path = str(tmp_path / "old.db")
    _db_with_relics(path)
    monkeypatch.setattr(db, "DATABASE_URL", "")
    monkeypatch.setattr(db, "SQLITE_PATH", path)
    assert drt.main([]) == 0
    out = capsys.readouterr().out
    assert "doc_types" in out and "kolejka_zlecenia" in out and "Podgląd" in out
    names = {r[0] for r in sqlite3.connect(path).execute("SELECT name FROM sqlite_master")}
    assert {"doc_types", "kolejka_zlecenia", "users"} <= names
    assert not [f for f in os.listdir(tmp_path) if ".bak" in f]


def test_us028_apply_backs_up_then_drops_only_relics(tmp_path, monkeypatch):
    import db

    path = str(tmp_path / "old.db")
    _db_with_relics(path)
    monkeypatch.setattr(db, "DATABASE_URL", "")
    monkeypatch.setattr(db, "SQLITE_PATH", path)
    assert drt.main(["--apply"]) == 0
    names = {r[0] for r in sqlite3.connect(path).execute("SELECT name FROM sqlite_master")}
    assert "users" in names
    assert not names & set(drt.RELIC_TABLES)
    backups = [f for f in os.listdir(tmp_path) if ".before-US-028-" in f]
    assert len(backups) == 1
    bak = sqlite3.connect(str(tmp_path / backups[0]))
    assert bak.execute("SELECT COUNT(*) FROM doc_types").fetchone()[0] == 2  # dane są w kopii
    assert drt.main([]) == 0  # ponownie: nic do zrobienia


def test_us028_postgres_requires_backup_confirmation(monkeypatch, capsys):
    import db

    class _Conn:
        def execute(self, sql, params=()):
            class R:
                def fetchall(self_inner):
                    return [("doc_types",)]

                def fetchone(self_inner):
                    return (3,)

            if sql.startswith("DROP"):
                raise AssertionError("DROP bez potwierdzenia kopii")
            return R()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(db, "DATABASE_URL", "postgresql://example/invalid")
    monkeypatch.setattr(db, "get_db", lambda: _Conn())
    assert drt.main(["--apply"]) == 2
    assert "pg_dump" in capsys.readouterr().out


def test_us028_drop_refuses_non_relic():
    c = sqlite3.connect(":memory:")
    try:
        drt.drop_relics(c, ["users"])
    except ValueError as e:
        assert "users" in str(e)
    else:
        raise AssertionError("drop_relics przyjął tabelę spoza listy")
