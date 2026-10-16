# RODO — przetwarzanie danych osobowych (wersja 0.1, do potwierdzenia)

> [SEC] Aplikacja przetwarza dane osobowe **wyłącznie pracowników/użytkowników** (konta, audyt).
> Artworki, mastery i master data nie zawierają danych osobowych (założenie Z-04 — do potwierdzenia).

## Administrator i role
- **Administrator danych:** organizacja wdrażająca (ACME — nazwa fikcyjna w portfolio); kontakt: PO.
- **Procesorzy:** dostawca hostingu (UE), Resend (e-mail), opcjonalnie Sentry, Anthropic, Mistral
  (fragmenty artworków — nie dane osobowe). Wymagane umowy powierzenia (DPA) — **status: do potwierdzenia**.

## Rejestr czynności (skrót)

| Czynność | Kategorie danych | Osoby | Podstawa (art. 6 ust. 1) | Retencja | Odbiorcy |
|---|---|---|---|---|---|
| Uwierzytelnianie i konta | nazwa, e-mail, dział, język, hash hasła, ostatnie logowanie | pracownicy | b) umowa / f) uzasadniony interes (dostęp do narzędzia) | okres zatrudnienia + 30 dni | hosting |
| Reset hasła | e-mail, token | pracownicy | jak wyżej | token 1 h (US-003) | Resend |
| Dziennik audytu | nazwa, IP, akcja, czas | pracownicy | f) bezpieczeństwo systemu | 12 miesięcy (US-014) | hosting |
| Rozliczanie kosztów AI | user_id, model, koszt | pracownicy | f) kontrola kosztów | 12 miesięcy | hosting |
| Komentarze/porównania | autorstwo | pracownicy | f) | jak porównania (do usunięcia przez właściciela) | hosting |
| Monitoring błędów | IP, ścieżka, stack | pracownicy | f) | wg Sentry (ustawić 30 dni, `send_default_pii=False`) | Sentry |

## Prawa osób — realizacja
| Prawo | Jak | Status |
|---|---|---|
| Dostęp / przenoszenie | eksport JSON danych konta (profil, audyt, porównania) | ❌ US-014 |
| Sprostowanie | profil (`/api/profile/update`) | ✅ |
| Usunięcie | dezaktywacja + anonimizacja po retencji (`username` → `deleted-<id>`, e-mail usunięty, audyt zachowany bez nazwy) | ❌ US-014 |
| Ograniczenie / sprzeciw | dezaktywacja konta | ⚠️ ręcznie w DB (US-009) |

## Minimalizacja i bezpieczeństwo
- Zbieramy tylko pola potrzebne do logowania i audytu; brak danych szczególnych kategorii.
- Hasła hashowane; sekrety w env; HTTPS/HSTS; kopie bazy na szyfrowanym wolumenie — **do potwierdzenia** (R-10).
- Do AI/OCR nie wysyłamy danych osobowych; wysyłka artworków wymaga decyzji PO (Z-04).

## Incydent (naruszenie ochrony danych)
Procedura w `docs/operacje/RUNBOOK.md` § Incydenty; ocena ryzyka dla osób i ewentualne zgłoszenie do UODO
w 72 h należy do administratora danych (PO).
