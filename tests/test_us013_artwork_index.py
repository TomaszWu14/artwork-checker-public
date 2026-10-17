"""US-013 — pokrycie logiki indeksu masterów artworków (artwork_index.py).

Czysta logika na izolowanej bazie SQLite w pamięci; syntetyczne nazwy plików
i ścieżki (żadnych odwołań do prawdziwego dysku Z:\\ ani sieci).
"""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest  # noqa: E402

import artwork_index as ai  # noqa: E402

_OPEN = []


@pytest.fixture(autouse=True)
def _close_dbs():
    yield
    while _OPEN:
        _OPEN.pop().close()


def _db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    _OPEN.append(db)
    return db


def _browse_db():
    """Baza z tabelami, których dotyka browse() (rejestr renderów, linki MARM)."""
    db = _db()
    db.execute(
        "CREATE TABLE artwork_render_registry (id INTEGER PRIMARY KEY, ref_norm TEXT, variant TEXT)"
    )
    db.execute("CREATE TABLE artwork_marm_link (id INTEGER PRIMARY KEY, art_ref_norm TEXT)")
    db.commit()
    return db


def _add(db, filename, rel_path=None, mtime=""):
    return ai.sync_entries(
        db,
        [{"filename": filename, "rel_path": rel_path or f"lib/{filename}", "source_mtime": mtime}],
    )


# ── Poziomy opakowania ────────────────────────────────────────────────────────


def test_us013_norm_level_aliases_and_unknown():
    assert ai._norm_level("KAR") == "karton"
    assert ai._norm_level(" Pouch ") == "op"
    assert ai._norm_level("opz") == "opz"
    assert ai._norm_level("—") == ""
    assert ai._norm_level(None) == ""
    assert ai._norm_level("paleta") == ""  # nieznany poziom → brak


def test_us013_other_level_keywords_excludes_own_level():
    other = ai._other_level_keywords("KAR")
    assert "pouch" in other and "single" in other
    assert "carton" not in other and "karton" not in other
    assert ai._other_level_keywords("") == set()


def test_us013_conf_key_with_and_without_level():
    assert ai._conf_key("rnbm-10001") == "RNBM10001"
    assert ai._conf_key("rnbm-10001", "KAR") == "RNBM10001" + ai._LEVEL_SEP + "karton"


def test_us013_pick_level_prefers_matching_then_non_conflicting():
    rows = [{"filename": "x_pouch.pdf"}, {"filename": "x_carton.pdf"}, {"filename": "x_plain.pdf"}]
    assert ai._pick_level([], "KAR") is None
    assert ai._pick_level(rows, None) == rows[0]
    assert ai._pick_level(rows, "KAR") == rows[1]
    # Brak pliku dla poziomu „sztuka" → bierzemy pierwszy NIEkolidujący (plain), nie pouch.
    assert ai._pick_level(rows, "SZT") == rows[2]
    # Same pliki innego poziomu → None (lepiej brak niż pouch jako karton).
    assert ai._pick_level([{"filename": "x_pouch.pdf"}], "KAR") is None


# ── Bootstrap tabeli ──────────────────────────────────────────────────────────


def test_us013_ensure_table_pg_branch_failures_are_swallowed(monkeypatch):
    # Na SQLite instrukcje pg_trgm/GIN padają — każda w try/except z rollbackiem,
    # więc ustawienie DATABASE_URL nie może wywrócić bootstrapu ani zepsuć tabeli.
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    db = _db()
    ai.ensure_table(db)
    _add(db, "RNBM10001_pouch Rev.01.pdf")
    assert db.execute("SELECT COUNT(*) FROM artwork_index").fetchone()[0] == 1


# ── Parsowanie wpisów agenta / sync ───────────────────────────────────────────


def test_us013_parse_entry_requires_rel_path_and_derives_filename():
    assert ai._parse_entry({"filename": "a.pdf"}) is None
    rec = ai._parse_entry({"rel_path": "lib\\sub\\ABC12345_carton Rev.05.pdf", "source_mtime": 7})
    assert rec["filename"] == "ABC12345_carton Rev.05.pdf"
    assert rec["ref_norm"] == "ABC12345"
    assert rec["revision_rank"] == 5
    assert rec["packaging_type"] == "carton"
    assert rec["source_mtime"] == "7"


def test_us013_parse_entry_survives_parser_exception(monkeypatch):
    def _boom(_fn):
        raise RuntimeError("parser down")

    monkeypatch.setattr(ai, "parse_master_filename", _boom)
    rec = ai._parse_entry({"rel_path": "lib/ABC12345_carton Rev.05.pdf"})
    assert rec["ref_norm"] == "" and rec["revision_rank"] == 0
    assert rec["filename"] == "ABC12345_carton Rev.05.pdf"


def test_us013_sync_entries_counts_skipped_and_applies_alias():
    db = _db()
    ai.add_alias(db, "ZZ-777", "nitrile_blue")
    res = ai.sync_entries(
        db,
        [
            {"filename": "no_path.pdf"},  # brak rel_path → skipped
            {"filename": "Easy_Nitrile_Blue_carton.pdf", "rel_path": "lib/easy.pdf"},
        ],
    )
    assert res == {"indexed": 1, "skipped": 1}
    row = db.execute("SELECT ref_norm, ref_code FROM artwork_index").fetchone()
    assert (row["ref_norm"], row["ref_code"]) == ("ZZ777", "ZZ-777")


# ── Aliasy ────────────────────────────────────────────────────────────────────


def test_us013_add_alias_validation_backfill_and_replace():
    db = _db()
    assert "error" in ai.add_alias(db, "", "x")
    assert "error" in ai.add_alias(db, "R1", "  ")
    _add(db, "mystery_pouch_a.pdf")
    _add(db, "other_pouch_b.pdf")
    res = ai.add_alias(db, "R-1", "mystery")
    assert res == {"ok": True, "matched": 1}
    assert ai.lookup_best(db, "R1")["filename"] == "mystery_pouch_a.pdf"
    # replace=True: stary alias i backfill cofnięte, nowy plik przejmuje REF.
    res = ai.add_alias(db, "R-1", "other", replace=True)
    assert res["matched"] == 1
    assert [a["pattern"] for a in ai.list_aliases(db)] == ["other"]
    assert ai.lookup_best(db, "R1")["filename"] == "other_pouch_b.pdf"
    old = db.execute(
        "SELECT ref_norm FROM artwork_index WHERE filename='mystery_pouch_a.pdf'"
    ).fetchone()
    assert old["ref_norm"] == ""


def test_us013_add_alias_escapes_like_wildcards():
    db = _db()
    _add(db, "abcXdef.pdf")
    _add(db, "abc_def.pdf")
    res = ai.add_alias(db, "R2", "abc_def")
    # '_' to literał, nie wildcard — dopasowany tylko jeden plik.
    assert res["matched"] == 1


def test_us013_delete_alias_by_id_and_bad_id():
    db = _db()
    ai.add_alias(db, "R3", "pat")
    aid = ai.list_aliases(db)[0]["id"]
    assert ai.delete_alias(db, "abc") == {"error": "Złe id"}
    assert ai.delete_alias(db, None) == {"error": "Złe id"}
    assert ai.delete_alias(db, str(aid)) == {"ok": True}
    assert ai.list_aliases(db) == []


def test_us013_lookup_best_alias_fallback_and_empty_ref():
    db = _db()
    assert ai.lookup_best(db, "  --  ") is None
    _add(db, "fancy_name_carton.pdf")
    # Alias dodany zanim plik się pojawił w indeksie z tym REF → backfill ustawia REF;
    # potem cofamy REF z wiersza, żeby wymusić ścieżkę fallbacku po wzorcu.
    ai.add_alias(db, "Q-9", "fancy_name")
    db.execute("UPDATE artwork_index SET ref_norm='', ref_code=''")
    db.commit()
    best = ai.lookup_best(db, "Q9", "KAR")
    assert best is not None and best["filename"] == "fancy_name_carton.pdf"
    assert ai.lookup_best(db, "Q9", "OP") is None  # carton ≠ pouch


def test_us013_all_revisions_empty_ref():
    assert ai.all_revisions(_db(), "") == []


# ── Import listingu ───────────────────────────────────────────────────────────


def test_us013_norm_mtime_polish_windows_export():
    assert ai._norm_mtime("") == ""
    assert ai._norm_mtime("5.3.2024 7:05") == "2024-03-05 07:05:00"
    assert ai._norm_mtime("05.03.2024") == "2024-03-05 00:00:00"
    assert ai._norm_mtime("2024-03-05T10:00:00") == "2024-03-05T10:00:00"


def test_us013_import_listing_empty_and_folder_rows():
    db = _db()
    assert ai.import_listing(db, []) == {
        "indexed": 0,
        "skipped": 0,
        "total_lines": 0,
        "candidates": 0,
    }
    rows = [
        ["FullName", "LastWriteTime", "IsFolder"],
        ["\\\\srv\\lib\\dir", "01.01.2024 10:00", "True"],
        ['"\\\\srv\\lib\\ABC12345_carton Rev.05.pdf"', "02.01.2024 11:30:15", "False"],
        ["\\\\srv\\lib\\notes.txt", "", "False"],
        ["", "", "False"],
        ["short"],  # krótszy wiersz
    ]
    res = ai.import_listing(db, rows)
    assert res["total_lines"] == 5
    assert res["candidates"] == 1
    assert res["indexed"] == 1
    r = db.execute("SELECT rel_path, source_mtime, ref_norm FROM artwork_index").fetchone()
    assert r["rel_path"] == "//srv/lib/ABC12345_carton Rev.05.pdf"
    assert r["source_mtime"] == "2024-01-02 11:30:15"
    assert r["ref_norm"] == "ABC12345"


def test_us013_import_listing_headerless_every_cell_is_candidate():
    db = _db()
    res = ai.import_listing(db, [["a/x1_pouch.pdf", "b/x2_carton.PDF", None], None])
    assert res["candidates"] == 2 and res["total_lines"] == 1


def test_us013_index_stats_and_packaging_types():
    db = _db()
    _add(db, "RNBM10001_pouch Rev.01.pdf")
    _add(db, "RNBM10001_carton Rev.02.pdf")
    st = ai.index_stats(db)
    assert st["total"] == 2 and st["with_ref"] == 2 and st["distinct_refs"] == 1
    assert st["last_scan"]
    assert ai.packaging_types(db) == ["carton", "pouch"]


# ── browse() ─────────────────────────────────────────────────────────────────


def _seed_browse(db):
    _add(db, "RNBM10001_pouch Rev.01.pdf")
    _add(db, "RNBM10001_pouch Rev.02.pdf")
    _add(db, "ABC12345_carton Rev.05.pdf")
    db.execute(
        "INSERT INTO artwork_render_registry(ref_norm, variant) VALUES('ABC12345','dieline')"
    )
    db.execute("INSERT INTO artwork_render_registry(ref_norm, variant) VALUES('ABC12345','photo')")
    db.execute("INSERT INTO artwork_marm_link(art_ref_norm) VALUES('RNBM10001')")
    db.commit()


def test_us013_browse_no_query_flags_and_pagination():
    db = _browse_db()
    _seed_browse(db)
    res = ai.browse(db, per_page="bad")  # zły per_page → domyślne 50
    assert res["per_page"] == 50 and res["page"] == 1 and res["total"] == 3
    assert res["packaging_types"] == ["carton", "pouch"]
    by_fn = {r["filename"]: r for r in res["rows"]}
    abc = by_fn["ABC12345_carton Rev.05.pdf"]
    assert abc["has_3d"] and abc["has_dieline"] and abc["has_photo"] and not abc["has_marm"]
    assert not by_fn["RNBM10001_pouch Rev.01.pdf"]["has_3d"]
    # Brak tabeli statusów → cichy fallback 'active'.
    assert all(r["status"] == "active" for r in res["rows"])
    p2 = ai.browse(db, per_page=2, page=2)
    assert p2["pages"] == 2 and len(p2["rows"]) == 1 and p2["packaging_types"] == []


def test_us013_browse_filters_variant_marm_current_packaging():
    db = _browse_db()
    _seed_browse(db)
    assert [r["ref_norm"] for r in ai.browse(db, variant="dieline")["rows"]] == ["ABC12345"]
    marm = ai.browse(db, marm_linked=True)
    assert {r["ref_norm"] for r in marm["rows"]} == {"RNBM10001"} and marm["total"] == 2
    cur = ai.browse(db, current_only=True)
    assert sorted(r["revision"] for r in cur["rows"]) == ["Rev.02", "Rev.05"]
    assert ai.browse(db, packaging="pouch")["total"] == 2
    assert ai.browse(db, variant="bogus")["total"] == 3  # nieznany wariant ignorowany


def test_us013_browse_hide_ignored_and_status_attached():
    import artwork_manage as am

    db = _browse_db()
    _seed_browse(db)
    am.ensure_status_table(db)
    db.execute(
        "INSERT INTO artwork_file_status(rel_path, status) VALUES('lib/RNBM10001_pouch Rev.01.pdf','ignored')"
    )
    db.commit()
    full = ai.browse(db)
    st = {r["filename"]: r["status"] for r in full["rows"]}
    assert st["RNBM10001_pouch Rev.01.pdf"] == "ignored"
    assert st["ABC12345_carton Rev.05.pdf"] == "active"
    hidden = ai.browse(db, hide_ignored=True)
    assert hidden["total"] == 2
    assert "RNBM10001_pouch Rev.01.pdf" not in {r["filename"] for r in hidden["rows"]}


def test_us013_browse_query_pins_exact_ref():
    db = _browse_db()
    _seed_browse(db)
    _add(db, "ABC1234_carton Rev.01.pdf")
    res = ai.browse(db, q="abc-12345")
    assert res["rows"][0]["ref_norm"] == "ABC12345"
    assert ai.browse(db, q="zzz-none")["total"] == 0


def test_us013_browse_query_over_rerank_cap_uses_sql_paging(monkeypatch):
    db = _browse_db()
    for i in range(6):
        _add(db, f"XQ{i:03d}_pouch Rev.01.pdf")
    _add(db, "XQ_carton Rev.01.pdf")
    monkeypatch.setattr(ai, "_RERANK_CAP", 3)
    res = ai.browse(db, q="XQ", per_page=2, page=1)
    assert res["total"] == 7
    assert len(res["rows"]) == 2
    # Pin na dokładny ref_norm działa także w ścieżce SQL.
    assert res["rows"][0]["ref_norm"] == "XQ"


# ── suggest_by_text ───────────────────────────────────────────────────────────


def test_us013_tok_quantity_suffix_and_bigrams():
    toks = ai._tok("Bed Bath A8 10")
    assert {"bed", "bath", "a8", "8", "10", "a10", "bedbath"} <= toks
    assert ai._word_tokens("the PDF rev x") == []


def test_us013_suggest_by_text_level_boost_and_empty():
    db = _db()
    assert ai.suggest_by_text(db, "  ") == []
    _add(db, "easycare_nitrile_gloves_pouch.pdf", mtime="2024-01-01")
    _add(db, "easycare_nitrile_gloves_carton.pdf", mtime="2023-01-01")
    _add(db, "unrelated_thing.pdf")
    res = ai.suggest_by_text(db, "easyCARE nitrile gloves", level="KAR")
    assert [r["filename"] for r in res] == [
        "easycare_nitrile_gloves_carton.pdf",
        "easycare_nitrile_gloves_pouch.pdf",
    ]
    assert res[0]["score"] > res[1]["score"]
    # 3 słowa + 2 bigramy sąsiednich słów (easycarenitrile, nitrilegloves).
    assert res[0]["shared"] == 5
    # Bez poziomu: równy score → nowszy plik pierwszy.
    res = ai.suggest_by_text(db, "easyCARE nitrile gloves")
    assert res[0]["filename"] == "easycare_nitrile_gloves_pouch.pdf"


def test_us013_suggest_by_text_short_tokens_fallback_key():
    db = _db()
    _add(db, "a8_x.pdf")
    # Tylko tokeny 1-znakowe/stop → słowa kluczowe puste, fallback na tokeny pochodne.
    assert ai.suggest_by_text(db, "8 a") == []


# ── Potwierdzenia / dryf rewizji ─────────────────────────────────────────────


def test_us013_confirm_validation_and_unconfirm():
    db = _db()
    assert "error" in ai.confirm_artwork(db, "", "x")
    assert "error" in ai.confirm_artwork(db, "R1", " ")
    assert ai.unconfirm_artwork(db, "R1") == {"ok": True, "removed": 0}
    # Plik spoza indeksu → potwierdzenie bez rewizji.
    res = ai.confirm_artwork(db, "R1", "lib/ghost.pdf", user="u", level="KAR")
    assert res["filename"] == "" and res["revision"] == "" and res["level"] == "karton"
    assert ai.get_confirmed(db, "R1", "KAR")["rel_path"] == "lib/ghost.pdf"
    assert ai.unconfirm_artwork(db, "R1", "KAR") == {"ok": True, "removed": 1}
    assert ai.get_confirmed(db, "R1", "KAR") is None
    assert ai.get_confirmed(db, "") is None


def test_us013_legacy_confirmation_hidden_for_other_level():
    db = _db()
    _add(db, "RNBM10001_pouch Rev.01.pdf")
    ai.confirm_artwork(db, "RNBM10001", "lib/RNBM10001_pouch Rev.01.pdf")  # bez poziomu
    assert ai.get_confirmed(db, "RNBM10001", "OP")["filename"].endswith("pouch Rev.01.pdf")
    assert ai.get_confirmed(db, "RNBM10001", "KAR") is None


def test_us013_lookup_for_comparison_drift_by_rank_and_mtime():
    db = _db()
    _add(db, "RNBM10001_pouch Rev.01.pdf", mtime="2024-01-01")
    ai.confirm_artwork(db, "RNBM10001", "lib/RNBM10001_pouch Rev.01.pdf")
    r = ai.lookup_for_comparison(db, "RNBM10001")
    assert r["needs_confirmation"] is False and r["revision_changed"] is False
    _add(db, "RNBM10001_pouch Rev.02.pdf")
    r = ai.lookup_for_comparison(db, "RNBM10001")
    assert r["revision_changed"] is True and r["group_master"] is None
    # Równy rank, nowsza data → też dryf.
    db2 = _db()
    _add(db2, "RNBM10001_pouch Rev.01.pdf", rel_path="old/a.pdf", mtime="2024-01-01")
    ai.confirm_artwork(db2, "RNBM10001", "old/a.pdf")
    _add(db2, "RNBM10001_pouch Rev.01 copy.pdf", rel_path="new/a.pdf", mtime="2024-06-01")
    assert ai.lookup_for_comparison(db2, "RNBM10001")["revision_changed"] is True


def test_us013_stale_confirmations_per_level():
    db = _db()
    _add(db, "RNBM10001_carton Rev.01.pdf")
    _add(db, "RNBM10001_pouch Rev.01.pdf")
    ai.confirm_artwork(db, "RNBM10001", "lib/RNBM10001_carton Rev.01.pdf", level="KAR")
    ai.confirm_artwork(db, "RNBM10001", "lib/RNBM10001_pouch Rev.01.pdf", level="OP")
    ai.confirm_artwork(db, "GONE1", "lib/none.pdf")  # brak w indeksie → pomijany
    assert ai.stale_confirmations(db) == []
    _add(db, "RNBM10001_carton Rev.03.pdf")
    stale = ai.stale_confirmations(db)
    assert len(stale) == 1
    s = stale[0]
    assert s["level"] == "karton"
    assert s["confirmed_rev"] == "Rev.01" and s["newest_rev"] == "Rev.03"
    assert s["newest_path"] == "lib/RNBM10001_carton Rev.03.pdf"


# ── Grupy mapowań ─────────────────────────────────────────────────────────────


def test_us013_groups_crud_and_dedup():
    db = _db()
    _add(db, "MASTER1_carton Rev.04.pdf")
    try:
        ai.save_group(db, "  ", "x", [])
        raise AssertionError("pusta nazwa powinna rzucić ValueError")
    except ValueError:
        pass
    gid = ai.save_group(
        db, "Gloves", "lib/MASTER1_carton Rev.04.pdf", ["ab-1", "AB1", "", None, "cd 2"]
    )
    groups = ai.list_groups(db)
    assert len(groups) == 1
    g = groups[0]
    assert g["refs"] == ["ab-1", "cd 2"] and g["refs_count"] == 2
    assert g["master_in_index"] is True and g["master_revision"] == "Rev.04"
    # Aktualizacja po gid; master spoza indeksu → nazwa z basename.
    assert ai.save_group(db, "Gloves2", "far/away/m.pdf", ["X1"], gid=gid) == gid
    g = ai.list_groups(db)[0]
    assert g["group_name"] == "Gloves2"
    assert g["master_filename"] == "m.pdf" and g["master_in_index"] is False
    ai.delete_group(db, gid)
    assert ai.list_groups(db) == []


def test_us013_list_groups_tolerates_bad_json():
    db = _db()
    ai.ensure_groups_table(db)
    db.execute(
        "INSERT INTO artwork_mapping_group(group_name, master_rel_path, refs_json) VALUES('G','', 'not json')"
    )
    db.commit()
    g = ai.list_groups(db)[0]
    assert g["refs"] == [] and g["master_filename"] == ""


def test_us013_lookup_group_master_and_comparison_fallback():
    db = _db()
    ai.ensure_table(db)
    assert ai.lookup_group_master(db, "") is None
    ai.save_group(db, "NoMaster", "", ["R9"])
    ai.ensure_groups_table(db)
    db.execute(
        "INSERT INTO artwork_mapping_group(group_name, master_rel_path, refs_json) VALUES('Bad','x.pdf','{oops')"
    )
    db.commit()
    assert ai.lookup_group_master(db, "R9") is None
    ai.save_group(db, "Real", "share/grp_master.pdf", ["r-9"])
    gm = ai.lookup_group_master(db, "R9")
    assert gm["via_group"] is True and gm["group_name"] == "Real"
    assert gm["filename"] == "grp_master.pdf" and gm["revision"] == ""
    cmp = ai.lookup_for_comparison(db, "R9")
    assert cmp["newest"] is None and cmp["confirmed"] is None
    assert cmp["group_master"]["rel_path"] == "share/grp_master.pdf"
    assert ai._group_master_view(db, "") is None


def test_us013_lookup_for_comparison_group_lookup_error_is_none(monkeypatch):
    db = _db()

    def _boom(*a, **k):
        raise RuntimeError("db gone")

    monkeypatch.setattr(ai, "lookup_group_master", _boom)
    assert ai.lookup_for_comparison(db, "R1")["group_master"] is None


# ── Składnica bajtów masterów ────────────────────────────────────────────────


def test_us013_master_file_store_roundtrip_and_wanted_paths():
    db = _db()
    with_bytes = b"%PDF-1.4 synthetic"
    try:
        ai.record_master_file(db, "lib/a.pdf", "a.pdf", data=None)
        raise AssertionError("brak bajtów powinien rzucić ValueError")
    except ValueError:
        pass
    try:
        ai.record_master_file(db, "lib/a.pdf", "a.pdf", data=b"")
        raise AssertionError("puste bajty powinny rzucić ValueError")
    except ValueError:
        pass
    assert ai.master_file_blob(db, "lib/a.pdf") is None
    assert ai.master_file_for(db, "lib/a.pdf") is None
    ai.record_master_file(
        db, "lib/a.pdf", "a.pdf", content_type=None, size="3", data=memoryview(with_bytes)
    )
    assert ai.master_file_for(db, "lib/a.pdf") == {
        "stored_name": "a.pdf",
        "content_type": "application/pdf",
    }
    assert ai.master_file_blob(db, "lib/a.pdf") == ("application/pdf", with_bytes)
    assert ai.available_master_paths(db) == {"lib/a.pdf"}
    # Upsert nadpisuje bajty.
    ai.record_master_file(db, "lib/a.pdf", "a2.pdf", data=bytearray(b"NEW"))
    assert ai.master_file_blob(db, "lib/a.pdf")[1] == b"NEW"

    ai.confirm_artwork(db, "R1", "lib/a.pdf")
    ai.confirm_artwork(db, "R2", "lib/b.pdf")
    ai.save_group(db, "G", "lib/c.pdf", ["R3"])
    assert ai.wanted_master_paths(db) == ["lib/b.pdf", "lib/c.pdf"]
