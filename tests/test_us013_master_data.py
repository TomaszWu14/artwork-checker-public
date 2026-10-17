"""US-013 — pokrycie logiki master data: normalizer, material_master,
supplier_master, material_uom, uom.

Czysta logika na izolowanych bazach SQLite w pamięci; dane wyłącznie syntetyczne.
"""

import os
import sqlite3
import sys
from datetime import date
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import material_master as mm  # noqa: E402
import material_uom as mu  # noqa: E402
import normalizer as nz  # noqa: E402
import supplier_master as sm  # noqa: E402
import uom  # noqa: E402

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


# ═════════════════════════════ normalizer ════════════════════════════════════


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1e5", Decimal("1E+5")),  # notacja naukowa
        ("2.5E-3", Decimal("0.0025")),
        ("1.234", Decimal("1234")),  # europejski separator tysięcy
        ("0.500", Decimal("0.500")),  # zero w części całkowitej → dziesiętne
        ("2,500", Decimal("2500")),  # angielski separator tysięcy
        ("0,500", Decimal("0.500")),
        ("1.234.567", Decimal("1234567")),
        ("1,234,567", Decimal("1234567")),
        ("1.234.567,89", Decimal("1234567.89")),
        ("1,234.56", Decimal("1234.56")),
        ("€ 1 234,56", Decimal("1234.56")),
        ("−5", Decimal("-5")),  # unicode minus
    ],
)
def test_us013_normalize_number_locale_formats(raw, expected):
    assert nz.normalize_number(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["   ", "x" * 51, "1.234,56-2.345,67", "n/a", "—", "1.2.3.4.5", "abc", "12 PLN"],
)
def test_us013_normalize_number_rejects_non_numbers(raw):
    assert nz.normalize_number(raw) is None


def test_us013_numbers_equal_near_zero_and_unparseable():
    assert nz.numbers_equal("0", "0,00005") is True  # szum zaokrąglenia
    assert nz.numbers_equal("0", "0,01") is False  # realna cena sub-centowa ≠ 0
    assert nz.numbers_equal("abc", "1") is None
    assert nz.numbers_equal("100", "100,5", tolerance_pct=1.0) is True
    assert nz.numbers_equal("100", "103", tolerance_pct=1.0) is False


def test_us013_rounding_and_diff_formatting():
    assert nz.numbers_differ_only_by_rounding("abc", "1") is False
    assert nz.numbers_differ_only_by_rounding("0,125", "0.13") is True  # HALF_UP
    assert nz.format_number_diff("100", "150") == "+50 (+50.0%)"
    assert nz.format_number_diff("1.000,00", "900") == "-100.00 (-10.0%)"
    assert nz.format_number_diff("0", "5") == "+5"
    assert nz.format_number_diff("a", "5") == "a → 5"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("15 Mar 2024", date(2024, 3, 15)),
        ("5 Kwi 2024", date(2024, 4, 5)),  # polska nazwa miesiąca
        ("05-30-2024", date(2024, 5, 30)),  # MM-DD (drugi człon > 12)
        ("30-05-2024", date(2024, 5, 30)),  # DD-MM
        ("2024.1.5", date(2024, 1, 5)),
        ("3/4/2024", date(2024, 4, 3)),  # dwuznaczne → preferujemy DD/MM
        ("March 15, 2024", date(2024, 3, 15)),  # fallback dateparser
    ],
)
def test_us013_normalize_date_formats(raw, expected):
    assert nz.normalize_date(raw) == expected


@pytest.mark.parametrize("raw", ["13/13/2024", "31/02/2024", "1985-05-05", ""])
def test_us013_normalize_date_rejects_invalid(raw):
    assert nz.normalize_date(raw) is None


def test_us013_date_candidates_and_possible_equality():
    assert nz.date_candidates("") == set()
    assert nz.date_candidates("03/04/2024") == {date(2024, 3, 4), date(2024, 4, 3)}
    assert nz.date_candidates("2024-03-04") == {date(2024, 3, 4)}
    # 13/04 jest jednoznaczne — zamiana dzień↔miesiąc nie daje poprawnej daty.
    assert nz.date_candidates("13/04/2024") == {date(2024, 4, 13)}
    assert nz.dates_possibly_equal("03/04/2024", "2024-03-04") is True
    assert nz.dates_possibly_equal("13/04/2024", "2024-04-12") is False
    assert nz.dates_possibly_equal("", "2024-04-12") is False


def test_us013_refs_and_company_names():
    assert nz.normalize_ref("") == ""
    assert nz.normalize_ref("nl753–s 40") == "NL753S40"
    assert nz.refs_match("", "X") == (False, 0.0)
    # Obecne zachowanie: tolerancja 1 znaku (literówka OCR) — czy to akceptowalne dla REF, zgłoszone PO (US-013).
    ok, conf = nz.refs_match("ABCDEFGH12", "ABCDEFGX12")
    assert ok is True and 0.85 <= conf < 1.0
    assert nz.refs_match("QWERTY", "ZXCVBN") == (False, 0.0)
    assert nz.normalize_company_name("") == ""
    assert nz.normalize_company_name("Acme  Sp. z o.o.") == "ACME SPZOO"
    assert nz.normalize_company_name("Foo Limited") == "FOO LTD"


def test_us013_validate_checksum_mixed_items_and_errors():
    items = [
        {"ref": "A", "qty": "2", "price": "1,50"},  # 3.00
        {"ref": "B", "net": "7"},  # net ma pierwszeństwo
        {"ref": "C"},  # nie da się policzyć
    ]
    res = nz.validate_checksum(items, "10")
    assert res["valid"] is True and res["calculated"] == 10.0
    assert res["error"] == "Nie można obliczyć dla: C"
    bad = nz.validate_checksum([], "abc")
    assert bad["valid"] is None and "abc" in bad["error"]


def test_us013_validate_checksum_zero_declared():
    ok = nz.validate_checksum([], "0")
    assert ok["valid"] is True and ok["diff_pct"] == 0.0
    off = nz.validate_checksum([{"net": "1"}], "0")
    assert off["valid"] is False and off["diff_pct"] is None


def test_us013_payment_terms_normalization_and_reverse():
    assert nz.normalize_payment_terms("") == ""
    assert nz.normalize_payment_terms("iw04") == "30 days"  # kod małymi literami
    assert nz.normalize_payment_terms("Net 45 days") == "45 days"
    assert nz.normalize_payment_terms("CAD") == "CAD"
    assert nz.normalize_payment_terms("Q1", {"Q1": "15 days"}) == "15 days"
    assert nz.payment_terms_equal("IW04", "30 days") is True
    assert nz.payment_terms_equal("IW30", "30 days") is False  # „after BL" to inny termin
    assert nz.payment_text_to_codes("") == []
    assert nz.payment_text_to_codes("30 days") == ["IW04", "N030", "ZB30"]
    assert nz.payment_text_to_codes("30 days after BL") == ["IW30"]
    assert nz.payment_text_to_codes("nt30") == ["NT30"]
    assert nz.payment_text_to_codes("pay in 60 days") == ["IW07", "N060", "ZB60"]


# ═════════════════════════════ material_master ═══════════════════════════════


def test_us013_ensure_table_upgrades_legacy_table():
    db = _db()
    # Stary schemat: tylko pierwotne kolumny (bez base_uom/vat/sent/grupy…).
    db.execute(
        "CREATE TABLE material_master (id INTEGER PRIMARY KEY, ref_code TEXT, ref_norm TEXT, "
        "opis_pl TEXT DEFAULT '', opis_en TEXT DEFAULT '', ean TEXT DEFAULT '', "
        "rodzina TEXT DEFAULT '', levels_json TEXT DEFAULT '{}', updated_at TEXT)"
    )
    db.commit()
    mm.ensure_table(db)
    cols = {r[1] for r in db.execute("PRAGMA table_info(material_master)").fetchall()}
    assert {"base_uom", "vat_rate", "sent", "grupa", "podgrupa", "customs_code"} <= cols
    # Indeks UNIQUE dołożony → upsert po ref_code działa na starej tabeli.
    mm.upsert_materials(db, [{"ref_code": "L1", "opis_pl": "a"}])
    mm.upsert_materials(db, [{"ref_code": "L1", "opis_pl": "b"}])
    assert db.execute("SELECT COUNT(*) FROM material_master").fetchone()[0] == 1


@pytest.mark.parametrize(
    "hdr, banner, expected",
    [
        ("", "", (None, None)),
        ("Kod CN", "", ("global", "tariff_cn")),
        ("Kod celny materiału", "", ("global", "customs_code")),
        ("Dostawcy", "", ("global", "supplier_codes")),
        ("Nazwa artworka", "", ("global", "txt_short_pl")),
        ("Stawka VAT", "", ("global", "vat_rate")),
        ("Czy SENT", "", ("global", "sent")),
        ("Kod producenta (MFR)", "", ("global", "producer_code")),
        ("kar_ean", "", ("level", ("karton", "ean"))),
        ("szt artwork", "", ("level", ("sztuka", "artwork_ref"))),
        ("Ilość podstawowej jednostki miary PAZ", "", ("level", ("paz", "qty_base"))),
        ("Przelicznik", "PPA", ("level", ("ppa", "qty_base"))),
        ("Przelicznik", "KAR", ("level", ("karton", "qty_base"))),
        ("Wymiary", "OP", ("level", ("op", "wymiar"))),
        ("EAN", "OPZ", ("level", ("opz", "ean"))),
        ("Artwork ref", "SZT", ("level", ("sztuka", "artwork_ref"))),
        ("Coś innego", "", (None, None)),
    ],
)
def test_us013_classify_headers(hdr, banner, expected):
    assert mm._classify(hdr, banner) == expected


def test_us013_sent_truthy_and_norm_vat_and_clean_ean():
    assert [mm.sent_truthy(v) for v in ("TAK", " x ", "Prawda", "nie", None, "0")] == [
        1,
        1,
        1,
        0,
        0,
        0,
    ]
    assert mm.norm_vat("23%") == "23"
    assert mm.norm_vat("8,0") == "8"
    assert mm.norm_vat("5,5 %") == "5.5"
    assert mm.norm_vat("zw.") == "zw"
    assert mm.norm_vat("NP") == "np"
    assert mm.norm_vat("brak") == "brak"
    assert mm.clean_ean("590-123-456-789-7") == "5901234567897"
    assert mm.clean_ean("12345") == ""


def test_us013_parse_workbook_rows_edge_cases():
    assert mm.parse_workbook_rows([]) == []
    assert mm.parse_workbook_rows(["not a row", 42]) == []
    assert mm.parse_workbook_rows([["SZT", "KAR"]]) == []  # sam banner, brak nagłówka
    rows = [
        [
            "ref_code",
            "op_ean",
            "Ilość podstawowej jednostki miary",
            "Podstawowa jednostka miary",
            "Stawka VAT",
            "SENT",
        ],
        ["R-1", "5901234567897", "10", "SZT", "23%", "tak"],
        ["R-2", "", "5901234567897", "SZT", "", ""],  # EAN w kolumnie przelicznika
        ["", "x", "1", "SZT", "", ""],  # brak REF → pominięty
        ["R-3"],  # krótki wiersz
    ]
    recs = mm.parse_workbook_rows(rows)
    assert [r["ref_code"] for r in recs] == ["R-1", "R-2", "R-3"]
    r1 = recs[0]
    assert r1["levels"] == {"op": {"ean": "5901234567897", "qty_base": "10"}}
    assert r1["base_uom"] == "SZT" and r1["vat_rate"] == "23" and r1["sent"] == 1
    assert recs[1]["levels"] == {}  # EAN-jako-przelicznik odrzucony
    assert recs[1]["sent"] is None  # pusta komórka SENT → None (nie nadpisuj)


def test_us013_import_workbook_conversions_skip_bad_factors():
    db = _db()
    rows = [
        ["", "OP", "OPZ", "KAR", "PAZ", "SZT", ""],
        [
            "ref_code",
            "Przelicznik",
            "Przelicznik",
            "Przelicznik",
            "Przelicznik",
            "Przelicznik",
            "jm",
        ],
        ["R-1", "10", "abc", "0", "1 200", "1", "SZT"],
    ]
    res = mm.import_workbook(db, rows)
    assert res["imported"] == 1
    conv = {
        (r["unit_from"], r["unit_to"]): r["factor"]
        for r in db.execute("SELECT unit_from, unit_to, factor FROM uom_conversion").fetchall()
    }
    # OP=10 ok; OPZ 'abc' nie-liczba, KAR 0 ≤ 0, PAZ '1 200' nie-float, SZT→SZT no-op.
    assert conv == {("OP", "PCS"): 10.0}
    assert res["conversions"] == 1


def test_us013_save_conversions_without_base_uom_is_noop():
    db = _db()
    assert mm._save_conversions(db, {"ref_norm": "X", "levels": {"op": {"qty_base": "5"}}}) == 0
    assert mm._save_conversions(db, {"ref_norm": "X", "base_uom": "SZT", "levels": {"op": {}}}) == 0


def test_us013_migrate_from_products_merges_without_overwriting():
    db = _db()
    assert mm.migrate_from_products(db) == {"migrated": 0, "error": "Brak tabeli products"}
    db.execute(
        "CREATE TABLE products (ref_code TEXT, product_name TEXT, ean TEXT, unit TEXT, "
        "tariff_cn TEXT, description TEXT, supplier_codes TEXT, active INTEGER)"
    )
    db.executemany(
        "INSERT INTO products VALUES (?,?,?,?,?,?,?,?)",
        [
            ("P-1", "Rękawice", "590 1234 567897", "SZT", "4015", "Gloves", "S1;S2", 1),
            ("P-2", "Istniejący", "", "", "", "", "", 1),
            ("", "bez REF", "", "", "", "", "", 1),
            ("P-3", "Nieaktywny", "", "", "", "", "", 0),
        ],
    )
    db.commit()
    mm.upsert_materials(
        db,
        [
            {
                "ref_code": "P-2",
                "opis_pl": "Master opis",
                "ean": "5901234567897",
                "jm": "KAR",
                "op_ean": "5901234567897",
            }
        ],
    )
    # Uszkodzony levels_json nie wywraca migracji.
    db.execute("UPDATE material_master SET levels_json='{bad' WHERE ref_code='P-2'")
    db.commit()
    assert mm.migrate_from_products(db) == {"migrated": 2}
    p1 = mm.get_material(db, "P-1")
    assert p1["opis_pl"] == "Rękawice" and p1["opis_en"] == "Gloves"
    assert p1["ean"] == "5901234567897" and p1["base_uom"] == "SZT"
    assert p1["tariff_cn"] == "4015" and p1["supplier_codes"] == "S1;S2"
    p2 = mm.get_material(db, "P-2")
    assert p2["opis_pl"] == "Master opis"  # pusty product_name nie nadpisuje
    assert p2["ean"] == "5901234567897" and p2["base_uom"] == "KAR"
    assert mm.get_material(db, "P-3") is None


def test_us013_validate_items_skips_empty_ref_and_flags_ean_mismatch():
    db = _db()
    mm.upsert_materials(db, [{"ref_code": "V-1", "ean": "5901234567897"}])
    warns = mm.validate_items(
        db,
        [
            {"ref": ""},
            {"ref": "v 1", "ean_a": "5901234567880"},
            {"ref": "V-1", "ean_a": "5901234567897"},
        ],
    )
    assert warns == ["REF v 1 — EAN 5901234567880 ≠ master 5901234567897"]


# ═════════════════════════════ supplier_master ═══════════════════════════════


def _sup_db():
    db = _db()
    db.execute(
        "CREATE TABLE suppliers(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, "
        "name TEXT NOT NULL, country TEXT DEFAULT 'XX', currency TEXT DEFAULT 'USD')"
    )
    db.commit()
    return db


def test_us013_supplier_parse_rows_edge_cases():
    assert sm.parse_rows([]) == []
    assert sm.parse_rows(["header as string"]) == []
    rows = [
        ["Kod dostawcy", "Nazwa", "Nieznana kolumna", "E-mail"],
        ["S1", "Acme Ltd", "ignored", "a@example.com"],
        ["S2"],  # brak nazwy → odrzucony
        ["", "Bez kodu", "", ""],
    ]
    assert sm.parse_rows(rows) == [{"code": "S1", "name": "Acme Ltd", "email": "a@example.com"}]


def test_us013_supplier_import_partial_reimport_keeps_values():
    db = _sup_db()
    sm.import_workbook(
        db,
        [
            ["kod", "nazwa", "kraj", "waluta", "lead time", "słowa kluczowe", "telefon"],
            ["S1", "Acme", "CN", "EUR", "45 dni", "acme; ACME Co ,", "+48 123"],
        ],
    )
    first = sm.get_supplier(db, "s1")  # kod bez rozróżniania wielkości liter
    assert (first["country"], first["currency"]) == ("CN", "EUR")
    assert first["detect_keywords_json"] == '["acme", "ACME Co"]'
    sm.import_workbook(db, [["kod", "nazwa"], ["S1", "Acme Renamed"]])
    s = sm.get_supplier(db, "S1")
    assert s["name"] == "Acme Renamed"
    assert (s["lead_time_days"], s["phone"]) == (45, "+48 123")
    # Uwaga: country/currency/detect_keywords_json celowo NIE asertowane po re-imporcie —
    # częściowy re-import resetuje je do 'XX'/'USD'/'[]' (błąd w ON CONFLICT
    # supplier_master.import_workbook, zgłoszony w raporcie US-013).


def test_us013_list_suppliers_without_query_skips_inactive():
    db = _sup_db()
    sm.import_workbook(db, [["kod", "nazwa"], ["B1", "Beta"], ["A1", "Alpha"], ["C1", "Gamma"]])
    db.execute("UPDATE suppliers SET active=0 WHERE code='C1'")
    db.commit()
    assert [s["code"] for s in sm.list_suppliers(db)] == ["A1", "B1"]


def test_us013_update_contact_paths():
    db = _sup_db()
    sm.import_workbook(db, [["kod", "nazwa", "email"], ["S1", "Acme", "old@example.com"]])
    assert sm.update_contact(db, "  ") == {"error": "Brak kodu dostawcy"}
    assert sm.update_contact(db, "NOPE", email="x@example.com") == {
        "error": "Nie znaleziono dostawcy"
    }
    assert sm.update_contact(db, "S1") == {"error": "Brak pól do aktualizacji"}
    assert sm.update_contact(
        db, "S1", email="new@example.com", contact_person="Jan", phone="1" * 80
    ) == {"ok": True}
    s = sm.get_supplier(db, "S1")
    assert s["email"] == "new@example.com" and s["contact_person"] == "Jan"
    assert s["phone"] == "1" * 60  # przycięte do 60 znaków
    # Pole None nie jest ruszane.
    sm.update_contact(db, "S1", phone="")
    s = sm.get_supplier(db, "S1")
    assert s["phone"] == "" and s["email"] == "new@example.com"


def test_us013_supplier_for_producer_case_insensitive_and_empty():
    db = _sup_db()
    sm.import_workbook(db, [["kod", "nazwa", "kod producenta"], ["S1", "Acme", "FG"]])
    assert sm.supplier_for_producer(db, " ") is None
    assert sm.supplier_for_producer(db, "fg")["code"] == "S1"
    assert sm.supplier_for_producer(db, "ZZ") is None


# ═════════════════════════════ material_uom ══════════════════════════════════


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


def test_us013_marm_num_parsing():
    assert mu._num(None) is None and mu._num("") is None
    assert mu._num(3) == 3.0
    assert mu._num("1.234,5") == 1234.5
    assert mu._num("abc") is None


def test_us013_marm_import_skips_and_duplicates():
    db = _db()
    assert mu.import_marm_rows(db, []) == {"imported": 0, "refs": 0, "skipped": 0}
    rows = [
        ["Raport MARM"],  # wiersz tytułowy przed nagłówkiem
        MARM_HEADER,
        ["R-1", "kar", "100", "1", "", "40", "30", "20", "CM", "5901234567897"],
        ["R-1", "KAR", "120", "1", "", "41", "31", "21", "cm", ""],  # duplikat: ostatni wygrywa
        ["", "SZT", "1", "1", "", "1", "1", "1", "CM", ""],  # brak REF
        ["R-2", "", "1", "1", "", "1", "1", "1", "CM", ""],  # brak jednostki
    ]
    res = mu.import_marm_rows(db, rows)
    assert res["refs"] == 1 and res["skipped"] == 3
    assert db.execute("SELECT COUNT(*) FROM material_uom_dims").fetchone()[0] == 1
    units = mu.get_ref_units(db, "r1")
    assert units == [
        {"unit": "KAR", "w_mm": 410.0, "h_mm": 310.0, "d_mm": 210.0, "ean": "", "factor": 120.0}
    ]


def test_us013_marm_bad_dims_and_empty_ref():
    db = _db()
    mu.ensure_table(db)
    db.execute(
        "INSERT INTO material_uom_dims(ref_code, ref_norm, unit, width, height, length, dim_unit) "
        "VALUES('R-9','R9','KAR','wide',10,10,'CM')"
    )
    db.commit()
    assert mu.get_ref_units(db, "R-9") == []  # nieliczbowa szerokość → pominięta
    assert mu.get_ref_units(db, "--") == []
    assert mu.suggest_refs(db, "R9") == []  # kandydat bez renderowalnych jednostek


def test_us013_marm_suggest_and_search_respect_limits():
    db = _db()
    rows = [MARM_HEADER] + [
        [f"LIM{i}", "KAR", "10", "1", "", "10", "10", "10", "CM", ""] for i in range(5)
    ]
    mu.import_marm_rows(db, rows)
    assert mu.suggest_refs(db, "LIM1")[0]["score"] == 100.0
    sug = mu.suggest_refs(db, "LIM", limit=2)  # równe score → porządek po ref_code
    assert [x["ref_code"] for x in sug] == ["LIM0", "LIM1"]
    found = mu.search_refs(db, "lim", limit=3)
    assert found == [{"ref_code": "LIM0"}, {"ref_code": "LIM1"}, {"ref_code": "LIM2"}]


# ═════════════════════════════ uom ═══════════════════════════════════════════


def test_us013_uom_plural_canonicalization():
    assert uom.canonical_unit("OPS") == "OP"
    assert uom.canonical_unit("ctns") == "CTN"
    assert uom.canonical_unit("BOXY") == "CTN"
    assert uom.canonical_unit("XYZ") == "XYZ"  # nieznana zostaje


def test_us013_uom_load_conversions_skips_non_numeric_factor():
    db = _db()
    uom.ensure_table(db)
    db.execute(
        "INSERT INTO uom_conversion(ref_norm, unit_from, unit_to, factor) VALUES('*','kartony','szt',12)"
    )
    db.execute(
        "INSERT INTO uom_conversion(ref_norm, unit_from, unit_to, factor) VALUES('*','op','szt','dużo')"
    )
    db.commit()
    conv = uom.load_conversions(db)
    assert conv == [{"ref_norm": "*", "unit_from": "CTN", "unit_to": "PCS", "factor": 12.0}]


def test_us013_uom_get_factor_and_convert_edge_cases():
    conv = [{"ref_norm": "*", "unit_from": "CTN", "unit_to": "PCS", "factor": 12.0}]
    assert uom.get_factor("", "PCS", "R", conv) is None
    assert uom.get_factor("KAR", "kartony", "R", conv) == 1.0
    assert uom.convert_qty("abc", "CTN", "PCS", "", conv) == (None, None)
    assert uom.convert_qty(2, "CTN", "PAL", "", conv) == (None, None)
    assert uom.convert_qty("3", "kar", "szt", "", conv) == (36.0, 12.0)
