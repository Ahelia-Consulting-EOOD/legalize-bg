"""The act profiles (reading/profiles.py, step S3): the register's form, the layout counts, the pairing and the verdict form."""
import csv
import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from reading import profiles as P

PAGE = """<html><body><div id="chrome"><img src="https://lex.bg/assets/im/logo.png"></div>
<div class="boxi">
<div class="TitleDocument">ЗАКОН ЗА ПРОБАТА</div>
<div class="Heading">Глава първа.</div>
<div class="Heading">Глава първа.</div>
<div class="Heading">ОБЩИ ПОЛОЖЕНИЯ</div>
<div class="Article"><img src="https://lex.bg/assets/images/blaws1.gif"><img src="https://lex.bg/assets/images/blaws2.gif">Чл. 1. Първа разпоредба.</div>
<div class="Article">Чл. 1<sup>а</sup>. Втора разпоредба.<br>Продължение без номер.</div>
<div class="Article">(2) Алинея.<br>Още един ред без номер.</div>
<div class="Article">Чл. 2.SUP>1. Трета.</div>
<div class="Article">Приложение № 1 към чл. 2</div>
<table><tr><td>а</td><td>б</td></tr><tr><td>в</td><td>г</td></tr></table>
<div class="Article"><img src="/files/formula.png">Формула.</div>
</div></body></html>"""

NO_ACT = """<html><body><div id="menu"><img src="https://lex.bg/assets/im/logo.png"><table><tr><td>Новини</td></tr></table></div></body></html>"""


def test_era_from_the_publication_date():
    assert [P.era_of(d) for d in ("2026-04-01", "2003-01-03", "2002-12-31", "1989-01-01", "1988-12-31", None, "", "abcd")] == \
        ["html", "html", "pdf", "pdf", "pre1989", "unknown", "unknown", "unknown"]


def test_layout_counts_from_the_page_blocks():
    counts, has_act = P.layout_features(PAGE.encode("cp1251"))
    assert has_act
    assert counts == {"annex_headings": 1, "table_rows": 2, "images": 1, "unnumbered_paragraphs": 3,   # a table cell is not a paragraph
                      "superscript_numbers": 2, "repeated_headings": 1}
    counts, has_act = P.layout_features(NO_ACT.encode("cp1251"))
    assert not has_act


def test_source_column():
    assert P.source_of({"fuente": "lex.bg", "identificador": "'-14917630'"}) == "lexbg:-14917630"
    assert P.source_of({"fuente": "dv.parliament.bg", "identificador": "2137259781", "provenance": {"base": {"material": 242220}}}) == "dv:242220"
    assert P.source_of({"fuente": "strategy.bg", "identificador": "1"}).startswith("strategy.bg:")


def _corpus(tmp_path: Path, acts: dict[str, dict]) -> Path:
    for cat in P.CATEGORIES:
        (tmp_path / cat).mkdir()
    for slug, (cat, fm) in acts.items():
        (tmp_path / cat / f"{slug}.md").write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True) + "---\n\n# x\n", encoding="utf-8")
    return tmp_path


def _catalog(tmp_path: Path, slugs: list[str]) -> Path:
    db = tmp_path / "catalog.db"
    con = sqlite3.connect(db)
    con.execute("create table laws (law_id text primary key, doc_id integer, title text not null, category text not null)")
    con.executemany("insert into laws values (?, 1, 't', 'laws')", [(s,) for s in slugs])
    con.commit()
    con.close()
    return db


def test_build_check_and_the_register_file(tmp_path):
    root = _corpus(tmp_path, {
        "zakon-za-probata": ("laws", {"titulo": "ЗАКОН ЗА ПРОБАТА", "identificador": "11", "rango": "закон", "fecha_publicacion": "2004-01-01", "fuente": "lex.bg"}),
        "2137254803": ("ordinances", {"titulo": "", "identificador": "2137254803", "rango": "наредба", "fecha_publicacion": None, "fuente": "lex.bg"}),
        "ukaz": ("regulations", {"titulo": "УКАЗ", "identificador": "-883197400", "rango": "правилник", "fecha_publicacion": "1974-05-01", "fuente": "strategy.bg"}),
    })
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "11.html").write_bytes(PAGE.encode("cp1251"))
    (raw / "2137254803.html").write_bytes(NO_ACT.encode("cp1251"))
    (root / P.COVERAGE_MAP).mkdir(parents=True)
    (root / P.COVERAGE_MAP / "acts-summary.csv").write_text("law_id,candidate_grade\nukaz,C\nzakon-za-probata,B-pending\n", encoding="utf-8")
    rows = P.build(root, raw)
    by = {r["slug"]: r for r in rows}
    assert [r["slug"] for r in rows] == ["2137254803", "ukaz", "zakon-za-probata"]
    assert by["zakon-za-probata"]["page_holds_act"] == "yes" and by["zakon-za-probata"]["annex_headings"] == 1 and by["zakon-za-probata"]["era"] == "html"
    assert by["zakon-za-probata"]["candidate_grade"] == "B-pending" and by["zakon-za-probata"]["source"] == "lexbg:11"
    assert by["2137254803"]["page_holds_act"] == "no" and by["2137254803"]["era"] == "unknown" and by["2137254803"]["candidate_grade"] == "none"
    assert all(by["2137254803"][k] == 0 for k in P.COUNTS)
    assert by["ukaz"]["page_holds_act"] == "no_page" and by["ukaz"]["era"] == "pre1989" and by["ukaz"]["candidate_grade"] == "C"
    out = tmp_path / "act-profiles.csv"
    P.write_register(rows, out)
    loaded = P.load_register(out)
    assert tuple(loaded[0]) == P.COLUMNS and len(loaded) == 3
    db = _catalog(tmp_path, ["zakon-za-probata", "2137254803", "ukaz"])
    assert P.check(loaded, root, db) == []
    # every departure from the form is named
    bad = [dict(r) for r in loaded]
    bad[0]["kind"] = "указ"
    bad[1]["table_rows"] = "3"            # a count on a page without an act
    bad[2]["source"] = "apis"
    bad[2]["known_defects_s2"] = "Dropped Section"
    problems = P.check(bad, root, _catalog(tmp_path / "c2", []) if (tmp_path / "c2").mkdir() is None else None)
    assert any("kind 'указ'" in p for p in problems) and any("table_rows 3 on a page without an act" in p for p in problems)
    assert any("source 'apis'" in p for p in problems) and any("known_defects_s2" in p for p in problems)
    assert sum("in the catalog without a row" in p for p in problems) == 0 and sum("row without a catalog entry" in p for p in problems) == 3
    # a missing row, a row too many, a duplicate
    problems = P.check(loaded[:2] + [dict(loaded[1], slug="extra")] + [dict(loaded[1])], root, db)
    assert any("zakon-za-probata: corpus file in laws without a row" in p for p in problems)
    assert any("extra: row without a corpus file" in p for p in problems) and any("ukaz: 2 rows" in p for p in problems)
    (out).write_text("slug,kind\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        P.load_register(out)


def test_candidates_share_words_or_the_number_with_the_year():
    titles = [
        {"id_mat": 1, "issue": "3/2004", "date": "2004-01-13", "title": "Наредба за отменяне на Наредба № 1 от 1991 г. за труда", "target": "Наредба № 1 от 1991 г. за труда", "words": ["труда"], "key": {"type": "наредба", "number": "1", "year": 1991}},
        {"id_mat": 2, "issue": "4/2004", "date": "2004-01-16", "title": "Наредба за отменяне на Наредба № 1 за условията за ветеринарния контрол", "target": "Наредба № 1 за условията за ветеринарния контрол", "words": ["ветеринарния", "контрол", "условията"], "key": {"type": "наредба", "number": "1", "year": None}},
        {"id_mat": 3, "issue": "5/2004", "date": "2004-01-20", "title": "Закон за отмяна на Закона за гражданското въздухоплаване", "target": "Закона за гражданското въздухоплаване", "words": ["въздухоплаване", "гражданското"], "key": None},
        {"id_mat": 4, "issue": "6/2004", "date": "2004-01-23", "title": "Закон за отмяна на Закона за гражданското състояние", "target": "Закона за гражданското състояние", "words": ["гражданското", "състояние"], "key": None},
    ]
    act = P.act_facts("naredba-1-za-zapasite", "ordinances", {"titulo": "НАРЕДБА № 1 ЗА НЕПРИКОСНОВЕНИТЕ ЗАПАСИ", "rango": "наредба", "fecha_publicacion": "1981-03-01", "estado": "vigente",
                                                             "amendment_history": [{"dv": "20/1981", "date": "1981-03-01"}]})
    assert act["key"] == {"type": "наредба", "number": "1", "year": 1981} and act["last_amendments"] == [{"dv": "20/1981", "date": "1981-03-01"}]
    c = P.candidates_for(act, titles)
    assert [x["id_mat"] for x in c] == [2] and c[0]["same_number"] and c[0]["shared_words"] == []   # 1991 is another наредба № 1
    law = P.act_facts("zakon-za-grazhdanskoto-vazduhoplavane", "laws", {"titulo": "ЗАКОН ЗА ГРАЖДАНСКОТО ВЪЗДУХОПЛАВАНЕ", "rango": "закон", "fecha_publicacion": "1972-12-01"})
    c = P.candidates_for(law, titles)
    assert [(x["id_mat"], x["score"]) for x in c] == [(3, 1.0), (4, 0.5)]   # one shared word pairs when the title has two words
    long = P.act_facts("x", "laws", {"titulo": "ЗАКОН ЗА УРЕЖДАНЕ НА ПРАВАТА НА ЛИЦАТА С ГРАЖДАНСКО СЪСТОЯНИЕ", "rango": "закон"})
    assert P.candidates_for(long, titles) == []   # one shared word is not enough for a long title
    assert P.same_number({"type": "наредба", "number": "1", "year": None}, {"type": "наредба", "number": "1", "year": 1991})
    assert not P.same_number({"type": "закон", "number": "1", "year": None}, {"type": "наредба", "number": "1", "year": None})


def _pairing_run(tmp_path: Path) -> tuple[Path, Path]:
    root = _corpus(tmp_path, {
        "zakon-za-a": ("laws", {"titulo": "ЗАКОН ЗА АВТОРСКИТЕ ПРАВА", "identificador": "1", "rango": "закон", "fecha_publicacion": "1951-01-01", "estado": "vigente", "fuente": "lex.bg"}),
        "zakon-za-b": ("laws", {"titulo": "ЗАКОН ЗА БАНКИТЕ", "identificador": "2", "rango": "закон", "fecha_publicacion": "1980-01-01", "estado": "derogado", "fuente": "lex.bg"}),
        "zakon-za-c": ("laws", {"titulo": "ЗАКОН ЗА ВОДИТЕ", "identificador": "3", "rango": "закон", "fecha_publicacion": "2000-01-01", "estado": "vigente", "fuente": "lex.bg"}),
    })
    (root / P.COVERAGE_MAP).mkdir(parents=True)
    (root / P.COVERAGE_MAP / "acts-summary.csv").write_text("law_id,candidate_grade\nzakon-za-a,C\nzakon-za-b,B-pending\nzakon-za-c,B-pending\n", encoding="utf-8")
    (root / P.COVERAGE_MAP / "predecessor-materials.csv").write_text("id_mat,law_id\n99,zakon-za-c\n", encoding="utf-8")
    mats = tmp_path / "materials.jsonl"
    rows = [
        {"status": "ok", "id_mat": 10, "issue_year": 2004, "issue_number": 7, "issue_date": "2004-01-27", "title": "Закон за отмяна на Закона за авторските права"},
        {"status": "ok", "id_mat": 11, "issue_year": 2005, "issue_number": 8, "issue_date": "2005-01-28", "title": "Закон за изменение на Закона за банките"},
        {"status": "ok", "id_mat": 99, "issue_year": 2006, "issue_number": 9, "issue_date": "2006-01-29", "title": "Закон за отмяна на Закона за водите"},
        {"status": "empty", "id_mat": None, "issue_year": 1995, "issue_number": 1},
    ]
    mats.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    run = tmp_path / "data" / "runs" / "t"
    return root, mats, run


def test_pairing_writes_the_facts_and_the_call_tasks(tmp_path):
    root, mats, run = _pairing_run(tmp_path)
    s = P.pair(root, run, mats, per_call=1)
    assert s["acts"] == 2 and s["repeal_titles"] == 1 and s["calls"] == ["call-01", "call-02"] and s["with_candidates"] == 1
    facts = json.loads((run / "pairings" / "zakon-za-a.json").read_text(encoding="utf-8"))
    assert [c["id_mat"] for c in facts["candidates"]] == [10] and facts["estado_lexbg"] == "vigente"
    task = (run / "calls" / "call-01.md").read_text(encoding="utf-8")
    assert "## zakon-za-a" in task and "material 10, ДВ 7/2004" in task and "Read only this file" in task and "call-01-answer.yaml" in task
    assert "none share words" in (run / "calls" / "call-02.md").read_text(encoding="utf-8")


def test_the_verdict_form_is_checked_and_the_list_carries_every_pairing(tmp_path):
    root, mats, run = _pairing_run(tmp_path)
    P.pair(root, run, mats, per_call=2)
    answer = run / "calls" / "call-01-answer.yaml"
    answer.write_text(yaml.safe_dump({"zakon-za-a": {"verdict": "repealed", "repealed_by": 10, "evidence": "the title names the act"}}, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="zakon-za-b: not answered"):
        P.collect(run, "call-01")
    assert not (run / "verdicts").exists()
    bad = {"zakon-za-a": {"verdict": "repealed", "repealed_by": 11, "evidence": "x"},
           "zakon-za-b": {"verdict": "in_force", "repealed_by": 10, "evidence": ""}, "zakon-za-z": {"verdict": "unknown", "repealed_by": None, "evidence": "y"}}
    problems = P.check_answer(bad, [json.loads((run / "pairings" / f"{s}.json").read_text(encoding="utf-8")) for s in ("zakon-za-a", "zakon-za-b")])
    assert problems == ["zakon-za-z: not in the task", "zakon-za-a: repealed_by 11 is not a candidate material of this act",
                        "zakon-za-b: repealed_by given with the verdict in_force", "zakon-za-b: evidence missing"]
    assert P.check_answer([], []) == ["the answer is not a mapping"]
    assert P.check_answer({"zakon-za-a": {"verdict": "maybe"}}, [{"slug": "zakon-za-a", "candidates": []}]) == ["zakon-za-a: keys outside the form"]
    answer.write_text(yaml.safe_dump({"zakon-za-a": {"verdict": "repealed", "repealed_by": 10, "evidence": "the title names the act"},
                                      "zakon-za-b": {"verdict": "unknown", "repealed_by": None, "evidence": "lex.bg says derogado, no title"}}, allow_unicode=True), encoding="utf-8")
    got = P.collect(run, "call-01")
    assert got["verdicts"] == {"repealed": 1, "unknown": 1}
    v = json.loads((run / "verdicts" / "zakon-za-a.json").read_text(encoding="utf-8"))
    assert v["repealed_by"]["id_mat"] == 10 and v["call"] == "call-01"
    out = root / "docs" / "data" / "pre-archive-acts-in-force.yaml"
    assert P.in_force_list(run, out) == {"acts": 2, "verdicts": {"repealed": 1, "unknown": 1}, "unanswered": []}
    assert P.check_in_force_list(out, run) == []
    doc = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert doc["entries"][0]["repealed_by"]["material"] == 10 and doc["entries"][1]["repealed_by"] is None
    assert (run.parents[2] / doc["entries"][0]["verdict_file"]).exists()
    (run / "verdicts" / "zakon-za-b.json").unlink()
    assert P.in_force_list(run, out)["unanswered"] == ["zakon-za-b"]
    assert P.check_in_force_list(out, run) == ["1 act(s) unanswered"]
    doc["entries"][0]["verdict"] = "in_force"
    out.write_text(yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")
    assert any("repealed_by does not match" in p for p in P.check_in_force_list(out, run))
