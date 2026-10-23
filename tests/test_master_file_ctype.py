"""Upload mastera: Content-Type z białej listy (rozszerzenie), nie z nagłówka klienta.

Regresja: klient wysyłał plik z mimetype `text/html`, który był zapisywany i potem
serwowany inline z /api/artwork/master-file/view (stored XSS na originie aplikacji).
"""

import io

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, set_session_csrf  # noqa: E402


def test_upload_ignores_client_mimetype(manager_client):
    set_session_csrf(manager_client, CSRF_TOKEN)
    rel = "XSS/evil_master.pdf"
    resp = manager_client.post(
        "/api/artwork/master-files/upload",
        data={
            "rel_path": rel,
            "file": (io.BytesIO(b"<script>alert(1)</script>"), "evil.pdf", "text/html"),
        },
        headers={"X-CSRF-Token": CSRF_TOKEN},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
    view = manager_client.get("/api/artwork/master-file/view", query_string={"rel_path": rel})
    assert view.status_code == 200
    assert view.mimetype == "application/pdf"


def test_safe_master_ctype_whitelist():
    import app as app_mod

    assert app_mod._safe_master_ctype("text/html") == "application/pdf"
    assert app_mod._safe_master_ctype(None) == "application/pdf"
    assert app_mod._safe_master_ctype("image/png") == "image/png"
