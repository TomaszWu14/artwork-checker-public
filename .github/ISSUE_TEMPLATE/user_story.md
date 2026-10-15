---
name: "[BA] User story"
about: Historyjka użytkownika z kryteriami akceptacji (Given/When/Then)
title: "US-XXX: <krótka nazwa>"
labels: ["user-story", "BA"]
assignees: []
---

## Historyjka
Jako **<rola>** chcę **<cel>**, aby **<korzyść>**.

## Kontekst / problem
<co dziś nie działa lub czego brakuje; link do `docs/analiza/WYMAGANIA.md` (FR-/NFR-/BR-)>

## Kryteria akceptacji
- [ ] **Given** <stan początkowy> **When** <akcja> **Then** <oczekiwany wynik>
- [ ] Given … When … Then …

## Kryteria bezpieczeństwa ([SEC] uzupełnia w kroku 2)
- [ ] Klasa danych: <publiczne / wewnętrzne / poufne / dane osobowe>
- [ ] Given użytkownik bez roli `<rola>` When wywołuje `<endpoint>` Then 403
- [ ] <zabezpieczenie z mini-STRIDE: `docs/bezpieczenstwo/THREAT_MODEL.md`>

## Wymagania niefunkcjonalne
<wydajność, dostępność, RODO, użyteczność — lub „brak dodatkowych”>

## Priorytet (MoSCoW)
Must / Should / Could / Won't — uzasadnienie: …

## Definition of Ready
- [ ] cel jasny · [ ] kryteria testowalne · [ ] zależności znane · [ ] dane i uprawnienia określone · [ ] otwarte pytania zapisane w `ZALOZENIA.md`

## Powiązania
Ryzyko: R-… · ADR: … · Testy: `tests/test_….py` · Macierz: `docs/analiza/SLEDZENIE.md`
