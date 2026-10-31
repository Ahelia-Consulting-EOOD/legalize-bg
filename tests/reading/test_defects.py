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
    # the act's own tail runs from the first provisions heading to the heading whose next line is КЪМ (an amending act's),
    # so the § 2 under the amending act's heading says nothing and only the empty section fires
    out = defects.scan_blocks(_blocks(qualified))
    assert [f["rule"] for f in out] == ["additional-empty"] and out[0]["block"] == 1 and defects.own_tail(_blocks(qualified)) == (1, 3)
    clean = ["Чл. 1. Текст.", "Допълнителна разпоредба", "§ 1. По смисъла на този закон.", "Заключителни разпоредби", "§ 2. Влиза в сила."]
    assert defects.scan_blocks(_blocks(clean)) == []
    twice = ["Допълнителна разпоредба", "Заключителни разпоредби", "§ 1. Текст.", "Допълнителна разпоредба", "Заключителни разпоредби"]
    assert len([f for f in defects.scan_blocks(_blocks(twice)) if f["rule"] == "additional-empty"]) == 1


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
    assert [f["rule"] for f in out] == ["paragraph-start-above-1"] and "no provisions heading" in out[0]["detail"]
    assert defects.own_tail(_blocks(no_heading)) is None
    assert defects.scan_blocks(_blocks(["§ 1. Текст.", "§ 2. Текст."])) == []


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
    decree = _blocks(["ПОСТАНОВЛЕНИЕ № 1", "Чл. 1. Приема Наредба.", "Заключителни разпоредби", "§ 1. Влиза в сила.", "НАРЕДБА", "Чл. 1. Текст.",
                      "Чл. 2. Текст.", "Допълнителни разпоредби", "§ 1. По смисъла.", "Заключителни разпоредби", "§ 2. Влиза в сила.", "Приложение № 1", "таблица"])
    assert defects.material_tail(decree) == (7, 11)                                   # after the last article, before the annex
    assert defects.material_tail(_blocks(["Заключителни разпоредби", "§ 1. x"])) == (0, 2)   # a material without articles
    assert defects.material_tail(_blocks(["Чл. 1. x", "Приложение № 1"])) is None
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
    assert problems == [] and written[0]["verdict"] == "confirmed" and written[0]["stage"] == "whole" and written[0]["tails_note"] == "the tails differ in form" and written[0]["material"] == 501
    c = defects.count(run_root)
    assert c["final"] == 4 and c["confirmed"] == ["zakon-b"] and c["by_kind"] == {"dropped_section": 1}
    written, _ = defects.collect(run_root)
    assert written == []   # collected once
    entries = defects.entries_for(run_root, tmp_path, added="2026-10-31")
    assert len(entries) == 1 and entries[0].slug == "zakon-b" and entries[0].defect == "dropped_section" and entries[0].address == "501" and entries[0].route == "history"
    assert entries[0].evidence[0]["kind"] == "register" and "§ 1 with one definition" in entries[0].note
    assert defects.route_for({"amendment_history": [{"dv": "1/2026"}]}) == "whole_act_from_material" and defects.route_for({}) == "whole_act_from_material"
    # no tails call is written for a candidate with a verdict
    calls3, settled3 = defects.tasks(run_root, tmp_path, raw_dir=tmp_path / "data" / "raw" / "lexbg", cache_dir=cache)
    assert calls3 == [] and settled3 == []


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
