"""tests/test_intake_db_error.py — /api/intake/artwork nie zwraca 201 przy błędzie zapisu do DB.

Błąd INSERT-a ma dać 500 (bez szczegółów wewnętrznych) i usunąć zapisany plik.
"""

import os

import pytest

pytest.importorskip("flask")

import app as app_mod  # noqa: E402  (conftest ustawia env przed importem)


class _FailingDB:
    """get_db() podwójnik: INSERT rzuca, rollback/close są no-op."""

    def execute(self, *a, **k):
        raise RuntimeError("secret internal db detail")

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _post(client, token="tok"):
    import io

    return client.post(
        "/api/intake/artwork",
        data={"file": (io.BytesIO(b"%PDF-1.4 test"), "a.pdf"), "sender": "x@y.z"},
        headers={"Authorization": f"Bearer {token}"},
        content_type="multipart/form-data",
    )


def test_intake_db_failure_returns_error_and_removes_file(client, monkeypatch, tmp_path):
    monkeypatch.setenv("INTAKE_TOKEN", "tok")
    monkeypatch.setattr(app_mod, "_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(app_mod, "get_db", lambda: _FailingDB())

    resp = _post(client)

    assert resp.status_code == 500
    assert resp.is_json
    assert "secret internal db detail" not in resp.get_data(as_text=True)
    intake_dir = tmp_path / "intake"
    assert not intake_dir.exists() or os.listdir(intake_dir) == []


def test_intake_success_still_201(client, monkeypatch, tmp_path):
    monkeypatch.setenv("INTAKE_TOKEN", "tok")
    monkeypatch.setattr(app_mod, "_DATA_DIR", str(tmp_path))

    resp = _post(client)

    assert resp.status_code == 201
    assert len(os.listdir(tmp_path / "intake")) == 1
