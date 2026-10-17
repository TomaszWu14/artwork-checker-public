# API — inwentaryzacja tras (stan: 2026-10-15)

> [DEV] Wygenerowano skryptem z dekoratorów `@app.route` / `@bp.route` (app.py + blueprints/).
> Kolumna **Dostęp**: `zalogowany` = `@login_required`; `rola≥X` = `@require_role("X")`
> (hierarchia `user < manager < superuser < admin`); wpisy bez dekoratora opisują
> kontrolę wykonywaną ręcznie w ciele funkcji. **CSRF** = `@csrf_protect` (token z
> `<meta name="csrf-token">` w nagłówku `X-CSRF-Token` lub polu `_csrf_token`).
>
> Obszar „Relikty DocCompare" to trasy odziedziczone po systemie-matce (dokumenty
> handlowe, Incoterms, kraje tranzytu, słownik tłumaczeń, dostawcy/szablony porównań).
> Decyzja o ich losie: patrz `docs/analiza/ZALOZENIA.md` (Z-03) i backlog US-010.

## Konwencje

- Odpowiedzi API: JSON; błędy jako `{"error": "..."}` z kodem HTTP (400/401/403/404/409/413/429/500).
- Uwierzytelnianie UI: sesja (cookie `HttpOnly`, `SameSite=Strict`, `Secure` w produkcji).
- Uwierzytelnianie maszynowe: `Authorization: Bearer <token>` — token synchronizacji biblioteki
  (generowany w aplikacji, tabela `settings`) oraz `INTAKE_TOKEN` (env) dla `/api/intake/artwork`.
- Limity: `MAX_CONTENT_LENGTH` = 200 MB; limit wywołań ciężkich endpointów 30/min/użytkownika
  (tabela `api_rate_events`); logowanie 5 prób / 15 min / IP.
- Zadania w tle: `/api/artwork/compare-progress/<pid>`, `/api/artwork/3d/status/<jid>`,
  `/api/artwork/batch/status/<id>` — polling stanu z tabel `async_jobs` / `artwork_batch_jobs`.

## Podsumowanie

| Obszar | Liczba tras |
|---|---|
| Porównanie artworków | 60 |
| Biblioteka / indeks masterów | 57 |
| Relikty DocCompare (do decyzji) | 52 |
| 3D / PalViz | 39 |
| Master data (materiały / dostawcy) | 35 |
| Admin / AI / integracje | 29 |
| Wspólne (historia, powiadomienia, pomoc) | 16 |
| Auth / profil | 9 |
| **Razem** | **297** |


### Porównanie artworków

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/artwork` | GET | zalogowany | — | `app.py:3797` |
| `/artwork/history` | GET | zalogowany | — | `app.py:3818` |
| `/artwork/kpi` | GET | zalogowany | — | `app.py:3903` |
| `/artwork/design-preview` | GET | zalogowany | — | `app.py:3985` |
| `/artwork/design-preview/<path:filename>` | GET | zalogowany | — | `app.py:3994` |
| `/artwork/admin` | GET | zalogowany | — | `app.py:4007` |
| `/api/artwork/preview-crops` | POST | zalogowany | tak | `app.py:4060` |
| `/api/artwork/split-compare` | POST | zalogowany | tak | `app.py:4246` |
| `/api/artwork/compare-progress/<pid>` | GET | zalogowany | — | `app.py:4508` |
| `/api/artwork/compare` | POST | zalogowany | tak | `app.py:4542` |
| `/api/artwork/pdf-page-count` | POST | zalogowany | tak | `app.py:4681` |
| `/api/artwork/report/<int:cid>` | GET | zalogowany | — | `app.py:5473` |
| `/api/artwork/report/<int:cid>/field-comment` | POST | zalogowany | tak | `app.py:5511` |
| `/api/artwork/report/<int:cid>/visibility` | POST | zalogowany | tak | `app.py:5551` |
| `/api/artwork/page/<cache_id>/<int:page_idx>` | GET | zalogowany | — | `app.py:5571` |
| `/api/artwork/pdf-pages` | POST | zalogowany | tak | `app.py:5583` |
| `/api/artwork/history` | GET | zalogowany | — | `app.py:5644` |
| `/api/artwork/compare-multi` | POST | zalogowany | tak | `app.py:5675` |
| `/artwork/report` | GET | zalogowany | — | `app.py:5797` |
| `/artwork/report/export-html` | GET | zalogowany | — | `app.py:5857` |
| `/artwork/report/export-docx` | GET | zalogowany | — | `app.py:5880` |
| `/artwork/report/export-pdf` | GET | zalogowany | — | `app.py:5903` |
| `/artwork/batch` | GET | zalogowany | — | `app.py:5929` |
| `/api/artwork/batch/pair` | POST | zalogowany | tak | `app.py:5936` |
| `/api/artwork/batch/start` | POST | zalogowany | tak | `app.py:6089` |
| `/api/artwork/batch/status/<int:job_id>` | GET | zalogowany | — | `app.py:6136` |
| `/api/artwork/batch/cancel/<int:job_id>` | POST | zalogowany | tak | `app.py:6171` |
| `/api/artwork/batch/run` | POST | zalogowany | tak | `app.py:6196` |
| `/api/artwork/batch/zip` | POST | zalogowany | tak | `app.py:6241` |
| `/artwork/zone-select` | GET | zalogowany | — | `app.py:6288` |
| `/api/artwork/zone-compare` | POST | zalogowany | tak | `app.py:6318` |
| `/api/artwork/field-queue/init` | POST | zalogowany | tak | `app.py:6351` |
| `/api/artwork/field-queue/compare` | POST | zalogowany | tak | `app.py:6526` |
| `/api/artwork/field-queue/<queue_id>` | DELETE | zalogowany | tak | `app.py:6568` |
| `/api/artwork/field-queue/finalize` | POST | zalogowany | tak | `app.py:6578` |
| `/api/artwork/zone-templates` | GET,DELETE | zalogowany | tak | `app.py:6620` |
| `/artwork/profiles` | GET | rola≥manager | — | `app.py:8873` |
| `/api/artwork/profiles` | GET | zalogowany | — | `app.py:9413` |
| `/api/artwork/profiles/<int:pid>/canvas` | GET | rola≥manager | — | `app.py:9444` |
| `/api/artwork/profiles/<int:pid>/thumb` | GET | zalogowany | — | `app.py:9566` |
| `/api/artwork/profiles/<int:pid>/move` | POST | rola≥manager | tak | `app.py:9586` |
| `/api/artwork/profiles/<int:pid>` | GET | zalogowany | — | `app.py:9604` |
| `/api/artwork/profiles` | POST | rola≥manager | tak | `app.py:9623` |
| `/api/artwork/profiles/import-csv` | POST | rola≥manager | tak | `app.py:9663` |
| `/api/artwork/profiles/<int:pid>` | PUT | rola≥manager | tak | `app.py:9728` |
| `/api/artwork/profiles/<int:pid>/history` | GET | rola≥manager | — | `app.py:9787` |
| `/api/artwork/profiles/<int:pid>/history/<int:hid>` | GET | rola≥manager | — | `app.py:9803` |
| `/api/artwork/profiles/ai-detect` | POST | rola≥manager | tak | `app.py:9830` |
| `/api/artwork/profiles/ai-detect-image` | POST | rola≥manager | tak | `app.py:9954` |
| `/api/artwork/profiles/<int:pid>` | DELETE | rola≥manager | tak | `app.py:10048` |
| `/api/artwork/profiles/<int:pid>/duplicate` | POST | rola≥manager | tak | `app.py:10062` |
| `/api/artwork/field-dict` | GET | rola≥manager | — | `app.py:10260` |
| `/api/artwork/field-dict` | POST | rola≥manager | tak | `app.py:10296` |
| `/api/artwork/field-dict/<int:fid>` | PUT | rola≥manager | tak | `app.py:10346` |
| `/api/artwork/field-dict/<int:fid>` | DELETE | rola≥manager | tak | `app.py:10394` |
| `/api/artwork/field-dict/set-rotation` | POST | zalogowany | tak | `app.py:10407` |
| `/api/artwork/field-feedback` | POST | rola≥user | tak | `app.py:10478` |
| `/api/artwork/field-stats` | GET | rola≥manager | — | `app.py:10513` |
| `/api/artwork/field-stats/reset/<field_name>` | DELETE | rola≥manager | tak | `app.py:10556` |
| `/api/artwork/profiles/to-map` | POST | rola≥manager | tak | `app.py:11280` |

### Biblioteka / indeks masterów

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/artwork/library` | GET | zalogowany | — | `app.py:3806` |
| `/library/download-agent` | GET | rola≥manager | — | `app.py:7503` |
| `/library` | GET | rola≥manager | — | `app.py:7515` |
| `/api/library/sync` | POST | token Bearer (sync) | — | `app.py:7605` |
| `/api/library/needed-masters` | GET | token Bearer (sync) | — | `app.py:7728` |
| `/api/library/browse` | GET | zalogowany | — | `app.py:7781` |
| `/api/library/search` | GET | sesja lub token (ręcznie) | — | `app.py:7884` |
| `/api/library/file/<int:fid>` | GET | zalogowany | — | `app.py:7938` |
| `/api/library/file/<int:fid>/thumb` | GET | zalogowany | — | `app.py:7965` |
| `/api/library/file/<int:fid>/glb` | GET | zalogowany | — | `app.py:8173` |
| `/api/library/file/<int:fid>/use` | POST | zalogowany | tak | `app.py:8528` |
| `/api/library/token-reset` | POST | rola≥admin | tak | `app.py:8575` |
| `/api/library/stats` | GET | rola≥manager | — | `app.py:8595` |
| `/api/artwork/masters/upload` | POST | rola≥manager | tak | `app.py:9261` |
| `/api/artwork/masters/download/<int:pid>` | GET | rola≥manager | — | `app.py:9515` |
| `/api/artwork/masters/storage-info` | GET | rola≥manager | — | `app.py:9539` |
| `/api/artwork/profiles/<int:pid>/master` | POST | rola≥manager | tak | `app.py:10202` |
| `/suppliers/master` | GET | zalogowany | — | `app.py:10863` |
| `/api/sup-master` | GET | zalogowany | — | `app.py:10870` |
| `/api/sup-master/<path:code>` | GET | zalogowany | — | `app.py:10882` |
| `/api/sup-master/<path:code>/contact` | PATCH | rola≥manager | tak | `app.py:10908` |
| `/api/sup-master/import` | POST | rola≥manager | tak | `app.py:10934` |
| `/api/artwork/index/sync` | POST | rola≥manager | tak | `app.py:11105` |
| `/api/artwork/index/status` | GET | zalogowany | — | `app.py:11125` |
| `/api/artwork/master-files/wanted` | GET | rola≥manager | — | `app.py:11137` |
| `/api/artwork/master-files/upload` | POST | rola≥manager | tak | `app.py:11150` |
| `/api/artwork/master-file/view` | GET | zalogowany | — | `app.py:11196` |
| `/api/artwork/master-files/from-path` | POST | rola≥manager | tak | `app.py:11232` |
| `/api/artwork/index/import` | POST | rola≥manager | tak | `app.py:11310` |
| `/artwork/index` | GET | zalogowany | — | `app.py:11371` |
| `/artwork/card/<ref>` | GET | zalogowany | — | `app.py:11378` |
| `/artwork/manage` | GET | rola≥manager | — | `app.py:11396` |
| `/api/artwork/manage/kpi` | GET | rola≥manager | — | `app.py:11405` |
| `/artwork/manage/unbound` | GET | rola≥manager | — | `app.py:11418` |
| `/api/artwork/manage/unbound` | GET | rola≥manager | — | `app.py:11425` |
| `/api/artwork/manage/suggest` | GET | rola≥manager | — | `app.py:11439` |
| `/api/artwork/manage/bind` | POST | rola≥manager | tak | `app.py:11455` |
| `/artwork/manage/gaps` | GET | rola≥manager | — | `app.py:11478` |
| `/api/artwork/manage/gaps` | GET | rola≥manager | — | `app.py:11485` |
| `/api/artwork/manage/duplicates` | GET | rola≥manager | — | `app.py:11498` |
| `/api/artwork/manage/file-status` | POST | rola≥manager | tak | `app.py:11511` |
| `/api/artwork/index/lookup` | GET | zalogowany | — | `app.py:11533` |
| `/api/artwork/index/suggest` | POST | zalogowany | tak | `app.py:11550` |
| `/api/artwork/index/stats` | GET | zalogowany | — | `app.py:11570` |
| `/api/artwork/index/browse` | GET | zalogowany | — | `app.py:11586` |
| `/artwork/aliases` | GET | zalogowany | — | `app.py:11610` |
| `/artwork/revisions` | GET | zalogowany | — | `app.py:11617` |
| `/api/artwork/alias` | GET,POST | zalogowany | tak | `app.py:11624` |
| `/api/artwork/alias/<int:aid>` | DELETE | rola≥manager | tak | `app.py:11650` |
| `/api/artwork/alias/suggest` | GET | zalogowany | — | `app.py:11663` |
| `/artwork/mapping-groups` | GET | zalogowany | — | `app.py:11692` |
| `/api/artwork/mapping-group` | GET,POST | zalogowany | tak | `app.py:11699` |
| `/api/artwork/mapping-group/<int:gid>` | DELETE | rola≥manager | tak | `app.py:11732` |
| `/api/artwork/confirm` | POST | rola≥manager | tak | `app.py:11746` |
| `/api/artwork/unconfirm` | POST | rola≥manager | tak | `app.py:11768` |
| `/api/artwork/confirm-status` | GET | zalogowany | — | `app.py:11786` |
| `/api/artwork/confirmations/stale` | GET | zalogowany | — | `app.py:11800` |

### Relikty DocCompare (do decyzji)

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/suppliers` | GET | zalogowany | — | `app.py:3205` |
| `/api/suppliers` | GET | zalogowany | — | `app.py:3457` |
| `/api/suppliers` | POST | rola≥admin | tak | `app.py:3464` |
| `/api/suppliers/<int:sid>` | PATCH | rola≥admin | tak | `app.py:3480` |
| `/api/suppliers/<int:sid>` | DELETE | rola≥admin | tak | `app.py:3505` |
| `/api/suppliers/detect` | POST | zalogowany | tak | `app.py:3516` |
| `/suppliers/wizard/new` | GET | rola≥admin | — | `app.py:3534` |
| `/suppliers/wizard/<int:sid>` | GET | rola≥admin | — | `app.py:3544` |
| `/api/suppliers/preview_table` | POST | rola≥admin | tak | `app.py:3583` |
| `/api/suppliers/<int:sid>/audit` | GET | rola≥admin | — | `app.py:3638` |
| `/api/suppliers/<int:sid>/stats` | GET | zalogowany | — | `app.py:3663` |
| `/api/suppliers/<int:sid>/rules` | GET | zalogowany | — | `app.py:7066` |
| `/api/suppliers/<int:sid>/rules` | POST | rola≥admin | tak | `app.py:7083` |

### 3D / PalViz

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/artwork/3d` | GET | zalogowany | — | `app.py:4707` |
| `/api/artwork/3d` | POST | zalogowany | tak | `app.py:4717` |
| `/artwork/3d/photo` | GET | zalogowany | — | `app.py:4770` |
| `/artwork/3d/marm` | GET | zalogowany | — | `app.py:4780` |
| `/api/artwork/3d/photo` | POST | zalogowany | tak | `app.py:4848` |
| `/api/artwork/3d/status/<jid>` | GET | zalogowany | — | `app.py:5058` |
| `/api/artwork/3d/accept` | POST | zalogowany | tak | `app.py:5111` |
| `/artwork/3d/model/<path:fname>` | GET | zalogowany | — | `app.py:5186` |
| `/api/artwork/3d/save-copy` | POST | rola≥manager | tak | `app.py:5242` |
| `/artwork/3d/batch` | GET | zalogowany | — | `app.py:5275` |
| `/api/artwork/3d/batch/start` | POST | zalogowany | tak | `app.py:5282` |
| `/api/artwork/3d/batch/from-library` | POST | zalogowany | tak | `app.py:5366` |
| `/api/artwork/3d/batch/status/<jid>` | GET | zalogowany | — | `app.py:5427` |
| `/api/artwork/3d/batch/zip/<jid>` | GET | zalogowany | — | `app.py:5445` |
| `/api/library/file/<int:fid>/3d` | GET | zalogowany | — | `app.py:8134` |
| `/api/library/file/<int:fid>/3d/accept` | POST | zalogowany | tak | `app.py:8209` |
| `/api/render-groups` | GET | zalogowany | — | `app.py:8359` |
| `/api/render-groups` | POST | zalogowany | tak | `app.py:8382` |
| `/api/render-groups/<int:gid>` | DELETE | zalogowany | tak | `app.py:8409` |
| `/api/render-groups/<int:gid>/render` | POST | zalogowany | tak | `app.py:8423` |
| `/api/render-groups/<int:gid>/push` | POST | rola≥manager | tak | `app.py:8448` |
| `/api/artwork/3d/render-refs` | POST | zalogowany | tak | `app.py:8495` |
| `/artwork/render-coverage` | GET | zalogowany | — | `app.py:8631` |
| `/api/artwork/render-coverage` | GET | zalogowany | — | `app.py:8648` |
| `/api/artwork/render/<int:registry_id>/push-retry` | POST | rola≥manager | tak | `app.py:8672` |
| `/admin/palviz-push` | GET | rola≥admin | — | `app.py:8693` |
| `/api/admin/palviz-push` | GET | rola≥admin | — | `app.py:8705` |
| `/api/artwork/profiles/<int:pid>/render` | POST | rola≥manager | tak | `app.py:10106` |
| `/api/artwork/profiles/render-blank` | POST | zalogowany | tak | `app.py:10167` |
| `/artwork/palviz` | GET | zalogowany | — | `blueprints/palviz.py:72` |
| `/api/artwork/palviz` | POST | zalogowany | tak | `blueprints/palviz.py:78` |
| `/artwork/palviz/glb/<name>` | GET | zalogowany | — | `blueprints/palviz.py:143` |
| `/artwork/palviz/zip/<name>` | GET | zalogowany | — | `blueprints/palviz.py:149` |
| `/artwork/palviz/batch` | GET | zalogowany | — | `blueprints/palviz.py:156` |
| `/api/artwork/palviz/batch` | POST | zalogowany | tak | `blueprints/palviz.py:162` |
| `/artwork/templates` | GET | zalogowany | — | `blueprints/palviz.py:229` |
| `/api/artwork/templates/analyze` | POST | rola≥manager | tak | `blueprints/palviz.py:235` |
| `/artwork/templates/preview/<name>` | GET | zalogowany | — | `blueprints/palviz.py:279` |
| `/api/artwork/templates/save` | POST | rola≥manager | tak | `blueprints/palviz.py:286` |

### Master data (materiały / dostawcy)

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/api/ref-database/upload` | POST | rola≥manager | tak | `app.py:8725` |
| `/api/ref-database/lookup` | GET | sesja (ręcznie) | — | `app.py:8809` |
| `/api/ref-database/stats` | GET | sesja (ręcznie) | — | `app.py:8836` |
| `/api/ref-database` | DELETE | rola≥admin | tak | `app.py:8854` |
| `/artwork/materials` | GET | rola≥manager | — | `app.py:10574` |
| `/api/artwork/pkg-level-types` | GET | rola≥manager | — | `app.py:10585` |
| `/api/artwork/pkg-level-types` | POST | rola≥manager | tak | `app.py:10599` |
| `/api/artwork/pkg-level-types/<int:ltid>` | PUT | rola≥manager | tak | `app.py:10626` |
| `/api/artwork/pkg-level-types/<int:ltid>` | DELETE | rola≥manager | tak | `app.py:10648` |
| `/api/materials` | GET | zalogowany | — | `app.py:10663` |
| `/api/materials/<path:ref>` | DELETE | rola≥manager | tak | `app.py:10726` |
| `/api/materials/<path:ref>` | PATCH | rola≥manager | tak | `app.py:10743` |
| `/api/materials/delete-old` | POST | rola≥manager | tak | `app.py:10778` |
| `/api/materials/<path:ref>` | GET | zalogowany | — | `app.py:10800` |
| `/api/materials/migrate-from-products` | POST | rola≥manager | tak | `app.py:10839` |
| `/materials` | GET | zalogowany | — | `app.py:10855` |
| `/api/materials/import` | POST | rola≥manager | tak | `app.py:10974` |
| `/api/materials/marm-import` | POST | rola≥manager | tak | `app.py:11020` |
| `/api/materials/marm/search` | GET | zalogowany | — | `app.py:11066` |
| `/api/materials/marm/suggest` | GET | zalogowany | — | `app.py:11079` |
| `/api/materials/marm/<path:ref>/units` | GET | zalogowany | — | `app.py:11093` |
| `/api/uom` | GET,POST,DELETE | zalogowany | tak | `app.py:11813` |
| `/api/artwork/materials` | GET | rola≥manager | — | `app.py:11861` |
| `/api/artwork/materials` | POST | rola≥manager | tak | `app.py:11939` |
| `/api/artwork/materials/<int:mid>` | PUT | rola≥manager | tak | `app.py:11965` |
| `/api/artwork/materials/<int:mid>` | DELETE | rola≥manager | tak | `app.py:11987` |
| `/api/artwork/materials/<int:mid>/levels/<int:ltid>` | PUT | rola≥manager | tak | `app.py:12002` |
| `/api/artwork/materials/import-csv` | POST | rola≥manager | tak | `app.py:12044` |
| `/api/artwork/materials/export-csv` | GET | rola≥manager | — | `app.py:12126` |
| `/products` | GET | zalogowany | — | `app.py:12613` |
| `/api/products` | GET | zalogowany | — | `app.py:12620` |
| `/api/products` | POST | rola≥manager | tak | `app.py:12657` |
| `/api/products/<int:pid>` | PUT | rola≥manager | tak | `app.py:12687` |
| `/api/products/<int:pid>` | DELETE | rola≥manager | tak | `app.py:12718` |
| `/api/products/import` | POST | rola≥manager | tak | `app.py:12731` |

### Admin / AI / integracje

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/health` | GET | publiczny | — | `app.py:1361` |
| `/api/admin/backup` | POST | rola≥admin | tak | `app.py:1390` |
| `/api/admin/schema-versions` | GET | rola≥admin | — | `app.py:1405` |
| `/admin` | GET | zalogowany | — | `app.py:2208` |
| `/api/admin/db-usage` | GET | rola≥admin | — | `app.py:2293` |
| `/api/admin/db-limit` | POST | rola≥admin | tak | `app.py:2369` |
| `/activity` | GET | zalogowany | — | `app.py:2819` |
| `/api/ai/status` | GET | zalogowany | — | `app.py:6636` |
| `/api/ai/config` | GET,POST | rola≥admin | tak | `app.py:6647` |
| `/api/ai/budget` | GET,POST | zalogowany | tak | `app.py:6672` |
| `/api/ai/learn-document` | POST | zalogowany | tak | `app.py:6695` |
| `/api/ai/apply-profile` | POST | rola≥manager | tak | `app.py:6725` |
| `/api/ai/learn-comparison/<int:cid>` | POST | zalogowany | tak | `app.py:6743` |
| `/api/ai/apply-suggestions` | POST | rola≥manager | tak | `app.py:6773` |
| `/api/ai/pending-updates` | GET | rola≥manager | — | `app.py:6793` |
| `/api/ai/pending-updates/<pending_id>` | DELETE | rola≥manager | tak | `app.py:6804` |
| `/api/ai/learning-stats` | GET | zalogowany | — | `app.py:6816` |
| `/api/email/config` | GET,POST | rola≥admin | tak | `app.py:6953` |
| `/api/email/test` | POST | rola≥admin | tak | `app.py:6983` |
| `/settings/email` | GET | rola≥admin | — | `app.py:7010` |
| `/api-costs` | GET | rola≥manager | — | `app.py:7118` |
| `/api/admin/system-status` | GET | rola≥admin | — | `app.py:12165` |
| `/api/admin/activity-log` | GET | rola≥manager | — | `app.py:12259` |
| `/robots.txt` | GET | publiczny | — | `app.py:12379` |
| `/api/intake/artwork` | POST | token Bearer (INTAKE_TOKEN) | — | `app.py:12395` |
| `/api/webhooks` | GET | rola≥admin | — | `app.py:12521` |
| `/api/webhooks` | POST | rola≥admin | tak | `app.py:12537` |
| `/api/webhooks/<int:wid>` | DELETE | rola≥admin | tak | `app.py:12566` |
| `/api/webhooks/<int:wid>/test` | POST | rola≥admin | tak | `app.py:12579` |

### Wspólne (historia, powiadomienia, pomoc)

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/search` | GET | zalogowany | — | `app.py:1728` |
| `/history` | GET | zalogowany | — | `app.py:1787` |
| `/api/comparison/<int:cid>` | GET | zalogowany | — | `app.py:2548` |
| `/api/comparison/<int:cid>` | DELETE | zalogowany | tak | `app.py:2581` |
| `/api/comparisons/bulk_delete` | POST | zalogowany | tak | `app.py:2609` |
| `/api/comparison/<int:cid>/restore` | POST | zalogowany | tak | `app.py:2654` |
| `/api/comparison/<int:cid>/approve` | POST | rola≥manager | tak | `app.py:2680` |
| `/api/notifications` | GET | zalogowany | — | `app.py:2953` |
| `/api/notifications/<int:nid>/read` | POST | zalogowany | tak | `app.py:2977` |
| `/api/notifications/read-all` | POST | zalogowany | tak | `app.py:2991` |
| `/api/notifications/<int:nid>` | DELETE | zalogowany | tak | `app.py:3005` |
| `/api/comparison/<int:cid>/comment` | POST | zalogowany | tak | `app.py:6845` |
| `/api/comparison/<int:cid>/comments` | GET | zalogowany | — | `app.py:6882` |
| `/help` | GET | zalogowany | — | `app.py:7447` |
| `/data` | GET | zalogowany | — | `app.py:12603` |

### Auth / profil

| Ścieżka | Metody | Dostęp | CSRF | Plik:linia |
|---|---|---|---|---|
| `/` | GET | publiczny (redirect) | — | `app.py:1421` |
| `/login` | GET,POST | publiczny | tak | `app.py:1428` |
| `/set-language/<lang>` | GET | zalogowany | — | `app.py:1492` |
| `/forgot-password` | GET,POST | publiczny | tak | `app.py:1599` |
| `/reset-password` | GET,POST | publiczny | tak | `app.py:1658` |
| `/logout` | GET (potwierdzenie) / POST (CSRF, wylogowanie — US-017) | publiczny | — | `app.py:1720` |
| `/profile` | GET | zalogowany | — | `app.py:2724` |
| `/api/profile/update` | POST | zalogowany | tak | `app.py:2752` |
| `/api/profile/change-password` | POST | zalogowany | tak | `app.py:2785` |
| `/api/profile/export` | GET | zalogowany (własne dane) | — | `blueprints/users.py` (US-014, RODO art. 15/20) |
| `/api/admin/users/<int:uid>/export` | GET | rola≥admin | — | `blueprints/users.py` (US-014) |
| `/api/admin/users/<int:uid>/anonymize` | POST (`{"confirm": "<nazwa>"}`) | rola≥admin | tak | `blueprints/users.py` (US-014, RODO art. 17) |
