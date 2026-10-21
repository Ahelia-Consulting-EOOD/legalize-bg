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


def _setup(tmp_path, *, tail=".", committed=None, old_body="# ЗАКОН ЗА ПРОБАТА\n\n**Чл. 1.** Стар текст.\n", waived=None):
    root = tmp_path / "repo"
    (root / "laws").mkdir(parents=True)
    (root / "docs" / "data").mkdir(parents=True)
    waivers = (REPO / "docs" / "data" / "waivers.yaml").read_text(encoding="utf-8")
    if waived is not None:
        waivers = waivers.replace("  acts:\n    administrativnoprotsesualen-kodeks: 1\n",
                                  f"  acts:\n    administrativnoprotsesualen-kodeks: 1\n    {SLUG}: {waived}\n")
    (root / "docs" / "data" / "waivers.yaml").write_text(waivers, encoding="utf-8")
    (root / "laws" / f"{SLUG}.md").write_text(render_act(committed or COMMITTED, old_body), encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "user.email", "t@t")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "seed")

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw = PAGE.replace("{tail}", tail).encode("cp1251")
    (raw_dir / "999.html").write_bytes(raw)
    row = {"doc_id": 999, "slug": SLUG, "category": "laws", "url": "u", "fetched_at": "2026-10-21T00:00:00+00:00",
           "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "status": "ok"}
    (raw_dir / "manifest.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    run_dir = root / "data" / "runs" / RUN / SLUG
    run_dir.mkdir(parents=True)
    act = split_lexbg(raw)
    (run_dir / "blocks.json").write_text(json.dumps(act.to_dict(), ensure_ascii=False), encoding="utf-8")
    (run_dir / "map.json").write_text(json.dumps({str(k): v for k, v in MAP.items()}, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report-round0.json").write_text("{}", encoding="utf-8")
    md, *_ = ladder.evaluate(act, MAP, [], SLUG)
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
    p.write_text("other:\n  acts:\n    a: 1\ntag_remnants:\n  ruling: r\n  acts:\n    a: 4\n    b: 2\nlast:\n  acts:\n    c: 1\n", encoding="utf-8")
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
