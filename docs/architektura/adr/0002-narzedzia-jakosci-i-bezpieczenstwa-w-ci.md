# ADR-0002: Narzędzia jakości i bezpieczeństwa w CI

- **Status:** zaakceptowany (2026-10-15), do rewizji po US-002 i US-011
- **Role:** [DEV] + [SEC]

## Kontekst
CI blokowało tylko składnię i testy; skany bezpieczeństwa raz w miesiącu, doradczo. Definition of Done wymaga:
lint, testy, SAST, SCA, sekrety — bez nowych ustaleń wysokich/krytycznych. Repo publiczne na koncie
osobistym (darmowe minuty Actions, gitleaks bez licencji organizacyjnej).

## Decyzja

| Narzędzie | Cel | Tryb | Uzasadnienie |
|---|---|---|---|
| `ruff check` + `ruff format --check` | lint/format (reguły F, E9, W6) | **doradczy** do zamknięcia US-002 (66 błędów), potem blokujący | nie blokować pracy na legacy, ale ustalić datę |
| `python -m compileall` | składnia każdego modułu | blokujący | tani, łapie literówki poza testami |
| `pytest` (+ `pytest-cov` raport) | testy czystej logiki + integracyjne (Flask test client) | blokujący; próg pokrycia po decyzji Z-05 | 4 s, bez pakietów ML |
| `bandit -ll` | SAST Pythona (≥ średnie) | **blokujący** (dziś 0 ustaleń) | fałszywe alarmy oznaczać `# nosec Bxxx` z uzasadnieniem w linii |
| `semgrep` (`p/python`, `p/flask`, `p/owasp-top-ten`) | SAST wzorcowy, OWASP | doradczy do pierwszego triage, potem blokujący dla ERROR | reguły zewnętrzne — najpierw ocena szumu |
| `pip-audit -r requirements-prod.txt` | SCA (CVE w zależnościach) | **blokujący** | 0 CVE dziś; po US-011 działa na locku |
| `gitleaks` | sekrety w kodzie i historii | **blokujący** | `.gitleaks.toml` allowlistuje tylko syntetyczne dane testowe (opisane) |
| `trivy fs` (vuln, secret, misconfig) | konfiguracja Dockerfile, pliki | doradczy (misconfig Dockerfile „root user" otwarte → US-012) | po US-012 blokujący HIGH/CRITICAL |
| `trivy image` | obraz Docker | ręcznie / miesięcznie (`security.yml`) | obraz ML ~ kilka GB, build ~8 min — koszt minut (Z-05) |
| Dependabot (pip, actions, docker) | aktualizacje | tygodniowo, PR-y | wymaga lockfile dla pełnej wartości (US-011) |
| pre-commit (ruff, gitleaks, hooks) | lokalnie przed commitem | opcjonalny dla dewelopera | CONTRIBUTING.md |
| mypy | typowanie | **odroczone** | kod legacy bez adnotacji; rozważyć per nowy moduł |

Kolejność w pipeline: lint → testy → SAST → SCA → sekrety → skan konfiguracji. Wyniki jako artefakty
(JSON/SARIF). Uprawnienia workflow: `contents: read` (+ `security-events: write` tylko dla uploadu SARIF).

## Konsekwencje
- (+) Każdy PR ma widoczny wynik 7 kontroli; fałszywe alarmy są oznaczane, nie wyciszane hurtowo.
- (−) Dwa narzędzia doradcze (ruff, semgrep) do czasu triage — ryzyko „przyzwyczajenia się do żółtego";
  termin: zamknięcie US-002 (lint) i pierwszy triage semgrep w Sprint 1.
- (−) pip-audit na zakresach `>=` ocenia najnowsze wersje, nie te z produkcji — do czasu locka (US-011).
