"""Zapis kopii modelu 3D (GLB + PNG) do wskazanego katalogu — _a3d_copy_to_dir."""
import os
import pytest
import app as _app_mod


def test_copies_glb_and_png(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    dest = tmp_path / "dest"; dest.mkdir()
    glb = src / "1_abc.glb"; glb.write_bytes(b"glTF-fake")
    (src / "1_abc.png").write_bytes(b"PNG-fake")
    saved = _app_mod._a3d_copy_to_dir(str(glb), str(dest))
    assert sorted(os.path.basename(p) for p in saved) == ["1_abc.glb", "1_abc.png"]
    assert (dest / "1_abc.glb").read_bytes() == b"glTF-fake"


def test_missing_png_copies_only_glb(tmp_path):
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    dest = tmp_path / "d"; dest.mkdir()
    saved = _app_mod._a3d_copy_to_dir(str(glb), str(dest))
    assert [os.path.basename(p) for p in saved] == ["1_x.glb"]


def test_copy_roots_allowlist(tmp_path, monkeypatch):
    """Z ustawionym ARTWORK_COPY_ROOTS cel poza korzeniem jest odrzucany."""
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    allowed = tmp_path / "ok"; allowed.mkdir()
    outside = tmp_path / "nope"; outside.mkdir()
    monkeypatch.setenv("ARTWORK_COPY_ROOTS", str(allowed))
    assert _app_mod._a3d_copy_to_dir(str(glb), str(allowed))          # pod korzeniem: OK
    with pytest.raises(ValueError, match="dozwolonymi"):
        _app_mod._a3d_copy_to_dir(str(glb), str(outside))


def test_nonexistent_dir_raises(tmp_path):
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    with pytest.raises(ValueError, match="nie istnieje"):
        _app_mod._a3d_copy_to_dir(str(glb), str(tmp_path / "brak"))


# ── US-006: fail-closed bez ARTWORK_COPY_ROOTS w produkcji ────────────────────
def test_copy_disabled_in_production_without_roots(tmp_path, monkeypatch):
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    dest = tmp_path / "d"; dest.mkdir()
    monkeypatch.delenv("ARTWORK_COPY_ROOTS", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db.example.test/app")
    with pytest.raises(_app_mod.CopyRootsNotConfigured):
        _app_mod._a3d_copy_to_dir(str(glb), str(dest))
    assert not (dest / "1_x.glb").exists()


def test_copy_require_flag_without_database_url(tmp_path, monkeypatch):
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    dest = tmp_path / "d"; dest.mkdir()
    monkeypatch.delenv("ARTWORK_COPY_ROOTS", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ARTWORK_COPY_REQUIRE_ROOTS", "1")
    with pytest.raises(_app_mod.CopyRootsNotConfigured):
        _app_mod._a3d_copy_to_dir(str(glb), str(dest))


def test_symlink_escape_from_root_is_rejected(tmp_path, monkeypatch):
    glb = tmp_path / "1_x.glb"; glb.write_bytes(b"g")
    allowed = tmp_path / "ok"; allowed.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    link = allowed / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinki niedostępne")
    monkeypatch.setenv("ARTWORK_COPY_ROOTS", str(allowed))
    with pytest.raises(ValueError, match="dozwolonymi"):
        _app_mod._a3d_copy_to_dir(str(glb), str(link))


def _accepted_glb(monkeypatch, tmp_path, uid):
    up = tmp_path / "uploads"; (up / "artwork3d").mkdir(parents=True)
    name = f"{uid}_us006.glb"
    (up / "artwork3d" / name).write_bytes(b"glTF")
    monkeypatch.setitem(_app_mod.app.config, "UPLOAD_FOLDER", str(up))
    monkeypatch.setattr(_app_mod, "_a3d_accepted", lambda n: True)
    return name


def test_route_returns_503_when_disabled(manager_client, tmp_path, monkeypatch):
    from tests.conftest import CSRF_TOKEN, set_session_csrf
    with manager_client.session_transaction() as s:
        uid = s["user_id"]
    name = _accepted_glb(monkeypatch, tmp_path, uid)
    dest = tmp_path / "d"; dest.mkdir()
    monkeypatch.delenv("ARTWORK_COPY_ROOTS", raising=False)
    monkeypatch.setenv("ARTWORK_COPY_REQUIRE_ROOTS", "1")
    set_session_csrf(manager_client, CSRF_TOKEN)
    r = manager_client.post("/api/artwork/3d/save-copy", json={"glb_name": name, "dest_dir": str(dest)},
                            headers={"X-CSRF-Token": CSRF_TOKEN})
    assert r.status_code == 503
    assert "ARTWORK_COPY_ROOTS" in r.get_json()["error"]


def test_route_copies_under_root(manager_client, tmp_path, monkeypatch):
    from tests.conftest import CSRF_TOKEN, set_session_csrf
    with manager_client.session_transaction() as s:
        uid = s["user_id"]
    name = _accepted_glb(monkeypatch, tmp_path, uid)
    allowed = tmp_path / "ok"; allowed.mkdir()
    monkeypatch.setenv("ARTWORK_COPY_ROOTS", str(allowed))
    set_session_csrf(manager_client, CSRF_TOKEN)
    r = manager_client.post("/api/artwork/3d/save-copy", json={"glb_name": name, "dest_dir": str(allowed)},
                            headers={"X-CSRF-Token": CSRF_TOKEN})
    assert r.status_code == 200, r.data
    assert (allowed / name).exists()


def test_copy_roots_endpoint(manager_client, user_client, tmp_path, monkeypatch):
    allowed = tmp_path / "ok"; allowed.mkdir()
    monkeypatch.setenv("ARTWORK_COPY_ROOTS", str(allowed))
    d = manager_client.get("/api/artwork/3d/copy-roots").get_json()
    assert d["roots"] == [str(allowed.resolve())] and d["enabled"] is True
    monkeypatch.delenv("ARTWORK_COPY_ROOTS")
    monkeypatch.setenv("ARTWORK_COPY_REQUIRE_ROOTS", "1")
    d = manager_client.get("/api/artwork/3d/copy-roots").get_json()
    assert d == {"roots": [], "required": True, "enabled": False}


def test_copy_roots_endpoint_forbidden_for_user(user_client):
    assert user_client.get("/api/artwork/3d/copy-roots").status_code == 403
