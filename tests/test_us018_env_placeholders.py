"""US-018 — placeholdery z szablonów .env traktowane jak brak sekretu (R-09).

Kryteria: SECRET_KEY=YOUR_SECRET_KEY_HERE + DATABASE_URL ustawione → aplikacja odmawia
startu; DATABASE_URL=YOUR_DATABASE_URL_HERE → czytelny błąd zamiast psycopg2;
.env.example / .env.staging.example nie zawierają wartości sekretów.
"""
import re
from pathlib import Path

import pytest

pytest.importorskip("flask")

import app as _app_mod
import db as _db_mod

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value,expected", [
    ("", True),
    ("   ", True),
    (None, True),
    ("YOUR_SECRET_KEY_HERE", True),
    ("your_database_url_here", True),
    ("changeme", True),
    ("change-me", True),
    ("dev-secret", True),
    ("doccompare-local-secret-2024", True),
    ("password", True),
    ("test-integration-secret", False),
    ("4f3c2b1a" * 8, False),
])
def test_is_placeholder_secret(value, expected):
    assert _app_mod._is_placeholder_secret(value) is expected


def test_startup_validation_fatal_on_placeholder_secret_in_production(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@db.example.test:5432/app")
    monkeypatch.setenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")
    with pytest.raises(SystemExit):
        _app_mod._validate_startup_config()


def test_startup_validation_fatal_on_placeholder_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "YOUR_DATABASE_URL_HERE")
    monkeypatch.setenv("SECRET_KEY", "4f3c2b1a" * 8)
    with pytest.raises(SystemExit):
        _app_mod._validate_startup_config()


def test_startup_validation_passes_with_real_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@db.example.test:5432/app")
    monkeypatch.setenv("SECRET_KEY", "4f3c2b1a" * 8)
    _app_mod._validate_startup_config()   # nie rzuca


def test_startup_validation_only_warns_in_dev(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")
    _app_mod._validate_startup_config()   # dev: ostrzeżenie, nie SystemExit


def test_db_rejects_placeholder_database_url():
    with pytest.raises(SystemExit):
        _db_mod._reject_placeholder_url("YOUR_DATABASE_URL_HERE")
    assert _db_mod._reject_placeholder_url("") is None
    assert _db_mod._reject_placeholder_url("postgresql://u:p@h/db") is None


_SECRET_KEYS = {
    "SECRET_KEY", "DATABASE_URL", "APP_BASE_URL", "RESEND_API_KEY", "EMAIL_FROM",
    "ANTHROPIC_API_KEY", "MISTRAL_API_KEY", "GLM_OCR_API_KEY", "SAFECUBE_API_KEY",
    "TRACKCARGO_API_KEY", "MAERSK_CONSUMER_KEY", "TRACK17_API_KEY", "SHIPSGO_API_KEY",
    "SENTRY_DSN", "REDIS_URL",
}


@pytest.mark.parametrize("fname", [".env.example", ".env.staging.example"])
def test_env_templates_have_no_secret_values(fname):
    text = (ROOT / fname).read_text(encoding="utf-8")
    offenders = []
    for line in text.splitlines():
        m = re.match(r"^([A-Z0-9_]+)=(.*)$", line.strip())
        if m and m.group(1) in _SECRET_KEYS and m.group(2).strip():
            offenders.append(line)
    assert not offenders, f"{fname}: wartości sekretów w szablonie: {offenders}"
    assert "_HERE" not in text
