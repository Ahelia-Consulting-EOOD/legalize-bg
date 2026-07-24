"""FR-032 two-index search tests: insert API + tier-2 overscan with the
breadth-corrected best-segment score (D-056 as amended 2026-07-23).

Fixture dbs are built through migrate() so they carry the REAL v5 schema.
"""

import sqlite3

import pytest

from index.fts import (
    BREADTH_ALPHA,
    BREADTH_SATURATION,
    TIER2_OVERSCAN,
    bg_normalize,
    insert_segment_rows,
    insert_title_row,
    search_fts,
)
from index.migrations import migrate


@pytest.fixture()
def conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    migrate(conn)
    return conn


def _add_act(conn, law_id, title, body, category, doc_id=1):
    conn.execute(
        "INSERT INTO laws (law_id, doc_id, title, category) VALUES (?,?,?,?)",
        (law_id, doc_id, title, category))
    insert_title_row(conn, law_id=law_id, title=title, category=category)
    insert_segment_rows(conn, law_id=law_id, body=body, category=category)


# ── insert API ─────────────────────────────────────────────────────────

def test_insert_title_row_normalizes(conn):
    insert_title_row(conn, law_id="a", title="ЗАКОНЪТ за Нещо",
                     category="laws")
    row = conn.execute("SELECT title FROM laws_fts").fetchone()
    assert row["title"] == bg_normalize("ЗАКОНЪТ за Нещо")


def test_insert_segment_rows_shapes(conn):
    body = ("Преамбюл на акта.\n\n"
            "**Чл. 1.** Първи член за киберсигурност.\n\n"
            "**§ 1.** Параграф от ПЗР.\n")
    insert_segment_rows(conn, law_id="a", body=body, category="laws")
    rows = conn.execute(
        "SELECT seg_no, kind, label, body FROM articles_fts"
        " ORDER BY CAST(seg_no AS INTEGER)").fetchall()
    assert [r["seg_no"] for r in rows] == ["0", "1", "2"]
    assert [(r["kind"], r["label"]) for r in rows] == [
        ("preamble", ""), ("article", "чл. 1"), ("para", "§ 1")]
    assert rows[1]["body"] == bg_normalize(
        "**Чл. 1.** Първи член за киберсигурност.\n\n")


def test_insert_segment_rows_rejects_non_tiling_segmentation(conn, monkeypatch):
    """The corpus-wide coverage gate (design §9): a segmentation whose
    spans do not tile the body exactly must abort the act's indexing,
    never silently index partial text (the D-047 lesson)."""
    import index.fts as fts
    from index.segments import Segment

    def corrupt(body, normalize, max_bytes=None):
        return [(Segment("other", "", 0, max(0, len(body) - 1)),
                 normalize(body[:-1]))]

    monkeypatch.setattr(fts, "segment_texts", corrupt)
    with pytest.raises(ValueError, match="coverage invariant"):
        insert_segment_rows(conn, law_id="a", body="Текст на акт.",
                            category="laws")


def test_insert_segment_rows_empty_body_writes_nothing(conn):
    insert_segment_rows(conn, law_id="a", body="", category="laws")
    assert conn.execute(
        "SELECT COUNT(*) FROM articles_fts").fetchone()[0] == 0


# ── tier 1 (title) unchanged in shape ──────────────────────────────────

def test_title_query_served_from_title_tier(conn):
    _add_act(conn, "zop", "Закон за обществените поръчки",
             "**Чл. 1.** Обхват.", "laws", doc_id=10)
    _add_act(conn, "other", "Наредба за горите",
             "**Чл. 1.** Гори.", "ordinances", doc_id=11)
    hits = search_fts(conn, "обществени поръчки", limit=10)
    assert hits[0]["law_id"] == "zop"
    assert hits[0]["matched_kind"] is None  # title-tier hit
    assert "<b>" in hits[0]["snippet"]


# ── tier 2 (segments) ──────────────────────────────────────────────────

@pytest.fixture()
def body_corpus(conn):
    # 'broad' matches the term in 3 separate articles; 'narrow' once in
    # a tiny § — neither title mentions it, so tier 2 must serve.
    _add_act(conn, "broad", "Закон за мрежите",
             "**Чл. 1.** Уредба на киберсигурност в мрежите и системите.\n\n"
             "**Чл. 2.** Органи по киберсигурност и контрол по него.\n\n"
             "**Чл. 3.** Санкции при нарушения на киберсигурност.\n",
             "laws", doc_id=1)
    _add_act(conn, "narrow", "Наредба за печатите",
             "**Чл. 1.** Печати и щемпели.\n\n"
             "**§ 1.** Значение: киберсигурност.\n",
             "ordinances", doc_id=2)
    return conn


def test_body_hits_carry_segment_attribution(body_corpus):
    hits = search_fts(body_corpus, "киберсигурност", limit=10)
    ids = [h["law_id"] for h in hits]
    assert set(ids) == {"broad", "narrow"}
    for h in hits:
        assert h["matched_kind"] in {"article", "para"}
        assert h["matched_label"]
        assert "<b>киберсигурност</b>" in h["seg_snippet"]


def test_body_tier_dedups_acts(body_corpus):
    hits = search_fts(body_corpus, "киберсигурност", limit=10)
    ids = [h["law_id"] for h in hits]
    assert len(ids) == len(set(ids))


def test_breadth_corrected_score_formula(body_corpus):
    """Act score MUST equal best-segment bm25 − α·n/(n+5) with n counted
    over the fixed overscan window — recomputed here from raw SQL."""
    hits = search_fts(body_corpus, "киберсигурност", limit=10)
    raw = body_corpus.execute(
        "SELECT law_id, bm25(articles_fts) AS s FROM articles_fts"
        " WHERE articles_fts MATCH ? ORDER BY bm25(articles_fts) LIMIT ?",
        (bg_normalize("киберсигурност"), TIER2_OVERSCAN)).fetchall()
    best, cnt = {}, {}
    for r in raw:
        lid = r["law_id"]
        best.setdefault(lid, r["s"])
        cnt[lid] = cnt.get(lid, 0) + 1
    for h in hits:
        lid = h["law_id"]
        expected = best[lid] - BREADTH_ALPHA * cnt[lid] / (
            cnt[lid] + BREADTH_SATURATION)
        assert h["score"] == pytest.approx(expected, abs=0), (
            f"{lid}: score {h['score']} != best {best[lid]} - breadth")


def test_breadth_rewards_multi_segment_act(body_corpus):
    """'broad' (3 matching articles) must outrank 'narrow' (1 tiny §)
    — with rang-tiers equal-or-favoring broad (laws vs ordinances) AND
    the breadth correction, the canonical-act inversion measured in the
    spike must not occur here."""
    hits = search_fts(body_corpus, "киберсигурност", limit=10)
    assert hits[0]["law_id"] == "broad"


def test_category_filter_applies_to_body_tier(body_corpus):
    hits = search_fts(body_corpus, "киберсигурност",
                      category="ordinances", limit=10)
    assert [h["law_id"] for h in hits] == ["narrow"]


def test_malformed_query_returns_empty(body_corpus):
    assert search_fts(body_corpus, '"unbalanced', limit=10) == []
    assert search_fts(body_corpus, "*", limit=10) == []


def test_missing_articles_fts_propagates(conn):
    conn.execute("DROP TABLE articles_fts")
    _add = conn.execute
    _add("INSERT INTO laws (law_id, doc_id, title, category)"
         " VALUES ('a', 1, 'Тест', 'laws')")
    insert_title_row(conn, law_id="a", title="Тест", category="laws")
    with pytest.raises(sqlite3.OperationalError):
        search_fts(conn, "киберсигурност", limit=10)


def test_overscan_constant_is_fixed_500():
    # Determinism contract: breadth counts (hence scores) must not vary
    # with the caller's limit.
    assert TIER2_OVERSCAN == 500
    assert BREADTH_ALPHA == 4.0
    assert BREADTH_SATURATION == 5.0
