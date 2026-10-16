# Checklista OWASP ASVS 4.0 — poziom L2 (wybrany; założenie T-03)

> [SEC] Status: ✅ spełnione · ⚠️ częściowo · ❌ brak · ➖ nie dotyczy. Odniesienia do kodu i historyjek.
> Pełna weryfikacja L2 wymaga przeglądu każdej z 297 tras — poniżej stan na 2026-10-15 na próbce
> reprezentatywnej (auth, upload, pliki, admin, integracje).

| Rozdział | Wymaganie (skrót) | Status | Dowód / działanie |
|---|---|---|---|
| V1 Architektura | model zagrożeń, klasyfikacja danych, komponenty i granice zaufania | ⚠️ | `THREAT_MODEL.md`, `KLASYFIKACJA_DANYCH.md` v0.1 (ten PR) |
| V1.14 | sekrety poza kodem, konfiguracja przez env | ⚠️ | `.env.example`; klucz AI w DB → US-004 |
| V2.1 Hasła | ≥ 12 znaków, lista haseł słabych, brak limitu górnego < 64 | ⚠️ | min. 8 (`app.py:1685`), max 1000 ✅ → US-005 |
| V2.2 Ogólne | ochrona przed brute-force, generyczne komunikaty | ⚠️ | limit per IP w pamięci → US-005; komunikaty ✅ |
| V2.4 Przechowywanie | hash z solą (scrypt/pbkdf2/argon2) | ✅ | Werkzeug `generate_password_hash` |
| V2.5 Odzyskiwanie | token losowy, jednorazowy, krótki czas, nie w logach | ⚠️ | jawny w DB, 24 h → US-003 |
| V2.8 2FA | MFA dla kont uprzywilejowanych | ❌ | decyzja Z-02 |
| V3.2 Sesja | nowy ID po logowaniu, wygaśnięcie | ✅ | `session.clear()` + `permanent` 8 h |
| V3.4 Cookie | Secure, HttpOnly, SameSite | ✅ | `app.py:147–151` (Secure auto w prod) |
| V3.5 Tokeny API | tokeny losowe, porównanie stałoczasowe, odwoływalne | ✅ | sync token (reset), intake (env), `compare_digest` |
| V4.1 Kontrola dostępu | po stronie serwera, deny-by-default, role | ✅ | `core/security.py`; 3 trasy ze sprawdzeniem ręcznym |
| V4.2 Operacje | IDOR, CSRF | ✅ | kontrola właściciela + testy; `csrf_protect` |
| V4.3 Admin | funkcje admina chronione, bez „ukrytych” endpointów | ⚠️ | `require_role("admin")`; brak testu 403 per rola dla każdej trasy → SEC-007 |
| V5.1 Walidacja | wejście walidowane po stronie serwera (typ, długość, zakres) | ⚠️ | ręcznie; plan Pydantic (`PLAN_REFAKTORU.md` #5) |
| V5.2 Sanityzacja | brak eval/dynamicznego kodu; sanityzacja promptów LLM | ⚠️ | brak `eval`; prompt → US-007 |
| V5.3 Wyjście | kodowanie kontekstowe (HTML/JS/URL), parametryzowany SQL | ⚠️ | Jinja autoescape ✅, SQL ✅; `innerHTML` + CSP → US-008 |
| V6 Kryptografia | losowość z CSPRNG, bez własnych algorytmów | ✅ | `secrets`, `hmac`, `hashlib` (md5 tylko do nazw plików, `usedforsecurity=False`) |
| V7.1 Logi | bez sekretów i tokenów; zdarzenia bezpieczeństwa logowane | ✅ | grep ✅; `audit_log` login/CSRF/reset |
| V7.4 Błędy | brak tracebacków dla klienta, generyczne 500 | ✅ | `@app.errorhandler(500)`, PalViz RD-1 |
| V8.1 Dane | klasyfikacja, retencja, brak danych w cache klienta | ⚠️ | `Cache-Control: no-store` dla zalogowanych ✅; retencja → US-014 |
| V8.3 Dane osobowe | minimalizacja, eksport/usunięcie | ❌ | `RODO.md`, US-014 |
| V9 Komunikacja | TLS, HSTS, brak mixed content | ✅ | HSTS `max-age=31536000; preload` w prod; CDN tylko https |
| V10 Złośliwy kod | brak backdoorów, zależności zweryfikowane, integralność | ⚠️ | pip-audit ✅ (0 CVE); brak locka/hashy → US-011 |
| V11 Logika biznesowa | limity, sekwencje, anty-automatyzacja | ⚠️ | rate limit 30/min ✅; budżet AI ✅; brak limitu intake/sync |
| V12.1 Upload | limit rozmiaru, typ po zawartości, bez wykonania | ⚠️ | 200 MB, magic bytes, `secure_filename` ✅; limit stron ❌ (US-019); przegląd 39 miejsc |
| V12.3 Pliki | brak traversal, brak serwowania spoza katalogu | ✅ | `realpath`/`safe_join`; `save-copy` → US-006 |
| V13 API | JSON, CSRF dla cookie-auth, Bearer dla maszyn, rate limit | ✅ | `X-CSRF-Token`, Bearer, 429 |
| V14.1 Build | pipeline z testami, SAST, SCA, sekretami; obraz non-root | ⚠️ | `ci.yml` (ten PR); `USER` → US-012 |
| V14.2 Zależności | aktualne, inwentaryzowane, bez niepotrzebnych | ⚠️ | 50+ pakietów ML opcjonalnych; Dependabot (ten PR) |
| V14.3 Ujawnianie | brak nagłówka `Server`, debug wyłączony w prod | ✅ | `Server` usuwany; `app.run` tylko lokalnie 127.0.0.1 |
| V14.4 Nagłówki | CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Frame-Options | ⚠️ | wszystkie obecne; CSP z `unsafe-*` → US-008 |
| V14.5 Walidacja żądań | `Content-Type`, `Origin`/`SameSite` | ✅ | `SameSite=Strict`, MIME uploadu |

**Podsumowanie:** 14 ✅ · 15 ⚠️ · 3 ❌ · 0 ➖. Cel: 0 ❌ i ≤ 5 ⚠️ po Sprintach 1–2.
