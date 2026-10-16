# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie: [SemVer](https://semver.org/lang/pl/).
Wersja aplikacji: `constants.APP_VERSION`.

## [Unreleased]

### Added
- Proces zespołowy BA/DEV/SEC: `CONTRIBUTING.md` (role, kroki 1–7, Definition of Ready/Done), `SECURITY.md`,
  szablony issue (user story, bug, security) i PR z checklistami, `CODEOWNERS`, Dependabot.
- Audyt repozytorium z trzech perspektyw: `docs/AUDYT.md` (top 10 ryzyk, dług techniczny, luki wymagań).
- Dokumentacja analizy (`docs/analiza/`: wizja, interesariusze, procesy, wymagania v0.1, backlog MoSCoW, słownik,
  założenia/pytania do PO, macierz śledzenia), architektury (`docs/architektura/`: C4, ERD, inwentaryzacja API,
  ADR-0001…0003), bezpieczeństwa (`docs/bezpieczenstwo/`: klasyfikacja danych, STRIDE, rejestr ryzyk, RODO, ASVS L2),
  testów (`docs/testy/STRATEGIA_TESTOW.md`) i operacji (`docs/operacje/RUNBOOK.md`).
- CI (`ci.yml`): lint (ruff, doradczo), compileall + pytest z raportem pokrycia, Bandit (blokujący ≥ średnie),
  Semgrep (doradczo), pip-audit (blokujący), gitleaks (blokujący), Trivy fs/config (doradczo); artefakty raportów.
- `.gitleaks.toml` z udokumentowaną allowlistą danych testowych; pre-commit z gitleaks i hookami porządkowymi.

### Changed
- README: sekcja „Proces i dokumentacja” z linkami do nowych dokumentów.

### Security
- US-005: blokada konta po 10 nieudanych logowaniach w 15 min (liczona w `audit_log`, wspólna dla workerów,
  odporna na rotację IP, bez enumeracji kont) z wpisem `login_lockout`; polityka haseł przy resecie i zmianie
  hasła: min. 12 znaków, litera i cyfra, bez nazwy użytkownika, bez popularnych haseł (R-01).
- Zidentyfikowano i zaplanowano (bez zmian w kodzie w tym wydaniu): limity logowania w DB i blokada konta
  (US-005), hash tokenów resetu (US-003), sekrety tylko z env (US-004), ochrona promptów AI (US-007),
  CSP bez `unsafe-eval` (US-008), `save-copy` fail-closed (US-006) — patrz `docs/bezpieczenstwo/RYZYKA.md`.

## [1.0.0-artwork] — 2026-08

### Added
- Wydzielenie aplikacji Artwork z DocCompare v6 (spec `docs/superpowers/specs/2026-08-12-artwork-fork-design.md`):
  porównanie artworków, walidacja GS1/EAN, indeks masterów, 3D/PalViz, master data.
- Konto `admin` z losowym hasłem przy pierwszym starcie (bez kont-widm).

### Fixed
- Lista kontrolna EAN oceniana wyłącznie po wynikach sumy kontrolnej (#2).
