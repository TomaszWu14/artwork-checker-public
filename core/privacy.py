"""
core/privacy.py — RODO (US-014): eksport danych konta, anonimizacja i retencja.

Decyzje PO (2026-10-17):
  • eksport (prawo dostępu/przenoszenia) — użytkownik pobiera własne dane, admin dane dowolnego konta;
  • usunięcie = anonimizacja: admin ręcznie albo automatycznie po 30 dniach od dezaktywacji
    (okres zatrudnienia + 30 dni, docs/bezpieczenstwo/RODO.md); porównania i wyniki zostają,
    tracą tylko powiązanie z osobą;
  • retencja 12 miesięcy: audit_log (nazwa, IP), api_rate_events, api_usage — usuwane raz na dobę.

Zależy tylko od warstwy db (blueprint/app → core, nigdy odwrotnie).
"""

from __future__ import annotations

import datetime as _dt
import logging
import re
import secrets
import threading
import time

from werkzeug.security import generate_password_hash

from constants import ACCOUNT_ANONYMIZE_AFTER_DAYS, PERSONAL_DATA_RETENTION_DAYS

logger = logging.getLogger("doccompare")

# Kolumny tekstowe przechowujące NAZWĘ użytkownika (nie id) — przy anonimizacji podmieniane.
# Każda tabela może nie istnieć na danej bazie (moduły tworzą je leniwie) — błędy pomijamy.
_USERNAME_TEXT_COLUMNS = (
    ("audit_log", "username"),
    ("artwork_profile_history", "changed_by_name"),
    ("supplier_audit_log", "changed_by"),
    ("suppliers", "profile_updated_by"),
    ("artwork_marm_link", "updated_by"),
    ("artwork_3d_orientation", "accepted_by"),
)

_EXPORT_USER_COLS = (
    "id, username, email, role, department, language, phone, "
    "COALESCE(is_active,1) AS is_active, created_at, last_login"
)


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)


def _ts(d: _dt.datetime) -> str:
    # Format zgodny z datetime('now') w SQLite i NOW()::TEXT w PostgreSQL (porównanie tekstowe ISO).
    return d.strftime("%Y-%m-%d %H:%M:%S")


def anon_name(uid: int) -> str:
    return f"deleted-{int(uid)}"


def _rows(db, sql: str, params=()) -> list:
    """Zapytanie odporne na brak tabeli/kolumny (opcjonalne moduły) — wtedy pusta lista."""
    try:
        return [dict(r) for r in db.execute(sql, params).fetchall()]
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return []


# ── Eksport (art. 15 i 20) ────────────────────────────────────────────────────


def export_user_data(db, uid: int) -> dict | None:
    """Dane osobowe konta i dane z nim powiązane, w formacie JSON. Bez hasha hasła i tokenów."""
    try:
        user = db.execute(f"SELECT {_EXPORT_USER_COLS} FROM users WHERE id=?", (uid,)).fetchone()  # nosec B608
    except Exception:
        db.rollback()
        user = db.execute(
            "SELECT id, username, email, role, department, created_at, last_login FROM users WHERE id=?",
            (uid,),
        ).fetchone()
    if not user:
        return None
    user = dict(user)
    name = user["username"]
    return {
        "generated_at": _ts(_now()) + " UTC",
        "notice": "Eksport danych osobowych konta (RODO art. 15/20). Hasło i tokeny nie są eksportowane.",
        "account": user,
        "audit_log": _rows(
            db,
            "SELECT created_at, event, detail, ip FROM audit_log WHERE username=? ORDER BY created_at",
            (name,),
        ),
        "comparisons": _rows(
            db,
            "SELECT id, created_at, doc_type, file_a, file_b, status, diff_count FROM comparisons "
            "WHERE user_id=? ORDER BY created_at",
            (uid,),
        ),
        "comparison_comments": _rows(
            db,
            "SELECT comparison_id, comment, comment_type, created_at FROM comparison_comments "
            "WHERE user_id=? ORDER BY created_at",
            (uid,),
        ),
        "artwork_field_comments": _rows(
            db,
            "SELECT * FROM artwork_field_comments WHERE created_by=? ORDER BY created_at",
            (uid,),
        ),
        "notifications": _rows(
            db,
            "SELECT type, title, message, is_read, created_at FROM notifications WHERE user_id=? "
            "ORDER BY created_at",
            (uid,),
        ),
        "api_usage": _rows(
            db,
            "SELECT created_at, model, call_type, input_tokens, output_tokens, cost_usd FROM api_usage "
            "WHERE user_id=? ORDER BY created_at",
            (uid,),
        ),
    }


# ── Anonimizacja (art. 17) ────────────────────────────────────────────────────


def _scrub_detail(db, old: str, new: str) -> int:
    """Zastępuje nazwę w opisach zdarzeń audytu — tylko jako całe słowo (nie fragment innego słowa)."""
    pat = re.compile(r"(?<![\w.-])" + re.escape(old) + r"(?![\w.-])")
    n = 0
    for r in _rows(db, "SELECT id, detail FROM audit_log WHERE detail LIKE ?", (f"%{old}%",)):
        new_detail = pat.sub(new, r["detail"] or "")
        if new_detail != r["detail"]:
            db.execute("UPDATE audit_log SET detail=? WHERE id=?", (new_detail, r["id"]))
            n += 1
    return n


def _try(db, sql: str, params=()) -> bool:
    """Jeden krok w osobnej transakcji: błąd (np. brak opcjonalnej tabeli) nie cofa wcześniejszych
    kroków — na PostgreSQL nieudane polecenie unieważnia całą otwartą transakcję."""
    try:
        db.execute(sql, params)
        db.commit()
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return False


def anonymize_user(db, uid: int) -> str | None:
    """Usuwa dane identyfikujące konta; zwraca nową nazwę (`deleted-<id>`) albo None, gdy brak konta.

    Zostają: porównania, wyniki, komentarze merytoryczne (powiązane z kontem `deleted-<id>`),
    zdarzenia audytu (bez nazwy i bez IP). Konto nie może się zalogować (losowe hasło, nieaktywne).
    Kolejność: najpierw tabele zależne (potrzebują starej nazwy), na końcu `users` — przerwana
    anonimizacja da się bezpiecznie powtórzyć.
    """
    row = db.execute("SELECT id, username FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        return None
    old, new = row["username"], anon_name(uid)
    if old != new:
        for table, col in _USERNAME_TEXT_COLUMNS:
            _try(db, f"UPDATE {table} SET {col}=? WHERE {col}=?", (new, old))  # nosec B608 — stała lista
        try:
            _scrub_detail(db, old, new)
            db.commit()
        except Exception:
            db.rollback()
    _try(db, "UPDATE audit_log SET ip='' WHERE username=?", (new,))
    _try(db, "DELETE FROM password_reset_tokens WHERE user_id=?", (uid,))
    _try(db, "DELETE FROM notifications WHERE user_id=?", (uid,))
    for col in ("phone", "avatar_initials", "allowed_modules"):
        _try(db, f"UPDATE users SET {col}='' WHERE id=?", (uid,))  # nosec B608 — stała lista kolumn
    db.execute(
        "UPDATE users SET username=?, email=NULL, department='', password_hash=?, is_active=0, "
        "anonymized_at=COALESCE(anonymized_at, ?) WHERE id=?",
        (new, generate_password_hash(secrets.token_urlsafe(32)), _ts(_now()), uid),
    )
    db.commit()
    return new


# ── Retencja i automatyczna anonimizacja ─────────────────────────────────────


def purge_expired(db, now: _dt.datetime | None = None) -> dict:
    """Usuwa dane osobowe starsze niż PERSONAL_DATA_RETENTION_DAYS (12 mies.)."""
    now = now or _now()
    cutoff = now - _dt.timedelta(days=PERSONAL_DATA_RETENTION_DAYS)
    out = {}
    for table, sql, param in (
        ("audit_log", "DELETE FROM audit_log WHERE created_at < ?", _ts(cutoff)),
        ("api_usage", "DELETE FROM api_usage WHERE created_at < ?", _ts(cutoff)),
        # api_rate_events.created_at to znacznik czasu UNIX (float)
        (
            "api_rate_events",
            "DELETE FROM api_rate_events WHERE created_at < ?",
            cutoff.replace(tzinfo=_dt.timezone.utc).timestamp(),
        ),
    ):
        try:
            cur = db.execute(sql, (param,))
            out[table] = max(cur.rowcount or 0, 0)
            db.commit()
        except Exception:
            db.rollback()
            out[table] = 0
    return out


def anonymize_inactive(db, now: _dt.datetime | None = None) -> list[int]:
    """Anonimizuje konta nieaktywne dłużej niż ACCOUNT_ANONYMIZE_AFTER_DAYS (30 dni)."""
    now = now or _now()
    # Konta dezaktywowane przed US-014 nie mają daty — liczymy 30 dni od teraz (bez natychmiastowego usunięcia).
    try:
        db.execute(
            "UPDATE users SET deactivated_at=? WHERE COALESCE(is_active,1)=0 AND deactivated_at IS NULL "
            "AND anonymized_at IS NULL",
            (_ts(now),),
        )
        db.commit()
    except Exception:
        db.rollback()
        return []
    cutoff = _ts(now - _dt.timedelta(days=ACCOUNT_ANONYMIZE_AFTER_DAYS))
    ids = [
        r["id"]
        for r in _rows(
            db,
            "SELECT id FROM users WHERE COALESCE(is_active,1)=0 AND anonymized_at IS NULL "
            "AND deactivated_at < ?",
            (cutoff,),
        )
    ]
    for uid in ids:
        anonymize_user(db, uid)
    return ids


def run_maintenance(get_db) -> dict:
    db = get_db()
    try:
        purged = purge_expired(db)
        anonymized = anonymize_inactive(db)
    finally:
        db.close()
    if any(purged.values()) or anonymized:
        logger.info("RODO: retencja %s, zanonimizowane konta %s", purged, anonymized)
    return {"purged": purged, "anonymized": anonymized}


_started = False


def start_daily_maintenance(get_db, interval_s: int = 24 * 3600) -> bool:
    """Wątek-demon: przegląd przy starcie i raz na dobę. Idempotentny — kilka workerów nie szkodzi."""
    global _started
    if _started:
        return False
    _started = True

    def _loop():
        time.sleep(30)  # nie spowalniaj startu aplikacji
        while True:
            try:
                run_maintenance(get_db)
            except Exception as e:  # pragma: no cover - log i kolejna próba za dobę
                logger.warning("RODO: przegląd retencji nie powiódł się: %s", e)
            time.sleep(interval_s)

    threading.Thread(target=_loop, name="privacy-maintenance", daemon=True).start()
    return True
