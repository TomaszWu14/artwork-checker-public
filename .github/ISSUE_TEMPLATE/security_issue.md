---
name: "[SEC] Security issue (bez szczegółów exploitu)"
about: Ustalenie bezpieczeństwa do obsłużenia w procesie — szczegóły techniczne prywatnym kanałem (SECURITY.md)
title: "security: <ogólny opis bez PoC>"
labels: ["security", "SEC"]
assignees: []
---

> ⚠️ **To jest publiczne repozytorium.** Nie wklejaj tu kroków exploitacji, payloadów ani danych z produkcji.
> Podatności zgłaszaj prywatnie wg `SECURITY.md`; ten szablon służy do śledzenia prac po zgłoszeniu.

## Klasa ustalenia
- Kategoria (OWASP Top 10 / ASVS): …
- Waga: 🔴 krytyczna / 🟠 wysoka / 🟡 średnia / ⚪ niska — uzasadnienie (wpływ × prawdopodobieństwo)
- Źródło: przegląd SEC / skaner (Bandit / Semgrep / pip-audit / gitleaks / Trivy) / zgłoszenie zewnętrzne

## Opis ogólny (bezpieczny do publikacji)
<jaki mechanizm jest słaby i jaki ma to skutek — bez instrukcji „jak wykorzystać”>

## Zabezpieczenie docelowe
<co ma być spełnione; kryterium Given/When/Then; które SEC-xxx z `THREAT_MODEL.md`>

## Rejestr ryzyk
R-… w `docs/bezpieczenstwo/RYZYKA.md`: mitygować / akceptować (decyzja PO, data przeglądu)

## Weryfikacja
- [ ] test regresji w `tests/` · [ ] skan w CI bez nowych ustaleń · [ ] przegląd SEC ✅ w PR · [ ] wpis w `CHANGELOG.md` (sekcja *Security*)
