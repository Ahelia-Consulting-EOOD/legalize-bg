"""Tests of the reading architecture: splitter partition, assembler round-trip, checks, ladder."""
from pathlib import Path

import pytest

from reading.assembler import assemble, strip_markers
from reading.checks import run_all
from reading.labels import validate_entries
from reading.ladder import merge, next_round_tasks, round0_tasks
from reading.splitter import Block, SplitAct, split_lexbg

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "html"


@pytest.fixture(scope="module")
def zzd():
    return split_lexbg((FIX / "zzd.html").read_bytes())


def test_splitter_partitions_the_region_text(zzd):
    assert zzd.has_spine
    assert len(zzd.blocks) > 100
    assert all(b.text == b.text.strip() and b.text for b in zzd.blocks)
    assert [b.i for b in zzd.blocks] == list(range(len(zzd.blocks)))
    covered = sorted(i for s in zzd.sections for i in s.blocks)
    assert covered == list(range(len(zzd.blocks))), "every block is in exactly one section"
    assert max(len(s.blocks) for s in zzd.sections) <= 60 + 20


def test_splitter_drops_chrome_and_keeps_articles(zzd):
    assert any(b.text.startswith("Чл. 1.") for b in zzd.blocks)
    assert not any("picRefsFromActs" in b.text for b in zzd.blocks)
    assert zzd.dropped_by_splitter


def _act(texts, hints=None):
    hints = hints or ["Article"] * len(texts)
    blocks = [Block(i, t, h) for i, (t, h) in enumerate(zip(texts, hints))]
    return SplitAct(blocks=blocks, sections=[], dropped_by_splitter={}, has_spine=True)


def test_assembler_copies_text_and_round_trips():
    act = _act(["ЗАКОН ЗА НЕЩО", "Глава първа.", "ОБЩИ", "Чл. 1. Текст на член първи.", "(2) Втора алинея.", "продължение.", "1. точка едно;", "Форум"],
               ["TitleDocument", "Title", "Title", "Article", "Article", "Article", "Article", "unknown"])
    smap = {0: {"label": "title"}, 1: {"label": "chapter_heading"}, 2: {"label": "chapter_heading"}, 3: {"label": "article_head", "n": "1"},
            4: {"label": "alinea", "n": "2"}, 5: {"label": "continuation"}, 6: {"label": "item", "n": "1"}, 7: {"label": "drop", "note": "chrome"}}
    md, placed, dropped = assemble(act.blocks, smap)
    assert "# ЗАКОН ЗА НЕЩО" in md and "### Глава първа. ОБЩИ" in md and "**Чл. 1.** Текст" in md and "(2) Втора алинея. продължение." in md
    assert dropped == [7] and placed == [0, 1, 2, 3, 4, 5, 6]
    md2, ex = run_all(act.blocks, smap)
    assert not [e for e in ex if e["kind"] == "reassembly"]


def test_checks_find_order_nesting_duplicates_and_fragments():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 1. Дубъл.", "1. точка", "Чл. 3. SUP>текст", "Чл. 2. назад"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "alinea", "n": "3"},
            3: {"label": "article_head", "n": "1"}, 4: {"label": "item", "n": "1"}, 5: {"label": "article_head", "n": "3"},
            6: {"label": "article_head", "n": "2"}}
    md, ex = run_all(act.blocks, smap)
    kinds = {e["kind"] for e in ex}
    assert {"alinea_order", "duplicate_address", "fragment", "article_order"} <= kinds
    assert not any(e["kind"] == "reassembly" for e in ex)


def test_checks_flag_uncovered_and_unknown():
    act = _act(["Чл. 1. Едно.", "нещо"])
    md, ex = run_all(act.blocks, {0: {"label": "article_head", "n": "1"}})
    assert any(e["kind"] == "unknown" and e["block"] == 1 for e in ex)


def test_validate_entries_refuses_bad_shapes():
    got, probs = validate_entries([{"i": 0, "label": "article_head", "n": "x"}, {"i": 1, "label": "nonsense"}, {"i": 1, "label": "alinea", "n": "1"}], [0, 1, 2])
    assert 1 in got and 0 not in got
    kinds = sorted(p["kind"] for p in probs)
    assert kinds == ["bad_label", "bad_number", "missing_entry", "missing_entry"], "block 0 has no accepted entry either"


def test_ladder_round0_and_next_round():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 2. Две."])
    act.sections = [type("S", (), {"k": 0, "blocks": [0, 1, 2, 3]})()]
    tasks = round0_tasks(act)
    assert tasks[0]["target"] is None and [b["i"] for b in tasks[0]["blocks"]] == [0, 1, 2, 3]
    smap, probs = merge({}, [(tasks[0], [{"i": 0, "label": "article_head", "n": "1"}, {"i": 1, "label": "alinea", "n": "1"},
                                          {"i": 2, "label": "alinea", "n": "3"}, {"i": 3, "label": "article_head", "n": "2"}])])
    md, ex = run_all(act.blocks, smap)
    nxt = next_round_tasks(act, smap, ex, 1)
    assert nxt and nxt[0]["target"] == 2 and [b["i"] for b in nxt[0]["blocks"]] == [1, 2, 3]
    assert nxt[0]["blocks"][0]["current_label"] == "alinea"
    smap2, _ = merge(smap, [(nxt[0], [{"i": 2, "label": "continuation", "n": None}])])
    assert smap2[2]["label"] == "continuation"


def test_splitter_keeps_every_character_of_every_fixture():
    """The joined blocks equal the region text, whitespace removed: no word is lost or duplicated (review finding 1)."""
    import re
    from bs4 import BeautifulSoup
    from fetcher.bg.text_parser import content_region
    from reading.splitter import decode, SKIP_CLASSES, INLINE_TAGS
    for name in ("zzd.html", "zop.html", "gpk.html", "ppz-aktsizi.html", "naredba-04-14.html"):
        raw = (FIX / name).read_bytes()
        act = split_lexbg(raw)
        soup = BeautifulSoup(decode(raw), "lxml")
        region, _ = content_region(soup)
        for el in list(region.find_all(True)):
            if getattr(el, "decomposed", False):
                continue
            if (set(el.get("class") or []) & SKIP_CLASSES) and el.name not in INLINE_TAGS:
                el.decompose()
        expected = re.sub(r"\s+", "", region.get_text())
        got = re.sub(r"\s+", "", "".join(b.text for b in act.blocks))
        assert got == expected, f"{name}: {len(got)} vs {len(expected)} characters"


def test_titled_article_round_trips():
    act = _act(["Предмет и цел", "Чл. 1. Текст.", "(2) Втора."], ["Title", "Article", "Article"])
    smap = {0: {"label": "article_title"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "alinea", "n": "2"}}
    md, ex = run_all(act.blocks, smap)
    assert "Предмет и цел **Чл. 1.** Текст." in md
    assert not [e for e in ex if e["kind"] == "reassembly"], ex


def test_targeted_merge_reads_only_the_target():
    act = _act(["Чл. 1. Едно.", "(1) а", "(3) б", "Чл. 2. Две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "alinea", "n": "3"}, 3: {"label": "article_head", "n": "2"}}
    task = {"round": 1, "task": 0, "target": 2, "blocks": [{"i": 1}, {"i": 2}, {"i": 3}]}
    smap2, probs = merge(dict(smap), [(task, [{"i": 2, "label": "continuation", "n": None}])])
    assert smap2[2]["label"] == "continuation" and smap2[1]["label"] == "alinea" and probs == []
    smap3, probs = merge(dict(smap), [(task, [{"i": 1, "label": "nonsense"}, {"i": 2, "label": "continuation"}])])
    assert smap3[1]["label"] == "alinea" and smap3[2]["label"] == "continuation" and probs == []


def test_malformed_answers_are_refused_not_crashed():
    for bad in ({"i": 0, "label": "title"}, [[1]], ["x"], [None], [{"i": True, "label": "title"}], [{"i": "x", "label": "title"}], [{"i": 0, "label": ["title"]}]):
        got, probs = validate_entries(bad, [0, 1])
        assert not got or all(isinstance(k, int) and not isinstance(k, bool) for k in got)
        assert all(isinstance(p["block"], int) for p in probs)


def test_checks_catch_drops_text_mismatch_first_alinea_and_sign_order():
    letters = "абвгдежзик"
    act = _act(["Чл. 1. Едно.", "(2) втора", "Чл. 2. Две.", "(1) а", "Чл. 3. Три.", "§ 5. x", "§ 3. y"] + [f"{c}) буква" for c in letters])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "2"}, 2: {"label": "drop", "note": "x"},
            3: {"label": "alinea", "n": "1"}, 4: {"label": "article_head", "n": "4"}, 5: {"label": "paragraph_sign", "n": "5"},
            6: {"label": "paragraph_sign", "n": "3"}}
    for k, c in enumerate(letters):
        smap[7 + k] = {"label": "letter", "n": c}
    md, ex = run_all(act.blocks, smap)
    kinds = [e["kind"] for e in ex]
    assert "alinea_order" in kinds, "(2) right after an article head without (1)"
    assert "drop_of_provision" in kinds
    assert "label_text_mismatch" in kinds, "Чл. 3 labelled n=4"
    assert "sign_order" in kinds
    assert "letter_order" not in kinds, "и) then к) is the Bulgarian lettering order"


def test_hidden_addresses_and_drops_inside_the_act_are_exceptions():
    """Second review, findings 7 and 8: a continuation or quoted label on an opener, and a drop between placed blocks."""
    act = _act(["ДОБАВИ", "Чл. 1. Едно.", "Чл. 2. Две.", "§ 2. Текст.", "бележка", "Чл. 3. Три.", "Релевантни актове"])
    smap = {0: {"label": "drop", "note": "chrome"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "continuation"},
            3: {"label": "quoted"}, 4: {"label": "drop", "note": "looks like chrome"}, 5: {"label": "article_head", "n": "3"},
            6: {"label": "drop", "note": "chrome"}}
    md, ex = run_all(act.blocks, smap)
    by = {(e["kind"], e["block"]) for e in ex}
    assert ("label_text_mismatch", 2) in by, "continuation on Чл. 2."
    assert ("label_text_mismatch", 3) in by, "quoted on § 2. with no quotation mark"
    assert ("drop_inside_act", 4) in by
    assert not any(e["block"] in (0, 6) and e["kind"].startswith("drop") for e in ex), "chrome before and after the act"
    smap[3] = {"label": "quoted"}
    act2 = _act(["Чл. 1. Едно.", "„Чл. 12. Цитат.“", "§ 2. След чл. 1001 се прибавя:", "Глава X-а", "Чл. 1001а. Текст.", "Чл. 1001б. Текст.", "-----", "Законът е приет."])
    smap2 = {0: {"label": "article_head", "n": "1"}, 1: {"label": "quoted"}, 2: {"label": "paragraph_sign", "n": "2"}, 3: {"label": "quoted"},
             4: {"label": "quoted"}, 5: {"label": "quoted"}, 6: {"label": "drop", "note": "separator"}, 7: {"label": "adoption_formula"}}
    _, ex2 = run_all(act2.blocks, smap2)
    assert not any(e["kind"] in ("label_text_mismatch", "drop_inside_act") for e in ex2), "a quoted run and a separator line pass"


def test_numbering_gaps_are_source_findings():
    from reading.ladder import SOURCE_FINDINGS
    act = _act(["Чл. 2. Две.", "Чл. 3. Три.", "Чл. 5. Пет.", "Чл. 5а. Пет-а.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 2. Текст.", "§ 4. Текст.",
                "КЪМ ЗАКОНА ЗА ИЗМЕНЕНИЕ", "§ 45. Текст.", "§ 48. Текст."])
    smap = {0: {"label": "article_head", "n": "2"}, 1: {"label": "article_head", "n": "3"}, 2: {"label": "article_head", "n": "5"},
            3: {"label": "article_head", "n": "5а"}, 4: {"label": "provisions_heading"}, 5: {"label": "paragraph_sign", "n": "2"},
            6: {"label": "paragraph_sign", "n": "4"}, 7: {"label": "provisions_heading"}, 8: {"label": "paragraph_sign", "n": "45"},
            9: {"label": "paragraph_sign", "n": "48"}}
    _, ex = run_all(act.blocks, smap)
    gaps = [(e["kind"], e["block"]) for e in ex if e["kind"] in ("article_gap", "sign_gap")]
    assert gaps == [("article_gap", 0), ("article_gap", 2), ("sign_gap", 5), ("sign_gap", 6)]
    act = _act(["Чл. 1. Едно.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. Текст.", "§ 2. Текст."])
    _, ex = run_all(act.blocks, {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"},
                                 2: {"label": "paragraph_sign", "n": "1"}, 3: {"label": "paragraph_sign", "n": "2"}})
    assert not any(e["kind"] in ("article_gap", "sign_gap") for e in ex)
    assert {"article_gap", "sign_gap"} <= SOURCE_FINDINGS


def test_first_alinea_is_read_only_from_the_head():
    act = _act(["Чл. 1. Лицата по т. 1 (2) са длъжни.", "(1) Първа", "Чл. 2. (Изм. - ДВ, бр. 1 от 2020 г., в сила от 01.01.2007 г. (*)) (1) Първа.", "(2) Втора",
                "§ 3. (1) Първа.", "(2) Втора"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "article_head", "n": "2"},
            3: {"label": "alinea", "n": "2"}, 4: {"label": "paragraph_sign", "n": "3"}, 5: {"label": "alinea", "n": "2"}}
    _, ex = run_all(act.blocks, smap)
    assert not any(e["kind"] == "alinea_order" for e in ex)


def test_validator_accepts_integer_numbers_and_splitter_folds_newlines():
    got, probs = validate_entries([{"i": 0, "label": "item", "n": 1}], [0])
    assert got[0]["n"] == "1" and not probs
    from reading.splitter import _WS
    assert _WS.sub(" ", "Чл. 1. Текст\r\n\nвтори ред") == "Чл. 1. Текст втори ред"


def test_collect_rebuilds_the_map_from_earlier_rounds(tmp_path, monkeypatch):
    """Second review, finding 5: re-collecting a round never keeps a later round's labels."""
    import json
    import subprocess
    import sys
    run = tmp_path / "runs"
    slug = "zakon-za-izplashtane-na-zadalzheniyata-ugovoreni-v-zlato"
    raw = Path(__file__).resolve().parents[2] / "data" / "raw" / "lexbg"
    import re as _re
    corpus = Path(__file__).resolve().parents[2] / "laws" / f"{slug}.md"
    if not corpus.exists():
        pytest.skip("corpus file not on disk")
    doc_id = _re.search(r"^identificador:\s*'?(-?\d+)'?", corpus.read_text(encoding="utf-8"), _re.M).group(1)
    if not (raw / f"{doc_id}.html").exists():
        pytest.skip("raw page not fetched")
    py = sys.executable
    root = Path(__file__).resolve().parents[2]
    assert subprocess.run([py, "reading/run.py", "prepare", "--slug", slug, "--out", str(run)], cwd=root, capture_output=True).returncode == 0
    d = run / slug
    blocks = json.loads((d / "blocks.json").read_text(encoding="utf-8"))["blocks"]
    # round 0: every block labelled continuation except the first (title), one of them with low confidence
    entries = [{"i": b["i"], "label": "title" if b["i"] == 0 else "unknown", "conf": "high"} for b in blocks]
    for t in sorted((d / "tasks" / "round0").glob("*.json")):
        task = json.loads(t.read_text(encoding="utf-8"))
        mine = [e for e in entries if e["i"] in {b["i"] for b in task["blocks"]}]
        (d / "maps" / "round0" / t.name).write_text(json.dumps(mine), encoding="utf-8")
    assert subprocess.run([py, "reading/run.py", "collect", "--slug", slug, "--round", "0", "--out", str(run)], cwd=root, capture_output=True).returncode == 0
    r1 = sorted((d / "tasks" / "round1").glob("*.json"))
    assert r1, "unknown labels make round-1 tasks"
    for t in r1:
        task = json.loads(t.read_text(encoding="utf-8"))
        (d / "maps" / "round1" / t.name).write_text(json.dumps([{"i": task["target"], "label": "editorial_note", "conf": "high"}]), encoding="utf-8")
    assert subprocess.run([py, "reading/run.py", "collect", "--slug", slug, "--round", "1", "--out", str(run)], cwd=root, capture_output=True).returncode == 0
    m1 = json.loads((d / "map.json").read_text(encoding="utf-8"))
    assert all(v["label"] in ("title", "editorial_note") for v in m1.values())
    # re-collect round 0: the round-1 labels are gone from the map, its answers set aside, its report removed
    assert subprocess.run([py, "reading/run.py", "collect", "--slug", slug, "--round", "0", "--out", str(run)], cwd=root, capture_output=True).returncode == 0
    m0 = json.loads((d / "map.json").read_text(encoding="utf-8"))
    assert all(v["label"] in ("title", "unknown") for v in m0.values())
    assert not (d / "report-round1.json").exists()
    assert not list((d / "maps" / "round1").glob("*.json"))
