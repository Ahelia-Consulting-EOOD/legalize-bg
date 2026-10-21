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
    act = _act(["ДОБАВИ В МОИТЕ АКТОВЕ", "Чл. 1. Едно.", "Чл. 2. Две.", "§ 2. Текст.", "бележка", "Чл. 3. Три.",
                "Релевантни актове от Европейското законодателство", "Регламенти:", "РЕГЛАМЕНТ (ЕС) 2024/1183"])
    smap = {0: {"label": "drop", "note": "chrome"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "continuation"},
            3: {"label": "quoted"}, 4: {"label": "drop", "note": "looks like chrome"}, 5: {"label": "article_head", "n": "3"},
            6: {"label": "drop", "note": "chrome"}, 7: {"label": "drop", "note": "chrome"}, 8: {"label": "drop", "note": "chrome"}}
    md, ex = run_all(act.blocks, smap)
    by = {(e["kind"], e["block"]) for e in ex}
    assert ("label_text_mismatch", 2) in by, "continuation on Чл. 2."
    assert ("label_text_mismatch", 3) in by, "quoted on § 2. with no quotation mark"
    assert ("drop_inside_act", 4) in by
    assert not any(e["block"] in (0, 6, 7, 8) and e["kind"].startswith("drop") for e in ex), "the page's known chrome before and after the act"
    smap[3] = {"label": "quoted"}
    act2 = _act(["Чл. 1. Едно.", "„Чл. 12. Цитат.“", "§ 2. След чл. 1001 се прибавя:", "„Глава X-а", "Чл. 1001а. Текст.", "Чл. 1001б. Текст.“", "-----", "Законът е приет."])
    smap2 = {0: {"label": "article_head", "n": "1"}, 1: {"label": "quoted"}, 2: {"label": "paragraph_sign", "n": "2"}, 3: {"label": "quoted"},
             4: {"label": "quoted"}, 5: {"label": "quoted"}, 6: {"label": "drop", "note": "separator"}, 7: {"label": "adoption_formula"}}
    _, ex2 = run_all(act2.blocks, smap2)
    assert not any(e["kind"] in ("label_text_mismatch", "drop_inside_act") for e in ex2), "a quoted run opened with a mark, and a separator line, pass"


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


def test_third_review_hidden_addresses_and_edge_drops():
    """Third review, M1 to M4: addresses under other labels, after a closed quotation, in a gap or after the last head; act text dropped at the edges."""
    # M1: a repealed article labelled repeal_note, also before a suffixed number
    act = _act(["ЗАКОН", "Чл. 1. а", "Чл. 2. Две.", "Чл. 3. (Отм. - ДВ, бр. 1 от 2000 г.)", "Чл. 3а. Текст."])
    smap = {0: {"label": "title"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "article_head", "n": "2"},
            3: {"label": "repeal_note"}, 4: {"label": "article_head", "n": "3а"}}
    _, ex = run_all(act.blocks, smap)
    assert ("hidden_address", 3) in {(e["kind"], e["block"]) for e in ex}
    for label in ("editorial_note", "unnumbered_alinea", "annex_row", "table_row", "chapter_heading", "unnumbered_item"):
        smap[3] = {"label": label}
        _, ex = run_all(act.blocks, smap)
        assert ("hidden_address", 3) in {(e["kind"], e["block"]) for e in ex}, label
    # M2: a quoted block after a closed quotation, in the act's own provisions and as the last §
    act = _act(["Чл. 1. Едно.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. В чл. 5 се създава ал. 3:", "„(3) Текст.“", "§ 2. Текст.", "§ 3. Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"}, 2: {"label": "paragraph_sign", "n": "1"},
            3: {"label": "quoted"}, 4: {"label": "quoted"}, 5: {"label": "paragraph_sign", "n": "3"}}
    _, ex = run_all(act.blocks, smap)
    kinds = {(e["kind"], e["block"]) for e in ex}
    assert ("label_text_mismatch", 4) in kinds, "§ 2 after a closed quotation is not in the run"
    act2 = _act([b.text for b in act.blocks[:5]])
    _, ex = run_all(act2.blocks, {k: v for k, v in smap.items() if k < 5})
    assert ("label_text_mismatch", 4) in {(e["kind"], e["block"]) for e in ex}, "also when it is the act's last §"
    # M2/M3: a chapter of the act hidden as a quoted run at the end of the article sequence
    act = _act(["Чл. 1. Едно.", "Чл. 2. Две.", "Глава трета", "Чл. 3. Три.", "Чл. 4. Четири.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "article_head", "n": "2"}, 2: {"label": "quoted"}, 3: {"label": "quoted"},
            4: {"label": "quoted"}, 5: {"label": "provisions_heading"}, 6: {"label": "paragraph_sign", "n": "1"}}
    _, ex = run_all(act.blocks, smap)
    assert {("label_text_mismatch", 3), ("label_text_mismatch", 4)} <= {(e["kind"], e["block"]) for e in ex}, "a run with no mark cannot hide a chapter"
    # the ЗЗД case: an amending § introduces provisions of another act printed without quotation marks; they go to the ladder
    act = _act(["Чл. 1. Едно.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. След чл. 1001 се прибавя:", "Глава X-а", "Чл. 1001а. Текст.", "Чл. 1001б. Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"}, 2: {"label": "paragraph_sign", "n": "1"},
            3: {"label": "quoted"}, 4: {"label": "quoted"}, 5: {"label": "quoted"}}
    _, ex = run_all(act.blocks, smap)
    assert [e["block"] for e in ex if e["kind"] == "label_text_mismatch"] == [4, 5]
    # M4: act text dropped at the edges; a separator cell inside a table is not a separator line
    act = _act(["ЗАКОН ЗА X", "Чл. 1. Едно.", "Вид", "....................", "Чл. 2. Две.", "Законът е приет от 41-ото Народно събрание.", "Приложение № 1 към чл. 1", "Образец"])
    smap = {0: {"label": "drop", "note": "chrome"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "table_row"}, 3: {"label": "drop", "note": "dash"},
            4: {"label": "article_head", "n": "2"}, 5: {"label": "drop", "note": "formula"}, 6: {"label": "drop", "note": "annex"}, 7: {"label": "drop", "note": "annex"}}
    _, ex = run_all(act.blocks, smap)
    by = {(e["kind"], e["block"]) for e in ex}
    assert {("drop_outside_act", 0), ("drop_inside_act", 3), ("drop_outside_act", 5), ("drop_outside_act", 6), ("drop_outside_act", 7)} <= by
    # the ЗЗД fragment
    _, ex = run_all(_act(["Чл. 5./span> до 7"]).blocks, {0: {"label": "unnumbered_alinea"}})
    assert any(e["kind"] == "fragment" for e in ex)


def test_fourth_review_quoted_runs_last_provisions_malformed_heads_and_placed_chrome():
    """Fourth review: a quoted run is anchored by an opening mark; the last alinea or item cannot hide as quoted;
    a malformed § head is a source finding; the page's chrome under a content label is an exception."""
    # A: a run that stays open through a block ending with a closing mark and punctuation
    act = _act(["Чл. 1. Едно:", "„(4) Текстът се прилага.“;", "Чл. 1а. Текст.", "Чл. 2. Две."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "quoted"}, 2: {"label": "quoted"}, 3: {"label": "article_head", "n": "2"}}
    _, ex = run_all(act.blocks, smap)
    assert ("label_text_mismatch", 2) in {(e["kind"], e["block"]) for e in ex}, "the quotation closed with “; so Чл. 1а is outside it"
    # B: a run opened without a mark
    act = _act(["Чл. 1. Едно:", "Текст без кавички", "Чл. 1а. Текст."])
    _, ex = run_all(act.blocks, {0: {"label": "article_head", "n": "1"}, 1: {"label": "quoted"}, 2: {"label": "quoted"}})
    assert ("label_text_mismatch", 2) in {(e["kind"], e["block"]) for e in ex}
    # a marked run that spans blocks passes
    act = _act(["§ 1. В чл. 5 се създава:", "„(3) Текст,", "който продължава", "и свършва.“", "§ 2. Текст."])
    smap = {0: {"label": "paragraph_sign", "n": "1"}, 1: {"label": "quoted"}, 2: {"label": "quoted"}, 3: {"label": "quoted"}, 4: {"label": "paragraph_sign", "n": "2"}}
    _, ex = run_all(act.blocks, smap)
    assert not ex
    # E: the last alinea or item labelled quoted
    for last in ("(2) Втора.", "2. кметът."):
        act = _act(["Чл. 1. Едно.", "(1) Първа:", "1. областният управител;", last, "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1. Текст."])
        smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "alinea", "n": "1"}, 2: {"label": "item", "n": "1"}, 3: {"label": "quoted"},
                4: {"label": "provisions_heading"}, 5: {"label": "paragraph_sign", "n": "1"}}
        _, ex = run_all(act.blocks, smap)
        assert ("label_text_mismatch", 3) in {(e["kind"], e["block"]) for e in ex}, last
    # malformed § heads are heads with a source finding, not label errors
    act = _act(["Чл. 1. Едно.", "ЗАКЛЮЧИТЕЛНИ РАЗПОРЕДБИ", "§ 1 По смисъла на наредбата", "§ 2 . Изпитът се провежда"])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "provisions_heading"}, 2: {"label": "paragraph_sign", "n": "1"}, 3: {"label": "paragraph_sign", "n": "2"}}
    _, ex = run_all(act.blocks, smap)
    assert [e["kind"] for e in ex] == ["malformed_head", "malformed_head"]
    # the page's chrome under a content label
    act = _act(["ДОБАВИ В МОИТЕ АКТОВЕ", "Чл. 1. Едно.", "Релевантни актове от Европейското законодателство"])
    _, ex = run_all(act.blocks, {0: {"label": "preamble"}, 1: {"label": "article_head", "n": "1"}, 2: {"label": "annex_heading"}})
    assert [e["block"] for e in ex if e["kind"] == "chrome_placed"] == [0, 2]


def test_annex_articles_are_annex_rows_not_hidden_addresses():
    act = _act(["Чл. 1. Едно.", "Чл. 2. Две.", "Приложение към чл. 2", "ФИНАНСОВИ ПРАВИЛА", "Чл. 1. Бюджетът.", "(2) Текст."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "annex_row"}, 2: {"label": "annex_heading"}, 3: {"label": "annex_heading"},
            4: {"label": "annex_row"}, 5: {"label": "annex_row"}}
    _, ex = run_all(act.blocks, smap)
    assert [e["block"] for e in ex if e["kind"] == "hidden_address"] == [1], "an annex_row before any annex heading still hides an address"


def test_provisions_heading_groups_without_kam_and_quoted_section_numbers():
    """Наказателен кодекс: lex.bg omits "КЪМ" on one amending block, inverts the heading order on another, numbers a section 'Раздел I "а".'."""
    act = _act(["Чл. 1. Едно.", 'Раздел I "а".', "Престъпления против кредиторите", "Чл. 2. Две.",
                "Преходни и Заключителни разпоредби", "§ 1. Текст.", "§ 2. Текст.",
                "Преходни и Заключителни разпоредби", "ЗАКОНА ЗА БЮДЖЕТА ЗА 2015 Г.", "(ОБН. - ДВ, БР. 107 ОТ 2014 Г.)", "§ 10. Текст.",
                "Преходни и Заключителни разпоредби", "КЪМ ЗАКОНА ЗА ДЪРЖАВНА АГЕНЦИЯ", "Преходни и Заключителни разпоредби", "§ 3. Текст.",
                "Допълнителна разпоредба", "Обяснение на някои думи", "Чл. 3. Думите."])
    smap = {0: {"label": "article_head", "n": "1"}, 1: {"label": "section_heading"}, 2: {"label": "section_heading"}, 3: {"label": "article_head", "n": "2"},
            4: {"label": "provisions_heading"}, 5: {"label": "paragraph_sign", "n": "1"}, 6: {"label": "paragraph_sign", "n": "2"},
            7: {"label": "provisions_heading"}, 8: {"label": "provisions_heading"}, 9: {"label": "editorial_note"}, 10: {"label": "paragraph_sign", "n": "10"},
            11: {"label": "provisions_heading"}, 12: {"label": "provisions_heading"}, 13: {"label": "provisions_heading"}, 14: {"label": "paragraph_sign", "n": "3"},
            15: {"label": "provisions_heading"}, 16: {"label": "provisions_heading"}, 17: {"label": "article_head", "n": "3"}}
    md, ex = run_all(act.blocks, smap)
    assert not [e for e in ex if e["kind"] in ("empty_section", "sign_order", "sign_gap", "article_gap")], ex
    assert '#### Раздел I "а". Престъпления против кредиторите' in md


def test_news_and_forum_footer_is_tail_chrome():
    """Наредба № 5's page ends with lex.bg's news-and-forum footer instead of the EU list; forum titles open like provisions."""
    act = _act(["Чл. 1. Едно.", "Новини", "Почина съдия", "Форум", "Чл.159 Ал. 1 от ЗДП", "© Lex.bg | общи условия"])
    smap = {0: {"label": "article_head", "n": "1"}}
    smap.update({i: {"label": "drop", "note": "footer"} for i in range(1, 6)})
    _, ex = run_all(act.blocks, smap)
    assert not [e for e in ex if e["kind"].startswith("drop")], ex
    smap[1] = {"label": "annex_row"}
    _, ex = run_all(act.blocks, smap)
    assert any(e["kind"] == "chrome_placed" and e["block"] == 1 for e in ex)


def test_fifth_review_sub_letters_superscripts_elisions_quoted_chapters_and_nested_items():
    """ЗДДС, ДОПК, ГПК, КТК: doubled and tripled sub-letters, a two-digit superscript leaked as 'SUP>13', lex.bg's
    dotted elision line before a list that resumes at 5., a chapter quoted in full whose first line holds an inner
    quotation, a numbered sub-list under an item that ends with a colon, an item head without its space, and the
    correspondence-table link under the title."""
    # the validator accepts аа) and ааа), and a superscript of two digits
    smap, problems = validate_entries([{"i": 0, "label": "letter", "n": "аа"}, {"i": 1, "label": "letter", "n": "ббб"},
                                       {"i": 2, "label": "article_head", "n": "143я13"}], [0, 1, 2])
    assert not problems and len(smap) == 3
    act = _act(["ГРАЖДАНСКИ ПРОЦЕСУАЛЕН КОДЕКС", "Таблица за съответствие между разпоредбите на ГПК (нов) и ГПК (отм.)",
                "Чл. 1. Едно:", "1. първо:", "а) буква:", "аа) под-буква;", "бб) под-буква:", "ааа) под-под-буква;", "ббб) под-под-буква;",
                "вв) под-буква;", "б) буква;", "2. второ.",
                "Чл. 143я.SUP>13. (Нов - ДВ, бр. 100 от 2022 г.) (1) Текст.", "(2) Текст.",
                "Чл. 144. (1) Списък:", "1. Лице е:", "1. едно;", "2. две.", "2. Друго.",
                "Чл. 145. Текст:", "1.Член 708 се изменя така:",
                "Преходни и Заключителни разпоредби", "§ 1. В Закона:", "1. Създава се глава трета \"а\":",
                '"Глава трета "а"', "ПРОИЗВОДСТВО ЗА ВРЪЩАНЕ", "Чл. 22а. (1) Молбата.", "(2) Текст.", 'Чл. 22б. Съдът."',
                "2. В чл. 25 се създава т. 5:", '"5. в случаите."',
                "§ 2. В Кодекса:", ". . . . . . . . . . . . . . . . . .", "5. Навсякъде думите се заменят.", "6. В останалите текстове.",
                '7. В чл. 20 думите "7:1" се заменят със "съотношение, както следва:', "а) за 2000 г. - 80:20;", 'б) за 2002 г. - 75:25."', "8. Член 109 се отменя."])
    smap = {0: {"label": "title"}, 1: {"label": "drop", "note": "lex.bg link to a correspondence table"},
            2: {"label": "article_head", "n": "1"}, 3: {"label": "item", "n": "1"}, 4: {"label": "letter", "n": "а"},
            5: {"label": "letter", "n": "аа"}, 6: {"label": "letter", "n": "бб"}, 7: {"label": "letter", "n": "ааа"}, 8: {"label": "letter", "n": "ббб"},
            9: {"label": "letter", "n": "вв"}, 10: {"label": "letter", "n": "б"}, 11: {"label": "item", "n": "2"},
            12: {"label": "article_head", "n": "143я13"}, 13: {"label": "alinea", "n": "2"},
            14: {"label": "article_head", "n": "144"}, 15: {"label": "item", "n": "1"}, 16: {"label": "item", "n": "1"}, 17: {"label": "item", "n": "2"},
            18: {"label": "item", "n": "2"}, 19: {"label": "article_head", "n": "145"}, 20: {"label": "item", "n": "1"},
            21: {"label": "provisions_heading"}, 22: {"label": "paragraph_sign", "n": "1"}, 23: {"label": "item", "n": "1"}}
    smap.update({i: {"label": "quoted"} for i in range(24, 29)})
    smap.update({29: {"label": "item", "n": "2"}, 30: {"label": "quoted"}, 31: {"label": "paragraph_sign", "n": "2"},
                 32: {"label": "editorial_note"}, 33: {"label": "item", "n": "5"}, 34: {"label": "item", "n": "6"},
                 35: {"label": "item", "n": "7"}, 36: {"label": "quoted"}, 37: {"label": "quoted"}, 38: {"label": "item", "n": "8"}})
    _, ex = run_all(act.blocks, smap)
    kinds = {e["kind"] for e in ex}
    assert not kinds & {"letter_order", "item_order", "alinea_order", "label_text_mismatch", "drop_inside_act", "article_gap"}, ex
    assert [e["block"] for e in ex if e["kind"] == "malformed_head"] == [20]
    assert [e["block"] for e in ex if e["kind"] == "fragment"] == [12]
    # the same sub-letters out of order, and a sub-list that does not open under a colon, are still exceptions
    smap[8] = {"label": "letter", "n": "ггг"}
    act.blocks[15].text = "1. Лице е;"
    _, ex = run_all(act.blocks, smap)
    assert any(e["kind"] == "letter_order" and e["block"] == 8 for e in ex)
    assert any(e["kind"] == "item_order" and e["block"] == 16 for e in ex)
