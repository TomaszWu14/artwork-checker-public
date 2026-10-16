"""US-004 — klucz Anthropic API wyłącznie ze środowiska (SEC-003, R-03).

Kryteria: POST /api/ai/config → 410 i brak wpisu w settings; helpery nie czytają klucza
z bazy ani nie modyfikują os.environ; wpis z poprzednich wersji jest usuwany przy starcie;
w kodzie nie ma przypisań do os.environ["ANTHROPIC_API_KEY"].
"""
import os
import re
from pathlib import Path

import pytest

pytest.importorskip("flask")

from tests.conftest import CSRF_TOKEN, set_session_csrf
import app as _app_mod
import ai_validator

ROOT = Path(__file__).resolve().parents[1]
LEGACY_KEY = "sk-ant-legacy-row-from-db-0000"


def _insert_legacy_row():
    db = _app_mod.get_db()
    try:
        db.execute("DELETE FROM settings WHERE category='ai' AND key='anthropic_api_key'")
        db.execute("INSERT INTO settings(category,key,value) VALUES('ai','anthropic_api_key',?)",
                   (LEGACY_KEY,))
        db.commit()
    finally:
        db.close()


def _legacy_row():
    db = _app_mod.get_db()
    try:
        return db.execute(
            "SELECT value FROM settings WHERE category='ai' AND key='anthropic_api_key'").fetchone()
    finally:
        db.close()


def test_post_config_is_gone_and_stores_nothing(admin_client):
    set_session_csrf(admin_client, CSRF_TOKEN)
    r = admin_client.post("/api/ai/config", json={"api_key": "sk-ant-api03-test-0000"},
                          headers={"X-CSRF-Token": CSRF_TOKEN})
    assert r.status_code == 410
    assert "ANTHROPIC_API_KEY" in r.get_json()["error"]
    assert _legacy_row() is None
    assert os.environ.get("ANTHROPIC_API_KEY", "") != "sk-ant-api03-test-0000"


def test_post_config_forbidden_for_manager(manager_client):
    # SEC-007: rola poniżej admina → 403 (nie 410).
    set_session_csrf(manager_client, CSRF_TOKEN)
    r = manager_client.post("/api/ai/config", json={"api_key": "sk-ant-x"},
                            headers={"X-CSRF-Token": CSRF_TOKEN})
    assert r.status_code == 403


def test_get_config_reports_env_source(admin_client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-0000")
    d = admin_client.get("/api/ai/config").get_json()
    assert d["api_key_set"] is True and d["source"] == "env"
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = admin_client.get("/api/ai/config").get_json()
    assert d["api_key_set"] is False and d["source"] == "none"


def _getter(module_name):
    if module_name == "ai_validator":
        return ai_validator._get_api_key
    # ai_learning importuje pdfplumber na poziomie modułu — w lekkim środowisku CI pomijamy
    return pytest.importorskip("ai_learning")._key


@pytest.mark.parametrize("module_name", ["ai_validator", "ai_learning"])
def test_helpers_ignore_database_and_do_not_touch_environ(module_name, monkeypatch):
    getter = _getter(module_name)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _insert_legacy_row()
    try:
        assert getter() == ""
        assert "ANTHROPIC_API_KEY" not in os.environ
        monkeypatch.setenv("ANTHROPIC_API_KEY", " sk-ant-env-1111 ")
        assert getter() == "sk-ant-env-1111"
    finally:
        _app_mod._purge_legacy_api_key_setting()


def test_artwork_comparator_helper_env_only(monkeypatch):
    ac = pytest.importorskip("artwork_comparator")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _insert_legacy_row()
    try:
        assert ac._get_api_key_artwork() == ""
        assert "ANTHROPIC_API_KEY" not in os.environ
    finally:
        _app_mod._purge_legacy_api_key_setting()


def test_startup_purge_removes_legacy_row_once():
    _insert_legacy_row()
    assert _app_mod._purge_legacy_api_key_setting() is True
    assert _legacy_row() is None
    assert _app_mod._purge_legacy_api_key_setting() is False


def test_no_environ_assignments_of_api_key_in_source():
    pattern = re.compile(r'os\.environ\[\s*["\']ANTHROPIC_API_KEY["\']\s*\]\s*=')
    offenders = []
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts or ".venv" in path.parts or "venv" in path.parts:
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, offenders
