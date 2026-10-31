"""The act profiles (reading/profiles.py, step S3): the register's form, the layout counts, the pairing and the verdict form."""
import gzip
import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from reading import profiles as P

PAGE = """<html><body><div id="chrome"><img src="https://lex.bg/assets/im/logo.png"></div>
<div class="content">
<div class="TitleDocument">ЗАКОН ЗА ПРОБАТА</div>
<div class="PreHistory">В сила от 01.01.2004 г.</div>
<div class="HistoryOfDocument">Обн. ДВ. бр. 1 от 3 Януари 2004г., изм. ДВ. бр. 5 от 2005г.<table><tr><td>x</td></tr></table><sup>h</sup></div>
<div class="boxi"><img src="/files/ad.png"><table><tr><td>реклама</td></tr></table><sup>a</sup>Реклама без номер</div>
<div class="Heading">Глава първа.</div>
<div class="Heading">Глава първа. ОБЩИ ПОЛОЖЕНИЯ</div>
<div class="Heading">Раздел I</div>
<div class="Article"><img src="https://lex.bg/assets/images/blaws1.gif"><img src="https://lex.bg/assets/images/blaws2.gif">Чл. 1. Първа разпоредба.</div>
<div class="Article">Чл. 1<sup>а</sup>. Втора разпоредба.<br>Продължение без номер.</div>
<div class="Article">(2) Алинея.<br>Още един ред без номер.</div>
<div class="Article">Чл. 2.SUP>1. Трета.</div>
<div class="Article">Вж. Приложение № 1 за формата.</div>
<div class="Heading">Приложение № 1 към чл. 2</div>
<table><tr><td>а<br>втори ред на клетката</td><td>б</td></tr><tr><td><p>в</p></td><td>г</td></tr></table>
<div class="Article"><img src="/files/formula.png">Формула.</div>
<div class="Article">Таблица за съответствие между разпоредбите на директивата</div>
<div class="Article">Релевантни актове от Европейското законодателство</div>
<div class="Article">Директива без номер</div>
<div class="Article"><img src="/files/eu.png"></div>
</div></body></html>"""

NO_ACT = """<html><body><div id="menu"><img src="https://lex.bg/assets/im/logo.png"><table><tr><td>Новини</td></tr></table></div></body></html>"""


def test_era_from_the_publication_date():
    assert [P.era_of(d) for d in ("2026-04-01", "2003-01-03", "2002-12-31", "1989-01-01", "1988-12-31", None, "", "abcd")] == \
        ["html", "html", "pdf", "pdf", "pre1989", "unknown", "unknown", "unknown"]


def test_layout_counts_from_the_act_blocks_only():
    counts, has_act = P.layout_features(PAGE.encode("cp1251"))
    assert has_act
    # the boxi subtree and the history line are left out (their row, image, sup and paragraph), the tail after the EU-acts
    # line is left out (its paragraph and image), the correspondence-table line is chrome, a cross-reference sentence is no
    # annex heading but an unnumbered paragraph, a cell's second line is a cell line, and the heading number printed twice
    # (once bare, once with its title) is one repeat; the superscripts are one tag and one leaked remnant
    assert counts == {"annex_headings": 1, "table_rows": 2, "images": 1, "unnumbered_paragraphs": 4,
                      "superscript_numbers": 2, "repeated_headings": 1}
    counts, has_act = P.layout_features(NO_ACT.encode("cp1251"))
    assert not has_act


def test_source_column():
    assert P.source_of({"fuente": "lex.bg", "identificador": "'-14917630'"}) == "lexbg:-14917630"
    assert P.source_of({"fuente": "dv.parliament.bg", "identificador": "2137259781", "provenance": {"base": {"material": 242220}}}) == "dv:242220"
    assert P.source_of({"fuente": "strategy.bg", "identificador": "1"}).startswith("strategy.bg:")


def _corpus(tmp_path: Path, acts: dict[str, dict]) -> Path:
    for cat in P.CATEGORIES:
        (tmp_path / cat).mkdir(exist_ok=True)
    for slug, (cat, fm) in acts.items():
        (tmp_path / cat / f"{slug}.md").write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True) + "---\n\n# x\n", encoding="utf-8")
    return tmp_path


def _catalog(tmp_path: Path, slugs: list[str]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
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
    # every departure from the form is named, and a well-formed value that differs from its source is refused
    bad = [dict(r) for r in loaded]
    bad[0]["kind"] = "указ"
    bad[0]["table_rows"] = "3"            # a count on a page without an act
    bad[1]["era"] = "html"                # well-formed, wrong: the file says 1974
    bad[1]["candidate_grade"] = "B-pending"
    bad[2]["source"] = "apis"
    bad[2]["known_defects_s2"] = "Dropped Section"
    bad[2]["images"] = "²"                # isdigit() is true for it; the check refuses it instead of crashing
    problems = P.check(bad, root, _catalog(tmp_path / "c2", []))
    assert any("kind 'указ'" in p for p in problems) and any("table_rows 3 on a page without an act" in p for p in problems)
    assert any("era 'html' differs from its source 'pre1989'" in p for p in problems) and any("candidate_grade 'B-pending' differs from its source 'C'" in p for p in problems)
    assert any("source 'apis'" in p for p in problems) and any("known_defects_s2" in p for p in problems) and any("images '²' is not a count" in p for p in problems)
    assert sum("in the catalog without a row" in p for p in problems) == 0 and sum("row without a catalog entry" in p for p in problems) == 3
    # a missing row, a row too many, a duplicate
    problems = P.check(loaded[:2] + [dict(loaded[1], slug="extra")] + [dict(loaded[1])], root, db)
    assert any("zakon-za-probata: corpus file in laws without a row" in p for p in problems)
    assert any("extra: row without a corpus file" in p for p in problems) and any("ukaz: 2 rows" in p for p in problems)
    out.write_text("slug,kind\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        P.load_register(out)


def test_what_a_title_repeals():
    assert P.repeal_target("Наредба за отменяне на Наредба № 1 от 1991 г. за труда") == "Наредба № 1 от 1991 г. за труда"
    assert P.repeal_target("Постановление № 5 от 2004 г. за изменение на Наредбата за X и за отмяна на Правилника за прилагане на Закона за Y") == \
        "Правилника за прилагане на Закона за Y"   # the repeal verb after an amending verb
    assert P.repeal_target("Решение за отмяна на лятната ваканция на Народното събрание") is None   # names no act
    assert P.repeal_target("Закон за изменение и допълнение на Закона за водите") is None
    assert P.repeal_target("Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове") is None   # a general decree
    assert P._GENERAL_REPEAL.search("Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове")
    assert P._GENERAL_REPEAL.search("Наредба за отменяне на наредби на министъра на земеделието")
    assert not P._GENERAL_REPEAL.search("Наредба за отменяне на Наредба № 1 за труда")


def test_lexbg_history_and_its_repeal_marker():
    h, m = P.lexbg_history(PAGE.encode("cp1251"))
    assert h.startswith("Обн. ДВ. бр. 1 от 3 Януари 2004г.") and m is None
    page = PAGE.replace("изм. ДВ. бр. 5 от 2005г.", "отм. ДВ. бр. 7 от 24 Януари 2006г.")
    h, m = P.lexbg_history(page.encode("cp1251"))
    assert m == "отм. ДВ. бр. 7 от 24 Януари 2006г."
    assert P.lexbg_history(None) == ("", None)


def test_candidates_share_words_or_the_number_with_the_year_and_read_the_general_decrees():
    titles = [
        {"id_mat": 1, "issue": "3/2004", "date": "2004-01-13", "title": "Наредба за отменяне на Наредба № 1 от 1991 г. за труда", "target": "Наредба № 1 от 1991 г. за труда", "words": ["труда"], "key": {"type": "наредба", "number": "1", "year": 1991}},
        {"id_mat": 2, "issue": "4/2004", "date": "2004-01-16", "title": "Наредба за отменяне на Наредба № 1 за условията за ветеринарния контрол", "target": "Наредба № 1 за условията за ветеринарния контрол", "words": ["ветеринарния", "контрол", "условията"], "key": {"type": "наредба", "number": "1", "year": None}},
        {"id_mat": 3, "issue": "5/2004", "date": "2004-01-20", "title": "Закон за отмяна на Закона за гражданското въздухоплаване", "target": "Закона за гражданското въздухоплаване", "words": ["въздухоплаване", "гражданското"], "key": None},
        {"id_mat": 4, "issue": "6/2004", "date": "2004-01-23", "title": "Закон за отмяна на Закона за гражданското състояние", "target": "Закона за гражданското състояние", "words": ["гражданското", "състояние"], "key": None},
    ]
    general = [{"id_mat": 9, "issue": "30/2005", "date": "2005-04-08", "title": "Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове",
                "lines": ["Отменят се:", "1. Правилник за устройство на електрическите уредби, приет с ПМС № 49 от 1977 г.", "2. Наредба № 1 за неприкосновените запаси на морските кораби (ДВ, бр. 20 от 1981 г.)"]}]
    act = P.act_facts("naredba-1-za-zapasite", "ordinances", {"titulo": "НАРЕДБА № 1 ЗА НЕПРИКОСНОВЕНИТЕ ЗАПАСИ", "rango": "наредба", "fecha_publicacion": "1981-03-01",
                                                             "amendment_history": [{"dv": "20/1981", "date": "1981-03-01"}]})
    assert act["key"] == {"type": "наредба", "number": "1", "year": 1981} and act["last_amendments"] == [{"dv": "20/1981", "date": "1981-03-01"}]
    c = P.candidates_for(act, titles, general)
    assert [(x["id_mat"], x["kind"]) for x in c] == [(9, "body_line"), (2, "title")]   # 1991 is another наредба № 1; the decree's line names this one
    assert c[0]["line"].startswith("2. Наредба № 1 за неприкосновените") and c[0]["shared_words"] == ["запаси", "неприкосновените"] and c[0]["same_number"]
    law = P.act_facts("zakon-za-grazhdanskoto-vazduhoplavane", "laws", {"titulo": "ЗАКОН ЗА ГРАЖДАНСКОТО ВЪЗДУХОПЛАВАНЕ", "rango": "закон", "fecha_publicacion": "1972-12-01"})
    c = P.candidates_for(law, titles)
    assert [(x["id_mat"], x["score"]) for x in c] == [(3, 1.0), (4, 0.5)]   # one shared word pairs when the title has two words
    long = P.act_facts("x", "laws", {"titulo": "ЗАКОН ЗА УРЕЖДАНЕ НА ПРАВАТА НА ЛИЦАТА С ГРАЖДАНСКО СЪСТОЯНИЕ", "rango": "закон"})
    assert P.candidates_for(long, titles) == []   # one shared word is not enough for a long title
    marked = dict(law, lexbg_repeal_marker="отм. ДВ. бр. 7 от 24 Януари 2006г.")
    c = P.candidates_for(marked, titles)
    assert c[0]["kind"] == "lexbg_marker" and c[0]["id_mat"] == 0 and [x["id_mat"] for x in c[1:]] == [3, 4]
    assert P.same_number({"type": "наредба", "number": "1", "year": None}, {"type": "наредба", "number": "1", "year": 1991})
    assert not P.same_number({"type": "закон", "number": "1", "year": None}, {"type": "наредба", "number": "1", "year": None})


def _pairing_run(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = _corpus(tmp_path, {
        "zakon-za-a": ("laws", {"titulo": "ЗАКОН ЗА АВТОРСКИТЕ ПРАВА", "identificador": "1", "rango": "закон", "fecha_publicacion": "1951-01-01", "estado": "vigente", "fuente": "lex.bg"}),
        "zakon-za-b": ("laws", {"titulo": "ЗАКОН ЗА БАНКИТЕ", "identificador": "2", "rango": "закон", "fecha_publicacion": "1980-01-01", "estado": "vigente", "fuente": "lex.bg"}),
        "zakon-za-c": ("laws", {"titulo": "ЗАКОН ЗА ВОДИТЕ", "identificador": "3", "rango": "закон", "fecha_publicacion": "2000-01-01", "estado": "vigente", "fuente": "lex.bg"}),
    })
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "2.html").write_bytes(PAGE.replace("изм. ДВ. бр. 5 от 2005г.", "отм. ДВ. бр. 7 от 24 Януари 2006г.").encode("cp1251"))
    (root / P.COVERAGE_MAP).mkdir(parents=True)
    (root / P.COVERAGE_MAP / "acts-summary.csv").write_text("law_id,candidate_grade\nzakon-za-a,C\nzakon-za-b,B-pending\nzakon-za-c,B-pending\n", encoding="utf-8")
    (root / P.COVERAGE_MAP / "predecessor-materials.csv").write_text("id_mat,law_id\n99,zakon-za-c\n", encoding="utf-8")
    with gzip.open(root / P.COVERAGE_MAP / "unresolved.csv.gz", "wt", encoding="utf-8") as f:
        f.write("kind,law_id,dv_year,dv_number,title\nunattributed_material,,2004,7,Закон за отмяна на Закона за авторските права\n"
                "unattributed_material,,2004,8,Закон за отмяна на Закона за старите бани\nunattributed_material,,2005,8,Закон за изменение на Закона за банките\n")
    mats = tmp_path / "materials.jsonl"
    rows = [
        {"status": "ok", "id_mat": 10, "issue_year": 2004, "issue_number": 7, "issue_date": "2004-01-27", "title": "Закон за отмяна на Закона за авторските права"},
        {"status": "ok", "id_mat": 11, "issue_year": 2005, "issue_number": 8, "issue_date": "2005-01-28", "title": "Закон за изменение на Закона за банките"},
        {"status": "ok", "id_mat": 12, "issue_year": 2005, "issue_number": 9, "issue_date": "2005-01-29", "title": "Постановление № 65 от 8 април 2005 г. за отменяне на нормативни актове"},
        {"status": "ok", "id_mat": 99, "issue_year": 2006, "issue_number": 9, "issue_date": "2006-01-29", "title": "Закон за отмяна на Закона за водите"},
        {"status": "empty", "id_mat": None, "issue_year": 1995, "issue_number": 1},
    ]
    mats.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    run = tmp_path / "data" / "runs" / "t"
    return root, mats, run


BODY = '<html><body><div style=" width: 100%;"><p>Отменят се:</p><p>1. Законът за банките (ДВ, бр. 1 от 1980 г.)</p></div></body></html>'


def test_pairing_writes_the_facts_the_decree_bodies_and_the_call_tasks(tmp_path):
    root, mats, run = _pairing_run(tmp_path)
    fetched = []

    def fetch(i):
        fetched.append(i)
        return BODY
    s = P.pair(root, run, mats, per_call=1, raw_dir=tmp_path / "raw", fetch=fetch)
    assert fetched == [12] and s["acts"] == 2 and s["repeal_titles"] == 1 and s["general_repeal_decrees"] == 1 and s["with_lexbg_marker"] == 1
    assert s["calls"] == {"call-01": ["zakon-za-a"], "call-02": ["zakon-za-b"]} and s["with_candidates"] == 2
    a = json.loads((run / "pairings" / "zakon-za-a.json").read_text(encoding="utf-8"))
    assert [c["id_mat"] for c in a["candidates"]] == [10] and a["lexbg_history"] == "" and "estado" not in a
    b = json.loads((run / "pairings" / "zakon-za-b.json").read_text(encoding="utf-8"))
    assert [(c["id_mat"], c["kind"]) for c in b["candidates"]] == [(0, "lexbg_marker"), (12, "body_line")] and b["lexbg_repeal_marker"].startswith("отм. ДВ. бр. 7")
    task = (run / "calls" / "call-02.md").read_text(encoding="utf-8")
    assert "## zakon-za-b" in task and "0 (lex.bg's own repeal marker)" in task and "a line of the general repeal decree" in task and "Законът за банките" in task
    assert "Read only this file" in task and "call-02-answer.yaml" in task and "`unknown` otherwise" in task
    rec = json.loads((run / "repeal-titles-reconciliation.json").read_text(encoding="utf-8"))
    assert rec["map_rows"] == 2 and rec["map_rows_in_our_set"] == 1 and rec["map_rows_missing"][0]["title"] == "Закон за отмяна на Закона за старите бани"


def test_the_verdict_form_is_checked_and_the_list_carries_every_pairing(tmp_path):
    root, mats, run = _pairing_run(tmp_path)
    P.pair(root, run, mats, per_call=2, raw_dir=tmp_path / "raw", fetch=lambda i: BODY)
    answer = run / "calls" / "call-01-answer.yaml"
    answer.write_text(yaml.safe_dump({"zakon-za-a": {"verdict": "repealed", "repealed_by": 10, "evidence": "the title names the act"}}, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="zakon-za-b: not answered"):
        P.collect(run, "call-01")
    assert not (run / "verdicts").exists()
    with pytest.raises(ValueError, match="not a call of this pairing"):
        P.collect(run, "call-09")
    batch = [json.loads((run / "pairings" / f"{s}.json").read_text(encoding="utf-8")) for s in ("zakon-za-a", "zakon-za-b")]
    bad = {"zakon-za-a": {"verdict": "repealed", "repealed_by": 11, "evidence": "x"},
           "zakon-za-b": {"verdict": "in_force", "repealed_by": 10, "evidence": ""}, "zakon-za-z": {"verdict": "unknown", "repealed_by": None, "evidence": "y"}}
    assert P.check_answer(bad, batch) == ["zakon-za-z: not in the task", "zakon-za-a: repealed_by 11 is not a candidate of this act",
                                          "zakon-za-b: repealed_by given with the verdict in_force", "zakon-za-b: evidence missing"]
    assert P.check_answer({"zakon-za-b": {"verdict": "repealed", "repealed_by": True, "evidence": "x"}}, batch[1:]) == ["zakon-za-b: repealed_by True is not a candidate of this act"]
    assert P.check_answer([], []) == ["the answer is not a mapping"]
    assert P.check_answer({"zakon-za-a": {"verdict": "maybe"}}, [{"slug": "zakon-za-a", "candidates": []}]) == ["zakon-za-a: keys outside the form"]
    answer.write_text(yaml.safe_dump({"zakon-za-a": {"verdict": "unknown", "repealed_by": None, "evidence": "the title names a same-titled predecessor; the history ends in 1951"},
                                      "zakon-za-b": {"verdict": "repealed", "repealed_by": 0, "evidence": "lex.bg's history line carries the repeal marker"}}, allow_unicode=True), encoding="utf-8")
    got = P.collect(run, "call-01")
    assert got["verdicts"] == {"unknown": 1, "repealed": 1}
    v = json.loads((run / "verdicts" / "zakon-za-b.json").read_text(encoding="utf-8"))
    assert v["repealed_by"]["kind"] == "lexbg_marker" and v["call"] == "call-01"
    # a task whose acts are not the ones the pairing assigned is refused
    task = run / "calls" / "call-01.md"
    task.write_text(task.read_text(encoding="utf-8").replace("## zakon-za-a", "## zakon-za-x"), encoding="utf-8")
    with pytest.raises(ValueError, match="not the ones the pairing assigned"):
        P.collect(run, "call-01")
    out = root / "docs" / "data" / "pre-archive-acts-in-force.yaml"
    assert P.in_force_list(run, out) == {"acts": 2, "verdicts": {"unknown": 1, "repealed": 1}, "unanswered": []}
    assert P.check_in_force_list(out, run) == []
    doc = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert doc["limits"] == P.LIMITS and doc["entries"][0]["repealed_by"] is None and doc["entries"][1]["repealed_by"]["material"] == 0
    assert (run.parents[2] / doc["entries"][1]["verdict_file"]).exists()
    # an edited list is refused, so is an empty one, so is a missing verdict
    doc["entries"][0]["verdict"] = "in_force"
    out.write_text(yaml.safe_dump(doc, allow_unicode=True), encoding="utf-8")
    assert "zakon-za-a: the entry differs from its verdict file" in P.check_in_force_list(out, run)
    out.write_text("", encoding="utf-8")
    assert P.check_in_force_list(out, run) == ["the list is empty or not a mapping with entries"]
    (run / "verdicts" / "zakon-za-b.json").unlink()
    assert P.in_force_list(run, out)["unanswered"] == ["zakon-za-b"]
    assert P.check_in_force_list(out, run) == ["1 act(s) unanswered"]
