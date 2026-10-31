"""Step S2 (reading/defects.py, reading/defect_kinds.py): the detector over raw pages, the materials, the calls, the verdicts, the register."""
import json
from pathlib import Path

import pytest
import yaml

import source_exceptions as sx
from reading import defect_kinds, defects
from reading.splitter import Block, split_lexbg

REPO = Path(__file__).resolve().parents[2]


def _blocks(texts):
    return [Block(i, t, "x") for i, t in enumerate(texts)]


# --- the two rules over blocks --------------------------------------------------------------------------------------

def test_additional_empty_fires_through_qualifiers_and_repeated_headings_and_once_per_page():
    base = ["Чл. 1. Текст.", "Допълнителна разпоредба", "Заключителни разпоредби", "§ 2. Влиза в сила."]
    assert [f["rule"] for f in defects.scan_blocks(_blocks(base))] == ["additional-empty", "paragraph-start-above-1"]
    qualified = ["Чл. 1. Текст.", "Допълнителни разпоредби", "(ОБН. - ДВ, БР. 1 ОТ 2020 Г.)", "Допълнителни разпоредби", "КЪМ ЗАКОНА ЗА ПРОБАТА",
                 "Преходни и Заключителни разпоредби", "§ 2. Влиза в сила."]
    # the second heading is the amending act's (its next line is КЪМ); the first is the act's own, and nothing of its own follows
    # it before the amending tail: no empty section between two own headings, no § of its own, no candidate
    out = defects.scan_blocks(_blocks(qualified))
    assert defects.own_tail(_blocks(qualified)) == (1, 3)
    assert [(f["rule"], f["block"], f.get("outside_own_tail")) for f in out] == [("additional-empty", 1, True), ("additional-empty", 3, True)]   # the closing heading is the amending act's
    # an own empty heading right before the own final heading, then the amending act's copy of that heading (naredba-8-2007's shape)
    own_pair = ["Чл. 1. x", "Допълнителна разпоредба", "Заключителна разпоредба", "Заключителна разпоредба", "КЪМ НАРЕДБА ЗА ИЗМЕНЕНИЕ", "§ 3. x"]
    out = defects.scan_blocks(_blocks(own_pair))
    assert defects.own_tail(_blocks(own_pair)) == (1, 3) and [(f["rule"], f["block"], f.get("outside_own_tail")) for f in out] == [("additional-empty", 1, None)]
    clean = ["Чл. 1. Текст.", "Допълнителна разпоредба", "§ 1. По смисъла на този закон.", "Заключителни разпоредби", "§ 2. Влиза в сила."]
    assert defects.scan_blocks(_blocks(clean)) == []
    twice = ["Допълнителна разпоредба", "Заключителни разпоредби", "§ 1. Текст.", "Допълнителна разпоредба", "Заключителни разпоредби"]
    assert len([f for f in defects.scan_blocks(_blocks(twice)) if f["rule"] == "additional-empty"]) == 1
    # an amending act's empty heading further down the page is recorded, outside the own tail, and makes no candidate
    later = ["Чл. 1. Текст.", "Допълнителни разпоредби", "§ 1. По смисъла.", "Заключителни разпоредби", "§ 2. Влиза в сила.",
             "Допълнителна разпоредба", "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ НА ЗАКОНА ЗА ПРОБАТА", "Заключителни разпоредби", "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ НА ЗАКОНА ЗА ПРОБАТА", "§ 9. Влиза в сила."]
    out = defects.scan_blocks(_blocks(later))
    assert [(f["rule"], f["block"], f.get("outside_own_tail")) for f in out] == [("additional-empty", 5, True)] and "outside the act's own provisions" in out[0]["detail"]


def test_the_paragraph_rule_reads_the_acts_own_tail_not_the_amending_tails():
    single = ["Чл. 1. Текст.", "Заключителни разпоредби", "Параграф единствен. Наредбата се издава на основание чл. 2.",
              "Заключителни разпоредби", "КЪМ НАРЕДБА ЗА ИЗМЕНЕНИЕ НА НАРЕДБА № 1", "§ 4. Наредбата влиза в сила."]
    assert defects.scan_blocks(_blocks(single)) == []          # a Параграф единствен tail is no candidate, whatever the amending tails number
    assert defects.own_tail(_blocks(single)) == (1, 3)
    own_above = ["Чл. 1. Текст.", "Преходни и заключителни разпоредби", "§ 3. Текст.", "Заключителни разпоредби КЪМ ЗАКОНА ЗА ПРОБАТА", "§ 1. Текст."]
    out = defects.scan_blocks(_blocks(own_above))
    assert [f["rule"] for f in out] == ["paragraph-start-above-1"] and "own provisions" in out[0]["detail"] and out[0]["block"] == 2
    no_heading = ["§ 5. Текст.", "§ 6. Текст."]
    out = defects.scan_blocks(_blocks(no_heading))
    assert [f["rule"] for f in out] == ["paragraph-start-above-1"] and "no provisions heading of its own" in out[0]["detail"]
    assert defects.own_tail(_blocks(no_heading)) is None and defects.own_scope(_blocks(no_heading)) == (0, 2)
    assert defects.scan_blocks(_blocks(["§ 1. Текст.", "§ 2. Текст."])) == []
    # a page whose only heading is an amending act's: nothing of the act's own provisions, no candidate (review A round 2, major 1)
    only_amending = ["Чл. 1. x", "Заключителни разпоредби", "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ", "§ 52. x"]
    assert defects.own_tail(_blocks(only_amending)) is None and defects.own_scope(_blocks(only_amending)) == (0, 1) and defects.scan_blocks(_blocks(only_amending)) == []
    assert defects.scan_blocks(_blocks(["КЪМ ЗАКОНА", "§ 8. x"])) == [] and defects.own_scope(_blocks(["КЪМ ЗАКОНА", "§ 8. x"])) is None
    # lex.bg's repeated heading after the КЪМ and (ОБН.) lines is the amending act's too (major 2)
    repeated = ["Чл. 1. x", "Заключителни разпоредби", "КЪМ ПОСТАНОВЛЕНИЕ № 197", "(ОБН. - ДВ, БР. 1 ОТ 2022 Г.)", "Заключителни разпоредби", "§ 28. x"]
    assert defects.own_tail(_blocks(repeated)) is None and defects.scan_blocks(_blocks(repeated)) == []
    own_then_repeated = ["Чл. 1. x", "Преходни разпоредби", "§ 3. x", "Заключителни разпоредби", "КЪМ ПОСТАНОВЛЕНИЕ № 197", "(ОБН. - ДВ)", "Заключителни разпоредби", "§ 28. x"]
    assert defects.own_tail(_blocks(own_then_repeated)) == (1, 3)


PAGE = """<html><body><div class="box"><div class="boxi">
<div class="TitleDocument" id="DocumentTitle"><p class="Title">ЗАКОН ЗА ПРОБАТА<br/></p></div>
<div class="Article">Чл. 1. Този закон урежда пробата.</div>
<div class="Article">Чл. 2. Пробата е публична.</div>
<div class="Title">Допълнителна разпоредба</div>
<div class="Title">Заключителни разпоредби</div>
<div class="FinalEdictsArticle">§ 2. Законът влиза в сила от деня на обнародването му.</div>
<div class="Title">Заключителни разпоредби</div>
<div class="Title">КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ НА ЗАКОНА ЗА ПРОБАТА</div>
<div class="FinalEdictsArticle">§ 9. Законът влиза в сила от 1 януари 2027 г.</div>
</div></div></body></html>"""
CHROME = """<html><body><div class="box"><div><a>ДОБАВИ В МОИТЕ АКТОВЕ</a></div></div></body></html>"""
MATERIAL = """<html><body><span class="mark">Брой 32 от 1.4.2026 г.</span>
<div style=" width: 100%;"><span style="font-size:8.5pt">
<p style="text-align:center"><b>ЗАКОН</b></p><p style="text-align:center"><b>за пробата</b></p>
<p style="text-align:justify"><b>Чл. 1. </b>Този закон урежда пробата.</p>
<p style="text-align:justify"><b>Чл. 2. </b>Пробата е публична.</p>
<p style="text-align:center">ДОПЪЛНИТЕЛНА РАЗПОРЕДБА</p>
<p style="text-align:justify"><b>§ 1. </b>По смисъла на този закон „проба“ е опит.</p>
<p style="text-align:center">ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ</p>
<p style="text-align:justify"><b>§ 2. </b>Законът влиза в сила от деня на обнародването му.</p>
</span></div></body></html>"""


def test_scan_page_and_the_tails():
    findings, facts = defects.scan_page(PAGE.encode("utf-8"))
    assert [f["rule"] for f in findings] == ["additional-empty", "paragraph-start-above-1"]
    assert facts["own_tail"] == {"start": 3, "end": 6, "lowest_sign": 2}
    assert defects.scan_page(CHROME.encode("utf-8")) == ([], {"has_spine": False})
    t = defects.texts_for({}, MATERIAL, PAGE.encode("utf-8"))
    assert t["lexbg"]["text"].splitlines()[0] == "ЗАКОН ЗА ПРОБАТА" and t["lexbg"]["text"].splitlines()[-1].startswith("§ 2.")
    assert "КЪМ" not in t["lexbg"]["text"] and "§ 9" not in t["lexbg"]["text"]
    assert "§ 1. По смисъла" in t["dv"]["text"] and t["dv"]["text"].splitlines()[:2] == ["за пробата", "Чл. 1. Този закон урежда пробата."]
    whole = defects.texts_for({}, MATERIAL, PAGE.encode("utf-8"), whole=True)
    assert "§ 9" in whole["lexbg"]["text"] and whole["dv"]["note"].startswith("the whole material")
    decree = _blocks(["ПОСТАНОВЛЕНИЕ № 1", "Чл. 1. Приема Наредба.", "Заключителни разпоредби", "§ 1. Влиза в сила.", "НАРЕДБА № Н-4 от 30 март 2026 г.", "Чл. 1. Текст.",
                      "Чл. 2. Текст.", "Допълнителни разпоредби", "§ 1. По смисъла.", "Заключителни разпоредби", "§ 2. В Наредба № 1:", "Чл. 16. (нов текст)",
                      "Приложение № 1", "таблица"])
    assert defects.material_tail(decree) == (7, 12)                                   # after the act's own title, before the annex; a quoted „Чл.“ inside a § does not end it
    assert defects.material_tail(_blocks(["УКАЗ № 1", "ЗАКОН", "за пробата", "Чл. 1. x", "Заключителни разпоредби", "§ 1. x"])) == (4, 6)
    # a decree in capitals with its own final provisions and its own annex before the regulation's title (material 118279's order)
    pms = _blocks(["ПОСТАНОВЛЕНИЕ № 208 ОТ 27 СЕПТЕМВРИ 2017 Г.", "Чл. 1. Приема Устройствен правилник.", "Заключителни разпоредби", "§ 1. Отменя се.", "§ 3. Постановлението влиза в сила.",
                   "Приложение към чл. 2, ал. 4", "численост", "УСТРОЙСТВЕН ПРАВИЛНИК", "на Министерството", "Глава първа", "Чл. 1. Текст.", "Чл. 2. Текст.",
                   "Преходни и заключителни разпоредби", "§ 1. Правилникът влиза в сила.", "Приложение № 1 към чл. 5", "ред"])
    assert defects.material_tail(pms) == (12, 14)
    # material 68522's order: the decree, its final provisions, then the regulation's title with its name on the same line
    pms2 = _blocks(["ПОСТАНОВЛЕНИЕ № 217 ОТ 14 СЕПТЕМВРИ 2012 Г.", "Чл. 1. Приема.", "Заключителни разпоредби", "§ 1. Отменя се.", "§ 2. Влиза в сила.",
                    "УСТРОЙСТВЕН ПРАВИЛНИК на Агенцията за устойчиво енергийно развитие", "Глава първа", "Чл. 1. x", "Чл. 7. x",
                    "Заключителни разпоредби", "Параграф единствен. Правилникът се приема.", "Приложение към чл. 7, ал. 3", "ред"])
    assert defects.material_tail(pms2) == (9, 11)
    assert defects.material_tail(_blocks(["ПОСТАНОВЛЕНИЕ № 1", "Заключителни разпоредби", "§ 1. x", "ТАРИФА за таксите", "Чл. 1. x", "Преходни разпоредби", "§ 1. x"])) == (5, 7)
    no_title = _blocks(["Чл. 1. x", "Чл. 2. x", "Заключителни разпоредби", "§ 1. В Закона за пробата се създава чл. 2а:", "Чл. 2а. (нов текст)", "§ 2. Влиза в сила."])
    assert defects.material_tail(no_title) == (2, 6)                                  # a „Чл.“ line quoted by a § is no article
    no_title_chapter = _blocks(["Чл. 1. x", "Заключителни разпоредби", "§ 1. x", "Глава втора", "Чл. 2. x", "Преходни разпоредби", "§ 2. x"])
    assert defects.material_tail(no_title_chapter) == (5, 7)                          # a chapter heading ends the quoted stretch
    assert defects.material_tail(_blocks(["ПОСТАНОВЛЕНИЕ № 1", "Чл. 1. Приема.", "Заключителни разпоредби", "§ 1. x", "НАРЕДБА", "Чл. 1. x", "Чл. 2. x"])) is None   # a title with no provisions after it
    assert defects.material_tail(_blocks(["Заключителни разпоредби", "§ 1. x"])) == (0, 2)   # a material without articles
    assert defects.material_tail(_blocks(["Чл. 1. x", "Приложение № 1"])) is None
    annex_rows = _blocks(["Чл. 1. x", "Заключителни разпоредби", "§ 1. x", "Приложение № 1", "Чл. 5. a row of the annex that opens like an article"])
    assert defects.material_tail(annex_rows) == (1, 3)                                # an annex row is no article
    assert defects.own_tail(_blocks(["Чл. 1. x", "Заключителни разпоредби", "§ 1. x", "Приложение № 1 към чл. 1", "ред"])) == (1, 3)
    text, note = defects.tail_text(_blocks(["a", "b", "c"]), None)
    assert text == "a\nb\nc" and note.startswith("no provisions heading")


# --- a run folder end to end ----------------------------------------------------------------------------------------

def _repo(tmp_path, pages):
    """A root with a raw store (manifest + pages), corpus files, a summary table and an empty exceptions list."""
    raw = tmp_path / "data" / "raw" / "lexbg"
    raw.mkdir(parents=True)
    (tmp_path / "laws").mkdir()
    (tmp_path / "docs" / "data").mkdir(parents=True)
    rows = []
    for k, (slug, html, hist) in enumerate(pages):
        doc_id = str(1000 + k)
        (raw / f"{doc_id}.html").write_bytes(html.encode("utf-8"))
        rows.append({"doc_id": doc_id, "slug": slug, "category": "laws", "status": "ok", "fetched_at": "t", "sha256": "x"})
        fm = {"titulo": f"ЗАКОН ЗА {slug.upper()}", "identificador": doc_id, "dv_issue": "32", "dv_year": 2026,
              "amendment_history": [{"dv": "32/2026", "date": "2026-04-01"}] + [{"dv": "55/2026", "date": "2026-06-16"}] * (hist - 1)}
        (tmp_path / "laws" / f"{slug}.md").write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True) + "---\n\n# x\n", encoding="utf-8")
    (raw / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    summary = tmp_path / "summary.csv"
    summary.write_text("law_id,title,base_source,dv_identifier\n" + "".join(f"{s},t,{bs},{dv}\n" for s, bs, dv in
                       [("zakon-a", "dv_html", "dv-500"), ("zakon-b", "unlocated", ""), ("zakon-c", "dv_pdf", ""), ("zakon-d", "unlocated", "")]), encoding="utf-8")
    sx.save(tmp_path / "docs" / "data" / "source-exceptions.yaml", [])
    return tmp_path / "data" / "runs" / "r", summary


INDEX = [{"status": "ok", "issue_year": 2026, "issue_number": 32, "id_mat": 501, "title": "Закон за zakon-b"},
         {"status": "ok", "issue_year": 2026, "issue_number": 32, "id_mat": 502, "title": "Закон за zakon-d, първи"},
         {"status": "ok", "issue_year": 2026, "issue_number": 32, "id_mat": 503, "title": "Закон за zakon-d, втори"},
         {"status": "ok", "issue_year": 2026, "issue_number": 33, "id_mat": 504, "title": "Постановление № 1 за приемане на Закон за zakon-f"}]


def test_scan_fetch_tasks_collect_count_and_entries(tmp_path, monkeypatch):
    run_root, summary = _repo(tmp_path, [("zakon-a", PAGE, 1), ("zakon-b", PAGE, 3), ("zakon-c", PAGE, 1), ("zakon-d", PAGE, 1), ("zakon-e", CHROME, 1)])
    out = defects.scan(tmp_path, run_root)
    doc = json.loads((run_root / "candidates.json").read_text(encoding="utf-8"))
    assert [c["slug"] for c in out] == ["zakon-a", "zakon-b", "zakon-c", "zakon-d"] and doc["pages"] == 5 and doc["pages_without_act"] == 1
    assert doc["by_rule"] == {"additional-empty": 4, "paragraph-start-above-1": 4}
    # attribution: the map, else one title hit in the cited issue, else none with its reason
    assert defects.attribute("zakon-a", tmp_path, summary, INDEX)["how"] == "coverage_map"
    assert defects.attribute("zakon-b", tmp_path, summary, INDEX) == {"id_mat": 501, "how": "index_title", "base_source": "unlocated", "issue": "32/2026"}
    a = defects.attribute("zakon-d", tmp_path, summary, INDEX)
    assert a["id_mat"] is None and "2 title hits" in a["reason"]
    assert defects.attribute("zakon-c", tmp_path, summary, [])["reason"].startswith("the index holds no HTML material")
    fm = yaml.safe_load((tmp_path / "laws" / "zakon-d.md").read_text(encoding="utf-8").split("---\n")[1])
    (tmp_path / "laws" / "zakon-f.md").write_text("---\n" + yaml.safe_dump({**fm, "titulo": "ЗАКОН ЗА ZAKON-F", "dv_issue": "33"}, allow_unicode=True) + "---\n", encoding="utf-8")
    assert defects.attribute("zakon-f", tmp_path, summary, INDEX)["id_mat"] == 504   # listed under the adopting decree's title
    cache = tmp_path / "cache"
    asked = []

    def fetch_one(id_mat):
        asked.append(id_mat)
        if id_mat == 500:
            return None   # the Gazette's error view
        (cache / f"{id_mat}.html").parent.mkdir(exist_ok=True)
        (cache / f"{id_mat}.html").write_text(MATERIAL, encoding="utf-8")
        return MATERIAL

    rec = defects.fetch(run_root, tmp_path, fetch_one, cache, summary, INDEX)
    assert rec["zakon-a"]["outcome"] == "error" and rec["zakon-b"]["outcome"] == "ok" and rec["zakon-b"]["issue"] == "32/2026"
    assert rec["zakon-c"]["outcome"] == "not_retrieved" and rec["zakon-d"]["outcome"] == "not_retrieved"
    rec = defects.fetch(run_root, tmp_path, fetch_one, cache, summary, INDEX)
    assert asked == [500, 501, 500]   # a material recorded ok is not asked for again; an error is
    calls, settled = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert sorted(s["slug"] for s in settled) == ["zakon-a", "zakon-c", "zakon-d"] and all(s["verdict"] == "unverified" and s["stage"] == "script" for s in settled)
    assert len(calls) == 1 and calls[0]["slugs"] == ["zakon-b"] and calls[0]["stage"] == "tails"
    call_text = Path(calls[0]["call_file"]).read_text(encoding="utf-8")
    assert "## Candidate 1: `zakon-b`" in call_text and "§ 1. По смисъла" in call_text and "`needs_whole_text`" in call_text and calls[0]["answer_file"] in call_text
    # the same call again is the same file; an answer outside the form is refused whole
    again, _ = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert [c["call"] for c in again] == [calls[0]["call"]]
    answer = Path(calls[0]["answer_file"])
    answer.write_text(json.dumps({"zakon-b": {"verdict": "confirmed", "kind": "nonsense", "gazette": "x", "note": "n"}}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert written == [] and len(problems) == 1 and "nonsense" in problems[0] and not defects.verdict_path(run_root, "zakon-b").exists()
    answer.write_text(json.dumps({"zakon-b": {"verdict": "needs_whole_text", "kind": None, "gazette": None, "note": "the tails differ in form"}}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert problems == [] and [w["verdict"] for w in written] == ["needs_whole_text"]
    c = defects.count(run_root)
    assert c["final"] == 3 and c["pending_whole_text"] == ["zakon-b"] and c["missing"] == [] and c["by_verdict"] == {"unverified": 3}
    assert "3 final of 4 candidates; 1 waiting" in defects.count_text(c)
    # the whole-text stage: one call per candidate, collected on its own; a second needs_whole_text is unverified
    calls2, settled2 = defects.tasks(run_root, tmp_path, stage="whole", raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert settled2 == [] and len(calls2) == 1 and calls2[0]["stage"] == "whole" and "§ 9" in Path(calls2[0]["call_file"]).read_text(encoding="utf-8")
    Path(calls2[0]["answer_file"]).write_text(json.dumps({"zakon-b": {"verdict": "confirmed", "kind": "dropped_section", "gazette": "§ 1 with one definition",
                                                                       "note": "lex.bg prints the heading with nothing under it"}}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert problems == [] and written[0]["verdict"] == "confirmed" and written[0]["stage"] == "whole" and written[0]["tails_note"] == "the tails differ in form"
    assert written[0]["material"] == 501 and written[0]["promulgation_material"] == 501 and written[0]["beyond_measured_range"] is False
    # a tails answer that arrives after the whole-stage verdict ranks below it and is refused (round 2, minor 3); the refusal is retired until the answer changes
    late = defects.write_call(run_root, ["zakon-b"], "tails", {"zakon-b": defects.texts_for({}, MATERIAL, PAGE.encode("utf-8")) | {"id_mat": 7}}, {c["slug"]: c for c in defects.load_candidates(run_root)})
    Path(late["answer_file"]).write_text(json.dumps({"zakon-b": {"verdict": "not_a_defect", "kind": None, "gazette": None, "note": "late"}}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert written == [] and len(problems) == 1 and "ranks below it" in problems[0]
    assert defects._read_json(run_root / "calls" / f"{late['call']}.json")["refused_for"]
    assert defects.collect(run_root) == ([], [])   # retired
    Path(late["answer_file"]).write_text(json.dumps({"zakon-b": {"verdict": "not_a_defect", "kind": None, "gazette": None, "note": "later"}}), encoding="utf-8")
    assert len(defects.collect(run_root)[1]) == 1   # a changed answer is read again, and refused again
    assert json.loads(defects.verdict_path(run_root, "zakon-b").read_text(encoding="utf-8"))["stage"] == "whole"
    c = defects.count(run_root)
    assert c["final"] == 4 and c["confirmed"] == ["zakon-b"] and c["by_kind"] == {"dropped_section": 1}
    # a confirmed verdict of an act a later scan no longer lists stands; any other verdict of such an act is to withdraw
    defects._write_json(defects.verdict_path(run_root, "zakon-x"), {"slug": "zakon-x", "verdict": "confirmed", "kind": "dropped_section", "stage": "tails", "note": "n", "material": 1})
    defects._write_json(defects.verdict_path(run_root, "zakon-y"), {"slug": "zakon-y", "verdict": "not_a_defect", "kind": None, "stage": "tails", "note": "n", "material": 1})
    c = defects.count(run_root)
    assert c["confirmed"] == ["zakon-b", "zakon-x"] and c["confirmed_outside_candidates"] == ["zakon-x"] and c["stray_verdicts"] == ["zakon-y"] and c["by_kind"] == {"dropped_section": 2}
    assert "kept: ['zakon-x']" in defects.count_text(c) and "to withdraw: ['zakon-y']" in defects.count_text(c)
    for s in ("zakon-x", "zakon-y"):
        defects.verdict_path(run_root, s).unlink()
    written, _ = defects.collect(run_root)
    assert written == []   # collected once
    entries = defects.entries_for(run_root, tmp_path, added="2026-10-31")
    assert len(entries) == 1 and entries[0].slug == "zakon-b" and entries[0].defect == "dropped_section" and entries[0].address == "501" and entries[0].route == "history"
    assert entries[0].evidence[0]["kind"] == "register" and entries[0].note.endswith("promulgation material 501 carries: § 1 with one definition")
    assert entries[0].evidence[1]["ref"].endswith("lex.bg prints the heading with nothing under it.")   # a note ends with a full stop
    assert defects.route_for({"amendment_history": [{"dv": "1/2026"}]}) == "whole_act_from_material" and defects.route_for({}) == "whole_act_from_material"
    # no tails call is written for a candidate with a verdict
    calls3, settled3 = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert calls3 == [] and settled3 == []
    # a script verdict for a material not retrieved then is re-tasked once the material is there
    (cache / "500.html").write_text(MATERIAL, encoding="utf-8")
    summary.write_text("law_id,title,base_source,dv_identifier\nzakon-a,t,dv_html,dv-500\n", encoding="utf-8")
    rec = defects.fetch(run_root, tmp_path, lambda i: MATERIAL, cache, summary, INDEX)
    assert rec["zakon-a"]["outcome"] == "ok"
    calls4, settled4 = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert [c["slugs"] for c in calls4] == [["zakon-a"]] and settled4 == []
    # a second call of the same stage over an answered slug is refused, never written over
    Path(calls4[0]["answer_file"]).write_text(json.dumps({"zakon-a": {"verdict": "not_a_defect", "kind": None, "gazette": None, "note": "same"}}), encoding="utf-8")
    assert defects.collect(run_root)[1] == []
    other = defects.write_call(run_root, ["zakon-a", "zakon-b"], "tails", {s: defects.texts_for({}, MATERIAL, PAGE.encode("utf-8")) | {"id_mat": 1} for s in ("zakon-a", "zakon-b")},
                               {c["slug"]: c for c in defects.load_candidates(run_root)})
    Path(other["answer_file"]).write_text(json.dumps({s: {"verdict": "not_a_defect", "kind": None, "gazette": None, "note": "x"} for s in ("zakon-a", "zakon-b")}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert written == [] and len(problems) == 1 and "already answered by" in problems[0] and "never written over" in problems[0]
    assert json.loads(defects.verdict_path(run_root, "zakon-a").read_text(encoding="utf-8"))["note"] == "same"
    # the raw page changed since the scan: refused
    (tmp_path / "data" / "raw" / "lexbg" / "1000.html").write_bytes((PAGE + "<!-- -->").encode("utf-8"))
    defects.verdict_path(run_root, "zakon-a").unlink()
    with pytest.raises(defects.DefectsError, match="no longer hashes as candidates.json"):
        defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)


def test_the_number_key_keeps_hyphens_and_letters():
    assert defects._number_key("НАРЕДБА № Н-4 от 30 март 2026 г. за организацията") == ("наредба", "н-4", "2026")
    assert defects._number_key("Наредба № 29 от 12 юли 2006 г. за минималното ниво") == ("наредба", "29", "2006") == defects._number_key("НАРЕДБА № 29 ОТ 12.07.2006 Г. ЗА ИЗИСКВАНИЯТА")
    assert defects._number_key("Постановление № 245 от 16 ноември 2005 г. за приемане") == ("постановление", "245", "2005") and defects._number_key("Закон за пробата") is None


def test_answers_are_held_to_the_form():
    ok = {"a": {"verdict": "not_a_defect", "kind": None, "gazette": None, "note": "same"}}
    assert defects.answer_problems(ok, ["a"]) == []
    assert defects.answer_problems([], ["a"]) == ["not a JSON object keyed by slug"]
    errs = defects.answer_problems({"a": {"verdict": "confirmed", "note": ""}, "b": {}}, ["a"])
    assert any("slugs not in the call" in e for e in errs) and any("kind None" in e for e in errs) and any("names what the Gazette carries" in e for e in errs) and any("note is missing" in e for e in errs)
    assert defects.answer_problems({"a": {"verdict": "unverified", "kind": "wrong_text", "note": "x"}}, ["a"]) == ["a: a kind is given with the verdict 'unverified'"]
    assert defects.answer_problems({"a": {"verdict": "unverified", "note": "x", "extra": 1}}, ["a"]) == ["a: keys outside the form: ['extra']"]
    assert defects.answer_problems({}, ["a"]) == ["a: no answer object"]


def test_the_whole_text_call_is_bounded_and_a_changed_cache_is_refused(tmp_path):
    run_root, summary = _repo(tmp_path, [("zakon-a", PAGE, 2)])
    defects.scan(tmp_path, run_root)
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "500.html").write_text(MATERIAL, encoding="utf-8")
    defects.fetch(run_root, tmp_path, lambda i: MATERIAL, cache, summary, [])
    (cache / "500.html").write_text(MATERIAL + "<!-- -->", encoding="utf-8")
    with pytest.raises(defects.DefectsError, match="no longer hashes"):
        defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    (cache / "500.html").write_text(MATERIAL, encoding="utf-8")
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "needs_whole_text", "stage": "tails", "note": "n", "kind": None})
    defects.MOST_WHOLE_TOKENS, keep = 10, defects.MOST_WHOLE_TOKENS
    try:
        calls, settled = defects.tasks(run_root, tmp_path, stage="whole", raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    finally:
        defects.MOST_WHOLE_TOKENS = keep
    assert calls == [] and settled[0]["verdict"] == "unverified" and "beyond one call's range" in settled[0]["note"]
    # the whole stage with the material gone: the tails note is carried into the script verdict
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "needs_whole_text", "stage": "tails", "note": "why", "kind": None})
    mats = defects._read_json(run_root / "materials.json")
    mats["zakon-a"]["outcome"] = "error"
    defects._write_json(run_root / "materials.json", mats)
    _, settled = defects.tasks(run_root, tmp_path, stage="whole", raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert settled[0]["tails_note"] == "why" and settled[0]["verdict"] == "unverified"
    with pytest.raises(defects.DefectsError, match="not tails or whole"):
        defects.tasks(run_root, tmp_path, stage="x")


def test_calls_are_packed_by_count_and_size(tmp_path):
    pages = [(f"zakon-{k}", PAGE, 1) for k in range(10)]
    run_root, summary = _repo(tmp_path, pages)
    summary.write_text("law_id,title,base_source,dv_identifier\n" + "".join(f"zakon-{k},t,dv_html,dv-{600 + k}\n" for k in range(10)), encoding="utf-8")
    defects.scan(tmp_path, run_root)
    cache = tmp_path / "cache"
    cache.mkdir()

    def fetch_one(i):
        (cache / f"{i}.html").write_text(MATERIAL, encoding="utf-8")
        return MATERIAL

    defects.fetch(run_root, tmp_path, fetch_one, cache, summary, [])
    calls, _ = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, per=4)
    assert [len(c["slugs"]) for c in calls] == [4, 4, 2]
    for p in (run_root / "calls").glob("*"):
        p.unlink()
    calls, _ = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, per=8, cap=1)
    assert [len(c["slugs"]) for c in calls] == [1] * 10   # a candidate above the cap gets its own call


# --- the register ----------------------------------------------------------------------------------------------------

def test_the_repositorys_register_loads_and_its_kinds_are_the_closed_set():
    doc = defect_kinds.load()
    assert sorted(e["kind"] for e in doc["kinds"]) == sorted(defects.KINDS) and sorted(defects.KINDS) == sorted(sx.DEFECTS)[:0] + sorted(k for k in sx.DEFECTS if k in defects.KINDS)
    assert set(defects.KINDS) <= set(sx.DEFECTS)   # a confirmed act can be listed with its kind


def test_the_register_is_held_to_its_form_and_synced_from_the_runs_verdicts(tmp_path):
    doc = defect_kinds.load()
    path = tmp_path / "docs" / "data" / "lexbg-defect-kinds.yaml"
    path.parent.mkdir(parents=True)
    doc["run"] = "r"
    for e in doc["kinds"]:   # the repository's examples belong to its run; here the run is a fresh one
        e["examples"], e["status"] = [], "named"
    defect_kinds.save(path, doc)
    assert defect_kinds.check(path, tmp_path) == []   # no run, no examples: nothing to compare
    bad = yaml.safe_load(path.read_text(encoding="utf-8"))
    bad["kinds"][0]["status"] = "confirmed"
    bad["kinds"][1]["detector"] = {"script": "reading/defects.py", "rule": "no-such-rule", "form": "x"}
    bad["kinds"][2]["evidence"] = []
    del bad["kinds"][3]["no_detector"]
    bad["kinds"].append({"kind": "typo", "status": "named", "description": "d", "evidence": [{"kind": "plan", "ref": "r"}], "detector": None, "no_detector": "n", "examples": []})
    defect_kinds.save(path, bad)
    problems = defect_kinds.check(path, tmp_path)
    assert len(problems) == 1
    msg = problems[0]
    for part in ("has at least one example", "does not carry the rule 'no-such-rule'", "evidence is not a non-empty list", "says why (no_detector)", "kind 'typo' is not one of"):
        assert part in msg, part
    # sync: the examples and the status follow the run's confirmed verdicts
    defect_kinds.save(path, doc)
    run_root = tmp_path / "data" / "runs" / "r"
    defects._write_json(run_root / "candidates.json", {"entries": [{"slug": "zakon-a"}, {"slug": "zakon-b"}]})
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "confirmed", "kind": "dropped_section", "note": "n"})
    defects._write_json(defects.verdict_path(run_root, "zakon-b"), {"slug": "zakon-b", "verdict": "not_a_defect", "kind": None, "note": "n"})
    assert defect_kinds.check(path, tmp_path) == ["dropped_section: examples [] are not the run's confirmed verdicts of the kind ['zakon-a'] (run sync)"]
    synced = defect_kinds.sync(path, tmp_path)
    assert synced["kinds"][0] == {**synced["kinds"][0], "status": "confirmed", "examples": ["zakon-a"]} and synced["kinds"][1]["status"] == "named"
    assert defect_kinds.check(path, tmp_path) == []
    assert path.read_text(encoding="utf-8").startswith(defect_kinds.HEADER)
    with pytest.raises(defect_kinds.RegisterError, match="not YAML|not a mapping"):
        path.write_text("kinds: [\n", encoding="utf-8")
        defect_kinds.load(path)


@pytest.mark.skipif(not (REPO / "data" / "runs" / defects.RUN_NAME / "candidates.json").exists(), reason="the S2 run is not on this machine")
def test_the_repositorys_register_matches_the_runs_verdicts():
    assert defect_kinds.check() == []


def test_confirmed_acts_enter_the_list_through_the_driver_and_the_history_route_stops_with_a_written_case_file(tmp_path):
    run_root, summary = _repo(tmp_path, [("zakon-a", PAGE, 1), ("zakon-b", PAGE, 3)])
    (tmp_path / "data" / "runs" / "route-ledger").mkdir(parents=True)
    defects.scan(tmp_path, run_root)
    for slug, mat in (("zakon-a", 500), ("zakon-b", 501)):
        defects._write_json(defects.verdict_path(run_root, slug), {"slug": slug, "verdict": "confirmed", "kind": "dropped_section", "stage": "tails",
                                                                   "gazette": "§ 1 with one definition", "note": "the heading is empty on lex.bg", "material": mat,
                                                                   "promulgation_material": mat, "call": "c"})
    out = defects.list_confirmed(run_root, str(tmp_path), run="r")   # a string root is accepted (round 2, minor 5)
    assert [e.slug for e in defects.entries_for(run_root, str(tmp_path))] == ["zakon-a", "zakon-b"]
    by = {r["slug"]: r for r in out}
    assert by["zakon-b"]["route"] == "history" and by["zakon-b"]["state"] == "stopped" and by["zakon-b"]["step"] == "engine" and by["zakon-b"]["added"]
    assert by["zakon-a"]["route"] == "whole_act_from_material" and by["zakon-a"]["state"] == "halted" and by["zakon-a"]["step"] == "amendment_search"
    case = (tmp_path / by["zakon-b"]["case_file"]).read_text(encoding="utf-8")
    assert "## Lessons learnt\n\nThe detector of FR-042 flagged the act" in case and "until the engine exists" in case
    assert "the heading is empty on lex.bg. The Gazette carries: § 1 with one definition." in case   # the note ends with a full stop before the next sentence
    assert "(not yet written)" not in case and "## The owner's ruling\n\n(not yet given)" in case
    entries = {e.slug: e for e in sx.load(tmp_path / "docs" / "data" / "source-exceptions.yaml")}
    assert entries["zakon-b"].state == "stopped" and entries["zakon-b"].defect == "dropped_section" and entries["zakon-b"].address == "501"
    assert entries["zakon-a"].state == "listed"
    # listed once: a second pass adds nothing and the stop stands with its prose
    again = {r["slug"]: r for r in defects.list_confirmed(run_root, tmp_path, run="r")}
    assert not again["zakon-b"]["added"] and again["zakon-b"]["state"] == "stopped" and again["zakon-b"]["detail"] == "already listed"
    assert (tmp_path / by["zakon-b"]["case_file"]).read_text(encoding="utf-8") == case
    prose = defects.case_prose({"material": 1, "note": "n", "gazette": "g", "kind": "wrong_text", "stage": "amendment", "promulgation_material": 2}, entries["zakon-a"], "r")
    assert "S5's batch" in prose["Proposal"] and "kind: wrong_text" in prose["Lessons learnt"] and "amending material 1 (the promulgation material is 2)" in prose["Lessons learnt"]
    # a verdict that changed (the amendment stage recorded its material) refreshes the note and the prose while the owner has not ruled
    v = json.loads(defects.verdict_path(run_root, "zakon-b").read_text(encoding="utf-8"))
    defects._write_json(defects.verdict_path(run_root, "zakon-b"), {**v, "stage": "amendment", "material": 900})
    defects.list_confirmed(run_root, tmp_path, run="r")
    assert "amending material 900" in (tmp_path / by["zakon-b"]["case_file"]).read_text(encoding="utf-8")
    assert sx.listed("zakon-b", tmp_path / "docs" / "data" / "source-exceptions.yaml").note.startswith("S2 of the plan of 31 October 2026: the Gazette's amending material 900")
    # the owner's ruling makes the file the owner's: nothing is refreshed after it
    case_path = tmp_path / by["zakon-b"]["case_file"]
    case_path.write_text(case_path.read_text(encoding="utf-8").replace("(not yet given)", "Leave it."), encoding="utf-8")
    defects._write_json(defects.verdict_path(run_root, "zakon-b"), {**v, "stage": "amendment", "material": 901})
    defects.list_confirmed(run_root, tmp_path, run="r")
    assert "amending material 900" in case_path.read_text(encoding="utf-8") and "Leave it." in case_path.read_text(encoding="utf-8")
    assert "amending material 900" in sx.listed("zakon-b", tmp_path / "docs" / "data" / "source-exceptions.yaml").note   # the list's note stays with the ruling too
    # a case file whose parts are not the three is refused, never written
    odd = tmp_path / "docs" / "cases" / "odd.md"
    odd.write_text("---\nrun: r\n---\n\n## Lessons learnt\n\n(not yet written)\n\n## Something else\n\n(x)\n\n## The owner's ruling\n\n(not yet given)\n", encoding="utf-8")
    with pytest.raises(defects.DefectsError, match="prose parts"):
        defects._fill_case(odd, run_root, entries["zakon-b"], "r")


def test_the_token_report_sums_the_calls(tmp_path):
    run_root = tmp_path / "data" / "runs" / "r"
    run_root.mkdir(parents=True)
    assert "0 calls, 0 tokens" in defects.token_report(run_root)
    (run_root / "usage.jsonl").write_text('{"call": "a", "candidates": 2, "content_tokens": 1000, "tokens": 5000, "duration_ms": 2000}\n'
                                          '{"call": "b", "kind": "review", "tokens": 7000, "duration_ms": 1000}\n', encoding="utf-8")
    text = defects.token_report(run_root, budget=10_000)
    assert "2 calls, 12,000 tokens counted once" in text and "budget of 10,000" in text
    assert "investigator: 1 calls, 5,000 tokens, 1,000 of content estimated, 2 candidates, 2,500 per candidate, 2 s" in text
    assert "review: 1 calls, 7,000 tokens" in text and "other calls: 1, about 4,000 per call beyond the content" in text
    (run_root / "usage.jsonl").write_text('{"call": "call-tails-1", "candidates": 2, "content_tokens": 1000, "tokens": 5000, "duration_ms": 2000}\n'
                                          '{"call": "call-whole-2", "candidates": 1, "content_tokens": 9000, "tokens": 3000, "duration_ms": 1000}\n', encoding="utf-8")
    text = defects.token_report(run_root)
    assert "tails calls: 1, about 4,000 per call beyond the content" in text and "whole calls" not in text
    assert "may not count everything the call read: call-whole-2 (9,000 content, 3,000 tokens)" in text


def test_the_amendment_call_reads_the_amending_material_whole(tmp_path):
    run_root, summary = _repo(tmp_path, [("zakon-a", PAGE, 2)])
    defects.scan(tmp_path, run_root)
    cache = tmp_path / "cache"
    cache.mkdir()

    def fetch_one(i):
        (cache / f"{i}.html").write_text(MATERIAL, encoding="utf-8")
        return MATERIAL

    with pytest.raises(defects.DefectsError, match="follows a tails verdict"):   # bounded: only after an unsettled tails verdict
        defects.amendment_call(run_root, "zakon-a", 900, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, fetch_one=fetch_one)
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "unverified", "stage": "tails", "note": "the promulgation cannot show it", "kind": None, "call": "c", "material": 500})
    with pytest.raises(defects.DefectsError, match="error view"):
        defects.amendment_call(run_root, "zakon-a", 900, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, fetch_one=lambda i: None)
    defects.MOST_WHOLE_TOKENS, keep = 10, defects.MOST_WHOLE_TOKENS
    try:
        with pytest.raises(defects.DefectsError, match="beyond one call's range"):
            defects.amendment_call(run_root, "zakon-a", 900, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, fetch_one=fetch_one)
    finally:
        defects.MOST_WHOLE_TOKENS = keep
    rec = defects.amendment_call(run_root, "zakon-a", 900, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, fetch_one=fetch_one)
    assert rec["stage"] == "amendment" and rec["slugs"] == ["zakon-a"] and rec["materials"] == {"zakon-a": 900}
    # while the amendment call is out, the whole stage leaves the act alone
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "needs_whole_text", "stage": "tails", "note": "n", "kind": None, "call": "c", "material": 500})
    assert defects.tasks(run_root, tmp_path, stage="whole", raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache) == ([], [])
    defects._write_json(defects.verdict_path(run_root, "zakon-a"), {"slug": "zakon-a", "verdict": "unverified", "stage": "tails", "note": "the promulgation cannot show it", "kind": None, "call": "c", "material": 500})
    text = Path(rec["call_file"]).read_text(encoding="utf-8")
    assert "the whole amending material 900" in text and "УКАЗ" not in text and "ЗАКОН" in text and "§ 9" not in text
    with pytest.raises(defects.DefectsError, match="never a second"):
        defects.amendment_call(run_root, "zakon-a", 901, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache, fetch_one=fetch_one)
    Path(rec["answer_file"]).write_text(json.dumps({"zakon-a": {"verdict": "confirmed", "kind": "dropped_section", "gazette": "§ 1", "note": "n"}}), encoding="utf-8")
    written, problems = defects.collect(run_root)
    assert problems == [] and written[0]["material"] == 900 and written[0]["promulgation_material"] is None   # no promulgation material recorded in this run
    assert written[0]["tails_note"] == "the promulgation cannot show it"
    with pytest.raises(defects.DefectsError, match="without a promulgation material"):   # the address is the promulgation material: refused without one
        defects.entries_for(run_root, tmp_path)
    Path(rec["answer_file"]).write_text(json.dumps({"zakon-a": {"verdict": "needs_whole_text", "kind": None, "gazette": None, "note": "n"}}), encoding="utf-8")
    rec2 = defects._read_json(run_root / "calls" / f"{rec['call']}.json")
    rec2.pop("collected_at")
    defects._write_json(run_root / "calls" / f"{rec['call']}.json", rec2)
    defects.verdict_path(run_root, "zakon-a").unlink()
    written, problems = defects.collect(run_root)
    assert problems == [] and written[0]["verdict"] == "unverified" and written[0]["note"].startswith("the amendment texts did not settle it either")
