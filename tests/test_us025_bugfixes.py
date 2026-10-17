"""US-025: regresje dla błędów wykrytych testami US-013 (decyzja PO 2026-10-17: „napraw błędy”).

Dane syntetyczne; bez bibliotek obrazu i sieci (atrapy jak w test_us013_*).
"""

import base64
import sqlite3
import types

import pytest

import artwork_index as ai
import barcode_validator as bv
import material_uom as mu
import supplier_master as sm
from artwork_report_engine import _build_supplier_validation, build_report_from_comparison

EAN13 = "5901234123457"
GTIN14 = "05901234123457"
UPCA = "036000291452"
EAN8 = "96385074"

_OPEN = []


@pytest.fixture(autouse=True)
def _close_dbs():
    yield
    while _OPEN:
        _OPEN.pop().close()


def _db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    _OPEN.append(db)
    return db


# ── 1. Nazwy formatów z zxing-cpp / pyzbar ───────────────────────────────────


@pytest.mark.parametrize(
    "fmt",
    ["EAN-13", "BarcodeFormat.EAN13", "EAN13", "EAN_13"],  # zxing-cpp 2.x, zxing-cpp 1.x, pyzbar
)
def test_us025_classify_ean13_names_from_all_readers(fmt):
    r = bv._classify(fmt, EAN13)
    assert r["type"] == "EAN-13"
    assert r["validation"]["valid"] is True


@pytest.mark.parametrize(
    "fmt, kind, code",
    [
        ("EAN-8", "EAN-8", EAN8),
        ("BarcodeFormat.EAN8", "EAN-8", EAN8),
        ("UPC-A", "UPC-A", UPCA),
        ("UPCA", "UPC-A", UPCA),
    ],
)
def test_us025_classify_ean8_upca_names(fmt, kind, code):
    r = bv._classify(fmt, code)
    assert r["type"] == kind and r["validation"]["valid"] is True


@pytest.mark.parametrize("fmt", ["Code 128", "BarcodeFormat.Code128", "CODE128", "CODE_128"])
def test_us025_classify_code128_parses_gs1(fmt):
    r = bv._classify(fmt, f"(01){GTIN14}(10)AB12")
    assert r["type"] == "Code128/GS1-128"
    assert r["gs1"]["gtin"] == GTIN14 and r["gs1"]["lot"] == "AB12"


@pytest.mark.parametrize("fmt", ["Data Matrix", "BarcodeFormat.DataMatrix", "DATAMATRIX"])
def test_us025_classify_datamatrix(fmt):
    assert bv._classify(fmt, f"(01){GTIN14}")["type"] == "DataMatrix/GS1"


def test_us025_classify_qr_and_unknown_unchanged():
    assert bv._classify("QR Code", "x") == {"type": "QR", "data": "x"}
    assert bv._classify("QRCODE", "x") == {"type": "QR", "data": "x"}
    assert bv._classify("Aztec", "x") == {"type": "Aztec", "data": "x"}


# ── 2. EAN-8 / UPC-A w tekście OCR ───────────────────────────────────────────


@pytest.mark.parametrize("code, kind", [(UPCA, "UPC-A"), (EAN8, "EAN-8"), (EAN13, "EAN-13")])
def test_us025_ocr_valid_upca_ean8_not_flagged(code, kind):
    r = bv.deep_validate_printed_data(f"EAN {code}")
    assert r["ok"] is True, r["issues"]
    assert r["details"][0] == {"level": "OK", "text": f"{kind} ({code}) — cyfra kontrolna poprawna"}


def test_us025_ocr_invalid_upca_reported_as_upca():
    r = bv.deep_validate_printed_data("EAN 036000291453")
    assert r["ok"] is False
    assert r["issues"] == ["UPC-A (036000291453): Błędna cyfra kontrolna: jest 3, powinno być 2"]
    assert r["details"][0]["level"] == "KRYTYCZNY"


# ── 3. Data ważności DD.MM.RRRR vs (17)RRMMDD ────────────────────────────────


@pytest.mark.parametrize(
    "src, expected",
    [
        ("2031-05-10", "310510"),
        ("10.05.2031", "310510"),
        ("10-05-2031", "310510"),
        ("10/05/2031", "310510"),
        ("310510", "310510"),
        ("maj 2031", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_us025_exp_yymmdd(src, expected):
    assert bv._exp_yymmdd(src) == expected


class _FakeImg:
    width, height = 10, 10

    def convert(self, mode):
        return _FakeImg()

    def close(self):
        pass


def _deep_with_barcode(monkeypatch, ocr_text, raw):
    monkeypatch.setattr(bv, "HAS_PIL", True)
    monkeypatch.setattr(bv, "_PIL_Image", types.SimpleNamespace(open=lambda buf: _FakeImg()))
    monkeypatch.setattr(
        bv,
        "read_barcodes_from_image",
        lambda img: [
            {"format": "Code 128", "raw_data": raw, "parsed": bv._classify("Code 128", raw)}
        ],
    )
    return bv.deep_validate_printed_data(ocr_text, base64.b64encode(b"x").decode())


def test_us025_european_exp_date_matches_gs1(monkeypatch):
    r = _deep_with_barcode(monkeypatch, "EXP: 10.05.2031", f"(01){GTIN14}(17)310510")
    assert r["ok"] is True, r["issues"]
    assert {
        "level": "OK",
        "text": "Data ważności w barcode (2031-05-10) zgodna z tekstem OCR (10.05.2031)",
    } in r["details"]


def test_us025_european_exp_date_mismatch_still_critical(monkeypatch):
    r = _deep_with_barcode(monkeypatch, "EXP: 11.05.2031", f"(01){GTIN14}(17)310510")
    assert r["ok"] is False
    assert r["issues"] == ["Data ważności w barcode (2031-05-10) ≠ tekst (11.05.2031)"]


def test_us025_barcode_without_ocr_ean_is_not_a_mismatch(monkeypatch):
    r = _deep_with_barcode(monkeypatch, "brak numeru w tekście", f"(01){GTIN14}")
    assert r["ok"] is True, r["issues"]
    assert not any("None" in d["text"] for d in r["details"])
    assert bv._normalize_ean("") == "" and bv._normalize_ean(GTIN14) == EAN13


# ── 4. Częściowy re-import dostawców ─────────────────────────────────────────


def _sup_db():
    db = _db()
    db.execute(
        "CREATE TABLE suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, "
        "name TEXT NOT NULL, country TEXT DEFAULT 'XX', currency TEXT DEFAULT 'USD')"
    )
    db.commit()
    return db


def test_us025_partial_reimport_keeps_country_currency_keywords():
    db = _sup_db()
    sm.import_workbook(
        db,
        [
            ["kod", "nazwa", "kraj", "waluta", "słowa kluczowe"],
            ["S1", "Acme", "CN", "EUR", "acme; ACME Co"],
        ],
    )
    sm.import_workbook(db, [["kod", "nazwa"], ["S1", "Acme2"]])
    s = sm.get_supplier(db, "S1")
    assert s["name"] == "Acme2"
    assert (s["country"], s["currency"]) == ("CN", "EUR")
    assert s["detect_keywords_json"] == '["acme", "ACME Co"]'


def test_us025_reimport_with_new_values_still_overwrites():
    db = _sup_db()
    sm.import_workbook(db, [["kod", "nazwa", "kraj", "waluta"], ["S1", "Acme", "CN", "EUR"]])
    sm.import_workbook(
        db,
        [["kod", "nazwa", "kraj", "waluta", "słowa kluczowe"], ["S1", "Acme", "DE", "PLN", "nowe"]],
    )
    s = sm.get_supplier(db, "S1")
    assert (s["country"], s["currency"]) == ("DE", "PLN")
    assert s["detect_keywords_json"] == '["nowe"]'


def test_us025_new_supplier_without_country_gets_defaults():
    db = _sup_db()
    sm.import_workbook(db, [["kod", "nazwa"], ["S9", "Nowy"]])
    s = sm.get_supplier(db, "S9")
    assert (s["country"], s["currency"], s["detect_keywords_json"]) == ("XX", "USD", "[]")


# ── 5. Lista kontrolna: dopasowanie nazw pól po słowach, nie podciągu ────────


def _checklist(fields):
    rows = [{"field": f, "val_a": "X", "val_b": "X", "changed": False} for f in fields]
    return {
        c["key"]: c["status"]
        for c in build_report_from_comparison({"field_report": rows}).checklist
    }


def test_us025_producent_does_not_count_as_ce_mark():
    st = _checklist(["Producent"])
    assert st["ce_mark"] == "warning"
    assert st["manufacturer_info"] == "ok"


@pytest.mark.parametrize("field", ["CE", "Oznaczenie CE", "CE 2797", "Znak CE/MDR", "MDR"])
def test_us025_real_ce_fields_still_detected(field):
    assert _checklist([field])["ce_mark"] == "ok"


def test_us025_prefix_keys_still_match_word_forms():
    st = _checklist(["Produkt sterylizowany", "Data ważności (EXP)", "Nr serii / LOT"])
    assert st["single_use_symbol"] == "ok"  # „steryl” jako początek słowa
    assert st["exp_placeholder"] == "ok"
    assert st["lot_placeholder"] == "ok"


def test_us025_short_keys_are_whole_words_only():
    st = _checklist(["Lotnisko", "Referencje klienta"])
    assert st["lot_placeholder"] == "warning"
    assert st["ref_present"] == "error"


# ── 6. Walidacja EAN dostawcy nie może „przejść”, gdy się nie wykonała ───────


def test_us025_supplier_ean_check_failure_is_warning(monkeypatch):
    def _boom(code):
        raise RuntimeError("x")

    monkeypatch.setattr(bv, "validate_barcode_number", _boom)
    checks = {c["field"]: c for c in _build_supplier_validation([], {"eans_b": [EAN13]})}
    ean = checks["EAN-13"]
    assert ean["status"] == "warning"
    assert "Nie udało się zweryfikować" in ean["note"]
    assert "poprawna" not in ean["note"]


def test_us025_supplier_ean_valid_still_ok():
    checks = {c["field"]: c for c in _build_supplier_validation([], {"eans_b": [EAN13, UPCA]})}
    assert checks["EAN-13"]["status"] == "ok"


# ── 7. Drobne ─────────────────────────────────────────────────────────────────


def _browse_db():
    db = _db()
    db.execute(
        "CREATE TABLE artwork_render_registry (id INTEGER PRIMARY KEY, ref_norm TEXT, variant TEXT)"
    )
    db.execute("CREATE TABLE artwork_marm_link (id INTEGER PRIMARY KEY, art_ref_norm TEXT)")
    db.commit()
    ai.ensure_table(db)
    return db


@pytest.mark.parametrize("q", ["%", "_", "---", "%%"])
def test_us025_browse_symbol_only_query_is_literal(q):
    db = _browse_db()
    for name in ["ABC-100_rev1.pdf", "XYZ-200_rev2.pdf"]:
        ai.sync_entries(db, [{"filename": name, "rel_path": f"lib/{name}", "source_mtime": ""}])
    res = ai.browse(db, q=q)
    expected = (
        0 if q in ("%", "%%", "---") else 2
    )  # „_” występuje w obu nazwach plików (literalnie)
    assert res["total"] == expected


def test_us025_browse_regular_query_still_matches_ref():
    db = _browse_db()
    ai.sync_entries(
        db, [{"filename": "ABC-100_rev1.pdf", "rel_path": "lib/a.pdf", "source_mtime": ""}]
    )
    assert ai.browse(db, q="abc100")["total"] == 1


MARM_HEADER = [
    "Materiał",
    "Jednostka miary",
    "Licznik",
    "Mianownik",
    "",
    "Szerokość",
    "Wysokość",
    "Długość",
    "Jednostka wymiaru",
    "EAN",
]


def test_us025_marm_duplicate_counted_once():
    db = _db()
    rows = [
        MARM_HEADER,
        ["R-1", "KAR", "100", "1", "", "40", "30", "20", "CM", ""],
        ["R-1", "kar", "120", "1", "", "41", "31", "21", "CM", ""],
        ["R-2", "SZT", "1", "1", "", "1", "1", "1", "CM", ""],
    ]
    res = mu.import_marm_rows(db, rows)
    stored = db.execute("SELECT COUNT(*) FROM material_uom_dims").fetchone()[0]
    assert res == {"imported": 2, "refs": 2, "skipped": 1}
    assert stored == res["imported"]
    assert mu.get_ref_units(db, "R1")[0]["factor"] == 120.0  # ostatni wiersz wygrywa
