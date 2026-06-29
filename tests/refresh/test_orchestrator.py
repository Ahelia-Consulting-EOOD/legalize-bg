"""Integration test for the refresh() orchestrator against a temp git repo.

Uses injected fakes for the tree transport, doc client, parser and metadata
parser (the real fetcher units are tested in tests/fetcher/). Here we verify
the orchestration: partition -> fetch/assemble -> classify -> typed commit,
with slug stability for EXISTING acts and file preservation for MISSING acts.
"""

import subprocess
from pathlib import Path

import pytest

from fetcher.bg.assembler import assemble_file
from refresh import refresh, load_state


# --- fakes ------------------------------------------------------------------


class FakeTreeTransport:
    def __init__(self, url_to_html):
        self._map = {u: h.encode("cp1251") for u, h in url_to_html.items()}

    def get_tree_page(self, url):
        return self._map.get(url, b"<html><body></body></html>")


def _tree_html(doc_ids):
    links = "".join(f'<a href="/laws/ldoc/{d}">{n}</a>' for d, n in doc_ids)
    return f"<html><body>{links}</body></html>"


class FakeClient:
    """fetch_soup(doc_id) -> the doc_id itself, used as an opaque token."""

    def __init__(self, available):
        self._available = set(available)

    def fetch_soup(self, doc_id):
        if doc_id not in self._available:
            raise KeyError(f"doc {doc_id} not fetchable")
        return doc_id

    def close(self):
        pass


class FakeParser:
    def __init__(self, bodies):
        self._bodies = bodies

    def convert(self, token):
        return self._bodies[token]


class FakeMeta:
    def __init__(self, metas):
        self._metas = metas

    def parse(self, token, doc_id, category):
        return dict(self._metas[token])


class FakeSoupClient:
    """fetch_soup(doc_id) -> a real BeautifulSoup carrying a HistoryOfDocument,
    so the MISSING-flip repeal detection can run against it."""

    def __init__(self, history_by_doc):
        from bs4 import BeautifulSoup
        self._BS = BeautifulSoup
        self._h = history_by_doc

    def fetch_soup(self, doc_id):
        h = self._h.get(doc_id, "")
        html = f'<html><body><div class="HistoryOfDocument">{h}</div></body></html>'
        return self._BS(html, "lxml")

    def close(self):
        pass


# --- repo + corpus fixtures -------------------------------------------------


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, check=True)


def _meta(doc_id, title, hist):
    return {
        "titulo": title,
        "identificador": str(doc_id),
        "pais": "bg",
        "rango": "закон",
        "fecha_publicacion": "1991-07-13",
        "ultima_actualizacion": hist[-1]["date"] if hist else "1991-07-13",
        "estado": "vigente",
        "fuente": "lex.bg",
        "category": "laws",
        "amendment_history": hist,
    }


def _commit_initial(tmp_path, rel, text):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    subprocess.run(["git", "add", str(rel)], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"[bootstrap] {rel}"],
                   cwd=tmp_path, check=True)


def _url(cat, page):
    return f"https://lex.bg/laws/tree/{cat}/{page}"


def _last_subject(tmp_path):
    return subprocess.run(["git", "log", "-1", "--format=%s"], cwd=tmp_path,
                          check=True, capture_output=True, text=True).stdout.strip()


def test_refresh_added_existing_missing_end_to_end(tmp_path):
    _init_repo(tmp_path)

    # Existing act 100, will be amended. Build its committed file from the
    # same assembler the refresh uses, so an UNCHANGED scrape would match.
    hist_old = [{"dv": "56/1991", "date": "1991-07-13"}]
    existing_meta = _meta(100, "Закон сто", hist_old)
    existing_body_old = "Член 1. Стар текст.\n"
    _commit_initial(tmp_path, "laws/zakon-sto.md",
                    assemble_file(existing_meta, existing_body_old))

    # Missing act 300: in corpus, absent from the lex.bg crawl -> must be kept.
    gone_meta = _meta(300, "Отишъл закон", [{"dv": "1/2000", "date": "2000-01-01"}])
    _commit_initial(tmp_path, "laws/otishal-zakon.md",
                    assemble_file(gone_meta, "Член 1. Текст.\n"))

    # lex.bg now serves 100 (amended) and 200 (new); 300 is gone.
    crawl_cfg = {"laws": 1}
    tree = FakeTreeTransport({
        _url("laws", 0): _tree_html([(100, "Закон сто"), (200, "Нов закон")]),
    })

    hist_new = hist_old + [{"dv": "85/2003", "date": "2003-09-26"}]
    fresh_100 = _meta(100, "Закон сто", hist_new)
    new_200 = _meta(200, "Нов закон", [{"dv": "9/2026", "date": "2026-01-01"}])

    client = FakeClient(available=[100, 200])
    parser = FakeParser({100: "Член 1. Нов текст.\n", 200: "Член 1. Новозаконов текст.\n"})
    meta = FakeMeta({100: fresh_100, 200: new_200})

    report = refresh(
        tmp_path, branch=None, crawl_config=crawl_cfg, today_iso="2026-06-21",
        tree_transport=tree, client=client, parser=parser, metadata_parser=meta,
        coverage_gate=lambda soup, body: {"uncovered_chars": 0, "buckets": {}},
    )

    # Partition outcomes
    assert [a["doc_id"] for a in report.added] == [200]
    assert [r["doc_id"] for r in report.reforma] == [100]
    assert report.popravka == []
    assert report.unchanged == []
    assert [m["doc_id"] for m in report.missing_kept] == [300]
    assert report.errors == []

    # EXISTING act keeps its slug; file now carries the fresh body.
    amended = (tmp_path / "laws" / "zakon-sto.md").read_text(encoding="utf-8")
    assert "Нов текст" in amended
    assert (tmp_path / "laws" / "zakon-sto.md").exists()

    # MISSING act file is preserved, not deleted.
    assert (tmp_path / "laws" / "otishal-zakon.md").exists()

    # ADDED act got a brand-new file under a minted slug.
    added_slug = report.added[0]["slug"]
    assert added_slug != "zakon-sto"
    assert (tmp_path / "laws" / f"{added_slug}.md").exists()

    # Checkpoint persisted both processed acts.
    state = load_state(tmp_path / ".refresh-state.json")
    assert state[100] == "reforma"
    assert state[200] == "nova"


def test_refresh_added_nonlaws_act_lands_in_corpus_dir_not_tree_slug(tmp_path):
    # An ADDED наредба arrives under the lex.bg tree slug "ords"; it MUST be
    # written to the corpus dir "ordinances", never to a literal "ords/" dir
    # (which index/build.py would never scan). Regression for the tree-slug
    # vs corpus-dir bug.
    _init_repo(tmp_path)
    crawl_cfg = {"ords": 1}
    tree = FakeTreeTransport({_url("ords", 0): _tree_html([(700, "Наредба нова")])})
    new_700 = _meta(700, "Наредба нова", [{"dv": "9/2026", "date": "2026-01-01"}])
    new_700["category"] = "ordinances"

    report = refresh(
        tmp_path, branch=None, crawl_config=crawl_cfg, today_iso="2026-06-21",
        tree_transport=tree, client=FakeClient([700]),
        parser=FakeParser({700: "Член 1.\n"}), metadata_parser=FakeMeta({700: new_700}),
        coverage_gate=lambda soup, body: {"uncovered_chars": 0, "buckets": {}},
    )
    assert [a["doc_id"] for a in report.added] == [700]
    slug = report.added[0]["slug"]
    assert (tmp_path / "ordinances" / f"{slug}.md").exists()
    assert not (tmp_path / "ords").exists()


def test_refresh_unchanged_act_is_skipped_no_commit(tmp_path):
    _init_repo(tmp_path)
    hist = [{"dv": "56/1991", "date": "1991-07-13"}]
    m = _meta(100, "Закон сто", hist)
    body = "Член 1. Текст.\n"
    _commit_initial(tmp_path, "laws/zakon-sto.md", assemble_file(m, body))
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                 check=True, capture_output=True, text=True).stdout.strip()

    tree = FakeTreeTransport({_url("laws", 0): _tree_html([(100, "Закон сто")])})
    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=FakeClient([100]),
        parser=FakeParser({100: body}), metadata_parser=FakeMeta({100: m}),
        coverage_gate=lambda soup, body: {"uncovered_chars": 0, "buckets": {}},
    )

    assert report.unchanged == [100]
    assert report.reforma == [] and report.popravka == []
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                check=True, capture_output=True, text=True).stdout.strip()
    assert head_after == head_before  # no new commit for an unchanged act


def test_refresh_resume_skips_already_processed(tmp_path):
    _init_repo(tmp_path)
    hist = [{"dv": "56/1991", "date": "1991-07-13"}]
    m = _meta(100, "Закон сто", hist)
    _commit_initial(tmp_path, "laws/zakon-sto.md", assemble_file(m, "Член 1.\n"))

    # Pre-seed the checkpoint as if 100 was already handled in a prior run.
    from refresh import save_state
    save_state(tmp_path / ".refresh-state.json", {100: "unchanged"})

    tree = FakeTreeTransport({_url("laws", 0): _tree_html([(100, "Закон сто")])})
    # Client raises if 100 is fetched -> proves the act was skipped, not refetched.
    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=FakeClient([]),  # nothing fetchable
        parser=FakeParser({}), metadata_parser=FakeMeta({}),
    )
    assert report.errors == []
    assert report.unchanged == [] and report.reforma == []


def test_refresh_popravka_when_body_changed_history_did_not(tmp_path):
    _init_repo(tmp_path)
    hist = [{"dv": "56/1991", "date": "1991-07-13"}]
    m = _meta(100, "Закон сто", hist)
    _commit_initial(tmp_path, "laws/zakon-sto.md",
                    assemble_file(m, "Член 1. Текст с грешка.\n"))

    tree = FakeTreeTransport({_url("laws", 0): _tree_html([(100, "Закон сто")])})
    # Same history, corrected body -> popravka.
    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=FakeClient([100]),
        parser=FakeParser({100: "Член 1. Текст без грешка.\n"}),
        metadata_parser=FakeMeta({100: m}),
        coverage_gate=lambda soup, body: {"uncovered_chars": 0, "buckets": {}},
    )
    assert [p["doc_id"] for p in report.popravka] == [100]
    assert report.reforma == []
    assert _last_subject(tmp_path) == "[popravka] Закон сто"


def test_refresh_missing_kept_by_default_not_deleted_not_committed(tmp_path):
    _init_repo(tmp_path)
    gone = _meta(300, "Отишъл закон", [{"dv": "1/2000", "date": "2000-01-01"}])
    _commit_initial(tmp_path, "laws/otishal-zakon.md",
                    assemble_file(gone, "Член 1.\n"))
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                 check=True, capture_output=True, text=True).stdout.strip()

    tree = FakeTreeTransport({_url("laws", 0): _tree_html([])})  # 300 absent
    report = refresh(
        tmp_path, branch=None, crawl_config={"laws": 1}, today_iso="2026-06-21",
        tree_transport=tree, client=FakeClient([]),
        parser=FakeParser({}), metadata_parser=FakeMeta({}),
    )
    assert [m["doc_id"] for m in report.missing_kept] == [300]
    assert (tmp_path / "laws" / "otishal-zakon.md").exists()  # not deleted
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                check=True, capture_output=True, text=True).stdout.strip()
    assert head_after == head_before  # no commit by default


def test_refresh_flip_repealed_missing_uses_real_repeal_date(tmp_path):
    # A MISSING act whose fresh lex.bg page shows an `отм. ДВ` marker is flipped
    # to derogado, with the [otmyana] author-date = the actual repeal date.
    _init_repo(tmp_path)
    gone = _meta(300, "Отменена наредба", [{"dv": "5/2006", "date": "2006-01-17"}])
    _commit_initial(tmp_path, "ordinances/otmenena.md", assemble_file(gone, "Чл. 1.\n"))

    tree = FakeTreeTransport({_url("ords", 0): _tree_html([])})  # 300 absent
    client = FakeSoupClient({300: "Обн. ДВ. бр. 5 от 17 Януари 2006г. , отм. ДВ. бр. 54 от 12 Юни 2026г."})
    report = refresh(
        tmp_path, branch=None, crawl_config={"ords": 1}, today_iso="2026-06-21",
        flip_missing_estado=True, tree_transport=tree, client=client,
        parser=FakeParser({}), metadata_parser=FakeMeta({}),
    )
    assert [o["doc_id"] for o in report.otmyana] == [300]
    assert report.missing_not_repealed == []
    text = (tmp_path / "ordinances" / "otmenena.md").read_text(encoding="utf-8")
    assert "estado: derogado" in text
    assert _last_subject(tmp_path) == "[otmyana] Отменена наредба"
    author_date = subprocess.run(["git", "log", "-1", "--format=%ai"], cwd=tmp_path,
                                 check=True, capture_output=True, text=True).stdout
    assert "2026-06-12" in author_date  # repeal date, not today


def test_refresh_flip_skips_missing_act_without_repeal_marker(tmp_path):
    # A MISSING act with NO `отм.` marker (e.g. a private-body bylaw) must NOT
    # be flipped — it left the tree for a non-repeal reason and needs review.
    _init_repo(tmp_path)
    gone = _meta(300, "Частен правилник", [])
    _commit_initial(tmp_path, "implementing/chasten.md", assemble_file(gone, "Чл. 1.\n"))
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                 check=True, capture_output=True, text=True).stdout.strip()

    tree = FakeTreeTransport({_url("reg_laws", 0): _tree_html([])})
    client = FakeSoupClient({300: "Приет от УС на САБ с Решение по Протокол от 08.07.2014 г."})
    report = refresh(
        tmp_path, branch=None, crawl_config={"reg_laws": 1}, today_iso="2026-06-21",
        flip_missing_estado=True, tree_transport=tree, client=client,
        parser=FakeParser({}), metadata_parser=FakeMeta({}),
    )
    assert [m["doc_id"] for m in report.missing_not_repealed] == [300]
    assert report.otmyana == []
    text = (tmp_path / "implementing" / "chasten.md").read_text(encoding="utf-8")
    assert "estado: vigente" in text  # untouched
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                                check=True, capture_output=True, text=True).stdout.strip()
    assert head_after == head_before  # no commit
