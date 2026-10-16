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
| `ruff format --check` | formatowanie | doradczy do decyzji PO o jednorazowym sformatowaniu 108 plików (US-020) | wielki diff bez wartości funkcjonalnej — osobna decyzja |
| `python -m compileall` | składnia każdego modułu | blokujący | tani, łapie literówki poza testami |
| `pytest` (+ `pytest-cov` raport) | testy czystej logiki + integracyjne (Flask test client) | blokujący; próg pokrycia po decyzji Z-05 | 4 s, bez pakietów ML |
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
- (−) Narzędzia doradcze (ruff format, semgrep, trivy misconfig) do czasu decyzji/triage — ryzyko „przyzwyczajenia się
  do żółtego"; ruff check jest już blokujący (US-002); termin triage semgrep: Sprint 2.
- (−) Lock obejmuje `requirements-prod.txt` (Render); pełny obraz ML (`requirements.txt` + torch z osobnego indeksu)
  nie ma jeszcze locka — kolejny krok (US-021). Lock nie aktualizuje się sam: PR Dependabota zmienia `requirements-prod.txt`,
  a lock regenerujemy poleceniem z nagłówka pliku (CONTRIBUTING).
