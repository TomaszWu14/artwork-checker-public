"""US-016: dokumenty opisujące DocCompare są w docs/archiwum/ z adnotacją, a aktualne dokumenty
nie odsyłają do ich starych ścieżek."""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHIVED = [
    "architektura_doccompare.md",
    "DOKUMENTACJA_IT.md",
    "PROCES_POTWIERDZENIE_ETD.md",
    "PROCES_ZAKUPY_FLOW.md",
]


@pytest.mark.parametrize("name", ARCHIVED)
def test_archived_doc_has_banner_and_index_entry(name):
    path = ROOT / "docs/archiwum" / name
    assert path.read_text(encoding="utf-8").startswith("> **ARCHIWUM (US-016")
    assert f"`{name}`" in (ROOT / "docs/archiwum/README.md").read_text(encoding="utf-8")


def test_old_paths_are_gone():
    for old in (
        "architektura.md",
        "DOKUMENTACJA_IT.md",
        "PROCES_POTWIERDZENIE_ETD.md",
        "PROCES_ZAKUPY_FLOW.md",
    ):
        assert not (ROOT / "docs" / old).exists(), old


def test_current_docs_do_not_link_to_old_paths():
    """Odnośniki markdown do starych ścieżek w aktualnych dokumentach (wzmianki w tekście są dozwolone)."""
    link = re.compile(
        r"\]\((?:\.\./)*(?:docs/)?(architektura\.md|DOKUMENTACJA_IT\.md|PROCES_[A-Z_]+\.md)\)"
    )
    hits = []
    for p in list((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md", ROOT / "CLAUDE.md"]:
        if "archiwum" in p.parts or not p.exists():
            continue
        hits += [f"{p.name}: {m.group(0)}" for m in link.finditer(p.read_text(encoding="utf-8"))]
    assert hits == []
