# ADR-0004: Etapowa migracja do ścisłej Content-Security-Policy (US-008)

- **Status:** zaakceptowany etap 1 (2026-10-16); etapy 2–4 — **decyzja PO** (koszt/zakres)
- **Role:** [SEC] + [DEV]

## Kontekst
CSP zawiera `'unsafe-inline'` i `'unsafe-eval'`, więc każdy XSS w szablonie jest wykonywalny (R-05).
Pomiar 2026-10-16: **65** bloków `<script>` inline, **407** handlerów `on*=` w 56 szablonach, Alpine.js
(standardowa wersja wymaga `eval`), React + Babel w przeglądarce (`artwork_report.html`, wymaga `eval`),
Tailwind Play CDN. Dodanie nonce przy zachowaniu `'unsafe-inline'` nic nie daje (przeglądarki wtedy
**ignorują** `'unsafe-inline'`, więc 407 handlerów przestałoby działać) — migracja musi iść etapami.

## Opcje
1. Natychmiast ścisła CSP — psuje większość UI; odrzucone.
2. **Etapy z CSP Report-Only** — ścisła polityka raportuje naruszenia, egzekwowana zostaje obecna; szablony
   migrowane strona po stronie, egzekwowanie po wyzerowaniu raportów.
3. Zostawić jak jest — R-05 otwarte bezterminowo.

## Decyzja
Opcja 2:
1. **Etap 1 (US-008, ten PR):** jedno kanoniczne `esc()` we wszystkich szablonach (escapuje `& < > " '`;
   wcześniej m.in. `artwork_3d_batch` nie escapował `"` w atrybutach `title`), test regresji;
   egzekwowane `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`; `X-XSS-Protection: 0`;
   ścisła polityka z nonce w `Content-Security-Policy-Report-Only` + `/csp-report` (limit 60/min, 16 KB).
2. **Etap 2 (US-022):** Alpine → build CSP (`@alpinejs/csp`, wymaga przeniesienia wyrażeń z atrybutów do
   `Alpine.data`), raport React/Babel → prekompilacja do statycznego JS, Tailwind Play CDN → zbudowany CSS;
   zdjęcie `'unsafe-eval'`.
3. **Etap 3 (US-023):** handlery `on*=` → `addEventListener` w plikach `static/js/*.js`; `nonce="{{ csp_nonce() }}"`
   na pozostałych `<script>`; szablon po szablonie, kierując się raportami.
4. **Etap 4:** zamiana Report-Only na egzekwowanie (`script-src 'self' 'nonce-…'`), zdjęcie `'unsafe-inline'` dla skryptów.

## Konsekwencje
- (+) Brak regresji UI teraz; mierzalny postęp (liczba raportów); ochrona atrybutów przed wstrzyknięciem już dziś.
- (−) Do końca etapu 4 R-05 pozostaje średnie (obniżone przez `esc`); etapy 2–3 to kilka dni pracy na 56 szablonach —
  wymaga decyzji PO o priorytecie.
- (−) `/csp-report` jest publiczny (przeglądarki nie wysyłają CSRF) — ograniczony rozmiarem i limitem; log przycięty,
  bez query stringów.
