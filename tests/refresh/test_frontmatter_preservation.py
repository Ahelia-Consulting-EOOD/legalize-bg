"""A re-scrape must not delete what lex.bg does not know about.

`MetadataParser` returns exactly the fourteen fields it can read off a lex.bg
page. Everything else an act carries — the Gazette provenance block, the
per-event fields on `amendment_history` — is written by another writer, and
passing the freshly parsed metadata straight to the writer deletes all of it.

The second harm is worse than the deletion and less obvious: the change
classifier compares the freshly rendered candidate against the committed text,
so an act whose committed frontmatter carries a key the candidate lacks never
compares equal. Every act is then classified as changed on every run, and a
refresh rewrites and re-commits the whole corpus for ever.
"""

from pathlib import Path

from corpus_gate import render_act
from refresh import LEXBG_METADATA_KEYS, merge_preserved, refresh
from tests.refresh.test_orchestrator import (
    FakeClient,
    FakeMeta,
    FakeParser,
    FakeTreeTransport,
    _commit_initial,
    _init_repo,
    _meta,
    _tree_html,
    _url,
)

_OPEN_GATE = {"uncovered_chars": 0, "buckets": {}}

_PROVENANCE = {
    "grade": "B-pending",
    "base": {"state": "snapshot", "issue": "32", "year": 2026},
    "pending_items": "chain scan incomplete",
}


def _committed(doc_id: int = 100, title: str = "Закон сто") -> dict:
    """A committed act enriched by a writer other than the lex.bg refresh."""
    fm = _meta(doc_id, title, [{"dv": "56/1991", "date": "1991-07-13"},
                               {"dv": "85/2003", "date": "2003-09-26"}])
    fm["amendment_history"] = [
        {"dv": "56/1991", "date": "1991-07-13", "source": "dv_pdf",
         "locator": "242220", "applied": "pending"},
        {"dv": "85/2003", "date": "2003-09-26", "source": "dv_html",
         "locator": "331002", "applied": "yes", "verified_against": "dv",
         "uncertainty": None},
    ]
    fm["provenance"] = dict(_PROVENANCE)
    return fm


def _fresh(doc_id: int = 100, title: str = "Закон сто") -> dict:
    """What MetadataParser returns for the same page: the fourteen keys, and
    amendment_history rows carrying only `dv` and `date`."""
    return _meta(doc_id, title, [{"dv": "56/1991", "date": "1991-07-13"},
                                 {"dv": "85/2003", "date": "2003-09-26"}])


def test_the_preserved_set_is_every_key_the_lex_bg_parser_does_not_produce():
    """The set is explicit, so a new parser field cannot silently join it."""
    from bs4 import BeautifulSoup

    from fetcher.bg.metadata import MetadataParser

    raw = (Path(__file__).resolve().parents[1] / "fixtures" / "html" / "zzd.html")
    soup = BeautifulSoup(raw.read_bytes().decode("cp1251", errors="replace"), "lxml")
    produced = set(MetadataParser().parse(soup, doc_id=1, category="laws"))
    assert produced == LEXBG_METADATA_KEYS


def test_merge_preserved_carries_a_block_the_parser_never_produces():
    merged = merge_preserved(_committed(), _fresh())
    assert merged["provenance"] == _PROVENANCE


def test_merge_preserved_carries_per_event_fields_by_matching_dv():
    merged = merge_preserved(_committed(), _fresh())
    rows = {row["dv"]: row for row in merged["amendment_history"]}
    assert rows["56/1991"]["source"] == "dv_pdf"
    assert rows["85/2003"]["applied"] == "yes"
    assert rows["85/2003"]["verified_against"] == "dv"
    assert "uncertainty" in rows["85/2003"]


def test_merge_preserved_lets_lex_bg_win_on_the_keys_it_owns():
    """Preservation is for keys the parser does not produce. A field lex.bg
    does produce is a re-scrape's whole point and must not be frozen."""
    committed = _committed()
    committed["titulo"] = "Стар несъответен титул"
    fresh = _fresh()
    assert merge_preserved(committed, fresh)["titulo"] == fresh["titulo"]


def test_merge_preserved_does_not_resurrect_a_row_lex_bg_dropped():
    committed = _committed()
    fresh = _meta(100, "Закон сто", [{"dv": "85/2003", "date": "2003-09-26"}])
    merged = merge_preserved(committed, fresh)
    assert [row["dv"] for row in merged["amendment_history"]] == ["85/2003"]


def test_merge_preserved_does_not_mutate_its_inputs():
    committed, fresh = _committed(), _fresh()
    merge_preserved(committed, fresh)
    assert "provenance" not in fresh
    assert fresh["amendment_history"][0] == {"dv": "56/1991", "date": "1991-07-13"}


# --- through the real refresh() --------------------------------------------


def _run(tmp_path, body: str, fresh: dict):
    return refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=FakeTreeTransport(
            {_url("laws", 0): _tree_html([(100, "Закон сто")])}),
        client=FakeClient(available=[100]),
        parser=FakeParser({100: body}),
        metadata_parser=FakeMeta({100: fresh}),
        coverage_gate=lambda soup, body: dict(_OPEN_GATE),
    )


def test_a_re_scrape_that_changes_nothing_is_unchanged_not_a_rewrite(tmp_path):
    """The whole corpus re-committed on every run is the cost of getting the
    classification wrong by one frontmatter key."""
    _init_repo(tmp_path)
    body = "**Чл. 1.** Текст.\n"
    _commit_initial(tmp_path, "laws/zakon-sto.md", render_act(_committed(), body))
    before = (tmp_path / "laws" / "zakon-sto.md").read_bytes()

    report = _run(tmp_path, body, _fresh())

    assert report.unchanged == [100]
    assert report.popravka == [] and report.reforma == []
    assert (tmp_path / "laws" / "zakon-sto.md").read_bytes() == before


def test_a_real_amendment_keeps_the_provenance_block_and_its_event_fields(tmp_path):
    _init_repo(tmp_path)
    _commit_initial(tmp_path, "laws/zakon-sto.md",
                    render_act(_committed(), "**Чл. 1.** Стар текст.\n"))

    fresh = _meta(100, "Закон сто", [{"dv": "56/1991", "date": "1991-07-13"},
                                     {"dv": "85/2003", "date": "2003-09-26"},
                                     {"dv": "9/2026", "date": "2026-01-15"}])
    report = _run(tmp_path, "**Чл. 1.** Нов текст.\n", fresh)

    assert [r["doc_id"] for r in report.reforma] == [100]
    written = (tmp_path / "laws" / "zakon-sto.md").read_text(encoding="utf-8")
    assert "Нов текст" in written
    assert "B-pending" in written
    assert "dv_pdf" in written and "verified_against: dv" in written
