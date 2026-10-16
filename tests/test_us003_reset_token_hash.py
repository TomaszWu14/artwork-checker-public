"""US-003 — tokeny resetu hasła przechowywane jako hash, ważne 1 h, nieprzekazywane do widoku.

Kryteria (docs/analiza/HISTORYJKI.md, US-003; SEC-002):
  * w bazie zapisany jest sha256(token), a link zawiera token jawny;
  * link działa raz; po 60 min „wygasł”; jawny token z poprzednich wersji nie działa;
  * strona /admin nie dostaje wartości tokenów (tylko liczbę aktywnych).
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, TEST_USERS, login
import app as _app_mod

NEW_PASSWORD = "Nowe-Haslo-US003-1234"


@pytest.fixture
def reset_env(monkeypatch):
    """E-mail zastąpiony atrapą (bez sieci); konto it_user dostaje adres e-mail;
    liczniki limitu /forgot-password wyczyszczone, żeby kolejność testów nie dawała 429."""
    sent = {}

    def _fake_send(to_email, username, reset_url):
        sent["to"], sent["username"], sent["url"] = to_email, username, reset_url
        return True

    monkeypatch.setattr(_app_mod, "_send_reset_email", _fake_send)
    db = _app_mod.get_db()
    try:
        db.execute("UPDATE users SET email=? WHERE username='it_user'", ("it_user@example.test",))
        db.execute("DELETE FROM audit_log WHERE event IN ('forgot_request','password_reset_request')")
        db.execute("DELETE FROM password_reset_tokens")
        db.commit()
    finally:
        db.close()
    with _app_mod._forgot_attempts_lock:
        _app_mod._forgot_attempts.clear()
    yield sent
    # przywróć hasło testowe, by inne testy mogły się logować
    db = _app_mod.get_db()
    try:
        db.execute("UPDATE users SET password_hash=? WHERE username='it_user'",
                   (_app_mod.generate_password_hash(TEST_USERS["it_user"][0]),))
        db.commit()
    finally:
        db.close()


def _request_reset(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    return client.post("/forgot-password",
                       data={"identifier": "it_user", "_csrf_token": CSRF_TOKEN})


def _token_from_url(url):
    m = re.search(r"token=([A-Za-z0-9_\-]+)", url)
    assert m, url
    return m.group(1)


def _row_for(token):
    db = _app_mod.get_db()
    try:
        return db.execute(
            "SELECT token, expires_at, used FROM password_reset_tokens "
            "WHERE token=?", (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    finally:
        db.close()


def test_token_stored_as_sha256_and_expires_within_one_hour(client, reset_env):
    r = _request_reset(client)
    assert r.status_code == 200
    token = _token_from_url(reset_env["url"])
    row = _row_for(token)
    assert row is not None, "w bazie powinien być hash tokenu"
    assert row["token"] != token and len(row["token"]) == 64
    exp = datetime.strptime(str(row["expires_at"])[:19], "%Y-%m-%d %H:%M:%S")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert timedelta(minutes=55) < (exp - now) <= timedelta(minutes=61)


def test_plain_token_from_url_resets_password_once(client, reset_env):
    _request_reset(client)
    token = _token_from_url(reset_env["url"])
    page = client.get(f"/reset-password?token={token}")
    assert page.status_code == 200
    assert "wygas" not in page.get_data(as_text=True).lower()
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    done = client.post("/reset-password", data={
        "token": token, "password": NEW_PASSWORD, "confirm": NEW_PASSWORD,
        "_csrf_token": CSRF_TOKEN})
    assert done.status_code == 200
    assert _row_for(token)["used"] == 1
    # nowe hasło działa
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    r = client.post("/login", data={"identifier": "it_user", "password": NEW_PASSWORD,
                                    "_csrf_token": CSRF_TOKEN})
    assert r.status_code in (302, 303)
    client.get("/logout")
    # ponowne użycie → wygasł
    again = client.get(f"/reset-password?token={token}")
    assert "wygas" in again.get_data(as_text=True).lower()


def test_legacy_plaintext_token_in_db_does_not_work(client, reset_env):
    db = _app_mod.get_db()
    try:
        uid = db.execute("SELECT id FROM users WHERE username='it_user'").fetchone()["id"]
        db.execute("INSERT INTO password_reset_tokens(user_id, token, expires_at) "
                   "VALUES (?, ?, datetime('now','+1 hour'))", (uid, "legacy-plaintext-token"))
        db.commit()
    finally:
        db.close()
    page = client.get("/reset-password?token=legacy-plaintext-token")
    assert "wygas" in page.get_data(as_text=True).lower()


def test_expired_token_is_rejected(client, reset_env):
    _request_reset(client)
    token = _token_from_url(reset_env["url"])
    db = _app_mod.get_db()
    try:
        db.execute("UPDATE password_reset_tokens SET expires_at=? WHERE token=?",
                   ("2000-01-01 00:00:00", hashlib.sha256(token.encode()).hexdigest()))
        db.commit()
    finally:
        db.close()
    page = client.get(f"/reset-password?token={token}")
    assert "wygas" in page.get_data(as_text=True).lower()


def test_overlong_token_redirects_to_login(client):
    r = client.get("/reset-password?token=" + "x" * 300)
    assert r.status_code in (302, 303)


def test_admin_page_does_not_receive_token_values(admin_client, reset_env, monkeypatch):
    _request_reset(admin_client)
    token = _token_from_url(reset_env["url"])
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    captured = {}
    real_render = _app_mod.render_template

    def _spy(name, **ctx):
        if name == "admin.html":
            captured.update(ctx)
        return real_render(name, **ctx)

    monkeypatch.setattr(_app_mod, "render_template", _spy)
    login(admin_client, "it_admin")
    page = admin_client.get("/admin")
    assert page.status_code == 200
    assert "reset_tokens" not in captured
    assert captured.get("reset_tokens_count", 0) >= 1
    html = page.get_data(as_text=True)
    assert token not in html and token_hash not in html
