"""US-010 (Z-03, decyzja PO 2026-10-17): relikty DocCompare usunięte z aplikacji.

Trasy stron i API reliktów nie istnieją; tabele w bazie zostają nietknięte (decyzja PO —
usunięcie danych to osobna decyzja). Funkcje Artwork, które dzieliły kod z reliktami, działają.
"""
import pathlib

import pytest

pytest.importorskip("flask")
import app as app_mod  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

REMOVED_PREFIXES = (
    "/checklists", "/api/checklists", "/doc-types", "/api/doc-types", "/templates", "/api/templates",
    "/incoterms", "/api/incoterms", "/transit-countries", "/api/transit-countries",
    "/translation-dictionary", "/api/translation-dictionary", "/scorecard", "/versions",
    "/duplicates", "/api/search",
)


def _rules():
    return [r.rule for r in app_mod.app.url_map.iter_rules()]


@pytest.mark.parametrize("prefix", REMOVED_PREFIXES)
def test_relic_routes_are_gone(prefix):
    hits = [r for r in _rules() if r == prefix or r.startswith(prefix + "/")]
    assert hits == []


def test_artwork_features_sharing_code_with_relics_remain():
    rules = set(_rules())
    for keep in ("/artwork/templates", "/api/artwork/manage/duplicates", "/search",
                 "/suppliers/master", "/api/ref-database/lookup", "/artwork/history"):
        assert keep in rules, keep


def test_relic_templates_and_blueprints_removed():
    for rel in ("templates/checklists.html", "templates/doc_types.html", "templates/templates.html",
                "templates/scorecard.html", "templates/versions.html", "templates/duplicates.html",
                "templates/incoterms_dictionary.html", "templates/transit_countries.html",
                "templates/translation_dictionary.html", "blueprints/incoterms.py",
                "blueprints/transit_countries.py", "blueprints/translation_dict.py"):
        assert not (ROOT / rel).exists(), rel


def test_tracking_relics_removed():
    import constants

    assert not hasattr(constants, "TRACKING_PROVIDERS") and not hasattr(constants, "DocType")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ("SAFECUBE_API_KEY", "TRACKCARGO_API_KEY", "MAERSK_CONSUMER_KEY", "TRACK17_API_KEY",
                "SHIPSGO_API_KEY"):
        assert key not in env


def test_search_links_artwork_results_to_artwork_history(admin_client):
    html = (ROOT / "templates/search.html").read_text(encoding="utf-8")
    assert "/artwork/history?q=" in html and 'href="/suppliers/master"' in html
    assert admin_client.get("/search?q=x").status_code == 200
