# Macierz śledzenia: wymaganie → historyjka → test → PR

> [BA] Aktualizowana przy odbiorze każdej historyjki (krok 6 procesu). Testy = pliki w `tests/`.
> „—" oznacza brak; to zarazem lista luk w pokryciu wymagań testami.

| Wymaganie | Historyjka | Test(y) | PR | Status |
|---|---|---|---|---|
| FR-001 logowanie | — (istniejące) | `test_integration.py`, `test_integration_api.py`, `conftest.py::login` | — | ✅ |
| FR-002 reset hasła | US-003 | `test_us003_reset_token_hash.py` | #19 | ✅ |
| FR-003 porównanie pary | — | `test_artwork_pdf.py`, `test_artwork_table_diff.py`, `test_text_layer.py` | — | ✅ (wąsko) |
| FR-004 raport różnic | — | `test_artwork_ocr_model.py`, `test_business_logic.py` | — | ✅ |
| FR-005 lista kontrolna | #2 (merged) | `test_checklist_ean_checksum.py` | #2 | ✅ |
| FR-006 kody GS1 | — | `test_barcode_validator.py`, `test_gs1_gtin.py` | — | ✅ |
| FR-007 strefy | — | — | — | ❌ |
| FR-008 batch | — | `test_jobs_queue.py` (kolejka), brak testu parowania | — | ⚠️ |
| FR-009 eksport | — | — | — | ❌ |
| FR-010 historia / IDOR | #3 Sprint 1 (historyczny) | `test_artwork_idor.py`, `test_artwork_3d_idor.py` | — | ✅ |
| FR-011 synchronizacja biblioteki | — | `test_library_sync_skip.py`, `test_upload_validation.py` | — | ✅ |
| FR-012 nazewnictwo i rewizje | spec 2026-09-02 | `test_artwork_naming.py`, `test_artwork_search_rank.py` | — | ✅ |
| FR-013 aliasy / mapowania / braki | — | `test_artwork_alias.py`, `test_artwork_manage.py`, `test_manage_pages.py`, `test_coverage_view.py` | — | ✅ |
| FR-014 karta artworku | spec 2026-09-03 | `test_artwork_card.py`, `test_artwork_marm_link.py`, `test_marm_suggest.py` | — | ✅ |
| FR-015 profile pól | — | `test_template_match.py`, `test_template_links.py` | — | ⚠️ |
| FR-016 model 3D | — | `test_artwork_3d*.py` (10 plików) | — | ✅ |
| FR-017 rejestr renderów / PalViz | — | `test_render_registry.py`, `test_palviz_push.py`, `test_artwork_palviz.py`, `test_palviz_auth.py` | — | ✅ |
| FR-018 master data | — | `test_material_master.py`, `test_material_uom.py`, `test_uom.py`, `test_supplier_master.py`, `test_supplier_lookup.py`, `test_pkg_level_seed.py` | — | ✅ |
| FR-019 intake | — | — | — | ❌ |
| FR-020 webhooki | — | — (SSRF guard bez testu) | — | ❌ |
| FR-021 budżet AI | — | `test_ai_hybrid.py`, `test_ai_json.py` | — | ⚠️ |
| FR-022 zarządzanie kontami (tworzenie z linkiem, rola, dezaktywacja, ochrona ostatniego admina) | US-009 | `test_us009_user_management.py` | #27 | ✅ |
| NFR-004 SQLite/PostgreSQL | — | `test_escape_like.py`, `test_ensure_memo.py`, `test_app_boots.py` | — | ✅ (tylko SQLite w CI) |
| NFR-008 bramki CI | US-000 | `.github/workflows/ci.yml` | #4 | ✅ |
| SEC-002 tokeny resetu | US-003 | `test_us003_reset_token_hash.py` | #19 | ✅ |
| SEC-003 sekrety z env | US-004 | `test_us004_api_key_env_only.py` | #20 | ✅ |
| SEC-001 limity logowania + blokada konta + polityka haseł | US-005 | `test_us005_login_hardening.py`, `test_integration_api.py::test_login_rate_limit_blocks_after_max_failures` | #21 | ✅ |
| SEC-004 prompt hardening (reguła systemowa, bloki <document>, wykrywanie injection, AI nie łagodzi werdyktu) | US-007 | `test_us007_prompt_hardening.py` | #24 | ✅ |
| SEC-006 pliki fail-closed (kopia 3D tylko do ARTWORK_COPY_ROOTS, realpath) | US-006 | `test_artwork_3d_save_copy.py` | #23 | ✅ |
| SEC-005 CSP (etap 1: report-only + jedno `esc`) | US-008 | `test_us008_csp_phase1.py` | #28 | ⚠️ (etap 1 z 4) |
| SEC-001 / SEC-007 — wylogowanie tylko POST+CSRF; ręczne kontrole sesji API odrzucają konta dezaktywowane | US-017 | `test_us017_logout_post.py` | #30 | ✅ |
| NFR / R-13 — limity renderowania PDF (strony, piksele przed renderem, DPI z env) | US-019 | `test_us019_render_limits.py` | #31 | ✅ |
| SEC-005 / SEC-008 — CSP etap 2a: bez CDN i Babel w przeglądarce, przypięte biblioteki w repo | US-022 | `test_us022_no_cdn.py`, job CI `frontend` | #33 | ✅ (etap 2a z 4) |
| SEC-007 403 per rola | US-009 i każda nowa trasa | `test_palviz_auth.py`, `test_artwork_idor.py` (wybrane) | — | ⚠️ |
| FR-011 / SEC-006 — import mastera ze ścieżki serwera (resolver fail-closed) | US-001 | `test_us001_master_path_resolver.py` | #17 | ✅ |
| NFR-008 — lint blokujący w CI (0 błędów ruff) | US-002 | `ruff check .` w `ci.yml` (krok blokujący) + `pytest` | #22 | ✅ |
| SEC-003 / R-09 — placeholdery `.env` odrzucane w produkcji | US-018 | `test_us018_env_placeholders.py` | #18 | ✅ |
| SEC-009 kontener non-root + HEALTHCHECK, Trivy misconfig blokujący | US-012 | `ci.yml` → job Trivy (DS-0002) | #25 | ✅ |
| SEC-008 lock obrazu ML (hashe, torch CPU, bez CUDA, instalowalność, regeneracja w CI) | US-021 | `ml-lock.yml` | chore/US-021 | 🔧 |
| SEC-008 zależności (lock z hashami, pip-audit na locku, Dependabot) | US-011 | `ci.yml` → job pip-audit (`--require-hashes`) | #26 | ✅ |
