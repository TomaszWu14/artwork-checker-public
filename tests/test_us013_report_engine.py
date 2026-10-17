"""US-013 — pokrycie logiki domenowej: artwork_report_engine.py.

Testy czystej logiki budowania raportu (dict/dataclass dla templates/artwork_report.html),
klasyfikacji statusów, listy kontrolnej MDR, rekomendacji zatwierdzenia, weryfikacji
danych dostawcy oraz eksportów (HTML / DOCX / PDF).

Środowisko CI nie ma python-docx ani ReportLab — eksporty DOCX/PDF testujemy na małych
atrapach modułów (wstrzykiwanych przez monkeypatch do sys.modules), które zapisują
strukturę dokumentu. Dzięki temu sprawdzamy realną logikę eksportu (treść, mapowanie
statusów, escapowanie znaczników ReportLab) bez ciężkich zależności. Brak sieci: klucz
API jest zawsze pusty, a urlopen podmieniany w testach komentarza AI.
"""

import base64
import importlib.util
import io
import json
import os
import re
import sys
import types

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import artwork_report_engine as are  # noqa: E402
from artwork_report_engine import (  # noqa: E402
    ArtworkReport,
    ReportFile,
    ReportMessage,
    ReportRow,
    build_report_from_comparison,
)

VALID_A = "5901234123457"
VALID_B = "4006381333931"
INVALID = "5901234123458"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Budowanie raportu nie może wołać sieci (komentarz AI usunięty w US-026)."""
    import urllib.request

    def _fail(*a, **k):
        raise AssertionError("raport wykonał wywołanie sieciowe")

    monkeypatch.setattr(urllib.request, "urlopen", _fail)


def _fr(field, a, b, changed=False, severity="info", note=""):
    return {
        "field": field,
        "val_a": a,
        "val_b": b,
        "changed": changed,
        "severity": severity,
        "note": note,
    }


# Wspólny zestaw pól — pokrywa wszystkie gałęzie routingu sekcji.
FIELD_REPORT = [
    _fr("REF", "DM-1", "DM-1"),
    _fr("EAN-13", VALID_A, INVALID, True, "critical", "EAN różny"),
    _fr("LOT", None, ""),
    _fr("EXP", "2030-01", "2031-01", True, "important"),
    _fr("Rewizja", "Rev.02", "Rev.01", True, "info"),
    _fr("Kolor Pantone", "PANTONE 299", "PANTONE 299"),
    _fr("Format arkusza", "300x150", "300x150"),
    _fr("Producent", "ACME", "ACME"),
    _fr("Nazwa produktu", "Skirt", "Skirt"),
]


def _report(**extra):
    d = {
        "file_a": "/srv/in/master/DM-1_master.pdf",
        "file_b": "/srv/in/DM-1_pouch.pdf",
        "field_report": FIELD_REPORT,
        "critical_count": 1,
        "important_count": 1,
        "ok_count": 5,
    }
    d.update(extra)
    return build_report_from_comparison(d)


def _check(report, key):
    return next(c for c in report.checklist if c["key"] == key)


# ─── status helpers & dataclasses ────────────────────────────────────────────


def test_us013_status_and_msg_class_mapping():
    assert are._status_class("") == "status-info"
    assert are._status_class(None) == "status-info"
    assert are._status_class("  Zgodny ") == "status-ok"
    assert are._status_class("NIEZGODNOSC") == "status-error"
    assert are._status_class("Tylko master") == "status-format"
    assert are._status_class("cos-innego") == "status-info"
    assert are._msg_class("") == "msg-info"
    assert are._msg_class("Krytyczny") == "msg-krytyczny"
    assert are._msg_class(" uwaga ") == "msg-uwaga"
    assert are._msg_class("???") == "msg-info"


def test_us013_dataclass_properties():
    f = ReportFile("a.pdf", "rola", "1x1", "—", "—", "Wzorzec")
    assert f.status_class == "status-wzorzec"
    row = ReportRow("x", "a", "b", "—", "Literowka")
    assert row.status_class == "status-literowka"
    m = ReportMessage("uwaga", "tekst")
    assert m.label == "[UWAGA]"
    assert m.msg_class == "msg-uwaga"

    r = ArtworkReport()
    assert r.files_count == 0
    assert r.has_summary is False
    r.summary_warnings.append(m)
    r.analyzed_files.append(f)
    assert r.has_summary is True
    assert r.files_count == 1


# ─── demo report ─────────────────────────────────────────────────────────────


def test_us013_demo_report_structure():
    r = are.build_demo_report()
    assert r.product_code == "DM-DEMO5-G"
    assert (r.critical_count, r.warning_count, r.ok_count) == (5, 4, 12)
    assert r.files_count == 3
    assert r.has_summary
    assert len(r.summary_errors) == 5 and all(m.level == "KRYTYCZNY" for m in r.summary_errors)
    assert [s["title"] for s in r.comparison_sections] == [
        "DANE IDENTYFIKACYJNE PRODUKTU",
        "DANE PRODUCENTA I EU REP",
        "KODY, DATY I BARKODY",
    ]
    assert "Pantone kolor 2: PANTONE 299 → PANTONE 294" in r.diff_items
    assert "Producent" in r.matched_items
    # Szablon (LOT) i Info nie są "zgodne"
    assert "LOT" not in r.matched_items
    assert "Wysokosc kodu 1D" not in r.matched_items
    lot = next(row for row in r.comparison_sections[2]["rows"] if row["field"] == "LOT")
    assert lot["status"] == "Szablon"


# ─── _build_comparison_sections ──────────────────────────────────────────────


def test_us013_comparison_sections_dict_rows_routing_and_classification():
    rows = [
        {"field": "REF", "val_a": "A1", "val_b": "A1", "status": "Zgodny"},
        {
            "field": "Producent",
            "val_a": "X",
            "val_b": "Y",
            "status": "Rozny",
            "severity": "important",
        },
        {"field": "Importer EU", "val_a": "I", "val_b": "I", "status": "Zgodny"},
        {"field": "LOT", "val_a": "—", "val_b": "—", "status": "Szablon"},
        {"field": "Kod kreskowy", "val_a": "1", "val_b": "2", "status": "Różnica"},
        {"field": "Nazwa", "val_a": "—", "val_b": "B", "status": "Zgodny"},
        {"field": "Opis", "val_a": "a", "val_b": "a", "status": "Info"},
    ]
    secs, matched, diffs = are._build_comparison_sections(rows)
    assert [r["field"] for r in secs[0]["rows"]] == ["REF", "Nazwa", "Opis"]
    assert [r["field"] for r in secs[1]["rows"]] == ["Producent", "Importer EU"]
    assert [r["field"] for r in secs[2]["rows"]] == ["LOT", "Kod kreskowy"]
    assert secs[1]["rows"][0]["severity"] == "important"
    assert secs[0]["rows"][0]["severity"] == "info"  # domyślna dla dict
    assert diffs == ["Producent: X → Y", "Kod kreskowy: 1 → 2"]
    # "Nazwa" ma val_a="—" → nie jest dopasowaniem; Info/Szablon też nie
    assert matched == ["REF", "Importer EU"]


def test_us013_comparison_sections_reportrow_severity_inference():
    rows = [
        ReportRow("EAN", "1", "2", "—", "Niezgodnosc"),
        ReportRow("Kolor", "a", "b", "—", "Zmiana"),
        ReportRow("Gauge", None, "", "—", "Brak"),
        ReportRow("Wymiar", "10", "10", "—", "Zgodny"),
    ]
    secs, matched, diffs = are._build_comparison_sections(rows)
    by = {r["field"]: r for s in secs for r in s["rows"]}
    assert by["EAN"]["severity"] == "critical"
    assert by["Kolor"]["severity"] == "important"
    assert by["Gauge"]["severity"] == "info"
    assert (by["Gauge"]["val_a"], by["Gauge"]["val_b"]) == ("—", "—")
    assert diffs == ["EAN: 1 → 2", "Kolor: a → b"]
    assert matched == ["Wymiar"]


# ─── _dims_close ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("362×467 mm", "367×467 mm", True),  # 1,4% — margines/spad arkusza
        ("300x150 mm", "320x150 mm", False),  # 6,25%
        ("10,5 x 20", "10.5x20", True),  # przecinek dziesiętny
        ("300x150", "300x150x20", False),  # inna liczba wymiarów
        ("", "300x150", False),
        ("brak", "brak", False),  # brak liczb po obu stronach
    ],
)
def test_us013_dims_close(a, b, expected):
    assert are._dims_close(a, b) is expected


def test_us013_dims_close_custom_tolerance():
    assert are._dims_close("100x100", "110x100", tol=0.1) is True
    assert are._dims_close("100x100", "110x100", tol=0.05) is False


# ─── _build_supplier_validation ──────────────────────────────────────────────


def _sv(fields, barcode=None):
    return {c["field"]: c for c in are._build_supplier_validation(fields, barcode or {})}


def test_us013_supplier_validation_valid_ean_and_filled_fields():
    fields = [
        _fr("EAN", VALID_A, VALID_A),
        _fr("LOT", "L1", "AB1234"),
        _fr("EXP", "x", "2031-05-10"),
        _fr("REF", "x", "DM-DEMO5-G"),
    ]
    res = _sv(fields, {"eans_b": [VALID_A, VALID_B]})
    assert res["EAN-13"]["status"] == "ok"
    assert res["EAN-13"]["value"] == f"{VALID_A}, {VALID_B}"
    assert res["LOT / Nr serii"] == {
        "field": "LOT / Nr serii",
        "value": "AB1234",
        "status": "ok",
        "note": "Pole wypełnione prawidłowo",
    }
    assert res["Data ważności (EXP)"]["status"] == "ok"
    assert res["REF / Nr katalogowy"]["status"] == "ok"
    assert res["REF / Nr katalogowy"]["value"] == "DM-DEMO5-G"


def test_us013_supplier_validation_invalid_checksum_is_error():
    res = _sv([], {"eans_b": [VALID_A, INVALID]})
    assert res["EAN-13"]["status"] == "error"
    assert res["EAN-13"]["note"] == f"Błędna suma kontrolna: {INVALID}"


def test_us013_supplier_validation_placeholders_are_warnings():
    fields = [
        _fr("EAN", "x", "5900000000000"),
        _fr("LOT", "x", "□□□□□"),
        _fr("EXP", "x", "XX-XX"),
        _fr("REF", "x", "X"),
    ]
    res = _sv(fields)
    assert res["EAN-13 (OCR)"]["status"] == "warning"
    assert res["EAN-13 (OCR)"]["value"] == "5900000000000"
    assert res["LOT / Nr serii"]["status"] == "warning"
    assert res["LOT / Nr serii"]["value"] == "□□□□□"
    assert res["Data ważności (EXP)"]["status"] == "warning"
    assert res["Data ważności (EXP)"]["note"] == "Wygląda jak niezapełniony placeholder"
    assert res["REF / Nr katalogowy"] == {
        "field": "REF / Nr katalogowy",
        "value": "X",
        "status": "warning",
        "note": "Sprawdź ręcznie",
    }


def test_us013_supplier_validation_missing_fields_are_errors():
    res = _sv([_fr("LOT", "L1", None)])  # None → „—"
    assert res["EAN-13"]["value"] == "nie wykryto"
    assert res["EAN-13"]["status"] == "warning"
    assert res["LOT / Nr serii"]["status"] == "error"
    assert res["Data ważności (EXP)"]["status"] == "error"
    assert res["Data ważności (EXP)"]["value"] == "—"
    assert res["REF / Nr katalogowy"]["value"] == "nie wykryto"


def test_us013_supplier_validation_maps_only_supplier_barcode_messages():
    msgs = [
        {"source": "A", "level": "KRYTYCZNY", "code_type": "EAN-13", "text": "A-only"},
        {"source": "B", "level": "OK", "code_type": "EAN-13", "text": "ok"},
        {"source": "B", "level": "KRYTYCZNY", "code_type": "GS1-128", "text": "bad"},
        {"source": "B", "level": "UWAGA", "code_type": "QR", "text": "warn"},
        {"source": "B", "text": "nolevel"},
    ]
    checks = are._build_supplier_validation([], {"messages": msgs})
    codes = [c for c in checks if c["field"].startswith("Kod (")]
    assert [(c["field"], c["value"], c["status"]) for c in codes] == [
        ("Kod (EAN-13)", "ok", "ok"),
        ("Kod (GS1-128)", "bad", "error"),
        ("Kod (QR)", "warn", "warning"),
        ("Kod (?)", "nolevel", "info"),
    ]


# ─── build_report_from_comparison (dict) ─────────────────────────────────────


def test_us013_build_report_files_and_versions():
    r = _report()
    assert r.product_code == "DM-1_master.pdf"
    assert r.product_name == "DM-1_pouch.pdf"
    assert r.master_version == "Rev.02"
    assert r.factory_version == "Rev.01"
    a, b = r.analyzed_files
    assert (a.role, a.ean, a.revision, a.status, a.size) == (
        "Etykieta master (wzorzec)",
        VALID_A,
        "Rev.02",
        "Wzorzec",
        "—",
    )
    assert (b.role, b.ean, b.revision, b.status) == (
        "Etykieta saszetki (fabryczna)",
        INVALID,
        "Rev.01",
        "Sprawdz",
    )


@pytest.mark.parametrize(
    "name,role",
    [
        ("X_carton_sticker.pdf", "Etykieta zbiorcza (fabryczna)"),
        ("supplier.pdf", "Etykieta (fabryczna)"),
    ],
)
def test_us013_build_report_role_guess(name, role):
    r = build_report_from_comparison({"file_a": "m.pdf", "file_b": name})
    assert r.analyzed_files[1].role == role
    # bez pól EAN/Rewizja → „—"
    assert r.analyzed_files[0].ean == "—"
    assert r.master_version == "—"


def test_us013_build_report_section_routing_and_statuses():
    r = _report()
    vd = {row.element: row for row in r.variable_data}
    assert list(vd) == ["REF", "EAN-13", "LOT", "EXP", "Rewizja", "Nazwa produktu"]
    assert vd["REF"].status == "Zgodny"
    assert vd["EAN-13"].status == "Niezgodnosc"
    assert vd["EXP"].status == "Rozny"
    assert vd["Rewizja"].status == "Zmiana"
    assert (vd["LOT"].master, vd["LOT"].carton, vd["LOT"].status) == (
        "— (pole puste, szablon)",
        "— (pole puste, szablon)",
        "Szablon",
    )
    assert [row.element for row in r.color_spec] == ["Kolor Pantone"]
    assert [row.element for row in r.dimensions] == ["Format arkusza"]
    # wiersz „format" trafia również do grafiki
    assert [row.element for row in r.graphics] == ["Format arkusza"]
    assert [(row.element, row.status) for row in r.manufacturer] == [("Producent", "Zgodny")]
    assert "EAN-13: 5901234123457 → 5901234123458" in r.diff_items
    assert "Producent" in r.matched_items and "LOT" not in r.matched_items


def test_us013_build_report_unchanged_empty_non_variable_field_is_brak():
    r = build_report_from_comparison({"field_report": [_fr("Opis", None, "")]})
    assert [(x.element, x.status) for x in r.variable_data] == [("Opis", "Brak")]


def test_us013_build_report_gs1_messages_and_summary():
    r = _report()
    assert [(m.level, m.text) for m in r.gs1_messages] == [
        ("KRYTYCZNY", f"EAN różny ({VALID_A} → {INVALID})"),
        ("UWAGA", "EXP: 2030-01 → 2031-01"),
        ("INFO", "Rewizja: Rev.02 → Rev.01"),
    ]
    assert [m.text for m in r.summary_errors] == [r.gs1_messages[0].text]
    assert [m.text for m in r.summary_warnings] == [r.gs1_messages[1].text]


def test_us013_build_report_gs1_none_values_never_render_literal_none():
    r = build_report_from_comparison(
        {"field_report": [_fr("GTIN", None, "123", True, "critical")], "critical_count": 1}
    )
    assert r.gs1_messages[0].text == "GTIN: — → 123"
    assert "None" not in r.gs1_messages[0].text


def test_us013_build_report_gs1_ok_message_only_when_clean():
    clean = build_report_from_comparison({"field_report": []})
    assert [(m.level, m.text) for m in clean.gs1_messages] == [
        ("OK", "Nie wykryto krytycznych roznic w kodach GS1/UDI.")
    ]
    # liczniki > 0 bez komunikatów → brak fałszywego „OK"
    dirty = build_report_from_comparison({"field_report": [], "important_count": 2})
    assert dirty.gs1_messages == []


def test_us013_build_report_section_diffs_to_section_comparison():
    page = {
        "page_num": 2,
        "pixel_diff_pct": 3.5,
        "summary": "s",
        "img_a_b64": None,
        "section_diffs": [
            {
                "section_label": "Ostrzeżenia",
                "severity": "critical",
                "diff_count": 2,
                "ai_decomposed": True,
                "rows": [
                    {"status": "equal", "content_a": "Do not reuse", "content_b": "Do not reuse"},
                    {"status": "changed", "content_a": "Sterile", "content_b": "Sterlie"},
                    {"status": "only_master", "content_a": "CE 2797", "content_b": None},
                    {"status": "only_factory", "content_a": "", "content_b": "NEW"},
                    {"status": "weird", "content_a": "x", "content_b": "x"},
                ],
            },
            {"section_key": "pusta", "rows": []},
            {"section_key": "klucz", "rows": [{"content_a": "a", "content_b": "a"}]},
        ],
        "text_diffs": [{"a": "ignored-because-section-diffs", "b": None}],
    }
    r = build_report_from_comparison({"page_diffs": [page]})
    assert len(r.section_comparison) == 2
    sec = r.section_comparison[0]
    assert (sec["label"], sec["severity"], sec["diff_count"], sec["has_diff"], sec["ai"]) == (
        "Ostrzeżenia",
        "critical",
        2,
        True,
        True,
    )
    assert [(x["status_label"], x["status_class"], x["is_diff"]) for x in sec["rows"]] == [
        ("OK", "status-ok", False),
        ("Roznica", "status-niezgodnosc", True),
        ("Brak w B", "status-uwaga", True),
        ("Brak w A", "status-uwaga", True),
        ("Info", "status-info", True),
    ]
    assert sec["rows"][2]["content_b"] == "—"
    assert sec["rows"][3]["content_a"] == "—"
    sec2 = r.section_comparison[1]
    assert (sec2["label"], sec2["has_diff"], sec2["severity"], sec2["ai"]) == (
        "klucz",
        False,
        "info",
        False,
    )
    # przy section_diffs fallback z text_diffs nie jest używany
    assert r.texts == []
    # wizualne porównanie strony
    assert r.page_diffs == [
        {
            "page_num": 2,
            "pixel_diff_pct": 3.5,
            "diff_regions": [],
            "summary": "s",
            "img_a_b64": "",
            "img_b_b64": "",
            "img_a_annot_b64": "",
            "img_b_annot_b64": "",
        }
    ]


def test_us013_build_report_text_diffs_fallback_dedup_and_status():
    long_text = "L" * 100
    tds = [
        {"content_a": "Sterile", "content_b": "Sterlie"},
        {"content_a": "Sterile", "content_b": "Sterlie"},  # duplikat
        {"a": "Only in master", "b": None, "severity": "error"},
        {"a": None, "b": "Only in supplier", "priority": "critical"},
        {"a": "", "b": None},  # pusty po obu stronach — pomijany
        {"content_a": long_text, "content_b": "x"},
    ]
    r = build_report_from_comparison({"page_diffs": [{"text_diffs": tds}]})
    assert [(t.master, t.carton, t.status) for t in r.texts] == [
        ("Sterile", "Sterlie", "Roznica"),
        ("Only in master", "—", "Brak w B"),
        ("—", "Only in supplier", "Brak w A"),
        (long_text, "x", "Roznica"),
    ]
    assert r.texts[3].element == "L" * 70
    # krytyczne różnice tekstu → komunikaty KRYTYCZNY
    crit = [m.text for m in r.gs1_messages if m.level == "KRYTYCZNY"]
    assert crit == [
        "Roznica tekstu (Usunieto): Only in master",
        "Roznica tekstu (Dodano): Only in supplier",
    ]
    assert r.page_diffs[0]["page_num"] == 1  # domyślny numer strony


def test_us013_build_report_defaults_for_empty_input():
    r = build_report_from_comparison(None)
    assert (r.product_code, r.product_name) == ("Plik A", "Plik B")
    assert [(x.element, x.status) for x in r.variable_data] == [("Brak danych", "Info")]
    assert [x.element for x in r.color_spec] == ["Specyfikacja koloru"]
    assert [(x.element, x.status) for x in r.manufacturer] == [("Producent / Manufacturer", "Brak")]
    # brak wymiarów po obu stronach → „Brak", nie „Zgodny"
    assert r.graphics[0].element == "Format arkusza (PDF)"
    assert r.graphics[0].status == "Brak"
    assert r.dimensions[0].status == "Brak"
    assert [(m.level, m.text) for m in r.barcode_messages] == [
        ("INFO", "Brak wyników walidacji kodów — zainstaluj zxingcpp lub pyzbar.")
    ]
    assert r.supplier_validation[0]["value"] == "nie wykryto"
    assert r.profile_fields == [] and r.performance == {} and r.global_color == {}


@pytest.mark.parametrize(
    "da,db,status",
    [
        ("362×467 mm", "367×467 mm", "Zgodny"),
        ("300x150 mm", "300x150 mm", "Zgodny"),
        ("300x150 mm", "100x130 mm", "Niezgodnosc"),
    ],
)
def test_us013_build_report_sheet_dimension_status(da, db, status):
    r = build_report_from_comparison({"dims_a": da, "dims_b": db})
    assert (r.dimensions[0].master, r.dimensions[0].carton) == (da, db)
    assert r.dimensions[0].status == status
    assert r.graphics[0].status == status
    assert r.analyzed_files[0].size == da


def test_us013_checklist_from_fields():
    r = _report()
    assert [c["key"] for c in r.checklist] == [k for k, _, _ in are.CHECKLIST_ITEMS]
    st = {c["key"]: c["status"] for c in r.checklist}
    assert st["ref_present"] == "ok"
    assert st["ean_present"] == "warning"  # obecny, ale zmieniony
    assert st["lot_placeholder"] == "warning"  # pusty po obu stronach
    assert st["exp_placeholder"] == "ok"
    assert st["single_use_symbol"] == "warning"
    assert st["sterility_mark"] == "warning"
    assert st["manufacturer_info"] == "ok"
    assert st["revision_present"] == "ok"
    assert st["product_name"] == "ok"
    assert st["colors_spec"] == "ok"
    assert st["dimensions_ok"] == "ok"
    assert st["warnings_present"] == "ok" and st["translations_ok"] == "ok"
    item = _check(r, "barcode_checksum")
    assert (item["status"], item["severity"]) == ("info", "critical")
    assert _check(r, "barcode_consistency")["status"] == "info"
    assert _check(r, "single_use_symbol")["note"] == "sprawdź symbol graficzny"


def test_us013_checklist_missing_fields():
    r = build_report_from_comparison({"field_report": [_fr("REF", None, None)]})
    st = {c["key"]: c["status"] for c in r.checklist}
    assert st["ref_present"] == "error"
    assert st["ean_present"] == "error"
    assert st["ce_mark"] == "warning"
    assert st["product_name"] == "warning"
    assert st["dimensions_ok"] == "warning"
    assert st["colors_spec"] == "info"
    assert st["manufacturer_info"] == "warning"


def test_us013_checklist_changed_ref_and_present_markings():
    fields = [
        _fr("REF", "A", "B", True, "critical"),
        _fr("Oznaczenie CE", "CE 2797", "CE 2797"),
        _fr("Sterile EO", "STERILE EO", "STERILE EO"),
        _fr("Seria", "□□□", "□□□"),
    ]
    st = {
        c["key"]: c["status"]
        for c in build_report_from_comparison({"field_report": fields}).checklist
    }
    assert st["ref_present"] == "warning"
    assert st["ce_mark"] == "ok"
    assert st["sterility_mark"] == "ok"
    assert st["lot_placeholder"] == "ok"


def test_us013_checklist_ai_regulatory_override():
    r = _report(ai_report={"regulatory_checklist": {"ce_mark": False, "ref_present": True}})
    ce = _check(r, "ce_mark")
    assert (ce["status"], ce["note"]) == ("error", "wg analizy AI")
    assert _check(r, "ref_present")["status"] == "ok"


def test_us013_checklist_barcode_items():
    ok_msgs = [
        {"source": "A", "level": "OK", "check": "checksum", "code_type": "EAN-13", "text": "ok"},
    ]
    r = build_report_from_comparison(
        {"barcode_report": {"messages": ok_msgs, "eans_a": [VALID_A, VALID_B, "x"]}}
    )
    assert _check(r, "barcode_checksum") == {
        "key": "barcode_checksum",
        "label": "Suma kontrolna kodów kreskowych (GS1)",
        "severity": "critical",
        "status": "ok",
        "note": f"EAN-13: {VALID_A}, {VALID_B}",
    }
    assert _check(r, "barcode_consistency")["status"] == "ok"

    no_sum = [{"source": "A", "level": "KRYTYCZNY", "check": "consistency", "text": "A≠B"}]
    r2 = build_report_from_comparison({"barcode_report": {"messages": no_sum}})
    c2 = _check(r2, "barcode_checksum")
    assert c2["status"] == "info" and "nie przeprowadzono walidacji sumy" in c2["note"]
    c3 = _check(r2, "barcode_consistency")
    assert (c3["status"], c3["note"]) == ("error", "Niezgodność kodu kreskowego z tekstem")


def test_us013_barcode_messages_and_summary_mapping():
    rep = {
        "messages": [
            {"source": "A", "level": "OK", "code_type": "EAN-13", "text": "poprawny"},
            {"level": "DZIWNY", "text": "x"},
        ],
        "eans_a": [VALID_A],
        "eans_b": [VALID_B],
        "lot_a": "L1",
        "lot_b": "L2",
        "barcode_gs1_a": {"01": "1"},
        "barcode_gs1_b": None,
    }
    r = build_report_from_comparison({"barcode_report": rep})
    assert [(m.level, m.text) for m in r.barcode_messages] == [
        ("OK", "[A] EAN-13: poprawny"),
        ("INFO", "[?] : x"),
    ]
    assert r.barcode_summary == {
        "eans_a": [VALID_A],
        "eans_b": [VALID_B],
        "lot_a": "L1",
        "lot_b": "L2",
        "gs1_a": {"01": "1"},
        "gs1_b": None,
    }


def test_us013_barcode_report_non_dict_is_ignored():
    r = build_report_from_comparison({"barcode_report": ["not", "a", "dict"]})
    assert r.barcode_summary["eans_a"] == []
    assert _check(r, "barcode_checksum")["status"] == "info"


# ─── rekomendacja zatwierdzenia ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "crit,imp,rec,conf",
    [
        (0, 0, "APPROVED", 90),
        (2, 0, "NEEDS_REVISION", 60),
        (9, 0, "NEEDS_REVISION", 30),  # dolne ograniczenie
        (0, 3, "APPROVED_WITH_NOTES", 60),
        (0, 20, "APPROVED_WITH_NOTES", 40),
    ],
)
def test_us013_heuristic_approval(crit, imp, rec, conf):
    r = build_report_from_comparison({"critical_count": crit, "important_count": imp})
    assert r.approval_recommendation == rec
    assert r.approval_confidence == conf
    if crit:
        assert r.approval_reason == f"Wykryto {crit} krytycznych różnic wymagających korekty."
    elif imp:
        assert r.approval_reason.startswith(f"Wykryto {imp} uwag")


def test_us013_ai_approval_kept_and_confidence_derived():
    r = build_report_from_comparison(
        {
            "ok_count": 8,
            "important_count": 2,
            "ai_report": {
                "approval_recommendation": "APPROVED_WITH_NOTES",
                "approval_reason": "drobne",
                "summary": "fallback summary",
                "confidence": "nie-liczba",
            },
        }
    )
    assert r.approval_recommendation == "APPROVED_WITH_NOTES"
    assert r.approval_reason == "drobne"
    assert r.ai_summary == "fallback summary"
    assert r.approval_confidence == 80  # 8 / 10 ok


def test_us013_ai_approval_confidence_defaults_when_no_counts():
    r = build_report_from_comparison(
        {"ai_report": {"approval_recommendation": "APPROVED", "summary_pl": "PL", "summary": "EN"}}
    )
    assert r.approval_recommendation == "APPROVED"
    assert r.approval_confidence == 50
    assert r.ai_summary == "PL"


def test_us013_ai_explicit_confidence_used():
    r = build_report_from_comparison(
        {"ai_report": {"approval_recommendation": "APPROVED", "confidence": 87.6}}
    )
    assert r.approval_confidence == 87


def test_us013_ai_error_report_falls_back_to_heuristic():
    r = build_report_from_comparison(
        {
            "critical_count": 1,
            "ai_report": {"error": "timeout", "approval_recommendation": "APPROVED"},
        }
    )
    assert r.approval_recommendation == "NEEDS_REVISION"
    assert r.approval_confidence == 70
    assert r.ai_summary == ""


# ─── build_report_from_comparison (obiekt ArtworkCompareResult) ──────────────


class _FakePage:
    def __init__(self, **kw):
        self.page_num = kw.get("page_num", 1)
        self.pixel_diff_pct = kw.get("pixel_diff_pct", 0.0)
        self.diff_regions = kw.get("diff_regions")
        self.summary = kw.get("summary")
        self.img_a_b64 = kw.get("img_a_b64")
        self.img_b_b64 = "BBB"
        self.img_a_annot_b64 = None
        self.img_b_annot_b64 = None
        self.text_diffs = kw.get("text_diffs")
        self.section_diffs = kw.get("section_diffs")


class _FakeResult:
    def __init__(self):
        self.file_a = "C:/x/master.pdf"
        self.file_b = "/tmp/up/supplier_carton.pdf"
        self.dims_a = None
        self.dims_b = "300x150 mm"
        self.field_report = None
        self.profile_active = True
        self.profile_name = "Profil ACME"
        self.page_diffs = [
            _FakePage(page_num=3, pixel_diff_pct=12.3456, diff_regions=[{"x": 1}], summary="zm"),
            _FakePage(text_diffs=[{"content_a": "A", "content_b": "B"}]),
        ]
        self.critical_count = None
        self.important_count = "2"
        self.ok_count = 4
        self.icon_comparison = ({"pair": 1},)
        self.ai_report = None
        self.barcode_report = {"eans_b": [VALID_B]}
        self.include_images_arg = "unset"

    def to_dict(self, include_images=True):
        self.include_images_arg = include_images
        return {
            "performance": {"enabled": True, "total_ms": 12},
            "colorimetry": {"global": {"delta_e": 1.2}},
        }


def test_us013_build_report_from_result_object():
    res = _FakeResult()
    r = build_report_from_comparison(res)
    assert res.include_images_arg is False
    assert (r.product_code, r.product_name) == ("master.pdf", "supplier_carton.pdf")
    assert r.analyzed_files[1].role == "Etykieta zbiorcza (fabryczna)"
    assert (r.critical_count, r.warning_count, r.ok_count) == (0, 2, 4)
    assert r.icon_comparison == [{"pair": 1}]
    assert [(p["page_num"], p["pixel_diff_pct"]) for p in r.page_diffs] == [(3, 12.35), (1, 0.0)]
    assert r.page_diffs[0]["diff_regions"] == [{"x": 1}]
    assert r.page_diffs[1]["diff_regions"] == [] and r.page_diffs[1]["summary"] == ""
    assert r.page_diffs[0]["img_b_b64"] == "BBB" and r.page_diffs[0]["img_a_annot_b64"] == ""
    assert [(t.master, t.carton) for t in r.texts] == [("A", "B")]
    # brak dims_a, jest dims_b → niezgodność arkusza
    assert r.dimensions[0].master == "—" and r.dimensions[0].status == "Niezgodnosc"
    assert r.barcode_summary["eans_b"] == [VALID_B]
    assert r.profile_active is True and r.profile_name == "Profil ACME"
    assert r.profile_fields == []  # field_report=None → []
    assert r.performance == {"enabled": True, "total_ms": 12}
    assert r.global_color == {"delta_e": 1.2}
    assert r.approval_recommendation == "APPROVED_WITH_NOTES"


def test_us013_profile_fields_and_disabled_performance():
    fr = [_fr("REF", "a", "a")]
    r = build_report_from_comparison(
        {
            "field_report": fr,
            "profile_active": True,
            "profile_name": "P1",
            "performance": {"enabled": False, "x": 1},
            "colorimetry": {"global": "nie-dict"},
        }
    )
    assert r.profile_fields is fr
    assert r.performance == {}
    assert r.global_color == {}


def test_us026_report_has_no_ai_comment():
    """US-026 (decyzja PO): komentarz AI nie jest generowany — brak pola i brak wywołania API."""
    r = _report()
    assert not hasattr(r, "ai_comment")
    assert not hasattr(are, "_generate_ai_comment")
    assert r.approval_recommendation == "NEEDS_REVISION"


# ─── eksport HTML ────────────────────────────────────────────────────────────


def test_us013_inline_assets_cannot_close_script_tag():
    assets = are._report_inline_assets()
    assert set(assets) == {"csp_actions", "react", "react_dom", "report_pf"}
    for key, src in assets.items():
        assert src, key
        assert "</script" not in src, key


def _strip_scripts_and_styles(html):
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.S | re.I)
    return re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.S | re.I)


def test_us013_render_html_escapes_user_controlled_values():
    r = build_report_from_comparison(
        {
            "file_a": "/up/<script>alert(1)<script>.pdf",
            "file_b": '/up/b"><img src=x onerror=alert(2)>.pdf',
            "field_report": [_fr("REF", "<b>A</b>", "B&C", True, "critical")],
            "critical_count": 1,
        }
    )
    html = are.render_report_html(r)
    assert html.lstrip().lower().startswith("<!doctype html")
    assert "<script>alert(1)" not in html
    assert "&lt;script&gt;alert(1)&lt;script&gt;.pdf" in html
    assert "<img src=x onerror" not in html
    assert "b&#34;&gt;&lt;img src=x onerror=alert(2)&gt;.pdf" in html
    assert "&lt;b&gt;A&lt;/b&gt;" in html
    # wszystkie bloki <script> mają nonce (ścisła CSP)
    script_attrs = re.findall(r"<script\b([^>]*)>.*?</script>", html, flags=re.S | re.I)
    assert script_attrs
    for attrs in script_attrs:
        assert "nonce=" in attrs, attrs
    # brak inline handlerów w znacznikach poza treścią skryptów/stylów
    assert not re.search(r"<[^>]+\son[a-z]+\s*=", _strip_scripts_and_styles(html), flags=re.I)


def test_us013_render_html_uses_given_template_env():
    calls = {}

    class _Tpl:
        def render(self, **kw):
            calls["kw"] = kw
            return "RENDERED"

    class _Env:
        def get_template(self, name):
            calls["name"] = name
            return _Tpl()

    rep = ArtworkReport(product_code="X")
    assert are.render_report_html(rep, template_env=_Env()) == "RENDERED"
    assert calls["name"] == "artwork_report.html"
    assert calls["kw"]["report"] is rep
    assert set(calls["kw"]["inline_assets"]) == {"csp_actions", "react", "react_dom", "report_pf"}


# ─── eksport DOCX (atrapa python-docx) ───────────────────────────────────────


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _DRun:
    def __init__(self, text):
        self.text = text
        self.bold = None
        self.font = _Obj(size=None, color=_Obj(rgb=None))


class _DPara:
    def __init__(self, text="", style=None, kind="p", level=None):
        self.runs = [_DRun(text)] if text else []
        self.style = style
        self.kind = kind
        self.level = level
        self.alignment = None

    def add_run(self, text):
        run = _DRun(text)
        self.runs.append(run)
        return run

    @property
    def text(self):
        return "".join(r.text for r in self.runs)


class _DCell:
    def __init__(self):
        self.paragraphs = [_DPara()]
        self.vertical_alignment = None

    @property
    def text(self):
        return self.paragraphs[0].text

    @text.setter
    def text(self, value):
        self.paragraphs = [_DPara(value)]


class _DRow:
    def __init__(self, cols):
        self.cells = [_DCell() for _ in range(cols)]


class _DTable:
    def __init__(self, rows, cols):
        self.kind = "table"
        self.cols = cols
        self.style = None
        self.columns = [_Obj(width=None) for _ in range(cols)]
        self.rows = [_DRow(cols) for _ in range(rows)]

    def add_row(self):
        row = _DRow(self.cols)
        self.rows.append(row)
        return row


class _DDocument:
    def __init__(self):
        self.sections = [_Obj()]
        self.body = []

    def add_heading(self, text, level=1):
        p = _DPara(text, kind="h", level=level)
        self.body.append(p)
        return p

    def add_paragraph(self, text="", style=None):
        p = _DPara(text, style=style)
        self.body.append(p)
        return p

    def add_table(self, rows, cols):
        t = _DTable(rows, cols)
        self.body.append(t)
        return t

    def save(self, buf):
        _DOCX_SAVED.append(self)
        buf.write(b"FAKE-DOCX")


_DOCX_SAVED = []


@pytest.fixture
def fake_docx(monkeypatch):
    _DOCX_SAVED.clear()
    docx = types.ModuleType("docx")
    docx.Document = _DDocument
    shared = types.ModuleType("docx.shared")
    shared.Pt = lambda v: ("pt", v)
    shared.Cm = lambda v: ("cm", v)
    shared.RGBColor = lambda r, g, b: f"#{r:02x}{g:02x}{b:02x}"
    enum = types.ModuleType("docx.enum")
    enum_text = types.ModuleType("docx.enum.text")
    enum_text.WD_ALIGN_PARAGRAPH = _Obj(CENTER="center")
    enum_table = types.ModuleType("docx.enum.table")
    enum_table.WD_ALIGN_VERTICAL = _Obj(CENTER="vcenter")
    for name, mod in {
        "docx": docx,
        "docx.shared": shared,
        "docx.enum": enum,
        "docx.enum.text": enum_text,
        "docx.enum.table": enum_table,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)
    return _DOCX_SAVED


def test_us013_export_docx_structure_and_status_symbols(fake_docx):
    r = _report()
    out = are.export_to_docx(r)
    assert out == b"FAKE-DOCX"
    doc = fake_docx[-1]
    assert doc.sections[0].left_margin == ("cm", 2.5)
    heading = doc.body[0]
    assert heading.text == "RAPORT PORÓWNAWCZY ARTWORKU — DM-1_master.pdf | DM-1_pouch.pdf"
    assert heading.alignment == "center"
    assert heading.runs[0].font.color.rgb == "#1a5276"

    tables = [b for b in doc.body if getattr(b, "kind", "") == "table"]
    # trzy niepuste sekcje porównania
    assert len(tables) == 3
    hdr = [c.text for c in tables[0].rows[0].cells]
    assert hdr == ["Pole / Element", "DM-1_master.pdf", "DM-1_pouch.pdf", "Status"]
    rows = {row.cells[0].text: row for t in tables for row in t.rows[1:]}
    assert rows["EAN-13"].cells[3].text == "⚠ RÓŻNICA"
    assert rows["EAN-13"].cells[3].paragraphs[0].runs[0].font.color.rgb == "#c0392b"
    assert rows["EXP"].cells[3].text == "⚠ RÓŻNICA"
    assert rows["Rewizja"].cells[3].text == "⚠ ZMIANA"
    assert rows["REF"].cells[3].text == "✓ ZGODNE"
    assert rows["LOT"].cells[3].text == "— SZABLON"
    assert rows["LOT"].cells[3].paragraphs[0].runs[0].font.color.rgb is None
    assert rows["REF"].cells[0].vertical_alignment == "vcenter"

    texts = [p.text for p in doc.body if getattr(p, "kind", "") != "table"]
    assert f"✓ ELEMENTY ZGODNE ({len(r.matched_items)})" in texts
    assert f"⚠ RÓŻNICE WYMAGAJĄCE WERYFIKACJI ({len(r.diff_items)})" in texts
    assert f"• EAN-13: {VALID_A} → {INVALID}" in texts
    bullets = [p for p in doc.body if getattr(p, "style", None) == "List Bullet"]
    assert len(bullets) == len(r.matched_items) + len(r.diff_items)
    assert "Komentarz:" not in texts  # US-026: brak komentarza AI


def test_us013_export_docx_empty_report_uses_fallback_headers(fake_docx):
    r = ArtworkReport(product_code="", product_name="—")
    r.comparison_sections = [
        {"title": "PUSTA", "rows": []},
        {"title": "S", "rows": [{"field": "X", "val_a": None, "status": "Nieznany"}]},
    ]
    are.export_to_docx(r)
    doc = fake_docx[-1]
    assert doc.body[0].text == "RAPORT PORÓWNAWCZY ARTWORKU — "
    assert doc.body[1].text == "Data porównania: —"
    texts = [getattr(b, "text", None) for b in doc.body]
    assert "PUSTA" not in texts and "S" in texts
    (table,) = [b for b in doc.body if getattr(b, "kind", "") == "table"]
    assert [c.text for c in table.rows[0].cells][1:3] == ["Plik A (wzorzec)", "—"]
    assert [c.text for c in table.rows[1].cells] == ["X", "—", "—", "Nieznany"]
    assert "Komentarz:" not in texts
    assert not any("ELEMENTY ZGODNE" in (t or "") for t in texts)


# ─── eksport PDF (atrapa ReportLab) ──────────────────────────────────────────


class _RLPara:
    def __init__(self, text, style=None):
        self.text = text
        self.style = style


class _RLImage:
    def __init__(self, fileobj, width, height):
        self.width = width
        self.height = height


class _RLImageReader:
    def __init__(self, fileobj):
        raw = fileobj.read()
        m = re.fullmatch(rb"FAKEIMG:(-?\d+)x(-?\d+)", raw)
        if not m:
            raise ValueError("not an image")
        self._size = (int(m.group(1)), int(m.group(2)))

    def getSize(self):
        return self._size


class _RLTable:
    def __init__(self, data, colWidths=None, repeatRows=0):
        self.data = data
        self.colWidths = colWidths
        self.style = None

    def setStyle(self, style):
        self.style = style


class _RLKeep:
    def __init__(self, flowables):
        self.flowables = flowables


class _RLDoc:
    def __init__(self, buf, **kw):
        self.buf = buf
        self.kw = kw

    def build(self, flow):
        _PDF_BUILT.append({"flow": flow, "kw": self.kw})
        self.buf.write(b"%PDF-FAKE")


_PDF_BUILT = []


def _flatten(items):
    for it in items:
        if isinstance(it, _RLPara):
            yield it
        elif isinstance(it, _RLTable):
            for row in it.data:
                yield from _flatten(row)
        elif isinstance(it, _RLKeep):
            yield from _flatten(it.flowables)


@pytest.fixture
def fake_reportlab(monkeypatch):
    _PDF_BUILT.clear()
    mods = {}

    def mod(name, **attrs):
        m = types.ModuleType(name)
        m.__dict__.update(attrs)
        mods[name] = m
        return m

    mod("reportlab")
    mod("reportlab.lib")
    mod("reportlab.lib.pagesizes", A4=(595, 842))
    mod("reportlab.lib.units", mm=1.0)
    mod("reportlab.lib.colors", HexColor=lambda s: s, white="#ffffff")
    mod(
        "reportlab.lib.styles",
        getSampleStyleSheet=lambda: {"Normal": "Normal"},
        ParagraphStyle=lambda name, parent=None, **kw: _Obj(name=name, parent=parent, **kw),
    )
    mod("reportlab.lib.utils", ImageReader=_RLImageReader)
    mod(
        "reportlab.platypus",
        SimpleDocTemplate=_RLDoc,
        Paragraph=_RLPara,
        Spacer=lambda w, h: ("spacer", w, h),
        Table=_RLTable,
        TableStyle=lambda cmds: list(cmds),
        Image=_RLImage,
        KeepTogether=_RLKeep,
    )
    mod("export_engine", PDF_FONT="DocFont", PDF_FONT_BOLD="DocFont-Bold")
    for name, m in mods.items():
        monkeypatch.setitem(sys.modules, name, m)
    return _PDF_BUILT


def _img(w, h):
    return base64.b64encode(f"FAKEIMG:{w}x{h}".encode()).decode()


def test_us013_export_pdf_escapes_reportlab_markup(fake_reportlab):
    r = _report(file_a="/up/<b>evil<b> & co.pdf")
    r.approval_reason = "a<b"
    out = are.export_to_pdf(r)
    assert out == b"%PDF-FAKE"
    built = fake_reportlab[-1]
    assert built["kw"]["title"] == "Raport porównawczy artworku"
    paras = list(_flatten(built["flow"]))
    texts = [p.text for p in paras]
    assert texts[0] == "RAPORT PORÓWNAWCZY ARTWORKU"
    assert paras[0].style.fontName == "DocFont-Bold"
    assert "&lt;b&gt;evil&lt;b&gt; &amp; co.pdf | DM-1_pouch.pdf" in texts
    assert not any("<b>evil" in t for t in texts)
    assert any(t.startswith("<b>Rekomendacja:</b> NEEDS_REVISION — a&lt;b") for t in texts), texts
    assert any("<b>Krytyczne:</b> 1</font>" in t for t in texts)
    # status → symbol + kolor
    assert '<font color="#c0392b">ROZNICA</font>' in texts
    assert '<font color="#d35400">ZMIANA</font>' in texts
    assert '<font color="#333333">SZABLON</font>' in texts
    assert f"- EAN-13: {VALID_A} → {INVALID}" in texts
    assert "<b>Komentarz:</b>" not in texts  # US-026
    # domyślny komunikat kodów kreskowych zawsze jest → sekcja obecna, EAN „—"
    assert "<b>Wzorzec A — EAN:</b> —" in texts
    assert any(t.startswith("- <b>[INFO]</b> Brak wyników walidacji kodów") for t in texts)


def test_us013_export_pdf_crops_barcodes_and_fallback_font(fake_reportlab, monkeypatch):
    monkeypatch.setitem(sys.modules, "export_engine", None)  # import → fallback Helvetica
    r = ArtworkReport()
    r.profile_fields = [
        {"display_name": "EAN <x>", "severity": "critical", "crop_a_b64": _img(158, 58)},
        {"field": "LOT", "severity": "warning", "crop_a_b64": "@@@", "crop_b_b64": _img(0, 10)},
        {"field_name": "nocrop"},
        "not-a-dict",
    ] + [{"field": f"F{i}", "crop_b_b64": _img(10, 10)} for i in range(45)]
    r.barcode_summary = {"eans_a": [VALID_A], "eans_b": [], "lot_a": "L<1>", "lot_b": None}
    r.matched_items = [f"m{i}" for i in range(100)]
    are.export_to_pdf(r)
    flow = fake_reportlab[-1]["flow"]
    paras = list(_flatten(flow))
    texts = [p.text for p in paras]
    assert paras[0].style.fontName == "Helvetica-Bold"
    assert "Wycinki pól — wzorzec vs dostawca" in texts
    keeps = [f for f in flow if isinstance(f, _RLKeep)]
    assert len(keeps) == 40  # limit wycinków
    hdr0, sub0 = keeps[0].flowables[0], keeps[0].flowables[2]
    assert (
        hdr0.text
        == '<b>EAN &lt;x&gt;</b>&nbsp;&nbsp;<font color="#c0392b" size="7">CRITICAL</font>'
    )
    img_a, img_b = sub0.data[1]
    assert isinstance(img_a, _RLImage)
    assert (img_a.width, img_a.height) == pytest.approx((79.0, 29.0))  # skala do 79 mm
    assert isinstance(img_b, _RLPara) and img_b.text == "—"
    hdr1, sub1 = keeps[1].flowables[0], keeps[1].flowables[2]
    assert '<font color="#d35400" size="7">WARNING</font>' in hdr1.text
    # uszkodzony base64 i zerowy rozmiar → „—"
    assert [c.text for c in sub1.data[1]] == ["—", "—"]
    assert '<font color="#666666" size="7"></font>' in keeps[2].flowables[0].text
    # kody kreskowe
    assert f"<b>Wzorzec A — EAN:</b> {VALID_A}&nbsp;&nbsp;LOT: L&lt;1&gt;" in texts
    assert "<b>Dostawca B — EAN:</b> —" in texts
    # wnioski — limit 80 pozycji, brak sekcji różnic i komentarza
    assert '<font color="#27ae60"><b>ELEMENTY ZGODNE (100)</b></font>' in texts
    assert sum(1 for t in texts if t.startswith("- m")) == 80
    assert not any("RÓŻNICE WYMAGAJĄCE" in t for t in texts)
    assert "<b>Komentarz:</b>" not in texts
    assert "Tabela porównawcza elementów" not in texts


def test_us013_export_pdf_minimal_report_skips_optional_sections(fake_reportlab):
    r = ArtworkReport(product_code="—")
    r.comparison_sections = [{"title": "PUSTA", "rows": []}]
    are.export_to_pdf(r)
    texts = [p.text for p in _flatten(fake_reportlab[-1]["flow"])]
    assert "Tabela porównawcza elementów" in texts
    assert "PUSTA" not in texts  # sekcja bez wierszy pomijana
    assert texts[0] == "RAPORT PORÓWNAWCZY ARTWORKU"
    assert texts[1] == "Data porównania: —"
    assert not any("Rekomendacja" in t for t in texts)
    assert not any("Weryfikacja kodów" in t for t in texts)
    assert not any("Podsumowanie" in t for t in texts)


def test_us013_export_pdf_reportlab_image_bytes_untouched(fake_reportlab):
    """Dekodowany obraz trafia do ImageReader bez modyfikacji (round-trip base64)."""
    seen = []

    class _SpyReader(_RLImageReader):
        def __init__(self, fileobj):
            data = fileobj.read()
            seen.append(data)
            super().__init__(io.BytesIO(data))

    sys.modules["reportlab.lib.utils"].ImageReader = _SpyReader
    r = ArtworkReport()
    r.profile_fields = [{"field": "X", "crop_a_b64": _img(20, 40)}]
    are.export_to_pdf(r)
    assert seen == [b"FAKEIMG:20x40"]
