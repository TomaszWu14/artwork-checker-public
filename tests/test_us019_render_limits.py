"""US-019 / R-13: limity renderowania PDF — liczba stron, rozmiar bitmapy, DPI z env."""

import pytest

from core import render_limits as rl


# ── Czysta logika (bez PyMuPDF — działa w CI) ─────────────────────────────────
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("300", 300),
        (" 150 ", 150),
        ("10", 72),
        ("5000", 400),
        ("abc", 300),
        (None, 300),
        ("", 300),
    ],
)
def test_clamp_dpi(raw, expected):
    assert rl.clamp_dpi(raw, 300) == expected


def test_capped_zoom_keeps_normal_pages_unchanged():
    # A4 (595×842 pt) w 300 DPI → 3508 px < 6000: bez zmian
    assert rl.capped_zoom(595, 842, 300 / 72) == pytest.approx(300 / 72)


def test_capped_zoom_limits_large_format_page():
    # Arkusz 2 × 2 m (~5669 pt) w 300 DPI dałby ~23 600 px boku
    z = rl.capped_zoom(5669, 5669, 300 / 72)
    assert 5669 * z <= rl.max_render_px() + 1


def test_capped_zoom_explicit_limit_and_degenerate_input():
    assert 1000 * rl.capped_zoom(1000, 500, 10.0, max_px=3500) == pytest.approx(3500)
    assert rl.capped_zoom(0, 0, 2.0) == 2.0


def test_page_indices_default_and_env(monkeypatch):
    monkeypatch.delenv("ARTWORK_MAX_PDF_PAGES", raising=False)
    assert list(rl.page_indices(3)) == [0, 1, 2]
    assert len(rl.page_indices(500)) == 50
    monkeypatch.setenv("ARTWORK_MAX_PDF_PAGES", "5")
    assert len(rl.page_indices(500)) == 5
    monkeypatch.setenv("ARTWORK_MAX_PDF_PAGES", "nonsense")
    assert len(rl.page_indices(500)) == 50
    monkeypatch.setenv("ARTWORK_MAX_PDF_PAGES", "0")  # dolna granica 1
    assert len(rl.page_indices(500)) == 1


def test_max_render_px_env_bounds(monkeypatch):
    monkeypatch.setenv("ARTWORK_MAX_RENDER_PX", "100")
    assert rl.max_render_px() == 500
    monkeypatch.setenv("ARTWORK_MAX_RENDER_PX", "999999")
    assert rl.max_render_px() == 20000


# ── Render przez PyMuPDF (pomijane, gdy brak pymupdf/PIL) ─────────────────────
def _make_pdf(path, pages, width_pt=200, height_pt=200):
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=width_pt, height=height_pt)
        page.insert_text((20, 40), f"strona {i + 1}")
    doc.save(str(path))
    doc.close()


@pytest.fixture
def comparator():
    pytest.importorskip("fitz")
    pytest.importorskip("PIL")
    return pytest.importorskip("artwork_comparator")


def test_load_pages_respects_page_limit(tmp_path, monkeypatch, comparator):
    pdf = tmp_path / "many.pdf"
    _make_pdf(pdf, 60)
    monkeypatch.delenv("ARTWORK_MAX_PDF_PAGES", raising=False)
    assert len(comparator._load_pages(str(pdf), 72)) == 50
    pdf2 = tmp_path / "many2.pdf"  # inny plik — bez trafienia w cache stron
    _make_pdf(pdf2, 12)
    monkeypatch.setenv("ARTWORK_MAX_PDF_PAGES", "4")
    assert len(comparator._load_pages(str(pdf2), 72)) == 4
    # Wskazana strona poza limitem nadal dostępna (wybór strony przez użytkownika)
    assert len(comparator._load_pages(str(pdf2), 72, page_idx=10)) == 1


def test_large_format_page_is_never_rendered_at_full_dpi(tmp_path, monkeypatch, comparator):
    """Bitmapa ma limit JUŻ przy renderze, a nie dopiero po zmniejszeniu."""
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "sheet.pdf"
    _make_pdf(pdf, 1, width_pt=5669, height_pt=2835)  # ~2 m × 1 m
    widths = []
    orig = fitz.Page.get_pixmap

    def spy(self, *a, **kw):
        pix = orig(self, *a, **kw)
        widths.append(max(pix.width, pix.height))
        return pix

    monkeypatch.setattr(fitz.Page, "get_pixmap", spy)
    imgs = comparator._load_pages(str(pdf), 300)
    assert widths and max(widths) <= comparator._MAX_IMG_PX + 2
    assert max(imgs[0].size) <= comparator._MAX_IMG_PX

    widths.clear()
    imgs = comparator._pdf_to_images(str(pdf), 300)
    assert widths and max(widths) <= comparator._MAX_IMG_PX + 2


def test_ocr_dpi_env_is_clamped():
    from core.render_limits import clamp_dpi

    # moduł liczy OCR_DPI tą samą funkcją; sprawdzamy kontrakt dla skrajnych wartości env
    assert clamp_dpi("2000", 300) == 400
    assert clamp_dpi("300dpi", 300) == 300
