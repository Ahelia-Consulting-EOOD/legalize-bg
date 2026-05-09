"""§7.1 / §7.2 / §7.3 data-quality acceptance tests against the real
catalog.db built from `main`. Skipped if catalog.db is missing — run
`python -m index.build` first to enable these tests.

These are the "did we keep our promises about real-world corpus
quirks?" tests. Unit tests cover the same code paths against the
in-memory `populated_conn` fixture; this file proves the behavior
holds against actual lex.bg-sourced data.
"""

import pathlib
import sqlite3

import pytest

from mcp_server.errors import ToolError
from mcp_server.server import build_app

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "catalog.db"


@pytest.fixture(scope="module")
def real_app():
    if not DB_PATH.exists():
        pytest.skip(
            f"catalog.db missing at {DB_PATH}; run `python -m index.build` "
            "from the repo root to enable real-corpus acceptance tests."
        )
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return build_app(conn=conn, corpus_root=REPO_ROOT)


def test_71_ambiguous_collision_slug(real_app):
    """§7.1 — pick a law whose slug ends in '-2' (collision-resolved)
    and search by its title. AMBIGUOUS_NAME must surface, with both
    candidates carrying distinct identificadors."""
    row = real_app._conn.execute(
        "SELECT law_id, title FROM laws WHERE law_id LIKE '%-2' AND title <> '' LIMIT 1"
    ).fetchone()
    assert row, (
        "no collision-suffixed law in catalog (expected ~5-10% per §7.1; "
        "rebuild catalog if this is wrong)"
    )
    title = row["title"]
    with pytest.raises(ToolError) as exc:
        real_app.call_tool_sync("get_law", {"name": title})
    assert exc.value.code == "AMBIGUOUS_NAME"
    candidates = exc.value.payload["candidates"]
    assert len(candidates) >= 2
    identificadors = {c["identificador"] for c in candidates}
    assert len(identificadors) == len(candidates), \
        "all collision candidates must have distinct identificadors"


def test_72_null_pub_date_returns_DATE_UNCERTAIN(real_app):
    """§7.2 — pick one of the 121 acts where date_uncertain=1 and
    expect the DATE_UNCERTAIN warning. The detection now reads the
    persisted column; this test would have silently broken under the
    old time-dependent rule."""
    row = real_app._conn.execute(
        "SELECT laws.law_id, laws.doc_id "
        "FROM laws JOIN law_versions USING(law_id) "
        "WHERE law_versions.date_uncertain = 1 LIMIT 1"
    ).fetchone()
    if not row:
        pytest.skip("no §7.2 acts in current build (expected 121 per §7.2)")
    result = real_app.call_tool_sync("get_law", {"name": str(row["doc_id"])})
    codes = [w["code"] for w in result["warnings"]]
    assert "DATE_UNCERTAIN" in codes


def test_72_null_pub_date_count_matches_canonical_data_model(real_app):
    """§7.2 promises exactly 121 acts have date_uncertain=1 in the
    bootstrap build. The canonical data model documents this number;
    deviation means either the bootstrap regressed or the doc is stale."""
    n = real_app._conn.execute(
        "SELECT COUNT(*) FROM law_versions WHERE date_uncertain = 1"
    ).fetchone()[0]
    assert n == 121, (
        f"§7.2 acts changed: was 121, now {n}. Update "
        "docs/data/canonical-data-model.md §7.2 if this is intentional."
    )


def test_73_empty_titulo_phantom_act(real_app):
    """§7.3 — doc_id -549676032 (the spot-check phantom). get_law via
    identificador succeeds with empty `titulo` (truthful), but search
    surfaces it with `<doc_id=N>` substituted in the title slot."""
    result = real_app.call_tool_sync("get_law", {"name": "-549676032"})
    assert result["law_id"]
    assert result["titulo"] == ""  # truthful empty (don't fake it)
    hits = real_app.call_tool_sync("search", {"query": "549676032"})
    phantom = [h for h in hits if h["law_id"] == result["law_id"]]
    assert phantom, "phantom act must remain findable via identificador"
    assert phantom[0]["title"].startswith("<doc_id=")


def test_73_phantom_count_matches_canonical_data_model(real_app):
    """§7.3 promises exactly 7 acts have empty titulo. `laws.title`
    stores the `<doc_id=N>` substitute (so FTS5 keeps them findable
    via doc_id); we count those placeholders to verify the §7.3 quota.

    The truthful empty `titulo` value is preserved in the .md
    frontmatter and surfaces via `get_law` — see the sibling
    `test_73_empty_titulo_phantom_act` for that contract."""
    n = real_app._conn.execute(
        "SELECT COUNT(*) FROM laws WHERE title LIKE '<doc_id=%'"
    ).fetchone()[0]
    assert n == 7, (
        f"§7.3 phantom count changed: was 7, now {n}. Update "
        "docs/data/canonical-data-model.md §7.3 if intentional."
    )


def test_search_finds_zop_via_indefinite_form(real_app):
    """D-022 symmetry: query 'обществени поръчки' (indefinite) finds
    ЗОП. (Top-3 ranking is FR-015 territory; for now we just require
    the law is in the result list, not the position.)"""
    hits = real_app.call_tool_sync(
        "search", {"query": "обществени поръчки", "limit": 20})
    hit_ids = [h["law_id"] for h in hits]
    assert "zakon-za-obshtestvenite-porachki" in hit_ids, \
        f"ЗОП missing from top-20; got first 5: {hit_ids[:5]}"


def test_search_finds_zop_via_definite_form(real_app):
    """D-022 symmetry: 'обществените поръчки' (plural definite) finds
    the same ЗОП — the plural-symmetry fix ensures both reduce."""
    hits = real_app.call_tool_sync(
        "search", {"query": "обществените поръчки", "limit": 20})
    hit_ids = [h["law_id"] for h in hits]
    assert "zakon-za-obshtestvenite-porachki" in hit_ids


def test_get_article_returns_real_zop_article_1(real_app):
    """End-to-end: ЗОП's чл. 1 is retrievable via identificador and
    returns a non-trivial article body containing 'Този закон'."""
    r = real_app.call_tool_sync(
        "get_article", {"law": "2136735703", "article": "чл. 1"})
    assert r["article"] == "1"
    assert r["paragraph"] is None
    assert "Този закон" in r["text"]
