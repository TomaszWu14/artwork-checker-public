"""US-017: wylogowanie tylko przez POST z CSRF; ręczne kontrole sesji w API
odrzucają konta dezaktywowane (SEC-001, ASVS V3.3 / V4.2.2)."""
import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, logout, set_session_csrf  # noqa: E402
import app as _app_mod  # noqa: E402


def _set_active(username, active):
    db = _app_mod.get_db()
    try:
        db.execute("UPDATE users SET is_active=? WHERE username=?", (1 if active else 0, username))
        db.commit()
    finally:
        db.close()


def test_get_logout_does_not_log_out(user_client):
    """Obca strona (<img src=/logout>) nie może wylogować użytkownika."""
    resp = user_client.get("/logout")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'method="POST"' in body and 'name="_csrf_token"' in body
    assert user_client.get("/artwork").status_code == 200   # sesja nadal ważna


def test_get_logout_anonymous_redirects_to_login(client):
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_post_logout_without_csrf_is_rejected(user_client):
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post("/logout", data={})
    assert resp.status_code == 403
    assert user_client.get("/artwork").status_code == 200


def test_post_logout_with_csrf_logs_out_and_audits(user_client):
    resp = logout(user_client)
    assert resp.status_code == 302
    assert user_client.get("/artwork").status_code == 302
    db = _app_mod.get_db()
    try:
        row = db.execute(
            "SELECT COUNT(*) FROM audit_log WHERE event='logout' AND username='it_user'").fetchone()
    finally:
        db.close()
    assert row[0] >= 1


def test_nav_uses_post_form_for_logout(user_client):
    html = user_client.get("/artwork").get_data(as_text=True)
    assert 'action="/logout"' in html
    assert 'href="/logout"' not in html


@pytest.mark.parametrize("path", ["/api/ref-database/stats", "/api/ref-database/lookup?ref=X"])
def test_deactivated_user_session_rejected_by_manual_api_checks(user_client, path):
    assert user_client.get(path).status_code == 200
    _set_active("it_user", False)
    try:
        assert user_client.get(path).status_code == 401
    finally:
        _set_active("it_user", True)


def test_deactivated_user_rejected_by_library_search(user_client):
    _set_active("it_user", False)
    try:
        assert user_client.get("/api/library/search?q=ab").status_code == 401
    finally:
        _set_active("it_user", True)
