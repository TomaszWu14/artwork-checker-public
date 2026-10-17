"""US-014 — RODO: retencja 12 mies., eksport danych konta, anonimizacja (decyzje PO 2026-10-17).

Kryteria:
- eksport JSON: użytkownik pobiera własne dane, admin dane dowolnego konta; bez hasha hasła i tokenów;
- anonimizacja: admin ręcznie (potwierdzenie nazwą) lub automatycznie po 30 dniach od dezaktywacji;
  nazwa → deleted-<id>, e-mail/dział/telefon usunięte, audyt bez nazwy i IP, porównania zostają;
- retencja: audit_log, api_usage, api_rate_events starsze niż 12 mies. usuwane.
"""

import datetime as dt
import json

import pytest

pytest.importorskip("flask")

from werkzeug.security import generate_password_hash

import app as _app_mod
from core import privacy
from tests.conftest import CSRF_TOKEN, TEST_USERS, set_session_csrf

H = {"X-CSRF-Token": CSRF_TOKEN}
PFX = "us014_"


def _db():
    return _app_mod.get_db()


def _ts(days_ago: float) -> str:
    d = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=days_ago)
    return d.strftime("%Y-%m-%d %H:%M:%S")


def _cleanup():
    db = _db()
    try:
        ids = [
            r[0]
            for r in db.execute(
                "SELECT id FROM users WHERE username LIKE ? OR username LIKE 'deleted-%'",
                (PFX + "%",),
            )
        ]
        for uid in ids:
            for sql in (
                "DELETE FROM password_reset_tokens WHERE user_id=?",
                "DELETE FROM notifications WHERE user_id=?",
                "DELETE FROM comparisons WHERE user_id=?",
                "DELETE FROM users WHERE id=?",
            ):
                db.execute(sql, (uid,))
        db.execute(
            "DELETE FROM audit_log WHERE username LIKE ? OR username LIKE 'deleted-%' OR detail LIKE ?",
            (PFX + "%", "%" + PFX + "%"),
        )
        for u, (_, role) in TEST_USERS.items():
            db.execute("UPDATE users SET role=?, is_active=1 WHERE username=?", (role, u))
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean():
    _cleanup()
    yield
    _cleanup()


def _mk_user(name, email=None, active=1, deactivated_days_ago=None, pwd="Us014-secret-1"):
    db = _db()
    try:
        cur = db.execute(
            "INSERT INTO users(username, email, password_hash, role, department, is_active, deactivated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                name,
                email,
                generate_password_hash(pwd),
                "user",
                "Jakość",
                active,
                _ts(deactivated_days_ago) if deactivated_days_ago is not None else None,
            ),
        )
        db.commit()
        return cur.lastrowid
    finally:
        db.close()


def _seed_personal(uid, name):
    db = _db()
    try:
        db.execute(
            "INSERT INTO audit_log(event, username, detail, ip, created_at) VALUES (?,?,?,?,?)",
            ("login_ok", name, f"logowanie {name}", "10.1.2.3", _ts(1)),
        )
        db.execute(
            "INSERT INTO audit_log(event, username, detail, ip, created_at) VALUES (?,?,?,?,?)",
            (
                "user_update",
                "it_admin",
                f"{name}: dezaktywowane; inne: x{name}y",
                "10.9.9.9",
                _ts(1),
            ),
        )
        db.execute(
            "INSERT INTO notifications(user_id, title, message) VALUES (?,?,?)",
            (uid, "Hej", "treść"),
        )
        db.execute(
            "INSERT INTO password_reset_tokens(user_id, token, expires_at) VALUES (?,?,?)",
            (uid, "tok-" + name, _ts(-1)),
        )
        db.execute(
            "INSERT INTO comparisons(user_id, doc_type, file_a, file_b, status) VALUES (?,?,?,?,?)",
            (uid, "artwork", "a.pdf", "b.pdf", "ok"),
        )
        db.commit()
    finally:
        db.close()


# ── retencja ──────────────────────────────────────────────────────────────────


def test_us014_purge_removes_only_older_than_12_months():
    db = _db()
    try:
        db.execute(
            "INSERT INTO audit_log(event, username, created_at) VALUES ('old', ?, ?)",
            (PFX + "a", _ts(400)),
        )
        db.execute(
            "INSERT INTO audit_log(event, username, created_at) VALUES ('new', ?, ?)",
            (PFX + "a", _ts(300)),
        )
        db.execute(
            "INSERT INTO api_usage(created_at, user_id, model) VALUES (?, -14, 'old')", (_ts(400),)
        )
        db.execute(
            "INSERT INTO api_usage(created_at, user_id, model) VALUES (?, -14, 'new')", (_ts(10),)
        )
        _app_mod._ensure_api_rate_table(db)
        now = dt.datetime.now(dt.timezone.utc).timestamp()
        db.execute(
            "INSERT INTO api_rate_events(user_id, created_at) VALUES (-14, ?)", (now - 400 * 86400,)
        )
        db.execute("INSERT INTO api_rate_events(user_id, created_at) VALUES (-14, ?)", (now - 60,))
        db.commit()
        out = privacy.purge_expired(db)
        assert out["audit_log"] >= 1 and out["api_usage"] >= 1 and out["api_rate_events"] >= 1
        events = [
            r[0] for r in db.execute("SELECT event FROM audit_log WHERE username=?", (PFX + "a",))
        ]
        assert events == ["new"]
        assert [r[0] for r in db.execute("SELECT model FROM api_usage WHERE user_id=-14")] == [
            "new"
        ]
        assert (
            db.execute("SELECT COUNT(*) FROM api_rate_events WHERE user_id=-14").fetchone()[0] == 1
        )
        db.execute("DELETE FROM api_usage WHERE user_id=-14")
        db.execute("DELETE FROM api_rate_events WHERE user_id=-14")
        db.commit()
    finally:
        db.close()


# ── anonimizacja ──────────────────────────────────────────────────────────────


def test_us014_anonymize_removes_identity_keeps_work():
    name = PFX + "jan"
    uid = _mk_user(name, email="jan@example.test")
    _seed_personal(uid, name)
    db = _db()
    try:
        assert privacy.anonymize_user(db, uid) == f"deleted-{uid}"
        u = db.execute(
            "SELECT username, email, department, is_active, anonymized_at FROM users WHERE id=?",
            (uid,),
        ).fetchone()
        assert u["username"] == f"deleted-{uid}" and u["email"] is None and u["department"] == ""
        assert u["is_active"] == 0 and u["anonymized_at"]
        assert (
            db.execute(
                "SELECT COUNT(*) FROM audit_log WHERE username=? OR detail LIKE ?",
                (name, f"%{name}:%"),
            ).fetchone()[0]
            == 0
        )
        own = db.execute(
            "SELECT ip FROM audit_log WHERE username=?", (f"deleted-{uid}",)
        ).fetchall()
        assert own and all(r["ip"] == "" for r in own)
        details = [
            r[0]
            for r in db.execute(
                "SELECT detail FROM audit_log WHERE event='user_update' AND detail LIKE ?",
                (f"%deleted-{uid}%",),
            )
        ]
        assert details == [f"deleted-{uid}: dezaktywowane; inne: x{name}y"]  # tylko całe słowo
        assert (
            db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=?", (uid,)).fetchone()[0]
            == 0
        )
        assert (
            db.execute(
                "SELECT COUNT(*) FROM password_reset_tokens WHERE user_id=?", (uid,)
            ).fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT COUNT(*) FROM comparisons WHERE user_id=?", (uid,)).fetchone()[0]
            == 1
        )
        assert privacy.anonymize_user(db, uid) == f"deleted-{uid}"  # idempotentne
    finally:
        db.close()


def test_us014_auto_anonymize_after_30_days_only():
    old = _mk_user(PFX + "old", active=0, deactivated_days_ago=31)
    recent = _mk_user(PFX + "recent", active=0, deactivated_days_ago=10)
    legacy = _mk_user(PFX + "legacy", active=0)  # dezaktywowane przed US-014 — bez daty
    active = _mk_user(PFX + "active")
    db = _db()
    try:
        done = privacy.anonymize_inactive(db)
        assert old in done and recent not in done and legacy not in done and active not in done
        names = {
            r["id"]: r
            for r in db.execute(
                "SELECT id, username, deactivated_at FROM users WHERE id IN (?,?,?,?)",
                (old, recent, legacy, active),
            )
        }
        assert names[old]["username"] == f"deleted-{old}"
        assert names[recent]["username"] == PFX + "recent"
        assert names[legacy]["deactivated_at"]  # zegar 30 dni startuje teraz
        assert names[active]["deactivated_at"] is None
    finally:
        db.close()


def test_us014_anonymized_account_cannot_log_in(client):
    name = PFX + "login"
    uid = _mk_user(name, pwd="Us014-secret-1")
    db = _db()
    try:
        privacy.anonymize_user(db, uid)
    finally:
        db.close()
    for ident in (name, f"deleted-{uid}"):
        with client.session_transaction() as s:
            s["_csrf_token"] = CSRF_TOKEN
        r = client.post(
            "/login",
            data={"identifier": ident, "password": "Us014-secret-1", "_csrf_token": CSRF_TOKEN},
        )
        assert r.status_code not in (302, 303)


# ── API: eksport ──────────────────────────────────────────────────────────────


def test_us014_user_exports_own_data(user_client):
    r = user_client.get("/api/profile/export")
    assert r.status_code == 200
    assert "attachment" in r.headers["Content-Disposition"]
    assert r.headers.get("Cache-Control") == "no-store"
    data = json.loads(r.data)
    assert data["account"]["username"] == "it_user"
    body = r.data.decode()
    assert "password_hash" not in body and "token" not in data["account"]
    assert set(data) >= {"account", "audit_log", "comparisons", "notifications", "api_usage"}


def test_us014_export_requires_login(client):
    r = client.get("/api/profile/export")
    assert r.status_code in (302, 401, 403)


def test_us014_admin_export_any_account_manager_forbidden(admin_client):
    uid = _mk_user(PFX + "exp", email="exp@example.test")
    _seed_personal(uid, PFX + "exp")
    r = admin_client.get(f"/api/admin/users/{uid}/export")
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data["account"]["email"] == "exp@example.test"
    assert any(e["event"] == "login_ok" for e in data["audit_log"])
    assert len(data["comparisons"]) == 1
    assert admin_client.get("/api/admin/users/999999/export").status_code == 404


def test_us014_manager_cannot_export_others(manager_client):
    uid = _mk_user(PFX + "mgr")
    assert manager_client.get(f"/api/admin/users/{uid}/export").status_code == 403


# ── API: anonimizacja ─────────────────────────────────────────────────────────


def test_us014_admin_anonymize_flow(admin_client):
    name = PFX + "anon"
    uid = _mk_user(name)
    url = f"/api/admin/users/{uid}/anonymize"
    assert admin_client.post(url, json={"confirm": name}).status_code in (400, 403)  # bez CSRF
    set_session_csrf(admin_client, CSRF_TOKEN)
    r = admin_client.post(url, json={"confirm": "zla-nazwa"}, headers=H)
    assert r.status_code == 400
    r = admin_client.post(url, json={"confirm": name}, headers=H)
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["user"]["username"] == f"deleted-{uid}"
    assert admin_client.post(url, json={"confirm": f"deleted-{uid}"}, headers=H).status_code == 409
    # zanonimizowanego konta nie da się reaktywować ani edytować
    r = admin_client.patch(f"/api/admin/users/{uid}", json={"is_active": True}, headers=H)
    assert r.status_code == 409
    db = _db()
    try:
        ev = db.execute(
            "SELECT detail FROM audit_log WHERE event='user_anonymize' ORDER BY id DESC"
        ).fetchone()
        assert ev and name not in ev[0] and f"deleted-{uid}" in ev[0]
    finally:
        db.close()


def test_us014_admin_cannot_anonymize_self(admin_client):
    db = _db()
    try:
        me = db.execute("SELECT id FROM users WHERE username='it_admin'").fetchone()[0]
    finally:
        db.close()
    set_session_csrf(admin_client, CSRF_TOKEN)
    r = admin_client.post(
        f"/api/admin/users/{me}/anonymize", json={"confirm": "it_admin"}, headers=H
    )
    assert r.status_code == 400


def test_us014_user_cannot_anonymize(user_client):
    uid = _mk_user(PFX + "victim")
    set_session_csrf(user_client, CSRF_TOKEN)
    r = user_client.post(
        f"/api/admin/users/{uid}/anonymize", json={"confirm": PFX + "victim"}, headers=H
    )
    assert r.status_code == 403


def test_us014_deactivation_starts_30_day_clock(admin_client):
    uid = _mk_user(PFX + "clock")
    set_session_csrf(admin_client, CSRF_TOKEN)
    assert (
        admin_client.patch(
            f"/api/admin/users/{uid}", json={"is_active": False}, headers=H
        ).status_code
        == 200
    )
    db = _db()
    try:
        assert db.execute("SELECT deactivated_at FROM users WHERE id=?", (uid,)).fetchone()[0]
    finally:
        db.close()
    assert (
        admin_client.patch(
            f"/api/admin/users/{uid}", json={"is_active": True}, headers=H
        ).status_code
        == 200
    )
    db = _db()
    try:
        assert (
            db.execute("SELECT deactivated_at FROM users WHERE id=?", (uid,)).fetchone()[0] is None
        )
    finally:
        db.close()


def test_us014_maintenance_runs_both_steps():
    uid = _mk_user(PFX + "maint", active=0, deactivated_days_ago=45)
    out = privacy.run_maintenance(_app_mod.get_db)
    assert uid in out["anonymized"]
    assert set(out["purged"]) == {"audit_log", "api_usage", "api_rate_events"}


def test_us014_daily_thread_starts_once(monkeypatch):
    started = []

    class _T:
        def __init__(self, target, name, daemon):
            assert daemon and name == "privacy-maintenance"
            started.append(target)

        def start(self):
            pass

    monkeypatch.setattr(privacy.threading, "Thread", _T)
    monkeypatch.setattr(privacy, "_started", False)
    assert privacy.start_daily_maintenance(_app_mod.get_db) is True
    assert privacy.start_daily_maintenance(_app_mod.get_db) is False
    assert len(started) == 1
