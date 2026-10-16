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
| `async_jobs`, `job_progress`, `artwork_batch_jobs` | zadania w tle | — |
| `intake_queue`, `webhooks`, `email_queue` | integracje | sekrety webhooków |
| `artwork_glb_cache`, `render_group`, `dieline_templates` | 3D | — |

## Wszystkie tabele (64) i miejsce definicji

`migrate_db.py`: api_usage, artwork_batch_jobs, artwork_glb_cache, artwork_mapping_group, artwork_marm_link,
artwork_master_file, artwork_profile_fields, artwork_profiles, artwork_render_registry, comparison_comments,
comparison_templates, comparisons, customs_agencies, doc_types, email_queue, intake_queue, job_progress,
kolejka_kontenery, kolejka_powiadomienia, kolejka_status_log, kolejka_zlecenia, library_files, po_line_items,
ref_database, render_group, schema_migrations, settings, supplier_analysis_log, supplier_audit_log, suppliers,
tickets, transit_countries, users, warehouse_receipts, warehouse_stock, zlecenia_transport_items,
zlecenia_transportowe.
`app.py`: api_rate_events, artwork_field_comments, artwork_field_dict, artwork_field_feedback, artwork_material,
artwork_material_level, artwork_pkg_level_type, artwork_profile_history, async_jobs, audit_log, cn_reference,
currency_rates, notifications, password_reset_tokens, products, sad_field_mapping, supplier_checklists,
translation_dictionary, webhooks.
`artwork_index.py`: artwork_alias, artwork_confirmed, artwork_index. `artwork_manage.py`: artwork_file_status.
`material_master.py`: material_master. `blueprints/palviz.py`: dieline_templates. `blueprints/incoterms.py`:
incoterms_dictionary.

**Relikty DocCompare (kandydaci do usunięcia, US-010):** customs_agencies, kolejka_*, zlecenia_*, warehouse_*,
tickets, po_line_items, sad_field_mapping, cn_reference, currency_rates, supplier_checklists, comparison_templates,
doc_types, products, transit_countries, incoterms_dictionary, translation_dictionary, email_queue.
