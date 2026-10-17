"""US-008 etap 1 — CSP report-only, jedno escapowanie HTML (SEC-005, R-05, ADR-0004)."""

import re
from pathlib import Path

import pytest

pytest.importorskip("flask")

import app as _app_mod

ROOT = Path(__file__).resolve().parents[1]


def test_enforced_csp_keeps_ui_working_and_adds_safe_directives(client):
    r = client.get("/login")
    csp = r.headers["Content-Security-Policy"]
    for d in (
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'self'",
    ):
        assert d in csp
    assert r.headers["X-XSS-Protection"] == "0"


def test_enforced_policy_is_strict_and_uses_per_request_nonce(client):
    # Etap 1 sprawdzał tu politykę Report-Only; od US-024 ta sama ścisła polityka jest egzekwowana.
    r1 = client.get("/login")
    r2 = client.get("/login")
    p1 = r1.headers["Content-Security-Policy"]
    p2 = r2.headers["Content-Security-Policy"]
    assert (
        "'unsafe-eval'" not in p1
        and "'unsafe-inline'" not in p1.split("script-src")[1].split(";")[0]
    )
    assert "script-src 'self' 'nonce-" in p1 and "report-uri /csp-report" in p1
    n1 = re.search(r"'nonce-([^']+)'", p1).group(1)
    n2 = re.search(r"'nonce-([^']+)'", p2).group(1)
    assert n1 != n2 and len(n1) >= 16


def test_no_separate_report_only_policy(client):
    for path in ("/login", "/health"):
        assert "Content-Security-Policy-Report-Only" not in client.get(path).headers


def test_csp_report_endpoint_accepts_and_limits(client):
    _app_mod._csp_report_times.clear()
    body = {
        "csp-report": {
            "violated-directive": "script-src",
            "blocked-uri": "inline",
            "document-uri": "https://x/artwork?token=secret",
        }
    }
    r = client.post("/csp-report", json=body, content_type="application/csp-report")
    assert r.status_code == 204
    big = client.post("/csp-report", data="x" * 20000, content_type="application/csp-report")
    assert big.status_code == 413
    for _ in range(70):
        client.post("/csp-report", json=body)
    assert len(_app_mod._csp_report_times) <= 60


def test_every_template_esc_escapes_quotes():
    """Każda definicja esc()/escHtml() w szablonach escapuje & < > " ' (regresja US-008)."""
    bad = []
    for f in sorted((ROOT / "templates").glob("*.html")):
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"function (esc|escHtml)\((\w+)\)\s*\{(.*?)\}\s*(?:\n|$)", text):
            body = m.group(3)
            if not ("&quot;" in body and "&#39;" in body):
                bad.append(f"{f.name}: {m.group(1)}")
    assert not bad, bad
