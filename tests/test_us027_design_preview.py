"""US-027 (decyzja PO 2026-10-17: „napraw”): /artwork/design-preview działa pod ścisłą CSP.

Wcześniej strona ładowała React i Babel z unpkg.com i kompilowała JSX w przeglądarce — CSP
(`script-src 'self' 'nonce-…'`, ADR-0004) blokowała to od US-022, strona była pusta.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = (ROOT / "static/design/index.html").read_text(encoding="utf-8")


def test_us027_no_external_or_babel_scripts():
    srcs = re.findall(r"<script[^>]*\bsrc=\"([^\"]+)\"", INDEX)
    assert srcs == [
        "/static/vendor/react/react.production.min.js",
        "/static/vendor/react/react-dom.production.min.js",
        "design_preview.js",
    ]
    assert "text/babel" not in INDEX
    assert "unpkg.com" not in INDEX
    # brak skryptów inline (bez nonce zablokowałaby je CSP)
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", INDEX)


def test_us027_bundle_built_from_sources():
    bundle = (ROOT / "static/design/design_preview.js").read_text(encoding="utf-8")
    assert bundle.startswith("// Zbudowane z frontend/src/design_preview/")
    assert "<" + "DesignCanvas" not in bundle  # JSX skompilowany
    for name in ["design-canvas", "shared", "artwork-svg", "variant-a", "variant-e", "app"]:
        assert f"// ── {name}.jsx ──" in bundle
        assert (ROOT / "frontend/src/design_preview" / f"{name}.jsx").is_file()
    assert "eval(" not in bundle and "new Function" not in bundle


def test_us027_vendored_react_present():
    for f in ["react.production.min.js", "react-dom.production.min.js"]:
        assert (ROOT / "static/vendor/react" / f).is_file()
