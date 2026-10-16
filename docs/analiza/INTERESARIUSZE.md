# Interesariusze

| Interesariusz | Rola | Interes / oczekiwanie | Wpływ | Kanał |
|---|---|---|---|---|
| Product Owner (Tomasz) | decyzje o zakresie, priorytetach, ryzyku, wydaniach | dojrzały proces widoczny w repo; działające narzędzie | wysoki | issues, PR, `ZALOZENIA.md` |
| Specjaliści ds. jakości / opakowań | użytkownicy końcowi (`user`) | szybkie, czytelne porównanie; mało fałszywych alarmów | wysoki | zgłoszenia błędów (szablon `bug`) |
| Manager działu | właściciel biblioteki masterów i master data | aktualny indeks, poprawne mapowania REF, kontrola potwierdzeń | wysoki | jak wyżej |
| Administrator IT / hosting | utrzymanie, kopie, sekrety, konta | prosty runbook, bezpieczna konfiguracja, niskie koszty | średni | `docs/operacje/RUNBOOK.md` |
| Dostawcy opakowań | pośredni (ich artworki są sprawdzane) | jasne, powtarzalne kryteria odrzucenia | niski | raport różnic |
| Dział regulacyjny / jakość (medyczne) | wymagania oznakowania (UDI, GS1, CE) | zgodność listy kontrolnej z regulacjami | średni | reguły biznesowe (`WYMAGANIA.md` BR-*) |
| PalViz (system zewnętrzny) | odbiorca renderów 3D | stabilny kontrakt API (idempotency) | średni | `palviz_push.py` |
| Agent synchronizacji `Z:\` | integracja on-prem | token, brak wynoszenia plików poza miniatury i potwierdzone mastery | średni | `library_sync.py` |
| Dostawcy API (Anthropic, Mistral, Resend, Sentry) | procesorzy danych | — | niski | umowy DPA (RODO.md) |
| Rekruter / audytor / nowy członek zespołu | czytelnicy repo | zrozumiały proces, dokumentacja, ślad decyzji | średni | README, `docs/`, PR-y |
