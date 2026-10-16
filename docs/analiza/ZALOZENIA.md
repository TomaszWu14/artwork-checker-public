# Założenia i pytania do Product Ownera

> [BA] Zgodnie z zasadą: gdy PO nie odpowiada, BA przyjmuje bezpieczne, minimalne założenie i oznacza je
> **do potwierdzenia**. Po odpowiedzi PO założenie staje się decyzją (data, kto) i trafia do ADR lub rejestru ryzyk.

## Pytania z pierwszej serii (2026-10-15)

| ID | Pytanie | Założenie robocze (do potwierdzenia) | Status |
|---|---|---|---|
| Z-01 | **Cel i mierniki.** Czy repo ma być przede wszystkim portfolio pokazującym proces (rekruterzy, audytorzy), czy narzędziem wdrażanym u klienta? Jakie mierniki sukcesu (czas kontroli, % wykrytych błędów, 0 incydentów)? | Oba: portfolio z realną jakością produkcyjną; mierniki z `WIZJA.md` jako propozycja | do potwierdzenia |
| Z-02 | **Użytkownicy i role.** Ile osób i z jakich działów korzysta? Czy role `manager`/`superuser` są potrzebne? Czy admin ma zakładać konta w UI (dziś brak funkcji), czy wystarczy skrypt CLI? Czy 2FA dla admina? | Kilkanaście osób, desktop; role zostają; konta w UI (US-009); 2FA dla admina odroczone | do potwierdzenia |
| Z-03 | **Zakres i relikty.** Które z 55 tras odziedziczonych po DocCompare usuwamy (checklisty dostaw, typy dokumentów, szablony porównań, kreator dostawców, Incoterms, kraje tranzytu, słownik tłumaczeń, scorecard, wersje, duplikaty)? Czy master data materiałów/dostawców zostaje? | Relikty do usunięcia w US-010 **po decyzji**; do tego czasu nie rozwijamy ich; master data zostaje (używane przez mapowanie) | do potwierdzenia |
| Z-04 | **Dane i RODO.** Czy artworki/mastery zawierają informacje poufne (klienci, ceny) lub dane osobowe poza kontami użytkowników? Gdzie hosting (UE)? Czy wysyłanie fragmentów artworków do Claude/Mistral jest akceptowalne (DPA)? | Artworki = dane wewnętrzne (know-how, oznaczenia medyczne), bez danych osobowych; hosting UE; AI/OCR API dozwolone wyłącznie z DPA i bez danych osobowych; do czasu potwierdzenia AI pozostaje opcjonalne (`use_ai` domyślnie off) | do potwierdzenia |
| Z-05 | **Bramki jakości.** Akceptujesz: próg pokrycia 80 % dla logiki domenowej, lint blokujący po US-002, pip-audit blokujący, build+skan obrazu Docker tylko ręcznie/miesięcznie (ciężki obraz ~8 min i kilka GB)? Język commitów EN (Conventional Commits), dokumentacja PL? | Tak dla wszystkich; obraz skanowany ręcznie/miesięcznie w `security.yml` | do potwierdzenia |
| Z-06 | **Sekrety w UI.** Czy funkcja wpisywania klucza Anthropic w panelu admina jest potrzebna (hosting bez dostępu do env)? Jeśli tak — szyfrowanie w bazie kluczem z env; jeśli nie — usunięcie. | Usunięcie (klucz tylko z env) — prostsze i bezpieczniejsze | do potwierdzenia |
| Z-07 | **Zapis kopii modeli 3D na serwerze** (`save-copy`): potrzebne w produkcji? Jakie katalogi docelowe? | Funkcja wyłączona w produkcji do czasu konfiguracji `ARTWORK_COPY_ROOTS` (US-006) | do potwierdzenia |

## Założenia techniczne przyjęte bez pytania (niskie ryzyko)

| ID | Założenie | Uzasadnienie |
|---|---|---|
| T-01 | Dokumentacja PL, kod/commity/nazwy EN, Conventional Commits | sekcja 8 promptu PO; spójność z istniejącym kodem |
| T-02 | Gałęzie: `feature/<US-id>-<nazwa>`, `fix/<US-id>-…`, `security/<US-id>-…`; merge do `main` tylko przez PR | CONTRIBUTING.md |
| T-03 | Poziom ASVS: **L2** (aplikacja wewnętrzna z danymi poufnymi firmy) | `CHECKLISTA_ASVS.md` |
| T-04 | Skany bezpieczeństwa w CI: Bandit ≥ średnie i pip-audit blokują; Semgrep, Trivy i lint doradcze do czasu triage | ADR-0002 |
| T-05 | Nie wprowadzamy Redis/RQ jako twardej zależności (plan w `docs/KOLEJKOWANIE.md`) | CLAUDE.md |
| T-06 | Stare dokumenty (`docs/architektura.md`, `DOKUMENTACJA_IT.md`, `PROCES_*`) zostają nietknięte do decyzji PO (US-016) | zasada „nie nadpisuj bez pytania" |

## Dziennik decyzji PO

| Data | ID | Decyzja | Gdzie zapisano |
|---|---|---|---|
| — | — | (brak — oczekiwanie na odpowiedzi) | — |
