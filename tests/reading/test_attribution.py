"""The attribution step (reading/attribution.py): which corpus act a material changes, from its fixed-form citations."""
import json

from fetcher.dv.resolver import CorpusAct
from reading import attribution as A, material as M
from reading.splitter import Block, SplitAct


def _corpus(*rows):
    acts = []
    for law_id, title, dv_issue, dv_year, category in rows:
        acts.append(CorpusAct(law_id=law_id, title=title, act_type=title.split()[0].casefold(), category=category, dv_issue=dv_issue, dv_year=dv_year,
                              fecha_publicacion=f"{dv_year}-01-01", estado="vigente", chain=frozenset({(dv_year, int(dv_issue))}),
                              amendment_history=(((dv_year, int(dv_issue)), f"{dv_year}-01-01"),)))
    return A.Attributor(acts)


ATTR = _corpus(("zakon-za-gorite", "ЗАКОН ЗА ГОРИТЕ", "19", 2011, "laws"),
               ("semeen-kodeks", "СЕМЕЕН КОДЕКС", "47", 2009, "codes"),
               ("naredba-5-ot-2006", "НАРЕДБА № 5 ОТ 28 ДЕКЕМВРИ 2006 Г. ЗА ТЕХНИЧЕСКИТЕ ПАСПОРТИ НА СТРОЕЖИТЕ", "7", 2007, "ordinances"),
               ("up-mf-2016", "УСТРОЙСТВЕН ПРАВИЛНИК НА МИНИСТЕРСТВОТО НА ФИНАНСИТЕ", "100", 2016, "regulations"),
               ("up-mf-2009", "УСТРОЙСТВЕН ПРАВИЛНИК НА МИНИСТЕРСТВОТО НА ФИНАНСИТЕ", "85", 2009, "regulations"))


def test_a_title_with_its_promulgation_attributes_and_a_predecessor_is_told_apart():
    t = ATTR.resolve("title", "Закона за горите", [19, 2011])
    assert (t.status, t.how, t.slug) == ("attributed", "title+promulgation", "zakon-za-gorite")
    old = ATTR.resolve("§18", "Закона за горите", [125, 1997])
    assert (old.status, old.slug) == ("predecessor_or_other", None) and "19/2011" in old.note and "125/1997" in old.note
    same = ATTR.resolve("title", "Устройствения правилник на Министерството на финансите", [85, 2009])
    assert same.slug == "up-mf-2009", "two corpus acts carry the title; the cited promulgation decides"
    assert ATTR.resolve("title", "Устройствения правилник на Министерството на финансите", None).status == "ambiguous"
    adj = ATTR.resolve("§3", "Семейния кодекс", [47, 2009])
    assert adj.slug == "semeen-kodeks", "an adjectival title is read back to its nominative"


def test_a_type_outside_the_corpus_and_a_numbered_ordinance():
    t = ATTR.resolve("title", "Тарифата за таксите, които се събират по Закона за туризма", [28, 2021])
    assert (t.status, t.how) == ("not_in_corpus", "type_outside_corpus")
    n = ATTR.resolve("title", "Наредба № 5 от 2006 г. за техническите паспорти на строежите", [7, 2007])
    assert n.slug == "naredba-5-ot-2006" and n.how in ("resolver", "title+promulgation")
    assert ATTR.resolve("title", "Закона за пробата", None).status == "not_in_corpus"


def _material(lines, hints=None):
    hints = hints or {}
    return M.parse(SplitAct(blocks=[Block(i, t, hints.get(i, "DvJustify")) for i, t in enumerate(lines)], sections=[], source="dv"))


def test_attribute_records_the_title_target_and_every_cross_act_target_in_the_fixed_form():
    m = _material(["ЗАКОН", "за изменение на Закона за горите", "(обн., ДВ, бр. 19 от 2011 г.)",
                   "§ 1. В чл. 4 думите „а“ се заменят с „б“.", "Преходни и заключителни разпоредби",
                   "§ 2. В Семейния кодекс (обн., ДВ, бр. 47 от 2009 г.) в чл. 5 думите „а“ се заменят с „б“.",
                   "§ 3. В Закона за горите (обн., ДВ, бр. 125 от 1997 г.) чл. 7 се отменя.",
                   "Законът е приет от 52-рото Народно събрание.", "Председател на Народното събрание: Михаела Доцова", "4984"],
                  {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 4: "DvCenter", 8: "DvRight"})
    rec = ATTR.attribute(123, m, {"title": "Закон за изменение на Закона за горите", "issue_number": 5, "issue_year": 2026, "section": "Народно събрание"})
    assert rec["status"] == "amends_corpus_act" and rec["issue"] == "5/2026"
    assert [(t["scope"], t["status"], t["slug"]) for t in rec["targets"]] == [("title", "attributed", "zakon-za-gorite"), ("§2", "attributed", "semeen-kodeks"),
                                                                              ("§3", "predecessor_or_other", None)]
    assert A.check(rec) == []
    rec["targets"][0]["status"] = "guessed"
    assert A.check(rec) and "guessed" in A.check(rec)[0]


def test_a_material_that_amends_no_corpus_act_and_one_with_parse_findings():
    other = _material(["ПОСТАНОВЛЕНИЕ № 160 ОТ 25 СЕПТЕМВРИ 2026 Г.", "за изменение на Тарифата за таксите, които се събират от Патентното ведомство", "МИНИСТЕРСКИЯТ СЪВЕТ", "ПОСТАНОВИ:",
                       "§ 1. В чл. 1 числото „10“ се заменя с „20“.", "Министър-председател: Румен Радев", "5000"], {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 3: "DvCenter", 5: "DvRight"})
    rec = ATTR.attribute(1, other)
    assert rec["status"] == "amends_other_acts" and rec["targets"][0]["how"] == "type_outside_corpus"
    broken = _material(["ЗАКОН", "за изменение на Закона за горите", "(обн., ДВ, бр. 19 от 2011 г.)", "§ 1. Член 4 се изменя така:",
                        "Чл. 4. Нов текст без кавички.", "Законът е приет.", "Председател на Народното събрание: Х", "1"], {0: "DvCenter", 1: "DvCenter", 2: "DvCenter", 6: "DvRight"})
    rec = ATTR.attribute(2, broken)
    assert rec["status"] == "parse_findings" and rec["findings"][0]["kind"] == "unquoted_provision" and rec["targets"][0]["slug"] == "zakon-za-gorite"


def test_measure_writes_one_record_per_material_and_a_summary(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    html = ('<html><body><div style=" width: 100%;"><p style="text-align: center">ЗАКОН</p><p style="text-align: center">за изменение на Закона за горите</p>'
            '<p style="text-align: center">(обн., ДВ, бр. 19 от 2011 г.)</p><p>§ 1. В чл. 4 думите „а“ се заменят с „б“.</p>'
            '<p>Законът е приет от 52-рото Народно събрание.</p><p style="text-align: right">Председател на Народното събрание: Х</p><p>4984</p></div></body></html>')
    (cache / "77.html").write_text(html, encoding="utf-8")
    summary = A.measure([77], tmp_path / "out", attr=ATTR, cache_dir=cache)
    rec = json.loads((tmp_path / "out" / "materials" / "77.json").read_text(encoding="utf-8"))
    assert rec["status"] == "amends_corpus_act" and rec["targets"][0]["slug"] == "zakon-za-gorite" and rec["instructions"] == 1
    assert summary["materials"] == 1 and summary["by_status"] == {"amends_corpus_act": 1} and summary["check_problems"] == []
    assert json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))["targets_by_how"] == {"title+promulgation": 1}


def test_a_decree_cited_for_the_act_it_adopts_and_an_amending_act_are_outside_the_corpus():
    # the review of 1 November 2026, B2 (material 246585 § 4)
    t = ATTR.resolve("§4", "Постановление № 266 на Министерския съвет от 2009 г. за приемане на Устройствен правилник на Министерството на финансите", [100, 2016])
    assert (t.status, t.how) == ("not_in_corpus", "type_outside_corpus") and "Устройствен правилник" in t.note
    a = ATTR.resolve("§25", "Закона за изменение и допълнение на Закона за горите", [94, 2015])
    assert (a.status, a.how) == ("not_in_corpus", "amending_act")


def test_the_full_definite_form_of_a_repealed_act_is_found():
    # B3 (material 245888 § 75): „Законът за … (обн., …) се отменя“
    t = ATTR.resolve("§75", "Законът за горите", [19, 2011], repeal=True)
    assert (t.status, t.slug, t.repeal) == ("attributed", "zakon-za-gorite", True)
    assert ATTR.resolve("§1", "Кодексът на пробата", None).status == "not_in_corpus"


def test_the_check_fails_on_a_promulgation_that_disagrees_and_on_a_missed_candidate():
    rec = {"material": 1, "status": "amends_corpus_act", "targets": [{"scope": "title", "status": "attributed", "how": "title+promulgation", "slug": "zakon-za-gorite",
                                                                      "cited_promulgation": [19, 2011], "act_promulgation": [19, 2011], "candidates": []}]}
    assert A.check(rec, ATTR.by_id) == []
    rec["targets"][0]["act_promulgation"] = [125, 1997]
    assert "is not the cited" in A.check(rec, ATTR.by_id)[0]
    missed = {"material": 2, "status": "amends_other_acts", "targets": [{"scope": "§8", "status": "not_in_corpus", "how": "resolver", "slug": None,
                                                                         "cited_promulgation": [19, 2011], "act_promulgation": None, "candidates": ["zakon-za-gorite"]}]}
    assert "was promulgated in the cited" in A.check(missed, ATTR.by_id)[0]
    assert A.check(missed) == [], "without the corpus the candidate check cannot run"
