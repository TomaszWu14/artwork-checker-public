"""Regresje skryptów inicjalizujących (błędy JS przerywające cały blok <script>).

- admin.html wywoływał niezdefiniowaną `loadRoleModules()` — ReferenceError przerywał init,
  więc nie działało przywracanie ostatniej zakładki panelu.
- artwork.html odwoływał się do usuniętego panelu uploadu (fileA/zoneA) — wyjątek przerywał
  blok, w którym inicjalizowane są `_pageImgs`, `_sections`, lightbox i skróty klawiszowe.
Sprawdzone też w Chromium (Playwright): brak `pageerror` na /artwork i /admin.
"""
import pathlib
import re

TEMPLATES = pathlib.Path(__file__).resolve().parent.parent / "templates"


def _defined_functions(text):
    return set(re.findall(r"(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", text))


def test_admin_init_calls_only_defined_functions():
    text = (TEMPLATES / "admin.html").read_text(encoding="utf-8")
    init = text.split("// ── init", 1)[1].split("</script>", 1)[0]
    called = set(re.findall(r"^([A-Za-z_$][\w$]*)\(\);", init, flags=re.M))
    assert called, "brak wywołań w bloku init"
    missing = called - _defined_functions(text)
    assert not missing, f"wywołania niezdefiniowanych funkcji: {missing}"


def test_artwork_legacy_upload_loop_is_guarded():
    text = (TEMPLATES / "artwork.html").read_text(encoding="utf-8")
    start = text.index("['A','B'].forEach(function(s){")
    head = text[start:start + 600]
    assert "if(!inp||!zone) return;" in head
