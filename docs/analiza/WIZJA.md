# Wizja produktu — Artwork Checker (v0.1, do potwierdzenia przez PO)

> [BA] Wersja robocza oparta na README, kodzie i audycie (`docs/AUDYT.md`). Pola oznaczone
> **[do potwierdzenia]** wymagają odpowiedzi PO — pytania w `ZALOZENIA.md`.

## Problem

Dział jakości i zakupów ręcznie porównuje projekty opakowań (artworki PDF) od dostawców z wzorcami
(masterami). Błędy w kodach kreskowych, datach, numerach REF, rewizjach i oznaczeniach regulacyjnych
(CE, LOT, EXP) wychodzą dopiero na gotowym towarze — koszt reklamacji, przestoju i ryzyko regulacyjne
(opakowania medyczne).

## Produkt

Wewnętrzna aplikacja webowa, która:

1. porównuje artwork dostawcy z masterem (tekst z pozycjami, obraz, strefy, pola) i generuje raport różnic
   z listą kontrolną elementów obowiązkowych,
2. waliduje kody kreskowe (EAN/UPC/GTIN, GS1-128) i ich zgodność z tekstem,
3. utrzymuje indeks ~31 tys. masterów z dysku sieciowego (wersje, aliasy, mapowania, potwierdzenia),
4. wizualizuje opakowanie w 3D z wykrojnika i przekazuje rendery do PalViz.

Wynik porównania jest **doradczy** — decyzję podejmuje człowiek (OCR myli 0/O, 1/I; AI jest wsparciem).

## Użytkownicy

| Persona | Rola w aplikacji | Cel |
|---|---|---|
| Specjalista ds. jakości / opakowań | `user` | szybko sprawdzić artwork dostawcy i udokumentować różnice |
| Lider / manager działu | `manager` | utrzymać bibliotekę masterów, profile pól, master data; zatwierdzać rendery |
| Administrator IT | `admin` | konfiguracja, konta, kopie, integracje, koszty AI |
| Agent synchronizacji (on-prem) | token | dostarczać metadane i miniatury z `Z:\` bez wynoszenia plików |
| PalViz / Power Automate / ERP | token / webhook | odbierać rendery, dostarczać PDF, otrzymywać zdarzenia |

Liczba użytkowników: kilkanaście osób, desktop, Chrome **[do potwierdzenia]**.

## Cele i mierniki sukcesu **[do potwierdzenia]**

| Cel | Miernik | Wartość docelowa (propozycja) |
|---|---|---|
| Skrócić kontrolę artworku | mediana czasu od uploadu do decyzji | < 5 min (dziś: ręcznie 20–40 min) |
| Wyłapać błędy przed drukiem | % błędów kodów/dat wykrytych przed zwolnieniem do druku | ≥ 95 % |
| Zero regresji bezpieczeństwa | ustalenia ≥ wysokie w skanach CI | 0 otwartych |
| Koszt AI pod kontrolą | miesięczny koszt API vs budżet | ≤ budżet (`/api/ai/budget`) |
| Dojrzały proces (portfolio) | każdy PR z przeglądem SEC i odbiorem BA | 100 % PR-ów |

## Zakres

**W zakresie:** porównanie artworków, kody GS1, biblioteka/indeks masterów, 3D/PalViz, master data
materiałów i dostawców w zakresie potrzebnym do mapowania artworków, administracja i integracje
(intake, webhooki, sync).

**Poza zakresem (relikty do usunięcia lub świadomego pozostawienia — Z-03):** porównywarka dokumentów
handlowych, transport/kolejka, portale zewnętrzne, Incoterms, kraje tranzytu, słownik tłumaczeń,
checklisty dostaw, scorecard dostawców.

## Ograniczenia

- Hosting w UE (Render Frankfurt / Coolify) **[do potwierdzenia]**; dane artworków nie opuszczają
  infrastruktury poza fragmentami wysyłanymi do API OCR/AI (Mistral, Anthropic) — wymaga zgody PO (Z-04).
- Jeden developer; repozytorium publiczne jako portfolio — żadnych danych produkcyjnych w repo.
- Ciężkie modele ML opcjonalne; produkcja musi działać na 8 GB RAM.

## Status

Aplikacja działa (wersja `1.0.0-artwork`); proces zespołowy (BA/DEV/SEC) wdrażany od 2026-10-15.
