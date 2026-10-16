# Procesy — AS-IS i TO-BE

## 1. Kontrola artworku dostawcy

### AS-IS (ręcznie, przed narzędziem)

```mermaid
flowchart LR
    A[Dostawca wysyła artwork PDF] --> B[Specjalista otwiera PDF i master obok siebie]
    B --> C{Porównanie wzrokowe<br/>tekst, kody, daty, wersja}
    C -->|błąd zauważony| D[E-mail do dostawcy z uwagami]
    C -->|nic nie widać| E[Zwolnienie do druku]
    E --> F[Błąd wychodzi na towarze]
    F --> G[Reklamacja / przestój / ryzyko regulacyjne]
```

Problemy: brak powtarzalności, brak śladu decyzji, kody kreskowe sprawdzane „na oko", zmęczenie uwagi
przy 31 tys. masterów i wielu rewizjach.

### TO-BE (z aplikacją)

```mermaid
flowchart TD
    A[Upload: artwork dostawcy + master z biblioteki lub pliku] --> B[Walidacja pliku<br/>magic bytes, rozmiar, hasło]
    B --> C[Ekstrakcja tekstu z pozycjami<br/>PyMuPDF / pdfplumber → kaskada OCR]
    C --> D[Porównanie: tekst, obraz SSIM/ΔE, strefy, pola z profilu]
    D --> E[Walidacja kodów: EAN/GTIN checksum, GS1-128 AI, kod ↔ tekst]
    E --> F{AI włączone?}
    F -->|tak| G[Claude: ocena różnic — wynik DORADCZY]
    F -->|nie| H
    G --> H[Raport: lista różnic + lista kontrolna REF/LOT/EXP/CE]
    H --> I{Decyzja człowieka}
    I -->|zgodne| J[Zapis w historii, eksport PDF/DOCX, webhook]
    I -->|niezgodne| K[Komentarze do pól, raport do dostawcy]
    J & K --> L[Audit log]
```

## 2. Utrzymanie biblioteki masterów

```mermaid
sequenceDiagram
    participant Z as Dysk Z:\ (on-prem)
    participant AG as library_sync.py (agent)
    participant API as /api/library/sync (Bearer token)
    participant DB as Baza (library_files, artwork_index)
    participant M as Manager
    AG->>Z: skan katalogów, checksum, miniatura
    AG->>API: POST meta + thumb (bez pełnego pliku)
    API->>DB: upsert po rel_path, parsowanie nazwy (REF, typ, rewizja)
    M->>DB: potwierdza master / alias / grupę mapowania
    AG->>API: GET /api/library/needed-masters
    API-->>AG: lista potwierdzonych masterów bez pliku
    AG->>API: POST pełny PDF tylko dla potrzebnych
```

## 3. Render 3D i push do PalViz

Dieline PDF → wykrycie paneli (crease lines / szablon wykrojnika) → tekstury → GLB (trimesh) → podgląd
`<model-viewer>` → akceptacja układu przez użytkownika → rejestr renderów → push (Bearer, Idempotency-Key)
do PalViz w wątku tła; bez `PALVIZ_PUSH_URL` push jest wyłączony.

## 4. Proces wytwórczy (zespół BA/DEV/SEC)

Opisany w `CONTRIBUTING.md` (kroki 1–7, Definition of Ready/Done). Ślad: issue → gałąź `feature/<id>` →
PR z checklistami → przegląd SEC → odbiór BA → akceptacja PO → merge → CHANGELOG.
