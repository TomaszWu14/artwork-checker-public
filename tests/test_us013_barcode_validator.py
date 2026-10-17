"""
US-013 — pokrycie logiki domenowej barcode_validator.py.

Testy czysto logiczne: bez PyMuPDF/Pillow/numpy/pyzbar/zxingcpp. Odczyt kodów z obrazu
jest podmieniany (monkeypatch) na syntetyczne listy zdekodowanych kodów lub atrapy
modułów w sys.modules, więc testy przechodzą w środowisku CI.

Kody użyte w testach (cyfry kontrolne policzone algorytmem GS1 mod-10):
  EAN-13  5901234123457, 4006381333931  (poprawne), 5901234123458 (błędna cyfra)
  EAN-8   96385074 (poprawny), 96385075 (błędny)
  UPC-A   036000291452 (poprawny), 036000291453 (błędny)
  GTIN-14 05901234123457 (indykator 0), 15901234123454 (indykator 1)
"""

import base64
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

import barcode_validator as bv

EAN_OK = "5901234123457"
EAN_OK2 = "4006381333931"
EAN_BAD = "5901234123458"
EAN8_OK = "96385074"
EAN8_BAD = "96385075"
UPC_OK = "036000291452"
UPC_BAD = "036000291453"
GTIN14_0 = "05901234123457"
GTIN14_1 = "15901234123454"


def _bc(fmt, raw):
    """Syntetyczny zdekodowany kod w formacie zwracanym przez read_barcodes_from_image."""
    return {"format": fmt, "raw_data": raw, "parsed": bv._classify(fmt, raw)}


def _levels(messages):
    return [m["level"] for m in messages]


def _texts(messages):
    return " | ".join(m["text"] for m in messages)


# ── walidatory numeru ─────────────────────────────────────────────────────────


def test_us013_normalize_ean_pads_and_strips_gtin14_indicator_zero():
    assert bv._normalize_ean("590-1234-123457") == EAN_OK
    assert bv._normalize_ean(GTIN14_0) == EAN_OK
    assert bv._normalize_ean("123456789012") == "0123456789012"
    # GTIN-14 z indykatorem != 0 zostaje 14-cyfrowy
    assert bv._normalize_ean(GTIN14_1) == GTIN14_1


def test_us013_ean13_accepts_gtin14_with_zero_indicator():
    r = bv.validate_ean13(GTIN14_0)
    assert r["valid"] is True
    assert r["digits"] == EAN_OK
    assert r["check_digit_expected"] == 7 and r["check_digit_actual"] == 7


def test_us013_ean13_rejects_gtin14_with_nonzero_indicator():
    r = bv.validate_ean13(GTIN14_1)
    assert r["valid"] is False
    assert r["check_digit_expected"] is None
    assert "indicator digit '1'" in r["error"]


def test_us013_ean13_bad_check_digit_message():
    r = bv.validate_ean13(EAN_BAD)
    assert r["valid"] is False
    assert r["check_digit_expected"] == 7 and r["check_digit_actual"] == 8
    assert r["error"] == "Błędna cyfra kontrolna: jest 8, powinno być 7"


def test_us013_ean8_valid_invalid_and_length():
    ok = bv.validate_ean8("9638-5074")
    assert ok["valid"] is True and ok["digits"] == EAN8_OK and ok["error"] is None
    bad = bv.validate_ean8(EAN8_BAD)
    assert bad["valid"] is False
    assert bad["check_digit_expected"] == 4 and bad["check_digit_actual"] == 5
    short = bv.validate_ean8("1234567")
    assert short["valid"] is False
    assert short["error"] == "Nieprawidłowa długość: 7 cyfr (oczekiwano 8)"


def test_us013_upca_valid_invalid_and_length():
    ok = bv.validate_upca(UPC_OK)
    assert ok["valid"] is True
    assert ok["ean"] == UPC_OK and ok["upca"] == UPC_OK and ok["digits"] == "0" + UPC_OK
    bad = bv.validate_upca(UPC_BAD)
    assert bad["valid"] is False and bad["check_digit_expected"] == 2
    wrong_len = bv.validate_upca("12345")
    assert wrong_len["valid"] is False
    assert "oczekiwano 12" in wrong_len["error"]
    assert "upca" not in wrong_len


@pytest.mark.parametrize(
    "code,typ,valid",
    [
        (EAN8_OK, "EAN-8", True),
        (UPC_OK, "UPC-A", True),
        (EAN_OK, "EAN-13", True),
        (GTIN14_0, "GTIN-14", True),
        (EAN_BAD, "EAN-13", False),
        ("12345", "EAN-13", False),
    ],
)
def test_us013_validate_barcode_number_dispatch(code, typ, valid):
    r = bv.validate_barcode_number(code)
    assert r["type"] == typ
    assert r["valid"] is valid


# ── GS1 ───────────────────────────────────────────────────────────────────────


def test_us013_parse_gs1_date_edge_cases():
    assert bv._parse_gs1_date("31051") is None
    assert bv._parse_gs1_date("31AB10") is None
    assert bv._parse_gs1_date("311310") is None  # miesiąc 13
    assert bv._parse_gs1_date("310000") is None  # miesiąc 00
    assert bv._parse_gs1_date("280200") == "2028-02-29"  # DD=00 → ostatni dzień, rok przestępny
    assert bv._parse_gs1_date("310431") is None  # 31 kwietnia
    assert bv._parse_gs1_date("310510") == "2031-05-10"


def test_us013_gs1_bytes_input_and_all_named_fields():
    r = bv.parse_gs1_128(f"(01){GTIN14_1}(21)SN1(11)250101".encode())
    assert r["raw"].startswith("(01)")
    assert r["gtin"] == GTIN14_1 and r["gtin_valid"] is True
    assert r["serial"] == "SN1"
    assert r["prod_date"] == "2025-01-01"
    assert r["errors"] == []
    assert r["missing_mandatory_ai"] == ["Data ważności", "LOT/Partia"]


def test_us013_gs1_unknown_ai_in_parenthesised_form():
    r = bv.parse_gs1_128(f"(01){GTIN14_0}(99)XYZ")
    assert r["gtin"] == GTIN14_0
    assert "Nierozpoznany AI: '(99)'" in r["errors"]
    assert [f["ai"] for f in r["fields"]] == ["01"]


def test_us013_gs1_invalid_date_parenthesised_reports_error():
    r = bv.parse_gs1_128("(17)310230")  # 30 lutego
    assert r["exp_date"] == "310230"
    assert any("Nieprawidłowa data Data ważności (AI 17)" in e for e in r["errors"])


def test_us013_gs1_fixed_ai_with_glued_next_ai_falls_back_to_scanner():
    # "(17)310510" + doklejone "10LOT9" bez nawiasu → wartość daty > 6 znaków
    r = bv.parse_gs1_128(f"(01){GTIN14_0}(17)31051010LOT9")
    assert r["exp_date"] == "2031-05-10"
    assert r["lot"] == "LOT9"
    assert r["errors"] == []
    assert r["missing_mandatory_ai"] == []


def test_us013_gs1_variable_ai_with_glued_fixed_ai_falls_back_to_scanner():
    r = bv.parse_gs1_128(f"(01){GTIN14_0}(10)ABC17310510")
    assert r["lot"] == "ABC"
    assert r["exp_date"] == "2031-05-10"


def test_us013_gs1_continuous_with_fnc1_separator():
    raw = f"01{GTIN14_0}10LOT7\x1d17310510"
    r = bv.parse_gs1_128(raw)
    assert r["lot"] == "LOT7"
    assert r["exp_date"] == "2031-05-10"
    assert r["gtin"] == GTIN14_0


def test_us013_gs1_continuous_leading_fnc1_and_invalid_date():
    r = bv.parse_gs1_128("\x1d17311399")
    assert [f["ai"] for f in r["fields"]] == ["17"]
    assert r["exp_date"] == "311399"
    assert any("AI 17" in e for e in r["errors"])


def test_us013_gs1_continuous_unknown_ai_stops_scan():
    r = bv.parse_gs1_128("99ABCDEF")
    assert r["fields"] == []
    assert r["errors"][0] == "Nierozpoznany AI przy poz. 0: '99AB'"
    assert r["missing_mandatory_ai"] == ["GTIN", "Data ważności", "LOT/Partia"]


def test_us013_gs1_continuous_bad_gtin_reported():
    r = bv.parse_gs1_128("0105901234123458")
    assert r["gtin_valid"] is False
    assert "Błędna cyfra kontrolna GTIN: 05901234123458" in r["errors"]


# ── _classify / _norm_ean13 / _decoded_eans / _lot_and_gs1 ────────────────────


@pytest.mark.parametrize(
    "fmt,raw,typ",
    [
        ("EAN_13", EAN_OK, "EAN-13"),
        ("EAN13", EAN_OK, "EAN-13"),
        ("EAN8", EAN8_OK, "EAN-8"),
        ("UPC_A", UPC_OK, "UPC-A"),
        ("UPC", UPC_OK, "UPC-A"),
        ("CODE128", f"(01){GTIN14_0}", "Code128/GS1-128"),
        ("DataMatrix", f"(01){GTIN14_0}", "DataMatrix/GS1"),
        ("QRCODE", "https://example.invalid", "QR"),
        ("PDF417", "abc", "PDF417"),
    ],
)
def test_us013_classify_by_format(fmt, raw, typ):
    p = bv._classify(fmt, raw)
    assert p["type"] == typ
    if typ in ("EAN-13", "EAN-8", "UPC-A"):
        assert p["validation"]["valid"] is True
    elif "GS1" in typ:
        assert p["gs1"]["gtin"] == GTIN14_0
    else:
        assert p["data"] == raw


def test_us013_norm_ean13():
    assert bv._norm_ean13(UPC_OK) == "0" + UPC_OK
    assert bv._norm_ean13(GTIN14_0) == EAN_OK
    assert bv._norm_ean13(EAN8_OK) == EAN8_OK
    assert bv._norm_ean13(None) == ""


def test_us013_decoded_eans_filters_invalid_errors_and_duplicates():
    barcodes = [
        _bc("EAN_13", EAN_OK),
        _bc("EAN_13", EAN_OK),  # duplikat
        _bc("EAN_13", EAN_BAD),  # zła suma → pominięty
        _bc("UPC_A", UPC_OK),  # → 13 cyfr z wiodącym 0
        _bc("EAN_8", EAN8_OK),
        _bc("CODE_128", f"(01){GTIN14_0}(10)L1"),  # GTIN-14/0 → EAN_OK (duplikat)
        _bc("CODE_128", f"(01){GTIN14_1}"),  # indykator 1 → pominięty
        _bc("CODE_128", f"(01)0{EAN_OK2}"),
        _bc("QR", "abc"),
        {"format": "error", "raw_data": "", "parsed": {}, "error": "boom"},
    ]
    assert bv._decoded_eans(barcodes) == [EAN_OK, "0" + UPC_OK, EAN8_OK, EAN_OK2]
    assert bv._decoded_eans(None) == []


def test_us013_lot_and_gs1_takes_first_values():
    barcodes = [
        {"format": "error", "raw_data": "", "parsed": {}, "error": "x"},
        _bc("EAN_13", EAN_OK),
        _bc("CODE_128", f"(01){GTIN14_0}(10)LOTA(17)310510"),
        _bc("CODE_128", "(10)LOTB"),
    ]
    lot, gs1 = bv._lot_and_gs1(barcodes)
    assert lot == "LOTA"
    assert gs1 == f"(01){GTIN14_0} (10)LOTA (17)310510"
    assert bv._lot_and_gs1([]) == (None, None)


# ── _check_barcodes_vs_text ───────────────────────────────────────────────────


def test_us013_check_ean13_match_mismatch_and_bad_checksum():
    msgs = bv._check_barcodes_vs_text(
        [
            _bc("EAN_13", EAN_OK),
            _bc("EAN_13", EAN_OK2),
            _bc("EAN_13", EAN_BAD),
            {"error": "x"},
        ],
        f"EAN {EAN_OK}",
        "A",
    )
    assert _levels(msgs) == ["OK", "KRYTYCZNY", "KRYTYCZNY"]
    assert all(m["source"] == "A" for m in msgs)
    assert f"({EAN_OK}) zgodny z tekstem" in msgs[0]["text"]
    assert "NIE ZGADZA SIĘ" in msgs[1]["text"] and EAN_OK in msgs[1]["text"]
    assert msgs[2]["check"] == "checksum" and "powinno być 7" in msgs[2]["text"]


def test_us013_check_ean13_mismatch_when_text_has_no_codes():
    msgs = bv._check_barcodes_vs_text([_bc("EAN_13", EAN_OK)], "brak numeru", "B")
    assert msgs[0]["level"] == "KRYTYCZNY"
    assert "brak EAN" in msgs[0]["text"]


def test_us013_check_ean8_and_upca_paths():
    msgs = bv._check_barcodes_vs_text(
        [
            _bc("EAN_8", EAN8_OK),
            _bc("UPC_A", UPC_OK),
            _bc("EAN_8", EAN8_BAD),
            _bc("UPC_A", UPC_BAD),
        ],
        f"{EAN8_OK} oraz 0{UPC_OK}",  # UPC-A wydrukowany jako EAN-13 z wiodącym 0
        "A",
    )
    assert [(m["code_type"], m["level"]) for m in msgs] == [
        ("EAN-8", "OK"),
        ("UPC-A", "OK"),
        ("EAN-8", "KRYTYCZNY"),
        ("UPC-A", "KRYTYCZNY"),
    ]
    assert msgs[2]["check"] == "checksum"


def test_us013_check_ean8_not_in_text():
    msgs = bv._check_barcodes_vs_text([_bc("EAN_8", EAN8_OK)], "nic", "A")
    assert msgs[0]["level"] == "KRYTYCZNY"
    assert "brak kodu" in msgs[0]["text"]


def test_us013_check_gs1_full_match():
    bc = _bc("CODE_128", f"(01){GTIN14_0}(17)310510(11)250101(10)LOT77")
    msgs = bv._check_barcodes_vs_text([bc], f"EAN {EAN_OK} LOT: LOT77", "A")
    assert _levels(msgs) == ["OK", "OK", "OK", "OK"]
    t = _texts(msgs)
    assert f"EAN-13={EAN_OK} — poprawny" in t
    assert "LOT (10)LOT77 zgodny" in t
    assert "data ważności (17): 2031-05-10" in t
    assert "data produkcji (11): 2025-01-01" in t


def test_us013_check_gs1_gtin_and_lot_mismatch():
    bc = _bc("CODE_128", f"(01){GTIN14_0}(10)LOT77")
    msgs = bv._check_barcodes_vs_text([bc], f"EAN {EAN_OK2} LOT: OTHER1", "B")
    assert _levels(msgs) == ["OK", "KRYTYCZNY", "KRYTYCZNY"]
    assert f"GTIN z GS1-128 ({EAN_OK}) NIE ZGADZA SIĘ" in msgs[1]["text"]
    assert "≠ LOT w tekście 'OTHER1'" in msgs[2]["text"]


def test_us013_check_gs1_bad_gtin_and_lot_without_text():
    bc = _bc("CODE_128", "(01)05901234123458(10)LOT77")
    msgs = bv._check_barcodes_vs_text([bc], "", "A")
    assert _levels(msgs) == ["KRYTYCZNY", "INFO"]
    assert "Błędna cyfra kontrolna" in msgs[0]["text"]
    assert "brak tekstu LOT" in msgs[1]["text"]


def test_us013_check_gs1_non_retail_gtin14_and_13_digit_gtin():
    msgs = bv._check_barcodes_vs_text([_bc("DATA_MATRIX", f"(01){GTIN14_1}")], EAN_OK, "A")
    assert _levels(msgs) == ["INFO"]
    assert "indykator=1" in msgs[0]["text"]
    # GTIN 13-cyfrowy (niekanoniczny, ale spotykany) → walidowany wprost jako EAN-13
    bc13 = {
        "format": "CODE_128",
        "raw_data": "",
        "parsed": {"type": "Code128/GS1-128", "gs1": {"gtin": EAN_OK}},
    }
    msgs13 = bv._check_barcodes_vs_text([bc13], EAN_OK, "A")
    assert _levels(msgs13) == ["OK"]


def test_us013_check_gs1_empty_payload_skipped():
    bc = {"format": "CODE_128", "raw_data": "", "parsed": {"type": "Code128/GS1-128", "gs1": {}}}
    assert bv._check_barcodes_vs_text([bc], EAN_OK, "A") == []


# ── validate_artwork_barcodes ─────────────────────────────────────────────────


def test_us013_artwork_no_lib_ocr_only(monkeypatch):
    monkeypatch.setattr(bv, "HAS_ZXING", False)
    monkeypatch.setattr(bv, "HAS_PYZBAR", False)
    r = bv.validate_artwork_barcodes(f"{EAN_OK} {EAN8_OK}", f"{EAN_OK} {EAN_BAD}", None, None)
    assert r["has_barcode_lib"] is False
    assert r["eans_a"] == [EAN_OK, EAN8_OK]
    assert r["eans_b"] == [EAN_OK, EAN_BAD]
    lv = [(m["source"], m["level"], m.get("code_type")) for m in r["messages"]]
    # checksum (EAN_OK nie powtarzany dla B), różnice A↔B, info o braku biblioteki
    assert ("A", "OK", "EAN-13") in lv
    assert ("A", "OK", "EAN-8") in lv
    assert ("B", "KRYTYCZNY", "EAN-13") in lv
    assert sum(1 for m in r["messages"] if m.get("check") == "checksum") == 3
    t = _texts(r["messages"])
    assert f"EAN {EAN8_OK} obecny tylko w wersji A" in t
    assert f"EAN {EAN_BAD} obecny tylko w wersji B" in t
    assert "(z tekstu OCR)" not in t  # przy niezgodności brak komunikatu zgodności
    assert r["messages"][-1]["source"] == "system"
    assert r["lot_a"] is None and r["barcode_gs1_b"] is None


def test_us013_artwork_no_codes_at_all(monkeypatch):
    monkeypatch.setattr(bv, "HAS_ZXING", False)
    monkeypatch.setattr(bv, "HAS_PYZBAR", False)
    r = bv.validate_artwork_barcodes("brak", "brak")
    assert r["messages"][0]["level"] == "INFO"
    assert "Nie wykryto EAN-13" in r["messages"][0]["text"]


def test_us013_artwork_ocr_match_and_one_sided(monkeypatch):
    monkeypatch.setattr(bv, "HAS_ZXING", False)
    monkeypatch.setattr(bv, "HAS_PYZBAR", False)
    r = bv.validate_artwork_barcodes(EAN_OK, EAN_OK)
    assert any(
        m["source"] == "A+B" and m["level"] == "OK" and "(z tekstu OCR)" in m["text"]
        for m in r["messages"]
    )
    # tylko jedna strona ma kod → brak porównania A+B (ani OK, ani KRYTYCZNY)
    r1 = bv.validate_artwork_barcodes(EAN_OK, "")
    assert not any(m["source"] == "A+B" for m in r1["messages"])


def test_us013_artwork_decoded_barcodes_take_precedence(monkeypatch):
    monkeypatch.setattr(bv, "HAS_ZXING", True)
    decoded = {
        "imgA": [_bc("UPC_A", UPC_OK), _bc("CODE_128", f"(01){GTIN14_0}(10)LOTA(17)310510")],
        "imgB": [_bc("EAN_13", "0" + UPC_OK), _bc("CODE_128", f"(01){GTIN14_0}(10)LOTB")],
    }
    monkeypatch.setattr(bv, "read_barcodes_from_image", lambda img: decoded[img])
    # OCR A zawiera błędnie odczytany kod — kod kreskowy ma pierwszeństwo w A↔B
    r = bv.validate_artwork_barcodes(
        f"0{UPC_OK} {EAN_OK} LOT: LOTA", f"0{UPC_OK} {EAN_OK} LOT: LOTB", ["imgA"], ["imgB"]
    )
    assert r["has_barcode_lib"] is True
    ab = [m for m in r["messages"] if m["source"] == "A+B"]
    assert len(ab) == 1 and ab[0]["level"] == "OK"
    assert "(z kodu kreskowego)" in ab[0]["text"]
    assert f"0{UPC_OK}" in ab[0]["text"] and EAN_OK in ab[0]["text"]
    assert r["lot_a"] == "LOTA" and r["lot_b"] == "LOTB"
    assert r["barcode_gs1_a"] == f"(01){GTIN14_0} (10)LOTA (17)310510"
    # sekcja 3 dodała komunikaty spójności dla obu stron
    assert any(m["source"] == "A" and "LOT (10)LOTA zgodny" in m["text"] for m in r["messages"])
    assert any(m["source"] == "B" and "LOT (10)LOTB zgodny" in m["text"] for m in r["messages"])


def test_us013_artwork_lib_present_but_no_images(monkeypatch):
    monkeypatch.setattr(bv, "HAS_PYZBAR", True)

    def _boom(img):
        raise AssertionError("nie powinno być wywołane bez obrazów")

    monkeypatch.setattr(bv, "read_barcodes_from_image", _boom)
    r = bv.validate_artwork_barcodes(EAN_OK, EAN_OK2, [], [])
    assert r["has_barcode_lib"] is True
    assert not any(m["source"] == "system" for m in r["messages"])
    assert sum(1 for m in r["messages"] if m["level"] == "KRYTYCZNY") == 2


# ── read_barcodes_from_image / atrapy bibliotek ───────────────────────────────


class _FakeImg:
    def __init__(self, size=(400, 200), tag="orig"):
        self.size = size
        self.tag = tag
        self.resized_to = None

    def convert(self, mode):
        return self

    def resize(self, size, resample):
        out = _FakeImg(size, tag="up")
        out.resized_to = (size, resample)
        return out


def _install_fake_pil(monkeypatch):
    pil = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")
    image_mod.LANCZOS = "LANCZOS"
    image_mod.BICUBIC = "BICUBIC"
    enh = types.ModuleType("PIL.ImageEnhance")

    class _Contrast:
        def __init__(self, img):
            self.img = img

        def enhance(self, factor):
            assert factor == 1.5
            return self.img

    enh.Contrast = _Contrast
    pil.Image = image_mod
    pil.ImageEnhance = enh
    monkeypatch.setitem(sys.modules, "PIL", pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_mod)
    monkeypatch.setitem(sys.modules, "PIL.ImageEnhance", enh)


def _install_fake_numpy(monkeypatch):
    np = types.ModuleType("numpy")
    np.array = lambda x: x
    monkeypatch.setitem(sys.modules, "numpy", np)


def test_us013_read_barcodes_dispatch(monkeypatch):
    assert bv.read_barcodes_from_image(None) == []
    monkeypatch.setattr(bv, "HAS_ZXING", False)
    monkeypatch.setattr(bv, "HAS_PYZBAR", False)
    assert bv.read_barcodes_from_image(object()) == []
    monkeypatch.setattr(bv, "HAS_PYZBAR", True)
    monkeypatch.setattr(bv, "_read_pyzbar", lambda img: ["pyzbar"])
    assert bv.read_barcodes_from_image(object()) == ["pyzbar"]
    monkeypatch.setattr(bv, "HAS_ZXING", True)
    monkeypatch.setattr(bv, "_read_zxing", lambda img: ["zxing"])
    assert bv.read_barcodes_from_image(object()) == ["zxing"]


def test_us013_upscale_small_large_and_broken(monkeypatch):
    _install_fake_pil(monkeypatch)
    small = _FakeImg((1000, 300))
    up = bv._upscale_for_barcode(small)
    assert up is not small
    assert up.resized_to == ((2600, 780), "LANCZOS")
    tiny = _FakeImg((100, 50))
    assert bv._upscale_for_barcode(tiny).size == (300, 150)  # skala ograniczona do 3.0
    big = _FakeImg((3000, 1000))
    assert bv._upscale_for_barcode(big) is big
    near = _FakeImg((2550, 100))  # skala ≤ 1.05 → bez zmian
    assert bv._upscale_for_barcode(near) is near
    broken = object()  # brak .size → wyjątek połknięty, zwraca oryginał
    assert bv._upscale_for_barcode(broken) is broken


def test_us013_read_zxing_with_fake_module_and_upscale_retry(monkeypatch):
    _install_fake_pil(monkeypatch)
    _install_fake_numpy(monkeypatch)
    calls = []

    class _Code:
        format = "EAN13"
        text = EAN_OK

    def read_barcodes(a, **kw):
        calls.append((a.tag, tuple(sorted(kw))))
        if kw.get("try_invert"):
            raise TypeError("old zxingcpp")
        if "try_rotate" in kw:
            raise TypeError("very old zxingcpp")
        return [] if a.tag == "orig" else [_Code()]

    monkeypatch.setattr(
        bv, "zxingcpp", types.SimpleNamespace(read_barcodes=read_barcodes), raising=False
    )
    out = bv._read_zxing(_FakeImg((500, 200)))
    assert out == [
        {
            "format": "EAN13",
            "raw_data": EAN_OK,
            "parsed": bv._classify("EAN13", EAN_OK),
        }
    ]
    assert out[0]["parsed"]["validation"]["valid"] is True
    # 3 próby (fallback kwargs) na oryginale + 3 na powiększonej kopii
    assert [c[0] for c in calls] == ["orig"] * 3 + ["up"] * 3


def test_us013_read_zxing_error_is_reported(monkeypatch):
    _install_fake_numpy(monkeypatch)

    def read_barcodes(a, **kw):
        raise RuntimeError("decoder crashed")

    monkeypatch.setattr(
        bv, "zxingcpp", types.SimpleNamespace(read_barcodes=read_barcodes), raising=False
    )
    out = bv._read_zxing(_FakeImg())
    assert out == [{"format": "error", "raw_data": "", "parsed": {}, "error": "decoder crashed"}]


def test_us013_read_pyzbar_with_fake_module(monkeypatch):
    _install_fake_pil(monkeypatch)
    _install_fake_numpy(monkeypatch)

    class _Sym:
        def __init__(self, typ, data):
            self.type = typ
            self.data = data

    def decode(arr):
        if arr.tag == "orig":
            return []
        return [_Sym("EAN13", EAN_OK.encode()), _Sym("CODE128", None)]

    monkeypatch.setattr(bv, "_pyzbar", types.SimpleNamespace(decode=decode), raising=False)
    out = bv._read_pyzbar(_FakeImg((800, 400)))
    assert out[0]["format"] == "EAN13" and out[0]["raw_data"] == EAN_OK
    assert out[0]["parsed"]["type"] == "EAN-13"
    assert out[1]["format"] == "CODE128" and out[1]["raw_data"] == ""
    assert "error" in out[1]


def test_us013_read_pyzbar_decode_failure(monkeypatch):
    _install_fake_pil(monkeypatch)
    _install_fake_numpy(monkeypatch)

    def decode(arr):
        raise ValueError("bad image")

    monkeypatch.setattr(bv, "_pyzbar", types.SimpleNamespace(decode=decode), raising=False)
    assert bv._read_pyzbar(_FakeImg()) == [
        {"format": "error", "raw_data": "", "parsed": {}, "error": "bad image"}
    ]


# ── deep_validate_printed_data ────────────────────────────────────────────────


def test_us013_deep_validate_text_only():
    r = bv.deep_validate_printed_data(f"LOT: AB1234 EAN {EAN_OK} EXP: 2031-05-10")
    assert r["ok"] is True
    assert r["lot"] == "AB1234" and r["ean"] == EAN_OK and r["exp_date"] == "2031-05-10"
    assert r["barcode_gs1"] is None
    assert _levels(r["details"]) == ["OK", "INFO"]
    assert "brak biblioteki" in r["details"][1]["text"]


def test_us013_deep_validate_bad_ean_and_no_ean():
    r = bv.deep_validate_printed_data(f"EAN {EAN_BAD}")
    assert r["ok"] is False
    assert r["issues"] == [f"EAN-13 ({EAN_BAD}): Błędna cyfra kontrolna: jest 8, powinno być 7"]
    r2 = bv.deep_validate_printed_data("Batch: XY99 (17)310510")
    assert r2["ok"] is True
    assert r2["lot"] == "XY99" and r2["ean"] is None and r2["exp_date"] == "310510"
    assert r2["details"][0] == {"level": "INFO", "text": "Nie znaleziono EAN-13 w tekście OCR"}


class _FakePilImage:
    def __init__(self, w=100, h=50):
        self.width, self.height = w, h
        self.closed = False

    def convert(self, mode):
        return _FakePilImage(self.width, self.height)

    def close(self):
        self.closed = True


def _patch_pil_open(monkeypatch, img=None, exc=None):
    def _open(buf):
        assert buf.read() == b"fake-png"
        if exc:
            raise exc
        return img

    monkeypatch.setattr(bv, "HAS_PIL", True)
    monkeypatch.setattr(bv, "_PIL_Image", types.SimpleNamespace(open=_open))


_B64 = base64.b64encode(b"fake-png").decode()


def test_us013_deep_validate_barcode_all_consistent(monkeypatch):
    _patch_pil_open(monkeypatch, _FakePilImage())
    monkeypatch.setattr(
        bv,
        "read_barcodes_from_image",
        lambda img: [_bc("CODE_128", f"(01){GTIN14_0}(17)310510(10)ab1234")],
    )
    r = bv.deep_validate_printed_data(f"LOT: AB1234 EAN {EAN_OK} EXP: 2031-05-10", _B64)
    assert r["ok"] is True, r["issues"]
    assert r["barcode_gs1"]["gtin"] == GTIN14_0
    assert _levels(r["details"]) == ["OK", "OK", "OK", "OK"]
    assert "LOT w barcode (ab1234) zgodny" in _texts(r["details"])


def test_us013_deep_validate_barcode_all_mismatched(monkeypatch):
    _patch_pil_open(monkeypatch, _FakePilImage())
    monkeypatch.setattr(
        bv,
        "read_barcodes_from_image",
        lambda img: [_bc("CODE_128", f"(01)0{EAN_OK2}(17)310510(10)ZZ9999")],
    )
    r = bv.deep_validate_printed_data(f"LOT: AB1234 EAN {EAN_OK} EXP: 2031-06-10", _B64)
    assert r["ok"] is False
    assert len(r["issues"]) == 3
    assert r["issues"][0] == f"EAN w barcode (0{EAN_OK2}) ≠ EAN w tekście ({EAN_OK})"
    assert r["issues"][1] == "LOT w barcode (ZZ9999) ≠ LOT w tekście (AB1234)"
    assert r["issues"][2] == "Data ważności w barcode (2031-05-10) ≠ tekst (2031-06-10)"


def test_us013_deep_validate_plain_ean13_barcode(monkeypatch):
    _patch_pil_open(monkeypatch, _FakePilImage())
    monkeypatch.setattr(
        bv, "read_barcodes_from_image", lambda img: [_bc("QR", "x"), _bc("EAN_13", EAN_OK)]
    )
    r = bv.deep_validate_printed_data(f"EAN {EAN_OK}", _B64)
    assert r["barcode_gs1"] == {"gtin": EAN_OK, "lot": None, "exp_date": None}
    assert r["ok"] is True
    assert f"EAN barcode ({EAN_OK}) zgodny z tekstem OCR ({EAN_OK})" in _texts(r["details"])


def test_us013_deep_validate_barcodes_without_gs1(monkeypatch):
    _patch_pil_open(monkeypatch, _FakePilImage())
    monkeypatch.setattr(bv, "read_barcodes_from_image", lambda img: [_bc("QR", "x")])
    r = bv.deep_validate_printed_data("nic", _B64)
    assert r["barcode_gs1"] is None
    assert r["details"][-1] == {
        "level": "INFO",
        "text": "Odczytano kody kreskowe, brak danych GS1-128",
    }


def test_us013_deep_validate_image_too_large(monkeypatch):
    big = _FakePilImage(10_000, 6_000)
    _patch_pil_open(monkeypatch, big)
    r = bv.deep_validate_printed_data(f"EAN {EAN_OK}", _B64)
    assert r["ok"] is False
    assert r["scan_error"] == "Image too large"
    assert r["issues"] == ["Obraz zbyt duży do analizy kodów kreskowych"]
    assert big.closed is True


def test_us013_deep_validate_image_decode_error(monkeypatch):
    _patch_pil_open(monkeypatch, exc=OSError("cannot identify image file"))
    r = bv.deep_validate_printed_data(f"EAN {EAN_OK}", _B64)
    assert r["ok"] is False
    assert r["scan_error"] == "cannot identify image file"
    assert r["issues"] == ["Nie można odczytać obrazu kodu kreskowego: cannot identify image file"]
