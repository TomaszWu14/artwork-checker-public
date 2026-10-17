"""US-001 — niezdefiniowane nazwy (ruff F821): resolver ścieżki mastera i martwa
gałąź „shipment” w _save_comparison.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md, US-001):
  * POST /api/artwork/master-files/from-path z istniejącym plikiem → 200 i wpis
    w artwork_master_file (wcześniej NameError → 500);
  * _save_comparison nie odwołuje się do usuniętych helperów transportu;
  * SEC-006: resolver nie wychodzi poza LIBRARY_FOLDER (traversal, ścieżki absolutne).
"""

import os

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, set_session_csrf
import app as _app_mod


@pytest.fixture
def library(tmp_path, monkeypatch):
    lib = tmp_path / "library"
    (lib / "BRAND" / "BOX").mkdir(parents=True)
    pdf = lib / "BRAND" / "BOX" / "REF123_box_rev2.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%synthetic master for tests\n")
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-1.4\n%outside library\n")
    monkeypatch.setitem(_app_mod.app.config, "LIBRARY_FOLDER", str(lib))
    monkeypatch.setitem(_app_mod.app.config, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    return {"lib": lib, "pdf": pdf, "outside": outside, "rel": "BRAND/BOX/REF123_box_rev2.pdf"}


def _db():
    return _app_mod.get_db()


# ── Resolver (jednostkowo) ────────────────────────────────────────────────────
def test_resolver_finds_file_under_library_folder(library):
    db = _db()
    try:
        got = _app_mod._resolve_artwork_master_path(db, library["rel"], "")
    finally:
        db.close()
    assert got == os.path.realpath(str(library["pdf"]))


def test_resolver_accepts_backslash_rel_path_and_filename_variant(library):
    db = _db()
    try:
        got = _app_mod._resolve_artwork_master_path(
            db, "BRAND\\BOX\\other.pdf", "REF123_box_rev2.pdf"
        )
    finally:
        db.close()
    assert got == os.path.realpath(str(library["pdf"]))


def test_resolver_uses_library_files_record_when_inside_library(library):
    db = _db()
    try:
        db.execute("DELETE FROM library_files WHERE rel_path=?", ("X/recorded.pdf",))
        db.execute(
            "INSERT INTO library_files(rel_path, filename, file_path) VALUES (?,?,?)",
            ("X/recorded.pdf", "recorded.pdf", str(library["pdf"])),
        )
        db.commit()
        got = _app_mod._resolve_artwork_master_path(db, "X/recorded.pdf", "")
        db.execute("DELETE FROM library_files WHERE rel_path=?", ("X/recorded.pdf",))
        db.commit()
    finally:
        db.close()
    assert got == os.path.realpath(str(library["pdf"]))


@pytest.mark.parametrize(
    "rel",
    [
        "../outside.pdf",
        "BRAND/../../outside.pdf",
        "",
        "BRAND/BOX/missing.pdf",
    ],
)
def test_resolver_rejects_traversal_and_missing(library, rel):
    db = _db()
    try:
        assert _app_mod._resolve_artwork_master_path(db, rel, "") is None
    finally:
        db.close()


def test_resolver_rejects_absolute_path_outside_library(library):
    db = _db()
    try:
        assert _app_mod._resolve_artwork_master_path(db, str(library["outside"]), "") is None
    finally:
        db.close()


def test_resolver_ignores_library_files_record_pointing_outside(library):
    # SEC-006: nawet gdy rekord w bazie wskazuje poza bibliotekę, resolver odmawia.
    db = _db()
    try:
        db.execute("DELETE FROM library_files WHERE rel_path=?", ("X/evil.pdf",))
        db.execute(
            "INSERT INTO library_files(rel_path, filename, file_path) VALUES (?,?,?)",
            ("X/evil.pdf", "evil.pdf", str(library["outside"])),
        )
        db.commit()
        got = _app_mod._resolve_artwork_master_path(db, "X/evil.pdf", "")
        db.execute("DELETE FROM library_files WHERE rel_path=?", ("X/evil.pdf",))
        db.commit()
    finally:
        db.close()
    assert got is None


# ── Trasa /api/artwork/master-files/from-path ────────────────────────────────
def test_from_path_route_imports_existing_master(manager_client, library):
    set_session_csrf(manager_client, CSRF_TOKEN)
    resp = manager_client.post(
        "/api/artwork/master-files/from-path",
        json={"rel_path": library["rel"], "filename": "REF123_box_rev2.pdf"},
        headers={"X-CSRF-Token": CSRF_TOKEN},
    )
    assert resp.status_code == 200, resp.data
    assert resp.get_json().get("ok") is True
    db = _db()
    try:
        import artwork_index as _ai

        rec = _ai.master_file_for(db, library["rel"])
        blob = _ai.master_file_blob(db, library["rel"])
    finally:
        db.close()
    assert rec and rec["stored_name"].endswith(".pdf")
    assert blob and blob[1].startswith(b"%PDF")


def test_from_path_route_returns_409_when_file_not_on_server(manager_client, library):
    set_session_csrf(manager_client, CSRF_TOKEN)
    resp = manager_client.post(
        "/api/artwork/master-files/from-path",
        json={"rel_path": "BRAND/BOX/not_synced_yet.pdf"},
        headers={"X-CSRF-Token": CSRF_TOKEN},
    )
    assert resp.status_code == 409
    assert resp.get_json().get("available") is False


def test_from_path_route_forbidden_for_user_role(user_client, library):
    # SEC-007: rola bez uprawnień dostaje 403.
    set_session_csrf(user_client, CSRF_TOKEN)
    resp = user_client.post(
        "/api/artwork/master-files/from-path",
        json={"rel_path": library["rel"]},
        headers={"X-CSRF-Token": CSRF_TOKEN},
    )
    assert resp.status_code == 403


# ── _save_comparison bez helperów transportu ─────────────────────────────────
def test_save_comparison_with_po_header_does_not_reference_removed_helpers():
    assert not hasattr(_app_mod, "_ensure_shipment")
    assert not hasattr(_app_mod, "_save_doc_to_shipment")
    db = _db()
    try:
        uid = db.execute("SELECT id FROM users WHERE username='it_admin'").fetchone()["id"]
    finally:
        db.close()
    result = {
        "status": "ok",
        "modules": {
            "table": {"headers": [{"key": "Numer PO", "val_a": "PO-4500001234", "val_b": ""}]}
        },
    }
    with _app_mod.app.test_request_context("/"):
        cid = _app_mod._save_comparison(uid, "artwork", "a.pdf", "b.pdf", result)
    assert cid
    db = _db()
    try:
        row = db.execute("SELECT po_number FROM comparisons WHERE id=?", (cid,)).fetchone()
    finally:
        db.close()
    assert row["po_number"] == "PO-4500001234"
