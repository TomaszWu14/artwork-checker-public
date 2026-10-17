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
| `ruff check` | lint (reguły F, E9, W6) | **blokujący** od US-002 (66 błędów usuniętych 2026-10-16) | realne błędy: niezdefiniowane nazwy, zduplikowane klucze, martwe zmienne |
| `ruff format --check` | formatowanie | **blokujący** od US-020 (jednorazowe formatowanie 124 plików 2026-10-17; ruff przypięty na 0.17.1) | jeden styl, brak sporów o formatowanie w przeglądach; commit formatujący w `.git-blame-ignore-revs` |
| `python -m compileall` | składnia każdego modułu | blokujący | tani, łapie literówki poza testami |
| `pytest` (+ `pytest-cov` raport) | testy czystej logiki + integracyjne (Flask test client) | blokujący; od US-013 blokuje też pokrycie < 80 % dla 9 modułów logiki domenowej (łącznie, decyzja PO 2026-10-17); pokrycie całego repo — informacyjnie | 4 s, bez pakietów ML |
| `bandit -ll` | SAST Pythona (≥ średnie) | **blokujący** (dziś 0 ustaleń) | fałszywe alarmy oznaczać `# nosec Bxxx` z uzasadnieniem w linii |
| `semgrep` (`p/python`, `p/flask`, `p/owasp-top-ten`) | SAST wzorcowy, OWASP | doradczy do pierwszego triage, potem blokujący dla ERROR | reguły zewnętrzne — najpierw ocena szumu |
| `pip-audit -r requirements-prod.lock --require-hashes` | SCA (CVE w zależnościach) | **blokujący** | od US-011 audytuje zamrożone wersje produkcyjne |
| `gitleaks` | sekrety w kodzie i historii | **blokujący** | `.gitleaks.toml` allowlistuje tylko syntetyczne dane testowe (opisane) |
| `trivy fs` (vuln, secret, misconfig) | konfiguracja Dockerfile, pliki | **blokujący** HIGH/CRITICAL od US-012 (DS-0002 naprawione) | kontener non-root |
| `trivy image` | obraz Docker | ręcznie / miesięcznie (`security.yml`) | obraz ML ~ kilka GB, build ~8 min — koszt minut (Z-05) |
| Dependabot (pip, actions, docker) | aktualizacje | tygodniowo, PR-y | wymaga lockfile dla pełnej wartości (US-011) |
| pre-commit (ruff, gitleaks, hooks) | lokalnie przed commitem | opcjonalny dla dewelopera | CONTRIBUTING.md |
| mypy | typowanie | **odroczone** | kod legacy bez adnotacji; rozważyć per nowy moduł |

Kolejność w pipeline: lint → testy → SAST → SCA → sekrety → skan konfiguracji. Wyniki jako artefakty
(JSON/SARIF). Uprawnienia workflow: `contents: read` (+ `security-events: write` tylko dla uploadu SARIF).

## Konsekwencje
- (+) Każdy PR ma widoczny wynik 7 kontroli; fałszywe alarmy są oznaczane, nie wyciszane hurtowo.
- (−) Narzędzia doradcze (semgrep, trivy misconfig; ruff format do US-020) do czasu decyzji/triage — ryzyko „przyzwyczajenia się
  do żółtego"; ruff check jest już blokujący (US-002); termin triage semgrep: Sprint 2.
- (−) Lock obejmuje `requirements-prod.txt` (Render); pełny obraz ML (`requirements.txt` + torch z osobnego indeksu)
  nie ma jeszcze locka — kolejny krok (US-021). Lock nie aktualizuje się sam: PR Dependabota zmienia `requirements-prod.txt`,
  a lock regenerujemy poleceniem z nagłówka pliku (CONTRIBUTING).
