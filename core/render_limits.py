"""core/render_limits.py — limity renderowania PDF (US-019, R-13).

Zalogowany użytkownik może wgrać PDF do 200 MB. Bez limitów jeden plik mógł:
  • mieć setki stron, z których każda była renderowana (OCR w 300 DPI),
  • mieć stronę wielkoformatową (np. 2 × 2 m), dla której PyMuPDF najpierw tworzył
    bitmapę o boku kilkudziesięciu tysięcy pikseli, a dopiero potem kod ją zmniejszał.

Ten moduł liczy powiększenie TAK, by bitmapa nigdy nie przekroczyła limitu pikseli
JUŻ przy renderze, ogranicza liczbę stron i DPI z konfiguracji. Czysty Python, bez
zależności od PyMuPDF — wywołujący przekazuje wymiary strony w punktach PDF (1/72 cala).

Konfiguracja (env):
  ARTWORK_MAX_PDF_PAGES  — maks. liczba renderowanych stron jednego pliku (domyślnie 50)
  ARTWORK_MAX_RENDER_PX  — maks. dłuższy bok renderowanej bitmapy w px (domyślnie 6000)
"""
from __future__ import annotations

import os

DPI_MIN = 72
DPI_MAX = 400

_DEFAULT_MAX_PAGES = 50
_DEFAULT_MAX_RENDER_PX = 6000


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    """Liczba z env w zakresie [lo, hi]; śmieci lub brak → wartość domyślna."""
    try:
        value = int(str(os.environ.get(name, default)).strip())
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


def max_pdf_pages() -> int:
    return _env_int("ARTWORK_MAX_PDF_PAGES", _DEFAULT_MAX_PAGES, 1, 500)


def max_render_px() -> int:
    return _env_int("ARTWORK_MAX_RENDER_PX", _DEFAULT_MAX_RENDER_PX, 500, 20000)


def clamp_dpi(value, default: int) -> int:
    """DPI z konfiguracji ograniczone do [72, 400]; niepoprawna wartość → default."""
    try:
        dpi = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(DPI_MIN, min(DPI_MAX, dpi))


def capped_zoom(width_pt: float, height_pt: float, zoom: float, max_px: int | None = None) -> float:
    """Powiększenie (piksele na punkt PDF) ograniczone tak, by dłuższy bok bitmapy
    nie przekroczył `max_px` (domyślnie ARTWORK_MAX_RENDER_PX).

    Strony mieszczące się w limicie renderują się dokładnie jak wcześniej
    (zwracane jest `zoom` bez zmian)."""
    limit = max_px if max_px else max_render_px()
    longest_pt = max(float(width_pt or 0), float(height_pt or 0))
    if longest_pt <= 0 or zoom <= 0:
        return zoom
    return min(zoom, limit / longest_pt)


def page_indices(page_count: int) -> range:
    """Indeksy stron do renderowania: najwyżej ARTWORK_MAX_PDF_PAGES pierwszych."""
    return range(min(max(0, int(page_count)), max_pdf_pages()))
