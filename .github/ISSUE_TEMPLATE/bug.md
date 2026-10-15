---
name: "Bug"
about: Błąd w działaniu aplikacji
title: "bug: <krótki opis>"
labels: ["bug"]
assignees: []
---

## Co się dzieje
<opis błędu; komunikat widoczny dla użytkownika (bez danych produkcyjnych i bez sekretów)>

## Kroki odtworzenia
1. …
2. …

## Oczekiwane zachowanie
…

## Środowisko
- wersja / commit: `constants.APP_VERSION` = … / `git rev-parse --short HEAD` = …
- baza: SQLite / PostgreSQL · przeglądarka: … · rola użytkownika: user / manager / admin

## Logi / zrzuty ekranu
<fragment `logs/app.log` bez tokenów, e-maili i IP; zrzut bez danych poufnych>

## Wpływ
Krytyczny (blokuje pracę) / Wysoki / Średni / Niski · dotyczy bezpieczeństwa? → użyj szablonu *Security issue*

## Powiązania
FR-… · US-… · test regresji: `tests/test_….py`
