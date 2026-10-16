"""US-009 — zarządzanie kontami przez administratora (FR-022, R-07, SEC-007).

Kryteria: admin tworzy konto → link do ustawienia hasła (hasło nie w e-mailu), audyt
`user_create`; ostatni aktywny admin nie może zostać zdezaktywowany ani zdegradowany;
rola user/manager → 403 na każdej trasie; zmiana roli działa od następnego żądania.
"""
import re

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, TEST_USERS, login, set_session_csrf
import app as _app_mod

H = {"X-CSRF-Token": CSRF_TOKEN}


def _db():
    return _app_mod.get_db()


def _cleanup(prefix="us009_"):
    db = _db()
    try:
        db.execute("DELETE FROM password_reset_tokens WHERE user_id IN "
                   "(SELECT id FROM users WHERE username LIKE ?)", (prefix + "%",))
        db.execute("DELETE FROM users WHERE username LIKE ?", (prefix + "%",))
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


@pytest.fixture
def sent(monkeypatch):
    box = {}

    def fake(to, user, url):
        box.update(to=to, user=user, url=url)
        return True
    monkeypatch.setattr(_app_mod, "_send_reset_email", fake)
    return box


def _create(client, **kw):
    set_session_csrf(client, CSRF_TOKEN)
    payload = {"username": "us009_anna", "email": "anna@example.test", "role": "user", "department": "QA"}
    payload.update(kw)
    return client.post("/api/admin/users", json=payload, headers=H)


def test_admin_creates_account_and_link_is_emailed(admin_client, sent):
    r = _create(admin_client)
    assert r.status_code == 201, r.data
    body = r.get_json()
    assert body["invite_sent"] is True and "setup_url" not in body
    assert sent["to"] == "anna@example.test" and "/reset-password?token=" in sent["url"]
    db = _db()
    try:
        audit = db.execute("SELECT COUNT(*) FROM audit_log WHERE event='user_create' AND detail LIKE 'us009_anna%'").fetchone()[0]
    finally:
        db.close()
    assert audit >= 1


def test_link_sets_password_and_user_can_log_in(admin_client, client, sent):
    _create(admin_client)
    token = re.search(r"token=([\w-]+)", sent["url"]).group(1)
    pw = "Nowe-Konto-2026-abc"
    with client.session_transaction() as s:
        s["_csrf_token"] = CSRF_TOKEN
    r = client.post("/reset-password", data={"token": token, "password": pw, "confirm": pw, "_csrf_token": CSRF_TOKEN})
    assert r.status_code == 200
    with client.session_transaction() as s:
        s["_csrf_token"] = CSRF_TOKEN
    r = client.post("/login", data={"identifier": "us009_anna", "password": pw, "_csrf_token": CSRF_TOKEN})
    assert r.status_code in (302, 303)


def test_without_email_admin_gets_setup_link(admin_client, monkeypatch):
    monkeypatch.setattr(_app_mod, "_send_reset_email", lambda *a: False)
    body = _create(admin_client, username="us009_bez_maila", email="").get_json()
    assert body["invite_sent"] is False and "/reset-password?token=" in body["setup_url"]


@pytest.mark.parametrize("bad,code", [
    ({"username": "x"}, 400),
    ({"username": "us009 spacja"}, 400),
    ({"email": "nie-email"}, 400),
    ({"role": "god"}, 400),
    ({"username": "it_user"}, 409),
])
def test_create_validation(admin_client, sent, bad, code):
    assert _create(admin_client, **bad).status_code == code


def test_admin_cannot_deactivate_or_demote_self(admin_client):
    set_session_csrf(admin_client, CSRF_TOKEN)
    with admin_client.session_transaction() as s:
        me = s["user_id"]
    assert admin_client.patch(f"/api/admin/users/{me}", json={"is_active": False}, headers=H).status_code == 400
    assert admin_client.patch(f"/api/admin/users/{me}", json={"role": "user"}, headers=H).status_code == 400


def test_last_active_admin_guard():
    """Obrona w głębi: nawet gdyby wywołujący nie był liczony jako aktywny admin,
    ostatniego aktywnego administratora nie da się zdegradować/zdezaktywować."""
    from blueprints.users import _active_admins_except
    db = _db()
    try:
        admins = [r["id"] for r in db.execute(
            "SELECT id FROM users WHERE role='admin' AND COALESCE(is_active,1)=1").fetchall()]
        assert _active_admins_except(db, admins[0]) == len(admins) - 1
        db.execute("UPDATE users SET is_active=0 WHERE role='admin' AND id<>?", (admins[0],))
        assert _active_admins_except(db, admins[0]) == 0
        db.rollback()
    finally:
        db.close()


def test_api_blocks_demoting_last_active_admin(admin_client, monkeypatch):
    set_session_csrf(admin_client, CSRF_TOKEN)
    target = _create(admin_client, username="us009_admin2", role="admin").get_json()["id"]
    import blueprints.users as bu
    monkeypatch.setattr(bu, "_active_admins_except", lambda db, uid: 0)
    assert admin_client.patch(f"/api/admin/users/{target}", json={"role": "user"}, headers=H).status_code == 409
    assert admin_client.patch(f"/api/admin/users/{target}", json={"is_active": False}, headers=H).status_code == 409


def _second_client(username):
    c = _app_mod.app.test_client()
    with _app_mod._login_attempts_lock:
        _app_mod._login_attempts.clear()
    assert login(c, username).status_code in (302, 303)
    return c


@pytest.mark.parametrize("fixture", ["user_client", "manager_client"])
def test_non_admin_roles_get_403(request, fixture):
    c = request.getfixturevalue(fixture)
    set_session_csrf(c, CSRF_TOKEN)
    assert c.get("/api/admin/users").status_code == 403
    assert c.post("/api/admin/users", json={"username": "us009_x"}, headers=H).status_code == 403
    assert c.patch("/api/admin/users/1", json={"role": "admin"}, headers=H).status_code == 403
    assert c.post("/api/admin/users/1/invite", headers=H).status_code == 403


def test_mutations_require_csrf(admin_client):
    assert admin_client.post("/api/admin/users", json={"username": "us009_nocsrf"}).status_code == 403


def test_role_change_takes_effect_on_next_request(admin_client):
    user_client = _second_client("it_user")
    db = _db()
    try:
        uid = db.execute("SELECT id FROM users WHERE username='it_user'").fetchone()["id"]
    finally:
        db.close()
    assert user_client.get("/api/admin/users").status_code == 403
    set_session_csrf(admin_client, CSRF_TOKEN)
    assert admin_client.patch(f"/api/admin/users/{uid}", json={"role": "admin"}, headers=H).status_code == 200
    assert user_client.get("/api/admin/users").status_code == 200   # bez ponownego logowania


def test_deactivation_logs_user_out_and_invalidates_links(admin_client, sent):
    user_client = _second_client("it_user")
    db = _db()
    try:
        uid = db.execute("SELECT id FROM users WHERE username='it_user'").fetchone()["id"]
    finally:
        db.close()
    set_session_csrf(admin_client, CSRF_TOKEN)
    admin_client.post(f"/api/admin/users/{uid}/invite", headers=H)
    assert admin_client.patch(f"/api/admin/users/{uid}", json={"is_active": False}, headers=H).status_code == 200
    r = user_client.get("/api/materials")
    assert r.status_code in (302, 303)
    db = _db()
    try:
        open_links = db.execute("SELECT COUNT(*) FROM password_reset_tokens WHERE user_id=? AND used=0", (uid,)).fetchone()[0]
    finally:
        db.close()
    assert open_links == 0
