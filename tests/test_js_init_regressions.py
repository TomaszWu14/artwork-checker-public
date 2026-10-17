"""Regresje skryptów inicjalizujących (błędy JS przerywające cały blok <script>).

- admin.html wywoływał niezdefiniowaną `loadRoleModules()` — ReferenceError przerywał init,
  więc nie działało przywracanie ostatniej zakładki panelu.
- artwork.html odwoływał się do usuniętego panelu uploadu (fileA/zoneA) — wyjątek przerywał
  blok, w którym inicjalizowane są lightbox i skróty klawiszowe; martwy kod usunięty w całości.
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


def _ids_defined(text):
    return set(re.findall(r"""id\s*=\s*\\?['"]([\w-]+)""", text))


def test_artwork_references_only_existing_elements():
    """Każde getElementById('literał') w artwork.html wskazuje element z szablonu (lub base.html).

    Martwy kod starego panelu uploadu/porównania i modalu biblioteki masterów odwoływał się
    do 43 nieistniejących elementów (fileA, zoneA, btnCompare, masterLibPreview…) — usunięty.
    """
    text = (TEMPLATES / "artwork.html").read_text(encoding="utf-8")
    used = set(re.findall(r"getElementById\(\s*['\"]([\w-]+)['\"]\s*\)", text))
    defined = _ids_defined(text) | _ids_defined(
        (TEMPLATES / "base.html").read_text(encoding="utf-8")
    )
    assert used, "brak odwołań getElementById — zmienił się format szablonu?"
    assert not (used - defined), f"odwołania do nieistniejących elementów: {sorted(used - defined)}"
