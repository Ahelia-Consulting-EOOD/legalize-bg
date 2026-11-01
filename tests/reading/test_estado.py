"""The estado run (reading/estado.py): lex.bg's history line and repeal note read with a fixed form, the act's repeal written through the gate."""
import json
import subprocess
from pathlib import Path

import pytest

from corpus_gate import render_act
from reading import estado as E
from refresh import _split_frontmatter

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw" / "lexbg"
TODAY = "2026-11-01"

REPEALED = "Обн. ДВ. бр. 97 от 7 Декември 1979г. , попр. ДВ. бр. 98 от 11 Декември 1979г. , изм. ДВ. бр. 48 от 18 Юни 1991г. , отм. ДВ. бр. 64 от 4 Август 2000г."
ALIVE = "Обн. ДВ. бр. 23 от 17 Март 2006г. , изм. и доп. ДВ. бр. 54 от 12 Юни 2026г."


def test_the_form_reads_the_repeal_as_the_last_entry():
    r = E.parse_history(REPEALED)
    assert (r.status, r.repeal_issue, r.repeal_date, r.marker) == ("repealed", "64/2000", "2000-08-04", "отм. ДВ. бр. 64 от 4 Август 2000г.")
    assert [e.verb for e in r.entries] == ["Обн.", "попр.", "изм.", "отм."]
    assert [e.issue for e in r.entries] == ["97/1979", "98/1979", "48/1991", "64/2000"]


def test_a_line_without_the_word_is_not_repealed_and_an_empty_one_has_no_history():
    assert E.parse_history(ALIVE).status == "not_repealed"
    assert E.parse_history("").status == "no_history"
    assert E.parse_history(None).status == "no_history"
    assert E.parse_history("   ").status == "no_history"


@pytest.mark.parametrize("line, says", [
    ("Обн. ДВ. бр. 82 от 19 Октомври 2010г. , отм. ДВ. бр. 97 от 15 Ноември 2024г. , изм. ДВ. бр. 58 от 18 Юли 2025г.", "1 Gazette entry follow"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , отм. ДВ. бр. 2 от 4 Януари 2005г. , отм. ДВ. бр. 3 от 5 Януари 2006г.", "2 entries carry"),
    ("Приета с Решение № 332 по Протокол № 48 от 19.05.2005 г.; отм. с Решение № 1867 от 28.02.2022 г. на ВАС", "no Gazette entry at all"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , изм. (отм. чл. 3) ДВ. бр. 2 от 4 Януари 2005г.", "not „отм.“ alone"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , отм. и доп. ДВ. бр. 2 от 4 Януари 2005г.", "not „отм.“ alone"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , отм. ДВ. бр. 2 от 2005г.", "no full date"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , отм. ДВ. бр. 2 от 4 Януари 2005г. (отм. частично)", "after the last Gazette entry"),
    ("Обн. ДВ. бр. 1 от 3 Януари 2004г. , изм. ДВ. бр. 2 от 4 Януари 2005г. ; частично отм.", "after the last Gazette entry"),
])
def test_every_other_line_with_the_word_is_unsettled_with_its_reason(line, says):
    r = E.parse_history(line)
    assert r.status == "unsettled" and says in r.reason, r.reason
    assert r.repeal_issue is None and r.repeal_date is None


def test_an_entry_in_numeric_date_form_is_read_too():
    r = E.parse_history("Обн. ДВ. бр. 1 от 03.01.2004 г. , отм. ДВ. бр. 2 от 04.01.2005 г.")
    assert (r.status, r.repeal_issue, r.repeal_date) == ("repealed", "2/2005", "2005-01-04")


HISTORY = '<span class="HistoryItem">Обн. ДВ. бр.<span class="HistoryReference">10</span> от 5 Февруари 2010г.</span> , <span class="HistoryItem">отм. ДВ. бр.<span class="HistoryReference">20</span> от 6 Март 2015г.</span>'
NOTE = "Отменена с <span>§ 2</span> от преходните и заключителните разпоредби на Наредба № 7 от 1 март 2015 г. за пробите - ДВ, бр. 20 от 6 март 2015 г., в сила от 10.03.2015 г."
PAGE = """<html><body><div class="box"><div class="boxi">
<div class="TitleDocument" id="DocumentTitle"><p class="Title">НАРЕДБА ЗА ПРОБАТА<br/></p></div>
<div class="HistoryOfDocument" id="historyOfDocument"><p class="Title">{history}</p></div>
<div><div>{note}</div></div>
<div class="Article">Чл. 1. Пробата.</div>
</div></div></body></html>"""


def page(history=HISTORY, note=NOTE) -> bytes:
    return PAGE.format(history=history, note=note).encode("cp1251")


def test_a_page_gives_the_reading_with_its_note_the_repealing_act_and_the_entry_into_force():
    r = E.read_page(page(), TODAY)
    assert (r.status, r.repeal_issue, r.repeal_date, r.note_issue, r.in_force) == ("repealed", "20/2015", "2015-03-06", "20/2015", "2015-03-10")
    assert r.note.startswith("Отменена с § 2 от преходните") and r.repealing_act == "§ 2 от преходните и заключителните разпоредби на Наредба № 7 от 1 март 2015 г. за пробите"
    assert E.read_page(page(history="", note=""), TODAY).reason == "the page's HistoryOfDocument element is empty"
    assert "no repeal entry" in E.read_page(page(history=""), TODAY).reason   # an empty line under a repeal note is listed, not passed over
    assert E.read_page(b"<html><body>x</body></html>", TODAY).reason == "the page carries no HistoryOfDocument element"
    assert E.read_page(None, TODAY).reason == "no page in the raw store"


def test_the_note_forms_the_masculine_and_the_latin_letter_and_a_date_in_name_form():
    r = E.read_page(page(note=NOTE.replace("Отменена с", "Отменен с")), TODAY)
    assert r.status == "repealed"
    r = E.read_page(page(note=NOTE.replace("Отменена с", "Отмененa с")), TODAY)   # Latin a, as lex.bg prints it on one page
    assert r.status == "repealed"
    r = E.read_page(page(note=NOTE.replace("в сила от 10.03.2015 г.", "в сила от 10 март 2015 г.")), TODAY)
    assert (r.status, r.in_force) == ("repealed", "2015-03-10")


@pytest.mark.parametrize("note, status, says", [
    (NOTE.replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г."), "repeal_pending", "takes effect on 2027-01-01"),
    (NOTE.replace("в сила от 10.03.2015 г.", "в сила считано от момента на започване на функционирането на ЕИСЕС"), "unsettled", "not a fixed date"),
    (NOTE.replace("в сила от 10.03.2015 г.", ""), "unsettled", "not a fixed date"),
    ("Отменено основание. С § 2 от преходните и заключителните разпоредби на Закона за пробите е отменен Законът за опитите - ДВ, бр. 20 от 6 март 2015 г., в сила от 1 март 2015 г.", "unsettled", "legal basis"),
    (NOTE.replace("бр. 20 от 6 март 2015 г.", "бр. 21 от 10 март 2015 г."), "unsettled", "the note names ДВ бр. 21/2015 and the line's repeal entry ДВ бр. 20/2015"),
    ("", "unsettled", "no note"),
    ("Някаква друга бележка.", "unsettled", "no note"),
])
def test_the_note_decides_pending_or_unsettled(note, status, says):
    r = E.read_page(page(note=note), TODAY)
    assert r.status == status and says in r.reason, (r.status, r.reason)


def test_the_entry_into_force_is_read_only_after_the_issue_never_from_the_repealing_acts_title():
    titled = NOTE.replace("за пробите", "за пробите (загл. изм. - ДВ, бр. 60 от 2025 г., в сила от 25.07.2025 г.)").replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г.")
    parts = E.parse_note(titled)
    assert parts["kind"] == "other" and parts["in_force"] is None   # two „в сила“, two „ДВ, бр.“: not read, listed
    r = E.read_page(page(note=titled), TODAY)
    assert r.status == "unsettled" and "form the parser does not read" in r.reason
    only_title = NOTE.replace("за пробите", "за пробите (в сила от 25.07.2015 г.)").replace(", в сила от 10.03.2015 г.", "")
    assert E.parse_note(only_title)["in_force"] is None   # a date inside the title is never the entry into force
    assert E.read_page(page(note=only_title), TODAY).reason == "the note's entry into force is not a fixed date"


def test_a_note_in_a_form_the_parser_does_not_read_is_unsettled_on_any_line():
    for note in ("Отменено с § 1 от Правила за пробите - ДВ, бр. 20 от 6 март 2015 г., в сила от 10.03.2015 г.", "Отменени с § 1 от нещо.", "Отменен."):
        r = E.read_page(page(note=note), TODAY)
        assert r.status == "unsettled" and "form the parser does not read" in r.reason, (note, r.status)
        alive = HISTORY.replace("отм. ДВ. бр.", "изм. ДВ. бр.")
        r = E.read_page(page(history=alive, note=note), TODAY)
        assert r.status == "unsettled" and "form the parser does not read" in r.reason, (note, r.status)


def test_the_note_is_looked_for_before_the_first_provision_only():
    body_note = PAGE.format(history=HISTORY.replace("отм. ДВ. бр.", "изм. ДВ. бр."), note="").replace(
        '<div class="Article">Чл. 1. Пробата.</div>', '<div class="Article">Чл. 1. Пробата.</div><div class="Article">Отменена с чл. 5 заповедта - ДВ, бр. 1 от 2 януари 2015 г., в сила от 02.01.2015 г.</div>')
    assert E.read_page(body_note.encode("cp1251"), TODAY).status == "not_repealed"
    # a municipal page prints „Публикуван: …“ in an article element above the note: the note is still found
    above = PAGE.format(history=HISTORY, note="").replace('<div class="Article">Чл. 1. Пробата.</div>',
                                                          '<div class="Article">Публикуван: https://example.test</div><div class="Article">' + NOTE + '</div><div class="Article">Чл. 1. Пробата.</div>')
    assert E.read_page(above.encode("cp1251"), TODAY).status == "repealed"


def test_a_pending_repeal_becomes_a_repeal_on_its_day():
    note = NOTE.replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г.")
    assert E.read_page(page(note=note), "2026-12-31").status == "repeal_pending"
    assert E.read_page(page(note=note), "2027-01-01").status == "repealed"


def test_a_note_without_a_repeal_entry_and_a_basis_note_on_an_alive_line_are_unsettled():
    alive = HISTORY.replace("отм. ДВ. бр.", "изм. ДВ. бр.")
    r = E.read_page(page(history=alive), TODAY)
    assert r.status == "unsettled" and "no repeal entry" in r.reason
    r = E.read_page(page(history=alive, note="Отменено основание. С § 2 е отменен Законът за опитите - ДВ, бр. 20 от 6 март 2015 г."), TODAY)
    assert r.status == "unsettled" and "legal basis" in r.reason
    assert E.read_page(page(history=alive, note=""), TODAY).status == "not_repealed"


@pytest.mark.skipif(not (RAW / "-554909183.html").exists(), reason="the raw store is not here")
def test_the_postal_ordinance_page_is_unsettled_its_note_repeals_the_basis():
    r = E.read_page((RAW / "-554909183.html").read_bytes(), TODAY)
    assert r.status == "unsettled" and "legal basis" in r.reason
    assert (r.repeal_issue, r.repeal_date) == ("64/2000", "2000-08-04") and "Законът за съобщенията" in r.note and r.repealing_act is None


@pytest.mark.skipif(not (RAW / "2135699150.html").exists(), reason="the raw store is not here")
@pytest.mark.parametrize("doc, status, says", [
    ("2135699150", "unsettled", "1 Gazette entry follow"),
    ("2135869662", "unsettled", "2 Gazette entries follow"),
    ("2135584936", "unsettled", "no Gazette entry"),
    ("2135794446", "unsettled", "not a fixed date"),
    ("-550490623", "unsettled", "no repeal entry"),
    ("2137213264", "repeal_pending", "2027-01-01"),
    ("2135880580", "repealed", ""),
    ("2136492309", "repealed", ""),
])
def test_the_real_pages_of_the_corpus_read_as_the_report_says(doc, status, says):
    r = E.read_page((RAW / f"{doc}.html").read_bytes(), TODAY)
    assert r.status == status and says in (r.reason or ""), (r.status, r.reason)
    if status == "repealed":
        assert r.in_force and r.in_force <= TODAY and r.note_issue == r.repeal_issue


COMMITTED = {"titulo": "НАРЕДБА ЗА ПРОБАТА", "identificador": "999", "pais": "bg", "rango": "наредба",
             "fecha_publicacion": "2010-02-05", "ultima_actualizacion": "2010-02-05", "estado": "vigente",
             "fuente": "lex.bg", "dv_issue": "10", "dv_year": 2010, "effective_date": None, "category": "ordinances",
             "eli": "/eli/bg/наредба/2010/2/5/naredba-za-probata/con", "amendment_history": [{"dv": "10/2010", "date": "2010-02-05"}]}
BODY = "# НАРЕДБА ЗА ПРОБАТА\n\n**Чл. 1.** Пробата.\n"
SLUG = "naredba-za-probata"


def _git(root, *args, env=None):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, env=env).stdout.strip()


def _repo(tmp_path, committed=None):
    root = tmp_path / "repo"
    (root / "ordinances").mkdir(parents=True)
    (root / "docs" / "data").mkdir(parents=True)
    (root / "docs" / "data" / "waivers.yaml").write_text((REPO / "docs" / "data" / "waivers.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "ordinances" / f"{SLUG}.md").write_text(render_act(committed or COMMITTED, BODY), encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "t")
    _git(root, "config", "user.email", "t@t")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "base")
    return root


def _waivers(root):
    return root / "docs" / "data" / "waivers.yaml"


def test_decide_names_the_outcome_for_each_act(tmp_path):
    root = _repo(tmp_path)
    path = root / "ordinances" / f"{SLUG}.md"
    row = E.decide(SLUG, "ordinances", path, page(), TODAY)
    assert (row["outcome"], row["repeal_row_in_history"], row["history_matches_page"]) == ("change", False, True)
    # the page carries an amendment the corpus has not absorbed: the repeal still counts, the rows do not match
    more = HISTORY.replace(" , <span class=\"HistoryItem\">отм.", " , <span class=\"HistoryItem\">изм. ДВ. бр. 15 от 1 Март 2012г.</span> , <span class=\"HistoryItem\">отм.")
    assert E.decide(SLUG, "ordinances", path, page(history=more), TODAY)["history_matches_page"] is False
    pending = page(note=NOTE.replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г."))
    assert E.decide(SLUG, "ordinances", path, pending, TODAY)["outcome"] == "pending"
    alive = page(history=HISTORY.replace("отм. ДВ. бр.", "изм. ДВ. бр."), note="")
    assert E.decide(SLUG, "ordinances", path, alive, TODAY)["outcome"] == "agree"
    assert E.decide(SLUG, "ordinances", path, None, TODAY)["outcome"] == "no_history"
    derog = {**COMMITTED, "estado": "derogado"}
    path.write_text(render_act(derog, BODY), encoding="utf-8")
    assert E.decide(SLUG, "ordinances", path, page(), TODAY)["outcome"] == "agree"
    for raw in (alive, pending, None):   # a derogado act is never set back, whatever the page says today
        assert E.decide(SLUG, "ordinances", path, raw, TODAY)["outcome"] == "kept_derogado"


def test_the_frontmatter_after_adds_the_repeal_row_only_when_the_page_matches():
    reading = E.read_page(page(), TODAY).to_dict()
    meta, changed = E.frontmatter_after(COMMITTED, {"slug": SLUG, "reading": reading, "history_matches_page": True})
    assert changed == ["estado", "amendment_history", "ultima_actualizacion"]
    assert meta["estado"] == "derogado" and meta["amendment_history"][-1] == {"dv": "20/2015", "date": "2015-03-06"} and meta["ultima_actualizacion"] == "2015-03-06"
    meta, changed = E.frontmatter_after(COMMITTED, {"slug": SLUG, "reading": reading, "history_matches_page": False})
    assert changed == ["estado"] and meta["amendment_history"] == COMMITTED["amendment_history"] and meta["ultima_actualizacion"] == "2010-02-05"
    with_row = {**COMMITTED, "amendment_history": [*COMMITTED["amendment_history"], {"dv": "20/2015", "date": "2015-03-06"}], "ultima_actualizacion": "2015-03-06"}
    meta, changed = E.frontmatter_after(with_row, {"slug": SLUG, "reading": reading, "history_matches_page": True})
    assert changed == ["estado"]
    with pytest.raises(E.WriteRefused, match="already derogado"):
        E.frontmatter_after({**COMMITTED, "estado": "derogado"}, {"slug": SLUG, "reading": reading, "history_matches_page": True})
    pending = E.read_page(page(note=NOTE.replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г.")), TODAY).to_dict()
    with pytest.raises(E.WriteRefused, match="repeal_pending, not repealed"):
        E.frontmatter_after(COMMITTED, {"slug": SLUG, "reading": pending, "history_matches_page": True})


def test_a_change_is_committed_with_its_trailers_record_and_repeal_date(tmp_path):
    root = _repo(tmp_path)
    path = root / "ordinances" / f"{SLUG}.md"
    row = E.decide(SLUG, "ordinances", path, page(), TODAY)
    run_dir = root / "data" / "runs" / "estado-test"
    w = E.write_change(row, root=root, run_dir=run_dir, waivers_path=_waivers(root))
    assert w.fields == ["estado", "amendment_history", "ultima_actualizacion"] and w.commit
    fm, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["estado"] == "derogado" and fm["ultima_actualizacion"] == "2015-03-06" and fm["amendment_history"][-1] == {"dv": "20/2015", "date": "2015-03-06"}
    assert body.lstrip("\n") == BODY   # the split keeps the blank line after the frontmatter
    msg = _git(root, "log", "-1", "--format=%B")
    assert msg.startswith("[otmyana] НАРЕДБА ЗА ПРОБАТА\n") and "in force from 2015-03-10" in msg
    assert "Source-Id: dv-20/2015\nSource-Date: 2015-03-06\nNorm-Id: 999\nRecord-Id: estado-test/naredba-za-probata/" in msg
    assert _git(root, "log", "-1", "--format=%ad", "--date=iso-strict").startswith("2015-03-06")
    record = json.loads((run_dir / "acts" / f"{SLUG}.json").read_text(encoding="utf-8"))
    assert record["repeal_issue"] == "20/2015" and record["in_force"] == "2015-03-10" and record["before"]["estado"] == "vigente" and record["after"]["estado"] == "derogado"
    assert record["repealing_act"].startswith("§ 2 от преходните")
    assert msg.strip().endswith(w.record_id) and w.record_id.endswith(E._sha256((run_dir / "acts" / f"{SLUG}.json").read_bytes())[:12])
    assert _git(root, "show", "--stat", "--format=", "HEAD").count("|") == 2  # the act and its record, nothing else
    assert _git(root, "status", "--porcelain") == ""


def test_a_refused_write_leaves_the_act_the_index_and_the_run_folder_untouched(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    path = root / "ordinances" / f"{SLUG}.md"
    before = path.read_text(encoding="utf-8")
    row = E.decide(SLUG, "ordinances", path, page(), TODAY)
    head = _git(root, "rev-parse", "HEAD")
    run_dir = root / "data" / "runs" / "t"

    def broken(*a, **kw):
        raise RuntimeError("boom")
    monkeypatch.setattr(E, "write_act", broken)
    with pytest.raises(RuntimeError):
        E.write_change(row, root=root, run_dir=run_dir, waivers_path=_waivers(root))
    assert path.read_text(encoding="utf-8") == before and _git(root, "rev-parse", "HEAD") == head
    assert not (run_dir / "acts" / f"{SLUG}.json").exists()   # the gate refused: no record of a write that did not happen
    monkeypatch.undo()
    # the gate wrote, the commit failed: the act is put back from HEAD and the record is removed
    real_git = E._git

    def failing(r, *args, **kw):
        if args and args[0] == "commit":
            raise subprocess.CalledProcessError(1, "git commit")
        return real_git(r, *args, **kw)
    monkeypatch.setattr(E, "_git", failing)
    with pytest.raises(subprocess.CalledProcessError):
        E.write_change(row, root=root, run_dir=run_dir, waivers_path=_waivers(root))
    assert path.read_text(encoding="utf-8") == before and _git(root, "rev-parse", "HEAD") == head
    assert _git(root, "status", "--porcelain") == "" and not (run_dir / "acts" / f"{SLUG}.json").exists()
    monkeypatch.undo()
    # without a commit, a failure after the gate wrote still puts the act back from HEAD
    monkeypatch.setattr(Path, "write_bytes", lambda self, data: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        E.write_change(row, root=root, run_dir=run_dir, waivers_path=_waivers(root), commit=False)
    monkeypatch.undo()
    assert path.read_text(encoding="utf-8") == before and _git(root, "status", "--porcelain") == ""
    # an uncommitted act is refused before anything is read, in both modes
    path.write_text(before + "\n", encoding="utf-8")
    for commit in (True, False):
        with pytest.raises(E.WriteRefused, match="uncommitted"):
            E.write_change(row, root=root, run_dir=run_dir, waivers_path=_waivers(root), commit=commit)


def test_run_write_skips_every_outcome_but_change_and_reports_refusals(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    path = root / "ordinances" / f"{SLUG}.md"
    change = E.decide(SLUG, "ordinances", path, page(), TODAY)
    for outcome in ("agree", "pending", "unsettled", "kept_derogado", "no_history"):
        written, refused = E.run_write([{**change, "outcome": outcome}], root=root, run_dir=root / "data" / "runs" / "t", waivers_path=_waivers(root))
        assert (written, refused) == ([], [])
    monkeypatch.setattr(E, "frontmatter_after", lambda *a: (_ for _ in ()).throw(E.WriteRefused("no")))
    written, refused = E.run_write([change], root=root, run_dir=root / "data" / "runs" / "t", waivers_path=_waivers(root))
    assert written == [] and refused == [{"slug": SLUG, "by": "run", "detail": ["no"]}]
    monkeypatch.undo()
    # a git failure (a hook, say) is rolled back, reported as a refusal, and the run goes on to the next act
    real_git = E._git

    def failing(r, *args, **kw):
        if args and args[0] == "commit":
            raise subprocess.CalledProcessError(1, ["git", "commit"], stderr="hook said no")
        return real_git(r, *args, **kw)
    monkeypatch.setattr(E, "_git", failing)
    written, refused = E.run_write([change, {**change, "outcome": "agree"}], root=root, run_dir=root / "data" / "runs" / "t", waivers_path=_waivers(root))
    assert written == [] and refused[0]["by"] == "git" and "hook said no" in refused[0]["detail"][0]
    assert _git(root, "status", "--porcelain") == ""


def test_the_report_counts_and_lists(tmp_path):
    root = _repo(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "999.html").write_bytes(page())
    rows = E.survey(root, raw, TODAY)
    rep = E.report_of(rows, "t", TODAY)
    assert (rep["acts"], rep["parsed"], rep["repealed_per_lexbg"], rep["to_change"], rep["repeal_pending"], rep["unsettled"], rep["no_history"]) == (1, 1, 1, 1, 0, 0, 0)
    assert rep["changes"][0]["in_force"] == "2015-03-10"
    (raw / "999.html").write_bytes(page(note=NOTE.replace("в сила от 10.03.2015 г.", "в сила от 01.01.2027 г.")))
    rep = E.report_of(E.survey(root, raw, TODAY), "t", TODAY)
    assert (rep["to_change"], rep["repeal_pending"]) == (0, 1) and rep["pending_acts"][0]["in_force"] == "2027-01-01"
    alive = page(history=HISTORY.replace("отм. ДВ. бр.", "изм. ДВ. бр."), note="").replace("<div class=\"Article\">".encode("cp1251"), "<div class=\"Article\">частично отм. ".encode("cp1251"))
    (raw / "999.html").write_bytes(alive)
    rows = E.survey(root, raw, TODAY)
    assert rows[0]["outcome"] == "agree"   # the word outside the history line and the note decides nothing
    compact = E.compact(rows[0])
    assert compact["history"] is None and compact["status"] == "not_repealed"


def test_the_cli_writes_the_report_and_the_survey(tmp_path, capsys):
    root = _repo(tmp_path)
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "999.html").write_bytes(page())
    assert E.main(["report", "--root", str(root), "--raw", str(raw), "--run", "t", "--today", TODAY]) == 0
    rep = json.loads((root / "data" / "runs" / "t" / "report.json").read_text(encoding="utf-8"))
    assert rep["to_change"] == 1 and rep["today"] == TODAY and "written" not in rep
    assert E.main(["write", "--commit", "--root", str(root), "--raw", str(raw), "--run", "t", "--today", TODAY]) == 0
    rep = json.loads((root / "data" / "runs" / "t" / "report.json").read_text(encoding="utf-8"))
    assert len(rep["written"]) == 1 and rep["refused"] == []
    assert "written  naredba-za-probata" in capsys.readouterr().out
    assert _git(root, "log", "-1", "--format=%s") == "[otmyana] НАРЕДБА ЗА ПРОБАТА"
    survey = json.loads((root / "data" / "runs" / "t" / "survey.json").read_text(encoding="utf-8"))
    assert survey[0]["outcome"] == "agree"   # the survey line says what the corpus now says
