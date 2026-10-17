"""US-022 (etap 2a, ADR-0004): frontend bez CDN i bez Babel w przeglądarce.

- szablony nie ładują skryptów/stylów z unpkg.com / cdn.tailwindcss.com / cdn.jsdelivr.net,
- CSP nie dopuszcza tych hostów,
- przypięte kopie bibliotek i zbudowane pliki są w repo,
- eksport raportu HTML (plik offline) ma React i widok pól wbudowane, bez zewnętrznych skryptów.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CDN_RE = re.compile(r"https://(unpkg\.com|cdn\.tailwindcss\.com|cdn\.jsdelivr\.net)")
VENDORED = [
    "static/vendor/react/react.production.min.js",
    "static/vendor/react/react-dom.production.min.js",
    "static/vendor/alpinejs/alpine-csp.min.js",
    "static/vendor/alpinejs/collapse.min.js",
    "static/vendor/lucide/lucide.min.js",
    "static/js/artwork_report_pf.js",
    "static/css/tailwind.css",
]


def test_templates_do_not_reference_cdns():
    offenders = [
        f"{p.name}: {m.group(0)}"
        for p in sorted((ROOT / "templates").glob("*.html"))
        for m in CDN_RE.finditer(p.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_no_in_browser_babel():
    for p in (ROOT / "templates").glob("*.html"):
        text = p.read_text(encoding="utf-8")
        assert 'type="text/babel"' not in text, p.name
        assert "babel.min.js" not in text, p.name


@pytest.mark.parametrize("rel", VENDORED)
def test_vendored_and_built_files_present(rel):
    path = ROOT / rel
    assert path.is_file() and path.stat().st_size > 500, rel


def test_versions_pinned_in_package_json():
    import json
    deps = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["devDependencies"]
    assert all(re.fullmatch(r"\d+\.\d+\.\d+", v) for v in deps.values()), deps


def test_csp_has_no_cdn_hosts():
    pytest.importorskip("flask")
    import app as _app_mod
    assert not CDN_RE.search(_app_mod._csp_enforced("n0nce"))


def test_exported_report_html_is_self_contained():
    pytest.importorskip("jinja2")
    from artwork_report_engine import build_demo_report, render_report_html
    report = build_demo_report()
    report.profile_active = True
    report.profile_fields = [{"field": "EAN", "severity": "critical", "changed": True,
                              "val_a": "5901234123457", "val_b": "5901234123458"}]
    html = render_report_html(report)
    assert not CDN_RE.search(html)
    assert not re.search(r"<script[^>]+src=", html)          # brak zewnętrznych skryptów
    assert "createRoot" in html and "React" in html          # widok pól wbudowany
    # treść wbudowanych plików nie może zamknąć tagu <script> przedwcześnie
    body = html.split("<body", 1)[1]
    assert body.count("<script") == body.count("</script>")
