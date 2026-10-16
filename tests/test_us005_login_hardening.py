"""US-005 — odporność logowania na brute-force i polityka haseł (SEC-001, R-01).

Kryteria (docs/analiza/HISTORYJKI.md, US-005):
  * limit per IP liczony w bazie (audit_log), niezależnie od workera;
  * 10 nieudanych prób na KONTO w 15 min (z dowolnych IP) → 429 także dla poprawnego hasła,
    wpis `login_lockout`; ten sam komunikat dla nieistniejącego konta (brak enumeracji);
  * blokada wygasa po oknie; polityka haseł przy resecie i zmianie hasła.
"""
import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, TEST_USERS, logout, set_session_csrf
import app as _app_mod

USER_PW = TEST_USERS["it_user"][0]
GOOD_PW = "Dobre-Haslo-2026-xyz"


def _clear_login_state():
    db = _app_mod.get_db()
    try:
        db.execute("DELETE FROM audit_log WHERE event IN ('login_fail','login_lockout','login')")
        db.execute("UPDATE users SET password_hash=? WHERE username='it_user'",
                   (_app_mod.generate_password_hash(USER_PW),))
        db.commit()
    finally:
        db.close()
    with _app_mod._login_attempts_lock:
        _app_mod._login_attempts.clear()


@pytest.fixture
def clean_login_state():
    _clear_login_state()
    yield
    _clear_login_state()


def _attempt(client, identifier, password, ip):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    return client.post("/login",
                       data={"identifier": identifier, "password": password, "_csrf_token": CSRF_TOKEN},
                       headers={"X-Forwarded-For": ip})


def _audit_count(event, username=None):
    db = _app_mod.get_db()
    try:
        if username:
            return db.execute("SELECT COUNT(*) FROM audit_log WHERE event=? AND username=?",
                              (event, username)).fetchone()[0]
        return db.execute("SELECT COUNT(*) FROM audit_log WHERE event=?", (event,)).fetchone()[0]
    finally:
        db.close()


# ── Limit per IP współdzielony przez bazę ─────────────────────────────────────
def test_ip_limit_counts_in_database_not_only_in_process_memory(client, clean_login_state):
    ip = "203.0.113.5"
    for _ in range(_app_mod._RATE_LIMIT_MAX):
        with _app_mod._login_attempts_lock:
            _app_mod._login_attempts.clear()   # „inny worker” — pamięć procesu pusta
        r = _attempt(client, "it_user", "wrong-password-xx", ip)
        assert r.status_code == 200
    with _app_mod._login_attempts_lock:
        _app_mod._login_attempts.clear()
    r = _attempt(client, "it_user", USER_PW, ip)
    assert r.status_code == 429


# ── Blokada konta przy rotacji IP ─────────────────────────────────────────────
def test_account_lockout_across_rotating_ips(client, clean_login_state):
    n = _app_mod.RATE_LIMIT_LOGIN_ACCOUNT_MAX
    for i in range(n):
        r = _attempt(client, "IT_USER", "wrong-password-xx", f"198.51.100.{i + 1}")
        assert r.status_code == 200, f"próba {i + 1}: {r.status_code}"
    assert _audit_count("login_lockout", "it_user") == 1
    r = _attempt(client, "it_user", USER_PW, "198.51.100.250")   # poprawne hasło, nowy IP
    assert r.status_code == 429
    assert "Zbyt wiele prób" in r.get_data(as_text=True)


def test_unknown_identifier_gets_identical_lockout_response(client, clean_login_state):
    n = _app_mod.RATE_LIMIT_LOGIN_ACCOUNT_MAX
    for i in range(n):
        _attempt(client, "ghost.user", "wrong-password-xx", f"198.51.100.{i + 1}")
    ghost = _attempt(client, "ghost.user", "wrong-password-xx", "198.51.100.251")
    _clear_login_state()
    for i in range(n):
        _attempt(client, "it_user", "wrong-password-xx", f"198.51.100.{i + 1}")
    real = _attempt(client, "it_user", "wrong-password-xx", "198.51.100.251")
    assert ghost.status_code == real.status_code == 429
    assert ghost.get_data(as_text=True) == real.get_data(as_text=True)


def test_lockout_expires_after_window(client, clean_login_state):
    n = _app_mod.RATE_LIMIT_LOGIN_ACCOUNT_MAX
    for i in range(n):
        _attempt(client, "it_user", "wrong-password-xx", f"198.51.100.{i + 1}")
    assert _attempt(client, "it_user", USER_PW, "198.51.100.252").status_code == 429
    db = _app_mod.get_db()
    try:
        db.execute("UPDATE audit_log SET created_at='2000-01-01 00:00:00' WHERE event='login_fail'")
        db.commit()
    finally:
        db.close()
    r = _attempt(client, "it_user", USER_PW, "198.51.100.253")
    assert r.status_code in (302, 303)
    logout(client)


# ── Polityka haseł ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("pw,username,ok", [
    ("short1", "", False),
    ("abcdefghijklm", "", False),          # brak cyfry
    ("123456789012", "", False),           # brak litery (i popularne)
    ("password1234", "", False),           # popularne
    ("password-1234", "", False),          # popularne po usunięciu znaków interpunkcyjnych
    ("aaaaaaaaaaa1", "", False),           # powtarzający się znak
    ("it_user-2026-abc", "it_user", False),  # zawiera nazwę użytkownika
    ("x" * 1001 + "1", "", False),
    (GOOD_PW, "it_user", True),
    ("Zielona-Lampa-77", "anna", True),
])
def test_password_policy(pw, username, ok):
    err = _app_mod._password_policy_error(pw, username)
    assert (err is None) is ok, err


def test_change_password_enforces_policy(user_client, clean_login_state):
    set_session_csrf(user_client, CSRF_TOKEN)
    hdr = {"X-CSRF-Token": CSRF_TOKEN}
    for bad in ("short1", "abcdefghijklm", "password1234", "it_user-2026-abc"):
        r = user_client.post("/api/profile/change-password",
                             json={"current_password": USER_PW, "new_password": bad}, headers=hdr)
        assert r.status_code == 400, bad
        assert r.get_json()["error"]
    r = user_client.post("/api/profile/change-password",
                         json={"current_password": USER_PW, "new_password": GOOD_PW}, headers=hdr)
    assert r.status_code == 200 and r.get_json().get("ok") is True


def test_reset_password_enforces_policy(client, clean_login_state):
    # Token wstawiony bezpośrednio; po US-003 w bazie jest hash — obsługujemy oba warianty.
    plain = "us005-reset-token-0123456789"
    stored = getattr(_app_mod, "_hash_reset_token", lambda t: t)(plain)
    db = _app_mod.get_db()
    try:
        uid = db.execute("SELECT id FROM users WHERE username='it_user'").fetchone()["id"]
        db.execute("DELETE FROM password_reset_tokens WHERE user_id=?", (uid,))
        db.execute("INSERT INTO password_reset_tokens(user_id, token, expires_at) "
                   "VALUES (?, ?, datetime('now','+1 hour'))", (uid, stored))
        db.commit()
    finally:
        db.close()
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    weak = client.post("/reset-password", data={"token": plain, "password": "password1234",
                                                "confirm": "password1234", "_csrf_token": CSRF_TOKEN})
    assert weak.status_code == 200
    assert "zbyt popularne" in weak.get_data(as_text=True)
    with client.session_transaction() as sess:
        sess["_csrf_token"] = CSRF_TOKEN
    good = client.post("/reset-password", data={"token": plain, "password": GOOD_PW,
                                                "confirm": GOOD_PW, "_csrf_token": CSRF_TOKEN})
    assert good.status_code == 200
    assert "zbyt popularne" not in good.get_data(as_text=True)
    r = _attempt(client, "it_user", GOOD_PW, "198.51.100.254")
    assert r.status_code in (302, 303)
    logout(client)
