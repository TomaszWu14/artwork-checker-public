"""R-08: obraz bazowy ML publikowany do własnego pakietu repo (artwork-ml-base).

Dockerfile.slim musi budować z tego samego obrazu, który workflow publikuje — inaczej deploy
pobierze stary, niezablokowany obraz `doccompare-ml-base` starej aplikacji.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMAGE = "artwork-ml-base"


def test_workflow_publishes_own_package():
    wf = (ROOT / ".github/workflows/ml-base-image.yml").read_text(encoding="utf-8")
    tags = re.findall(r"ghcr\.io/\$\{\{ steps\.meta\.outputs\.owner_lc \}\}/([\w.-]+):", wf)
    assert tags and set(tags) == {IMAGE}


def test_slim_dockerfile_uses_published_image():
    slim = (ROOT / "Dockerfile.slim").read_text(encoding="utf-8")
    base = re.search(r"^ARG ML_BASE_IMAGE=ghcr\.io/[\w.-]+/([\w.-]+):", slim, re.M)
    assert base and base.group(1) == IMAGE
