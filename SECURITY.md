# Polityka bezpieczeństwa

## Zgłaszanie podatności

Jeśli znajdziesz podatność, **nie otwieraj publicznego issue z detalami**. Zgłoś ją prywatnie:

1. GitHub → zakładka **Security** → **Report a vulnerability** (private vulnerability reporting), lub
2. e-mail do właściciela repozytorium (adres w profilu GitHub `TomaszWu14`), temat: `[SECURITY] artwork-checker`.

Podaj: opis, wersję/commit, kroki odtworzenia, wpływ, ewentualny PoC. Otrzymasz potwierdzenie w ciągu
**5 dni roboczych**, a plan naprawy w ciągu **30 dni** (krytyczne: priorytetowo). Prosimy o 90 dni na naprawę
przed publikacją (coordinated disclosure). W publicznym repo publikujemy jedynie opis ogólny (szablon issue
*Security issue*), bez szczegółów exploitu.

## Zakres

Kod w tym repozytorium: aplikacja Flask (`app.py`, `blueprints/`, `core/`, moduły domenowe), agent
`library_sync.py`, konfiguracja Docker/CI. Poza zakresem: usługi zewnętrzne (Anthropic, Mistral, Resend,
Sentry, PalViz), infrastruktura hostingu, ataki socjotechniczne, DoS wolumetryczny.

## Wspierane wersje

| Wersja | Wsparcie |
|---|---|
| `main` (`1.0.0-artwork`) | ✅ poprawki bezpieczeństwa |
| starsze / DocCompare v6 | ❌ |

## Zasady bezpieczeństwa projektu (skrót)

- Role i uprawnienia po stronie serwera dla każdego endpointu; test „brak dostępu” dla każdej roli.
- CSRF na mutacjach; cookie `HttpOnly`/`Secure`/`SameSite=Strict`; HSTS; CSP; brak nagłówka `Server`.
- Sekrety wyłącznie w zmiennych środowiskowych; `.env.example` bez wartości; gitleaks w CI.
- Upload: limit rozmiaru, walidacja typu po zawartości (magic bytes), `secure_filename`, katalog poza publicznym.
- Zapytania SQL parametryzowane przez `db.get_db()`; nazwy kolumn tylko z białych list.
- Logi bez haseł, tokenów i zbędnych danych osobowych; audyt operacji wrażliwych (`audit_log`).
- Treść PDF i odpowiedzi API traktowane jako dane, nie instrukcje (ochrona przed prompt injection — w toku, US-007).
- Zależności skanowane (pip-audit, Trivy), kod skanowany (Bandit, Semgrep) w CI; Dependabot tygodniowo.

Szczegóły: `docs/bezpieczenstwo/` (klasyfikacja danych, model zagrożeń, rejestr ryzyk, RODO, checklista ASVS).

## Ujawnione i naprawione

| Data | Opis | Naprawa |
|---|---|---|
| — | brak zgłoszeń zewnętrznych | — |
