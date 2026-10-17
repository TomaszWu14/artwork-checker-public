"""US-029 (PO 2026-10-17: „rób co uważasz najlepsze”): API /api/products usunięte.

Trasy CRUD/import nie miały UI i dublowały master data materiałów. Zostaje migracja danych
z tabeli `products` do `material_master` oraz przekierowanie /products → /materials.
"""

import pytest

pytest.importorskip("flask")

import app as _app_mod


def _rules():
    return {r.rule: r.methods for r in _app_mod.app.url_map.iter_rules()}


def test_us029_products_api_routes_gone():
    rules = _rules()
    assert not [r for r in rules if r.startswith("/api/products")]


def test_us029_migration_and_redirect_kept():
    rules = _rules()
    assert "POST" in rules["/api/materials/migrate-from-products"]
    assert "/products" in rules


def test_us029_products_api_404(admin_client):
    assert admin_client.get("/api/products").status_code == 404
