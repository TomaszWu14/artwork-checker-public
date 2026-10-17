# Model danych

> [DEV] ERD obejmuje tabele rdzenia artworkowego. Pełna lista 64 tabel z plikiem definiującym — na końcu.
> Schemat powstaje przez `migrate_db.py` (idempotentnie, przy starcie kontenera) oraz `CREATE TABLE IF NOT EXISTS`
> w modułach domenowych. Klucze obce są w większości **logiczne** (bez constraintów) — dziedzictwo SQLite.

```mermaid
erDiagram
    users ||--o{ comparisons : "user_id"
    users ||--o{ password_reset_tokens : "user_id"
    users ||--o{ api_usage : "user_id"
    users ||--o{ artwork_profile_history : "changed_by"
    comparisons ||--o{ artwork_field_comments : "comparison_id"
    comparisons ||--o{ comparison_comments : "comparison_id"
    artwork_profiles ||--o{ artwork_profile_fields : "profile_id"
    artwork_profiles ||--o{ artwork_profile_history : "profile_id"
    library_files ||--o| artwork_profiles : "master_pdf_path"
    library_files ||--o{ artwork_index : "rel_path"
    artwork_index ||--o{ artwork_confirmed : "ref_code, rel_path"
    artwork_index ||--o{ artwork_master_file : "rel_path"
    artwork_alias }o--|| material_master : "ref"
    artwork_mapping_group ||--o{ artwork_alias : "group"
    material_master ||--o{ artwork_material_level : "material_id"
    artwork_pkg_level_type ||--o{ artwork_material_level : "level_type_id"
    material_master ||--o{ artwork_marm_link : "ref"
    artwork_render_registry }o--o| render_group : "group_id"
    artwork_render_registry ||--o{ artwork_glb_cache : "source_hash"
    users {
        int id PK
        text username
        text email
        text password_hash
        text role "user|manager|superuser|admin"
        int is_active
        text department
        text language
        text last_login
    }
    comparisons {
        int id PK
        int user_id FK
        text doc_type "artwork"
        text file_a_name
        text file_b_name
        text status
        text result_json
        int is_public
        int is_deleted
        text created_at
    }
    library_files {
        int id PK
        text rel_path UK
        text filename
        text checksum
        text lvl1_lvl5
        text file_path
        blob thumb_data
        text ref
        text packaging_type
        text synced_at
    }
    artwork_index {
        int id PK
        text ref_code
        text rel_path
        text revision
        text packaging_level
        text status
    }
    artwork_confirmed {
        text ref_code
        text rel_path
        text filename
        text confirmed_by
        text confirmed_at
    }
    artwork_master_file {
        text rel_path PK
        text stored_name
        text content_type
        int size_bytes
        blob data
    }
    artwork_profiles {
        int id PK
        text name
        text master_pdf_path
        text canvas_json
    }
    artwork_profile_fields {
        int id PK
        int profile_id FK
        text field_name
        real x_y_w_h
    }
    material_master {
        int id PK
        text ref UK
        text description
        text ean
        text base_uom
    }
    artwork_render_registry {
        int id PK
        text ref_norm
        text variant "dieline|marm|photo"
        text source_hash
        text glb_path
        text push_status
        int push_attempts
    }
    audit_log {
        int id PK
        text event
        text username
        text detail
        text ip
        int duration_ms
        text extra
        text created_at
    }
    settings {
        text category
        text key
        text value
    }
```

## Tabele operacyjne

| Tabela | Rola | Dane wrażliwe |
|---|---|---|
| `users` | konta i role | dane osobowe, hash hasła |
| `password_reset_tokens` | tokeny resetu (jawne — US-003) | poufne |
| `settings` | konfiguracja (token sync, klucz AI — US-004, e-mail) | poufne |
| `audit_log` | ślad działań | dane osobowe (nazwa, IP) |
| `api_usage`, `api_rate_events` | koszty i limity wywołań | per użytkownik |
| `async_jobs`, `artwork_batch_jobs` | zadania w tle | — |
| `intake_queue`, `webhooks` | integracje | sekrety webhooków |
| `artwork_glb_cache`, `render_group`, `dieline_templates` | 3D | — |

## Wszystkie tabele i miejsce definicji (po US-028)

`migrate_db.py`: api_usage, artwork_batch_jobs, artwork_glb_cache, artwork_mapping_group, artwork_marm_link,
artwork_master_file, artwork_profile_fields, artwork_profiles, artwork_render_registry, comparison_comments,
comparisons, intake_queue, library_files, ref_database, render_group, schema_migrations, settings,
supplier_audit_log, suppliers, users.
`app.py`: api_rate_events, artwork_field_comments, artwork_field_dict, artwork_field_feedback, artwork_material,
artwork_material_level, artwork_pkg_level_type, artwork_profile_history, async_jobs, audit_log, notifications,
password_reset_tokens, products, webhooks.
`artwork_index.py`: artwork_alias, artwork_confirmed, artwork_index. `artwork_manage.py`: artwork_file_status.
`material_master.py`: material_master. `blueprints/palviz.py`: dieline_templates.

**Relikty DocCompare usunięte w US-028** (decyzja PO 2026-10-17: „usuń”): kod nie tworzy już 25 tabel
(`tools/drop_relic_tables.py` → `RELIC_TABLES`: kolejka_*, zlecenia_*, transport_queue, warehouse_*,
customs_agencies, po_line_items, doc_types, comparison_templates, translation_dictionary, incoterms_dictionary,
transit_countries, sad_field_mapping, cn_reference, currency_rates, supplier_checklists, delivery_checklists,
supplier_analysis_log, tickets, email_queue, job_progress). Z istniejących baz kasuje je jednorazowo operator
(RUNBOOK §4). **Zostają** (żywy kod): `products` (API `/api/products`, migracja do `material_master` — bez UI,
do decyzji PO), `intake_queue` (log `POST /api/intake/artwork`), `comparison_comments` (stara historia `/history`).
Kolumny `users.forwarder_id` / `users.customs_agency_id` zostają (usunięcie kolumn poza zakresem).
