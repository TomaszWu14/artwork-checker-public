"""US-013 (Z-05, decyzja PO 2026-10-17): blokujący próg pokrycia ≥ 80 % dla logiki domenowej.

Pilnuje, żeby próg i lista modułów w CI nie zostały po cichu obniżone/zawężone — każda zmiana
wymaga decyzji PO i aktualizacji docs/testy/STRATEGIA_TESTOW.md.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

DOMAIN = {
    "artwork_index.py",
    "artwork_naming.py",
    "artwork_report_engine.py",
    "barcode_validator.py",
    "material_master.py",
    "material_uom.py",
    "normalizer.py",
    "supplier_master.py",
    "uom.py",
}


def _env(name):
    m = re.search(rf'^\s+{name}:\s*"([^"]*)"', CI, re.M)
    assert m, f"brak {name} w ci.yml"
    return m.group(1)


def test_us013_domain_module_list_matches_po_decision():
    modules = set(_env("DOMAIN_COVERAGE_MODULES").split(","))
    assert modules == DOMAIN
    for f in modules:
        assert (ROOT / f).is_file(), f


def test_us013_threshold_not_lowered():
    assert int(_env("DOMAIN_COVERAGE_MIN")) >= 80


def test_us013_gate_step_is_blocking():
    step = re.search(r"- name: \"Pokrycie logiki domenowej[^\n]*\n(?P<body>(?:\s{8}[^\n]*\n)+)", CI)
    assert step, "brak kroku bramki pokrycia w ci.yml"
    body = step.group("body")
    assert "coverage report" in body
    assert '--include="$DOMAIN_COVERAGE_MODULES"' in body
    assert '--fail-under="$DOMAIN_COVERAGE_MIN"' in body
    assert "continue-on-error" not in body
    assert "|| true" not in body


def test_us013_strategy_doc_lists_same_modules():
    doc = (ROOT / "docs/testy/STRATEGIA_TESTOW.md").read_text(encoding="utf-8")
    for f in DOMAIN:
        assert f"`{f}`" in doc, f
