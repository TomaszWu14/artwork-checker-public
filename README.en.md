# Artwork — packaging artwork comparison

🇵🇱 [Polska wersja](README.md)

![Comparison result for an artwork pair: score and list of differences](docs/img/porownanie.jpg)

A Flask web app for purchasing and quality teams that compares packaging artwork PDFs from
suppliers against approved masters and catches differences in barcodes, dates, names and
revisions before they end up printed on the product.

> **Portfolio project.** Company names are replaced with fictional ones; demo and test data are synthetic.
>
> Source is published for viewing (portfolio), all rights reserved — see [`LICENSE`](LICENSE).
> Commit history was squashed when the portfolio copy was anonymised.

[![ci](https://github.com/TomaszWu14/artwork-checker-public/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/TomaszWu14/artwork-checker-public/actions/workflows/ci.yml)

## At a glance

| | |
|---|---|
| **Problem** | Supplier packaging artworks were compared with masters by hand — mistakes in barcodes, dates, names and revisions surfaced only on finished goods. |
| **Solution** | Zone-based PDF comparison (text + image), GS1/EAN validation, a master library with revision history, a difference report (PDF/Excel) and a 3D package preview. |
| **Stack** | Python, Flask, pdfplumber + PyMuPDF + camelot (PDF), RapidOCR/Tesseract (OCR), PostgreSQL/SQLite, gunicorn, Docker; frontend: Jinja templates + Alpine.js, pdf.js, three.js. |
| **Quality** | ~1200 tests (`pytest tests/`), GitHub Actions CI (lint, tests, domain-logic coverage gate, Bandit, Semgrep, pip-audit, gitleaks, Trivy). |

The UI is Polish-first, with an English mode (language switch in the app).

## Quick start

Lightweight set — the same dependencies as CI, enough to run the tests:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install pytest python-dateutil dateparser babel flask werkzeug "rapidfuzz>=3.0,<4.0"
python -m pytest tests/ -q       # some tests are skipped without PDF/OCR libraries
```

Full app (PDF parsing, OCR, export) — without the heavy ML packages:

```bash
pip install -r requirements-prod.txt   # full requirements.txt adds optional ML engines
python migrate_db.py                   # SQLite database in instance/
python app.py                          # http://localhost:5000
```

**Account:** on first start the app creates a single `admin` account with a **random password**,
printed to the console and saved to `INITIAL_ADMIN_PASSWORD.txt` in the project root (gitignored).
Log in, change the password and delete the file. Further accounts are created by the admin in
**Admin → Accounts**.

Optional: Tesseract (OCR) and Ghostscript improve PDF parsing quality.

## My contribution

Sole author — from analysing the team's process to deployment.

- Artwork ↔ master comparison engine: text extraction with positions, zone comparison
  (text + image) and an OCR cascade for text converted to outlines.
- GS1 validation: EAN/UPC/GTIN check digits, reading barcodes from images, barcode ↔ printed text consistency.
- Difference report with a checklist of mandatory elements (REF, LOT, EXP, CE…) and PDF/Excel export.
- Master library with revision history and a 3D package preview built from the dieline (three.js).

## Why this stack

Flask with Jinja templates is enough for an internal tool used by a dozen people and needs no
separate frontend. pdfplumber gives text with positions (the basis of zone comparison), and
PyMuPDF renders pages quickly for image comparison. Some artworks have text converted to outlines,
hence the OCR cascade (RapidOCR on CPU, Tesseract as fallback); heavy ML models are optional and
lazy-loaded. SQLite locally, PostgreSQL in production.

## Limitations and next steps

- `app.py` is ~13.4k lines and `artwork_comparator.py` ~8.9k — to be split into blueprints and smaller modules.
- Comparison quality depends on the PDF: scans and outlined text go through OCR, which confuses
  characters (0/O, 1/I) — results need human confirmation.
- Tests mainly cover pure logic (barcode validation, normalisation, report); the full
  PDF → report path is tested narrowly.
- The full install is heavy (OpenCV, camelot, optional ML models) — prefer the Docker image.

## Where to start reading the code

1. [`artwork_comparator.py` — `compare_artworks`](artwork_comparator.py) — entry point for comparing a PDF pair.
2. [`barcode_validator.py` — `validate_artwork_barcodes`](barcode_validator.py) — check digits and barcode consistency.
3. [`artwork_report_engine.py`](artwork_report_engine.py) — difference report and checklist.

## Structure

| File / directory | Role |
|---|---|
| `app.py` | Flask app (routes, views) |
| `artwork_comparator.py`, `artwork_zone_comparator.py` | artwork ↔ master comparison |
| `barcode_validator.py` | EAN/GS1 and date validation |
| `artwork_index.py`, `artwork_naming.py` | master library, revision naming |
| `artwork_3d.py`, `dieline_templates.py` | dielines and 3D preview |
| `export_engine.py`, `artwork_report_engine.py` | PDF/Excel reports |
| `templates/`, `static/` | UI |
| `tests/` | pytest suite |

## Security

Vulnerability reports: [`SECURITY.md`](SECURITY.md) (privately, via GitHub "Report a vulnerability").
CI on every PR: secrets (gitleaks), SAST (Bandit, Semgrep OWASP Top 10 gate for new code),
dependencies (pip-audit, npm audit, Trivy), weekly Dependabot. HTTP headers: CSP with nonces
(no `unsafe-inline`/`unsafe-eval` for scripts), `X-Frame-Options`, `nosniff`, `Referrer-Policy`,
`Permissions-Policy`, COOP, HSTS behind HTTPS. GitHub Actions are pinned to commit SHAs.

## Process and documentation

The repo is run as if by a team of **analyst [BA] + developer [DEV] + security [SEC]** with a
Product Owner making decisions — see [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CHANGELOG.md`](CHANGELOG.md).
Analysis, architecture (C4, data model, API, ADRs), security (STRIDE threat model, risk register,
GDPR, ASVS L2), test strategy and runbook live in [`docs/`](docs/) (in Polish).
