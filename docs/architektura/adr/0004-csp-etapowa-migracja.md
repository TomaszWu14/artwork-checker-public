# ADR-0004: Etapowa migracja do ścisłej Content-Security-Policy (US-008)

- **Status:** etap 1 zrealizowany (#28); etap 2a (US-022, #33); etap 2b (US-024 — Alpine CSP) **odłożony decyzją PO 2026-10-16**; etapy 3–4 zrealizowane (US-023, decyzja PO 2026-10-17) — z `'unsafe-eval'` do czasu US-024
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
2. **Etap 2a (US-022, Sprint 3):** raport React/Babel → JSX kompilowany przy budowie (`frontend/src` → `static/js`),
   Tailwind Play CDN → CSS budowany z repo, React/Alpine/lucide → przypięte kopie w `static/vendor` (build:
   `npm run build`, CI pilnuje zgodności). CSP bez `unpkg.com`, `cdn.tailwindcss.com`, `cdn.jsdelivr.net`.
   Pomiar przy implementacji: Alpine ~500 dyrektyw w 18 szablonach — przepisanie na `@alpinejs/csp` nie mieści
   się w jednym bezpiecznym PR, więc wydzielone.
   **Etap 2b (US-024):** Alpine → build CSP (wyrażenia z atrybutów do `Alpine.data`), szablon po szablonie;
   po nim zdjęcie `'unsafe-eval'` (to jedyny powód, dla którego zostaje po etapie 2a).
3. **Etap 3 (US-023):** handlery `on*=` → `addEventListener` w plikach `static/js/*.js`; `nonce="{{ csp_nonce() }}"`
   na pozostałych `<script>`; szablon po szablonie, kierując się raportami.
4. **Etap 4:** zamiana Report-Only na egzekwowanie (`script-src 'self' 'nonce-…'`), zdjęcie `'unsafe-inline'` dla skryptów.

### Realizacja etapów 3–4 (US-023, 2026-10-17)
Pomiar przed zmianą: **425** handlerów `on*=` w 24 szablonach (w tym ~100 w znacznikach budowanych w JS przez
`innerHTML`) i **67** skryptów inline bez nonce.
- **Handlery → `data-on-<zdarzenie>`** obsługiwane przez jeden skrypt `static/js/csp_actions.js`. Nasłuch w fazie
  capture na `document` przy pierwszym zdarzeniu podpina `addEventListener` na sam element z atrybutem — działa
  też dla elementów dodanych później przez `innerHTML` i zachowuje semantykę atrybutów `on*=` (`this`, `event`,
  kolejność względem innych nasłuchów, `stopPropagation`, `return false`). Czysta delegacja na `document`
  odwróciłaby kolejność względem nasłuchów kontenerów (np. przeciąganie pól w edytorze profili). Przepisanie
  każdego handlera na osobny `addEventListener` w ~100 miejscach generowanego HTML oznaczałoby przebudowę
  renderowania list.
- **Bez `eval`:** wyrażenie w atrybucie jest parsowane ścisłą gramatyką — sekwencja wywołań `nazwa(arg, …)`
  oraz `event.stopPropagation()/preventDefault()` i `return false`; argumenty to literały JS, `this`, `event`
  i kilka pól (`this.value`, `this.checked`, `this.dataset.X`…). 50 złożonych handlerów (np. `if(…)`, przypisania,
  IIFE) zastąpiły wbudowane akcje (`clickById`, `onKeys`, `onSelf`, `togglePassword`…) lub nazwane funkcje.
- **Biała lista funkcji:** wywołać można tylko funkcje zgłoszone przez `CspActions.allow(…)` w skrypcie z nonce
  (lub wbudowane). Bez niej wstrzyknięty atrybut `data-on-click="setTimeout('…')"` byłby obejściem CSP przy
  zachowanym `'unsafe-eval'`. Testy pilnują: brak `on*=`, nonce na każdym `<script>` inline, akcje tylko z białej
  listy, zgodność z gramatyką, poprawne escapowanie `|tojson` w atrybutach.
- **Egzekwowana polityka:** `script-src 'self' 'nonce-<na odpowiedź>' 'unsafe-eval'` (bez `'unsafe-inline'`).
  Report-Only pozostaje polityką docelową **bez** `'unsafe-eval'` — mierzy, co zostało do US-024 (tylko Alpine).
- **Weryfikacja e2e** (Chromium, polityka egzekwowana, 60 stron jako admin): 0 naruszeń poza
  `/artwork/design-preview` (eksperyment z `static/design/` ładujący unpkg — zepsuty już od #33, poza zakresem);
  wszystkie 812 elementów z akcjami parsują się i wskazują istniejące funkcje.

**Ryzyko szczątkowe:** do czasu US-024 Alpine (standardowy build) wykonuje wyrażenia z atrybutów `x-*` przez
`eval` — wstrzyknięty znacznik z dyrektywą Alpine w obszarze komponentu nadal byłby wykonywalny. Wstrzyknięty
`<script>` i atrybuty `on*=` są już blokowane przez przeglądarkę.

## Konsekwencje
- (+) Brak regresji UI teraz; mierzalny postęp (liczba raportów); ochrona atrybutów przed wstrzyknięciem już dziś.
- (−) Do końca etapu 4 R-05 pozostaje średnie (obniżone przez `esc`); etapy 2–3 to kilka dni pracy na 56 szablonach —
  wymaga decyzji PO o priorytecie.
- (−) `/csp-report` jest publiczny (przeglądarki nie wysyłają CSRF) — ograniczony rozmiarem i limitem; log przycięty,
  bez query stringów.
