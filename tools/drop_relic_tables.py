"""US-028: usunięcie tabel-reliktów DocCompare z ISTNIEJĄCEJ bazy (decyzja PO 2026-10-17: „usuń”).

Aplikacja i migrate_db.py już tych tabel nie tworzą (nowe instalacje ich nie mają). Ten skrypt kasuje
je — razem z danymi — w bazach, które je jeszcze mają. Celowo NIE jest częścią migrate_db.py: migracje
uruchamiają się same przy każdym starcie kontenera, a skasowanie danych ma być świadomą decyzją
operatora, uruchomioną raz, po kopii zapasowej.

    python tools/drop_relic_tables.py                     # podgląd: które tabele są i ile mają wierszy
    python tools/drop_relic_tables.py --apply             # SQLite: najpierw kopia bazy, potem DROP
    python tools/drop_relic_tables.py --apply --backup-done   # PostgreSQL: po własnym pg_dump

Baza wskazana jak dla aplikacji: DATABASE_URL (PostgreSQL) albo SQLITE_PATH.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db as _db  # noqa: E402

# Tabele bez kodu aplikacji (analiza US-028; trasy usunięte w US-010). Kolejność bez znaczenia —
# jedyne klucze obce prowadzą z reliktów do `users`, nie odwrotnie.
RELIC_TABLES: tuple[str, ...] = (
    # Kolejka / transport / magazyn / agencje celne
    "kolejka_kontenery",
    "kolejka_zlecenia",
    "kolejka_status_log",
    "kolejka_powiadomienia",
    "zlecenia_transportowe",
    "zlecenia_transport_items",
    "transport_queue",
    "warehouse_stock",
    "warehouse_receipts",
    "customs_agencies",
    "po_line_items",
    # Porównywarka dokumentów handlowych i słowniki
    "doc_types",
    "comparison_templates",
    "translation_dictionary",
    "incoterms_dictionary",
    "transit_countries",
    "sad_field_mapping",
    "cn_reference",
    "currency_rates",
    "supplier_checklists",
    "delivery_checklists",
    "supplier_analysis_log",
    # Inne nieużywane
    "tickets",
    "email_queue",
    "job_progress",
)


def _is_pg() -> bool:
    return bool(_db.DATABASE_URL)


def existing_relics(conn) -> dict[str, int]:
    """Relikty obecne w bazie → liczba wierszy."""
    if _is_pg():
        rows = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema()"
        ).fetchall()
    else:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    present = {r[0] for r in rows}
    out = {}
    for t in RELIC_TABLES:
        if t in present:
            # Nazwa tabeli wyłącznie ze stałej listy RELIC_TABLES (nie z wejścia).
            out[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]  # nosec B608
    return out


def drop_relics(conn, tables) -> list[str]:
    dropped = []
    for t in tables:
        if t not in RELIC_TABLES:  # obrona w głąb — nigdy nic spoza listy
            raise ValueError(f"{t} nie jest tabelą-reliktem")
        conn.execute(f"DROP TABLE IF EXISTS {t}")  # nosec B608 — nazwa ze stałej listy
        dropped.append(t)
    conn.commit()
    return dropped


def backup_sqlite(path: str) -> str:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"{path}.before-US-028-{ts}.bak"
    src = sqlite3.connect(path)
    dst = sqlite3.connect(dest)
    try:
        with dst:
            src.backup(dst)
    finally:
        src.close()
        dst.close()
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--apply", action="store_true", help="usuń tabele (bez tej flagi — tylko podgląd)"
    )
    ap.add_argument(
        "--backup-done",
        action="store_true",
        help="PostgreSQL: potwierdzam, że wykonano kopię zapasową (pg_dump)",
    )
    args = ap.parse_args(argv)

    conn = _db.get_db()
    try:
        found = existing_relics(conn)
        target = "PostgreSQL" if _is_pg() else f"SQLite {_db.SQLITE_PATH}"
        if not found:
            print(f"{target}: brak tabel-reliktów — nic do zrobienia.")
            return 0
        print(f"{target}: tabele-relikty do usunięcia ({len(found)}):")
        for t, n in found.items():
            print(f"  {t:28} {n:>8} wierszy")
        if not args.apply:
            print("\nPodgląd — nic nie usunięto. Uruchom z --apply, aby usunąć (dane przepadną).")
            return 0
        if _is_pg():
            if not args.backup_done:
                print("\nPostgreSQL: wykonaj najpierw pg_dump i uruchom z --apply --backup-done.")
                return 2
        else:
            print(f"\nKopia zapasowa: {backup_sqlite(_db.SQLITE_PATH)}")
        dropped = drop_relics(conn, list(found))
        print(f"Usunięto {len(dropped)} tabel.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
