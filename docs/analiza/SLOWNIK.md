# Słownik pojęć

| Termin | Definicja |
|---|---|
| **Artwork** | Projekt graficzny opakowania/etykiety/ulotki (PDF, czasem obraz) — wersja dostawcy („fabryczna") lub wzorcowa |
| **Master (wzorzec)** | Zatwierdzony artwork referencyjny przechowywany w bibliotece (`Z:\`), do którego porównuje się wersję dostawcy |
| **Rewizja** | Numer wersji mastera w nazwie pliku (cyfra, liczba rzymska lub litera); wyższa = nowsza (`artwork_naming.py`) |
| **REF** | Kod referencyjny produktu/materiału (klucz łączący artwork, master data i MARM) |
| **Alias REF** | Alternatywny kod wskazujący na ten sam materiał (tabela `artwork_alias`) |
| **Grupa mapowania** | Zbiór REF-ów traktowanych jako jeden produkt przy wyszukiwaniu masterów |
| **Potwierdzony master** | Master oznaczony przez managera jako obowiązujący dla REF (`artwork_confirmed`) |
| **Profil pól** | Szablon pozycji pól (EAN, REF, LOT, EXP…) na artworku, używany do porównania polowego (`artwork_profiles`) |
| **Strefa** | Prostokąt zaznaczony przez użytkownika do porównania lokalnego (`artwork_zone_comparator.py`) |
| **Lista kontrolna** | Zestaw elementów obowiązkowych na opakowaniu (REF, LOT, EXP, CE, EAN…) oceniany w raporcie |
| **EAN-13 / EAN-8 / UPC-A / GTIN-14** | Kody GS1 z cyfrą kontrolną; GTIN = ogólna nazwa identyfikatora handlowego |
| **GS1-128** | Kod liniowy z Application Identifiers: (01) GTIN, (10) LOT, (17) data ważności, (11) data produkcji; FNC1 rozdziela pola zmiennej długości |
| **AI (Application Identifier)** | Prefiks pola w GS1-128 — nie mylić z „AI" w sensie sztucznej inteligencji |
| **OCR / kaskada OCR** | Rozpoznawanie tekstu z obrazu: PyMuPDF/pdfplumber → RapidOCR → Tesseract → (opcjonalnie) Mistral/Claude Vision |
| **ΔE** | Różnica koloru w przestrzeni Lab; progi 7,0 (tekst) i 18,0 (grafika) |
| **SSIM** | Miara podobieństwa strukturalnego obrazów używana do map różnic |
| **Dieline (wykrojnik)** | Rysunek siatki opakowania z liniami cięcia i bigowania; źródło geometrii 3D |
| **GLB** | Binarny format glTF modelu 3D; podgląd przez `<model-viewer>` |
| **PalViz** | Zewnętrzny system (Django) wizualizacji palet/opakowań; odbiorca renderów (push z Idempotency-Key) |
| **MARM** | Dane materiałowe (SAP) powiązane z REF — wymiary, jednostki, poziomy opakowań |
| **Poziom opakowania** | SZT (sztuka), OP (opakowanie), OPZ (zbiorcze), KAR (karton), PAZ/PPA (paleta) — każdy z własnym EAN |
| **UOM** | Jednostka miary i przeliczniki między poziomami (`uom.py`) |
| **Agent synchronizacji** | Skrypt `library_sync.py` uruchamiany on-prem, wysyła metadane/miniatury do `/api/library/sync` |
| **Intake** | Endpoint przyjmujący PDF z Power Automate (`/api/intake/artwork`) |
| **Rejestr renderów** | Tabela `artwork_render_registry`: wariant (dieline/marm/photo), hash źródła, status pusha |
| **Rola** | `user` < `manager` < `superuser` < `admin` (`constants.ROLE_LEVEL`) |
| **Audit log** | Tabela `audit_log`: zdarzenie, użytkownik, IP, szczegóły, czas |
