"""The write path (reading/write.py): a read act goes through the gate into one commit with its run record."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from bs4 import BeautifulSoup

from corpus_gate import CorpusIntegrityError, render_act
from fetcher.bg.metadata import MetadataParser
from reading import ladder, waiver_count
from reading.splitter import split_lexbg
from reading.write import WriteRefused, build_frontmatter, main, write_staged
from refresh import _split_frontmatter, merge_preserved

REPO = Path(__file__).resolve().parents[2]
SLUG = "zakon-za-probata"
RUN = "run-x"

PAGE = """<html><body><div class="box"><div class="boxi">
<div><a>ДОБАВИ В МОИТЕ АКТОВЕ</a></div>
<div class="TitleDocument" id="DocumentTitle"><p class="Title">ЗАКОН ЗА ПРОБАТА<br/></p></div>
<div class="HistoryOfDocument" id="historyOfDocument"><p class="Title"><span class="HistoryItem">обн. ДВ. бр.<span class="HistoryReference">10</span> от 5 Февруари 2010г.</span>, <span class="HistoryItem">изм. ДВ. бр.<span class="HistoryReference">20</span> от 6 Март 2015г.</span></p></div>
<div class="Section">Глава първа.<br/>ОБЩИ ПОЛОЖЕНИЯ</div>
<div class="Article">Чл. 1. (1) Този закон урежда пробата.<br/>(2) Пробата е публична{tail}</div>
<div class="Article">Чл. 2. Законът влиза в сила от деня на обнародването му.</div>
<div class="FinalEdictsArticle">Релевантни актове от Европейското законодателство</div>
</div></div></body></html>"""

MAP = {0: {"label": "drop", "note": "chrome"}, 1: {"label": "title"}, 2: {"label": "chapter_heading"},
       3: {"label": "chapter_heading"}, 4: {"label": "article_head", "n": "1"}, 5: {"label": "alinea", "n": "2"},
       6: {"label": "article_head", "n": "2"}, 7: {"label": "drop", "note": "chrome"}}

COMMITTED = {"titulo": "ЗАКОН ЗА ПРОБАТА", "identificador": "999", "pais": "bg", "rango": "закон",
             "fecha_publicacion": "2010-02-05", "ultima_actualizacion": "2010-02-05", "estado": "vigente",
             "fuente": "lex.bg", "category": "laws", "amendment_history": [{"dv": "10/2010", "date": "2010-02-05"}],
             "materia": ["запазено"]}


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def _setup(tmp_path, *, tail=".", committed=None, old_body="# ЗАКОН ЗА ПРОБАТА\n\n**Чл. 1.** Стар текст.\n", waived=None,
           page=PAGE, smap=MAP):
    root = tmp_path / "repo"
    (root / "laws").mkdir(parents=True)
    (root / "docs" / "data").mkdir(parents=True)
    waivers = (REPO / "docs" / "data" / "waivers.yaml").read_text(encoding="utf-8")
    if waived is not None:
        head = waivers.index("  acts:\n", waivers.index("\ntag_remnants:\n")) + len("  acts:\n")
        waivers = waivers[:head] + f"    {SLUG}: {waived}\n" + waivers[head:]
    (root / "docs" / "data" / "waivers.yaml").write_text(waivers, encoding="utf-8")
    (root / "laws" / f"{SLUG}.md").write_text(render_act(committed or COMMITTED, old_body), encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "user.email", "t@t")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "seed")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw = page.replace("{tail}", tail).encode("cp1251")
    (raw_dir / "999.html").write_bytes(raw)
    row = {"doc_id": 999, "slug": SLUG, "category": "laws", "url": "u", "fetched_at": "2026-10-21T00:00:00+00:00",
           "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "status": "ok"}
    (raw_dir / "manifest.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    run_dir = root / "data" / "runs" / RUN / SLUG
    run_dir.mkdir(parents=True)
    act = split_lexbg(raw)
    (run_dir / "blocks.json").write_text(json.dumps(act.to_dict(), ensure_ascii=False), encoding="utf-8")
    (run_dir / "map.json").write_text(json.dumps({str(k): v for k, v in smap.items()}, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report-round0.json").write_text("{}", encoding="utf-8")
    md, *_ = ladder.evaluate(act, smap, [], SLUG)
    (run_dir / "staged.md").write_text(md, encoding="utf-8")
    return root, run_dir, raw_dir


def _write(root, run_dir, raw_dir, **kw):
    return write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, **kw)


def test_an_act_is_committed_with_its_trailers_provenance_and_run_record(tmp_path):
    root, run_dir, raw_dir = _setup(tmp_path)
    w = _write(root, run_dir, raw_dir)
    assert w.commit_type == "reforma"  # the page lists 20/2015, the committed frontmatter does not
    msg = _git(root, "log", "-1", "--format=%B")
    assert msg.startswith("[reforma] ЗАКОН ЗА ПРОБАТА\n\n")
    map_sha = hashlib.sha256((run_dir / "map.json").read_bytes()).hexdigest()
    for trailer in ("Source-Id: lexbg-999", "Source-Date: 2015-03-06", "Norm-Id: 999", f"Record-Id: {RUN}/{SLUG}/{map_sha[:12]}"):
        assert trailer in msg
    assert _git(root, "log", "-1", "--format=%aI").startswith("2015-03-06T00:00:00")
    files = set(_git(root, "show", "--name-only", "--format=", "HEAD").split())
    assert files == {f"laws/{SLUG}.md", f"data/runs/{RUN}/{SLUG}/map.json", f"data/runs/{RUN}/{SLUG}/report-round0.json"}
    fm, body = _split_frontmatter((root / "laws" / f"{SLUG}.md").read_text(encoding="utf-8"))
    assert body.lstrip("\n") == (run_dir / "staged.md").read_text(encoding="utf-8")
    assert "Релевантни" not in body and "ДОБАВИ" not in body  # ruling 9: chrome dropped
    prov = fm["provenance"]
    assert prov["base"]["source"] == "lexbg" and prov["base"]["state"] == "snapshot"
    assert prov["base"]["page_sha256"] == hashlib.sha256((raw_dir / "999.html").read_bytes()).hexdigest()
    assert prov["record"] == {"run": RUN, "map_sha256": map_sha,
                              "blocks_sha256": hashlib.sha256((run_dir / "blocks.json").read_bytes()).hexdigest()}
    assert prov["omissions"] == []
    assert fm["materia"] == COMMITTED["materia"]  # carried over as the refresh path does


def test_the_frontmatter_is_the_refresh_paths(tmp_path):
    root, run_dir, raw_dir = _setup(tmp_path)
    raw = (raw_dir / "999.html").read_bytes()
    fresh = MetadataParser().parse(BeautifulSoup(raw.decode("cp1251"), "lxml"), doc_id=999, category="laws")
    assert build_frontmatter(raw, "999", "laws", COMMITTED) == merge_preserved(COMMITTED, fresh)
    repealed = {**COMMITTED, "estado": "derogado"}
    assert build_frontmatter(raw, "999", "laws", repealed)["estado"] == "derogado"  # never un-repealed


def test_an_unchanged_history_is_a_popravka_and_a_second_write_is_unchanged(tmp_path):
    committed = {**COMMITTED, "amendment_history": [{"dv": "10/2010", "date": "2010-02-05"}, {"dv": "20/2015", "date": "2015-03-06"}]}
    root, run_dir, raw_dir = _setup(tmp_path, committed=committed)
    assert _write(root, run_dir, raw_dir).commit_type == "popravka"
    head = _git(root, "rev-parse", "HEAD")
    again = _write(root, run_dir, raw_dir)
    assert again.commit_type == "unchanged" and again.commit is None and _git(root, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("spoil, says", [
    ("page", "differs from its manifest line"),
    ("blocks", "splits into other blocks"),
    ("staged", "differs from the run's staged.md"),
    ("map", r"exception\(s\) on the page \(label_text_mismatch\)"),
])
def test_a_reading_that_does_not_hold_is_refused_before_the_gate(tmp_path, spoil, says):
    root, run_dir, raw_dir = _setup(tmp_path)
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    if spoil == "page":
        (raw_dir / "999.html").write_bytes((raw_dir / "999.html").read_bytes() + b" ")
    elif spoil == "blocks":
        d = json.loads((run_dir / "blocks.json").read_text(encoding="utf-8"))
        d["blocks"][4]["text"] += " x"
        (run_dir / "blocks.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    elif spoil == "staged":
        (run_dir / "staged.md").write_text("other", encoding="utf-8")
    else:
        (run_dir / "map.json").write_text(json.dumps({**{str(k): v for k, v in MAP.items()}, "6": {"label": "article_head", "n": "9"}}), encoding="utf-8")
    with pytest.raises(WriteRefused, match=says):
        _write(root, run_dir, raw_dir)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before
    assert _git(root, "rev-list", "--count", "HEAD") == "1\n"


def test_a_gate_refusal_leaves_the_act_unchanged(tmp_path):
    root, run_dir, raw_dir = _setup(tmp_path, tail="./STRONG>")  # a remnant the rulings do not repair, not waived
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    with pytest.raises(CorpusIntegrityError) as exc:
        _write(root, run_dir, raw_dir)
    assert {v.check for v in exc.value.violations} == {"tag_remnants"}
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before
    assert _git(root, "rev-list", "--count", "HEAD") == "1\n"


def test_a_waived_act_lowers_its_count_in_the_same_commit(tmp_path):
    root, run_dir, raw_dir = _setup(tmp_path, tail="./STRONG> и /B>", waived=3)  # waived for 3, carries 2
    _write(root, run_dir, raw_dir)
    assert f"    {SLUG}: 2\n" in (root / "docs" / "data" / "waivers.yaml").read_text(encoding="utf-8")
    assert "docs/data/waivers.yaml" in _git(root, "show", "--name-only", "--format=", "HEAD").split()


def test_a_refused_write_restores_a_lowered_waiver(tmp_path, monkeypatch):
    root, run_dir, raw_dir = _setup(tmp_path, waived=2)
    act_before = (root / "laws" / f"{SLUG}.md").read_bytes()
    waivers_before = (root / "docs" / "data" / "waivers.yaml").read_bytes()

    def refuse(path, *a, **kw):
        assert f"{SLUG}:" not in Path(kw["waivers_path"]).read_text(encoding="utf-8")  # lowered to zero: removed
        raise CorpusIntegrityError(path, [])
    monkeypatch.setattr("reading.write.write_act", refuse)
    with pytest.raises(CorpusIntegrityError):
        _write(root, run_dir, raw_dir)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == act_before
    assert (root / "docs" / "data" / "waivers.yaml").read_bytes() == waivers_before


def test_lower_count_only_lowers_and_leaves_an_empty_map(tmp_path):
    p = tmp_path / "w.yaml"
    each = '  expires: "the sweep; each act leaves the waiver as it is repaired"\n'
    p.write_text("other:\n" + each + "  acts:\n    a: 1\ntag_remnants:\n  ruling: r\n" + each + "  acts:\n    a: 4\n    b: 2\n"
                 "last:\n" + each + "  acts:\n    c: 1\nwhole:\n  expires: \"a detector ships\"\n  acts:\n    d: 3\n", encoding="utf-8")
    assert waiver_count.lower_count(p, "whole", "d", 0) is None  # an expiry that is not per act: the gate's to refuse
    assert waiver_count.lower_count(p, "tag_remnants", "a", 5) is None
    assert waiver_count.lower_count(p, "tag_remnants", "c", 0) is None  # c is waived under another check
    assert waiver_count.lower_count(p, "tag_remnants", "a", 1) is not None
    assert yaml.safe_load(p.read_text())["tag_remnants"]["acts"] == {"a": 1, "b": 2}
    waiver_count.lower_count(p, "tag_remnants", "a", 0)
    waiver_count.lower_count(p, "tag_remnants", "b", 0)
    w = yaml.safe_load(p.read_text())
    assert w["tag_remnants"]["acts"] == {} and w["other"]["acts"] == {"a": 1} and w["last"]["acts"] == {"c": 1}


def test_the_cli_prints_written_and_refused(tmp_path, monkeypatch, capsys):
    root, run_dir, raw_dir = _setup(tmp_path)
    shutil.copytree(run_dir, run_dir.parent / "zakon-bez-fayl")
    monkeypatch.setattr("reading.write.RUNS", root / "data" / "runs")
    monkeypatch.setattr("reading.write.RAW", raw_dir)
    import reading.write as w
    real = w.write_staged
    monkeypatch.setattr(w, "write_staged", lambda slug, rd, **kw: real(slug, rd, root=root, raw_dir=raw_dir, **kw))
    assert main(["--run", RUN, "--all"]) == 1
    out = capsys.readouterr().out
    report = json.loads(out[out.index("{"):])
    assert [x["slug"] for x in report["written"]] == [SLUG]
    assert [(x["slug"], x["by"]) for x in report["refused"]] == [("zakon-bez-fayl", "reading")]


def test_the_cli_reports_an_unexpected_error_and_carries_on(tmp_path, monkeypatch, capsys):
    root, run_dir, raw_dir = _setup(tmp_path)
    shutil.copytree(run_dir, run_dir.parent / "a-broken-folder")
    monkeypatch.setattr("reading.write.RUNS", root / "data" / "runs")
    import reading.write as w
    real = w.write_staged

    def staged(slug, rd, **kw):
        if slug == "a-broken-folder":
            raise FileNotFoundError("staged.md")
        return real(slug, rd, root=root, raw_dir=raw_dir, **kw)
    monkeypatch.setattr(w, "write_staged", staged)
    assert main(["--run", RUN, "--all"]) == 1
    out = capsys.readouterr().out
    report = json.loads(out[out.index("{"):])
    assert [x["slug"] for x in report["written"]] == [SLUG]  # the act after the broken folder is still written
    assert [(x["slug"], x["by"]) for x in report["refused"]] == [("a-broken-folder", "error")]


def test_an_omission_is_recorded_in_the_provenance_block(tmp_path):
    page = PAGE.replace("Глава първа.<br/>ОБЩИ", "Глава първа.<br/>Глава първа.<br/>ОБЩИ")  # lex.bg prints the heading again
    smap = {(k if k < 3 else k + 1): v for k, v in MAP.items()} | {3: {"label": "chapter_heading"}}
    root, run_dir, raw_dir = _setup(tmp_path, page=page, smap=smap)
    _write(root, run_dir, raw_dir)
    fm, _ = _split_frontmatter((root / "laws" / f"{SLUG}.md").read_text(encoding="utf-8"))
    assert fm["provenance"]["omissions"] == [{"kind": "superseded_heading", "blocks": [2]}]


def test_a_failed_commit_puts_the_act_and_the_waiver_back_and_a_rerun_commits(tmp_path, monkeypatch):
    root, run_dir, raw_dir = _setup(tmp_path, waived=2)
    act_before = (root / "laws" / f"{SLUG}.md").read_bytes()
    waivers_before = (root / "docs" / "data" / "waivers.yaml").read_bytes()
    import reading.write as w
    real = w._git

    def failing(r, *args, **kw):
        if args[0] == "commit":
            raise subprocess.CalledProcessError(1, ["git", "commit"])
        return real(r, *args, **kw)
    monkeypatch.setattr(w, "_git", failing)
    with pytest.raises(subprocess.CalledProcessError):
        _write(root, run_dir, raw_dir)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == act_before
    assert (root / "docs" / "data" / "waivers.yaml").read_bytes() == waivers_before
    assert _git(root, "diff", "--cached", "--name-only") == ""  # nothing left staged
    monkeypatch.setattr(w, "_git", real)
    assert _write(root, run_dir, raw_dir).commit is not None  # not taken for unchanged


def test_a_non_integrity_error_at_the_gate_restores_the_waiver(tmp_path, monkeypatch):
    root, run_dir, raw_dir = _setup(tmp_path, waived=2)
    waivers_before = (root / "docs" / "data" / "waivers.yaml").read_bytes()

    def broken(*a, **kw):
        raise ValueError("malformed waiver file")
    monkeypatch.setattr("reading.write.write_act", broken)
    with pytest.raises(ValueError):
        _write(root, run_dir, raw_dir)
    assert (root / "docs" / "data" / "waivers.yaml").read_bytes() == waivers_before


def test_a_failed_rollback_of_the_act_still_restores_the_waiver(tmp_path, monkeypatch):
    root, run_dir, raw_dir = _setup(tmp_path, waived=2)
    waivers_before = (root / "docs" / "data" / "waivers.yaml").read_bytes()
    import reading.write as w
    real = w._git

    def failing(r, *args, **kw):
        if args[0] in ("commit", "checkout"):
            raise subprocess.CalledProcessError(1, ["git", args[0]])
        return real(r, *args, **kw)
    monkeypatch.setattr(w, "_git", failing)
    with pytest.raises(subprocess.CalledProcessError):
        _write(root, run_dir, raw_dir)
    assert (root / "docs" / "data" / "waivers.yaml").read_bytes() == waivers_before


def test_a_failure_while_lowering_the_waiver_puts_it_back(tmp_path, monkeypatch):
    root, run_dir, raw_dir = _setup(tmp_path, waived=2)
    waivers_before = (root / "docs" / "data" / "waivers.yaml").read_bytes()
    import reading.write as w
    real = w.waiver_count.lower_count
    calls = []

    def second_fails(*a, **kw):
        calls.append(a)
        if len(calls) > 1:
            raise OSError("disk full")
        return real(*a, **kw)
    monkeypatch.setattr(w.waiver_count, "lower_count", second_fails)
    with pytest.raises(OSError):
        _write(root, run_dir, raw_dir)
    assert (root / "docs" / "data" / "waivers.yaml").read_bytes() == waivers_before


def test_an_uncommitted_act_is_refused_before_anything_changes(tmp_path):
    root, run_dir, raw_dir = _setup(tmp_path)
    act = root / "laws" / f"{SLUG}.md"
    act.write_text(act.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
    with pytest.raises(WriteRefused, match="uncommitted changes"):
        _write(root, run_dir, raw_dir)
    assert act.read_text(encoding="utf-8").endswith("hand edit\n")


def test_a_repaired_chrome_line_leaves_the_chrome_waiver_in_the_same_commit(tmp_path):
    # the page's own chrome is dropped by the reading (ruling 9); the old file carried it, so the act was waived
    root, run_dir, raw_dir = _setup(tmp_path, old_body="# ЗАКОН ЗА ПРОБАТА\n\nДОБАВИ В МОИТЕ АКТОВЕ\n")
    wp = root / "docs" / "data" / "waivers.yaml"
    text = wp.read_text(encoding="utf-8")
    head = text.index("  acts:", text.index("\nchrome:\n"))
    end = text.index("\n", head)
    wp.write_text(text[:head] + f"  acts:\n    {SLUG}: 1" + text[end:], encoding="utf-8")
    _git(root, "commit", "-qam", "waive")
    _write(root, run_dir, raw_dir)
    assert f"{SLUG}:" not in wp.read_text(encoding="utf-8")
    assert "docs/data/waivers.yaml" in _git(root, "show", "--name-only", "--format=", "HEAD").split()


# --- the exceptions list and the Gazette as a source (step S1 of the plan of 31 October 2026) -----------------

def _list_with(root, slug, route="whole_act_from_material"):
    import source_exceptions as sx
    p = root / "docs" / "data" / "source-exceptions.yaml"
    sx.save(p, [sx.Entry(slug=slug, title="t", defect="dropped_section", source="dv_html", address="77", route=route,
                         evidence=[{"kind": "plan", "ref": "the test"}], state="listed", added="2026-10-31")])
    return p


def test_a_listed_act_is_refused_on_the_lexbg_path_by_name_in_the_write_path_and_at_the_gate(tmp_path):
    from corpus_gate import ListedActRefused, SourceRef, write_act
    root, run_dir, raw_dir = _setup(tmp_path)
    lst = _list_with(root, SLUG)
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    with pytest.raises(WriteRefused, match=f"{SLUG}: on the exceptions list \\(dropped_section; source dv_html, route whole_act_from_material\\)"):
        _write(root, run_dir, raw_dir)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before
    with pytest.raises(ListedActRefused, match=f"{SLUG} is on the exceptions list"):
        write_act(root / "laws" / f"{SLUG}.md", COMMITTED, "**Чл. 1.** Текст.", source=SourceRef("lexbg", "999"),
                  waivers_path=root / "docs" / "data" / "waivers.yaml", exceptions_path=lst)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before
    write_act(root / "laws" / f"{SLUG}.md", COMMITTED, "**Чл. 1.** Текст.", source=SourceRef("dv", "77"),
              waivers_path=root / "docs" / "data" / "waivers.yaml", exceptions_path=lst)   # another source: not the lex.bg path
    assert (root / "laws" / f"{SLUG}.md").read_bytes() != before
    _list_with(root, "drug-zakon")   # another act listed: this one passes
    _git(root, "checkout", "--", f"laws/{SLUG}.md")
    assert _write(root, run_dir, raw_dir).commit is not None


def test_lost_text_refuses_the_write_under_the_amended_ruling_7(tmp_path):
    # the page prints the heading of the additional provision with nothing under it and opens the final provisions at § 2 (FR-042)
    page = PAGE.replace('<div class="Article">Чл. 2. Законът влиза в сила от деня на обнародването му.</div>',
                        '<div class="Article">Чл. 2. Текст.</div><div class="Section">Допълнителна разпоредба</div>'
                        '<div class="Section">Заключителни разпоредби</div><div class="Article">§ 2. Законът влиза в сила.</div>')
    smap = {**MAP, 7: {"label": "provisions_heading"}, 8: {"label": "provisions_heading"}, 9: {"label": "paragraph_sign", "n": "2"},
            10: {"label": "drop", "note": "chrome"}}
    root, run_dir, raw_dir = _setup(tmp_path, page=page, smap=smap)
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    with pytest.raises(WriteRefused, match=r"lost text on the page \(empty_section, sign_start\).*route investigate \(D-076\)"):
        _write(root, run_dir, raw_dir)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before


DV_MATERIAL = """<html><body><div class="titleHead">Народно събрание</div><span class="mark">Брой 32 от 1.4.2026 г.</span>
<div style=" width: 100%;"><span>
<p style="text-align:center">УКАЗ № 139</p><p style="text-align:justify">Да се обнародва Законът за пробата.</p>
<p style="text-align:right">Министър на правосъдието: Име</p>
<p style="text-align:center">ЗАКОН</p><p style="text-align:center">за пробата</p>
<p style="text-align:center">Глава първа</p><p style="text-align:center">ОБЩИ ПОЛОЖЕНИЯ</p>
<p style="text-align:justify"><b>Чл. 1. </b>(1) Този закон урежда пробата.<br/>(2) Пробата е публична.</p>
<p style="text-align:justify"><b>Чл. 2. </b>Законът влиза в сила от деня на обнародването му.</p>
<p style="text-align:center">ДОПЪЛНИТЕЛНА РАЗПОРЕДБА</p>
<p style="text-align:justify"><b>§ 1. </b>По смисъла на този закон „проба“ е опит.</p>
<p style="text-align:justify">Законът е приет от 51-вото Народно събрание на 19 март 2026 г.</p>
<p style="text-align:right">Председател на Народното събрание: Име</p><p style="text-align:justify">1563</p>
</span></div></body></html>"""
DV_MAP = {0: {"label": "drop", "note": "decree"}, 1: {"label": "drop", "note": "decree"}, 2: {"label": "drop", "note": "decree"},
          3: {"label": "title"}, 4: {"label": "title"}, 5: {"label": "chapter_heading"}, 6: {"label": "chapter_heading"},
          7: {"label": "article_head", "n": "1"}, 8: {"label": "alinea", "n": "2"}, 9: {"label": "article_head", "n": "2"},
          10: {"label": "provisions_heading"}, 11: {"label": "paragraph_sign", "n": "1"}, 12: {"label": "adoption_formula"},
          13: {"label": "drop", "note": "signature"}, 14: {"label": "drop", "note": "number"}}


def _setup_dv(tmp_path):
    from reading.splitter import split_dv
    root, run_dir, raw_dir = _setup(tmp_path, old_body="# ЗАКОН ЗА ПРОБАТА\n\n**Чл. 1.** Стар текст.\n\n## Допълнителна разпоредба\n\n## Заключителни разпоредби\n\n**§ 2.** Стар.\n")
    _list_with(root, SLUG)
    cache = tmp_path / "cache"
    cache.mkdir()
    html = DV_MATERIAL.encode("utf-8")
    (cache / "77.html").write_bytes(html)
    act = split_dv(html)
    (run_dir / "blocks.json").write_text(json.dumps(act.to_dict(), ensure_ascii=False), encoding="utf-8")
    (run_dir / "map.json").write_text(json.dumps({str(k): v for k, v in DV_MAP.items()}, ensure_ascii=False), encoding="utf-8")
    md, *_ = ladder.evaluate(act, DV_MAP, [], SLUG)
    (run_dir / "staged.md").write_text(md, encoding="utf-8")
    (run_dir / "material.json").write_text(json.dumps({"id_mat": 77, "sha256": hashlib.sha256(html).hexdigest(), "fetched_at": "2026-10-31T10:00:00+00:00",
                                                       "issue_number": 32, "issue_year": 2026, "issue_date": "2026-04-01", "section_path": "Официален раздел / НАРОДНО СЪБРАНИЕ"}), encoding="utf-8")
    return root, run_dir, raw_dir, cache


def test_an_act_is_committed_from_a_gazette_material_with_the_gazette_frontmatter(tmp_path):
    from reading.write import DV_FUENTE
    root, run_dir, raw_dir, cache = _setup_dv(tmp_path)
    w = write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    assert w.commit_type == "reforma" and w.commit   # the material's issue row is new to the committed history (ruling 11)
    msg = _git(root, "log", "-1", "--format=%B")
    map_sha = hashlib.sha256((run_dir / "map.json").read_bytes()).hexdigest()
    for trailer in ("Source-Id: dv-77", "Source-Date: 2026-04-01", "Norm-Id: 999", f"Record-Id: {RUN}/{SLUG}/{map_sha[:12]}"):
        assert trailer in msg
    fm, body = _split_frontmatter((root / "laws" / f"{SLUG}.md").read_text(encoding="utf-8"))
    assert fm["fuente"] == DV_FUENTE == "dv.parliament.bg" and fm["identificador"] == "999" and fm["titulo"] == COMMITTED["titulo"]
    assert fm["amendment_history"] == [{"dv": "32/2026", "date": "2026-04-01"}] and fm["dv_issue"] == "32" and fm["dv_year"] == 2026
    assert fm["fecha_publicacion"] == fm["ultima_actualizacion"] == "2026-04-01" and fm["estado"] == "vigente" and fm["materia"] == COMMITTED["materia"]
    assert fm["provenance"]["base"] == {"source": "dv", "state": "promulgated", "material": 77, "issue": "32/2026", "issue_date": "2026-04-01",
                                        "material_sha256": hashlib.sha256((cache / "77.html").read_bytes()).hexdigest(), "fetched_at": "2026-10-31T10:00:00+00:00"}
    assert fm["provenance"]["record"]["map_sha256"] == map_sha and fm["provenance"]["omissions"] == []
    assert body.lstrip("\n").startswith("# ЗАКОН за пробата\n\n### Глава първа ОБЩИ ПОЛОЖЕНИЯ\n\n**Чл. 1.** (1)") and "**§ 1.** По смисъла" in body
    assert "УКАЗ" not in body and "Председател" not in body
    again = write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    assert again.commit_type == "unchanged"


def test_a_gazette_reading_that_does_not_hold_is_refused(tmp_path):
    root, run_dir, raw_dir, cache = _setup_dv(tmp_path)
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    (cache / "77.html").write_bytes((cache / "77.html").read_bytes() + b" ")
    with pytest.raises(WriteRefused, match="differs from the run's material.json"):
        write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    (run_dir / "material.json").unlink()
    with pytest.raises(WriteRefused, match="no material.json"):
        write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() == before and _git(root, "rev-list", "--count", "HEAD") == "1\n"


def test_a_gazette_write_is_held_to_the_entrys_route_address_and_history(tmp_path):
    import source_exceptions as sx
    root, run_dir, raw_dir, cache = _setup_dv(tmp_path)
    lst = root / "docs" / "data" / "source-exceptions.yaml"
    before = (root / "laws" / f"{SLUG}.md").read_bytes()
    sx.update(lst, SLUG, route="history")
    with pytest.raises(WriteRefused, match="listed with the route whole_act_from_material \\(the list says history\\)"):
        write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    sx.update(lst, SLUG, route="whole_act_from_material", address="78")
    with pytest.raises(WriteRefused, match="material 77 is not the entry's address 78"):
        write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    sx.update(lst, SLUG, address="77")
    committed = {**COMMITTED, "amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}, {"dv": "55/2026", "date": "2026-06-16"}], "ultima_actualizacion": "2026-06-16"}
    (root / "laws" / f"{SLUG}.md").write_text(render_act(committed, "# x\n"), encoding="utf-8")
    _git(root, "commit", "-qam", "amended")
    with pytest.raises(WriteRefused, match="holds 55/2026 after the material's issue 32/2026"):
        write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache)
    assert (root / "laws" / f"{SLUG}.md").read_bytes() != before and _git(root, "rev-list", "--count", "HEAD") == "2\n"
    (root / "laws" / f"{SLUG}.md").write_bytes(before)
    _git(root, "commit", "-qam", "back")
    assert write_staged(SLUG, run_dir, root=root, raw_dir=raw_dir, cache_dir=cache).commit


def test_lost_text_on_the_lexbg_path_lists_the_act_for_investigation(tmp_path):
    import source_exceptions as sx
    page = PAGE.replace('<div class="Article">Чл. 2. Законът влиза в сила от деня на обнародването му.</div>',
                        '<div class="Article">Чл. 2. Текст.</div><div class="Section">Допълнителна разпоредба</div>'
                        '<div class="Section">Заключителни разпоредби</div><div class="Article">§ 2. Законът влиза в сила.</div>')
    smap = {**MAP, 7: {"label": "provisions_heading"}, 8: {"label": "provisions_heading"}, 9: {"label": "paragraph_sign", "n": "2"}, 10: {"label": "drop", "note": "chrome"}}
    root, run_dir, raw_dir = _setup(tmp_path, page=page, smap=smap)
    lst = _list_with(root, "drug-zakon")
    with pytest.raises(WriteRefused, match="lost text"):
        _write(root, run_dir, raw_dir)
    e = sx.listed(SLUG, lst)
    assert e is not None and e.route == "investigate" and e.source == "unknown" and e.address == "unknown" and e.evidence[0]["kind"] == "audit"
    with pytest.raises(WriteRefused, match="on the exceptions list"):
        _write(root, run_dir, raw_dir)   # listed now: refused by name before anything else
