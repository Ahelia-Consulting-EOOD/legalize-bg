"""The witnesses (reading/witnesses.py) and the portal fetch (scripts/raw_fetch_moj.py), step S1 of the plan of 31 October 2026."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

from reading import witnesses as W

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import raw_fetch_moj  # noqa: E402

PAGE = """<html><body><div class="box"><div class="boxi">
<div><a>ДОБАВИ В МОИТЕ АКТОВЕ</a></div>
<div class="TitleDocument" id="DocumentTitle"><p class="Title">ЗАКОН ЗА ПРОБАТА<br/></p></div>
<div class="Section">Глава първа.<br/>ОБЩИ ПОЛОЖЕНИЯ</div>
<div class="Article">Чл. 1. (1) Този закон урежда "пробата".<br/>(2) Пробата е публична – винаги.</div>
<div class="Article">Чл. 2. Законът влиза в сила от деня на обнародването му.</div>
<div class="FinalEdictsArticle">Релевантни актове от Европейското законодателство</div>
</div></div></body></html>"""
BODY = "# ЗАКОН ЗА ПРОБАТА\n\n### Глава първа ОБЩИ ПОЛОЖЕНИЯ\n\n**Чл. 1.** (1) Този закон урежда „пробата“.\n\n(2) Пробата e публична — винаги.\n\n**Чл. 2.** Законът влиза в сила от деня на обнародването му в „Държавен вестник“.\n"


def test_normalisation_removes_form_and_keeps_substance():
    assert W.normalise_line("Глава първа.") == "Глава първа" and W.normalise_line("Глава първа. ОБЩИ") == "Глава първа ОБЩИ"
    assert W.normalise_line("  „а“ – б  ") == '"а" - б' and W.normalise_line("Чл. 1. Текст.") == "Чл. 1. Текст."
    assert W.body_lines(BODY)[:2] == ["ЗАКОН ЗА ПРОБАТА", "Глава първа ОБЩИ ПОЛОЖЕНИЯ"]


def test_compare_finds_only_the_real_differences_with_context_and_lines():
    raw = PAGE.encode("cp1251")
    theirs, shape = W.witness_lines(raw)
    assert shape["chrome_before"] == 1 and shape["chrome_after"] == 1 and theirs[0] == "ЗАКОН ЗА ПРОБАТА"
    assert theirs[1] == "Глава първа ОБЩИ ПОЛОЖЕНИЯ"   # the number line joined to its title, as ours is
    diffs = W.compare(W.body_lines(BODY), theirs)
    assert [(d["kind"], d["ours"], d["witness"]) for d in diffs] == [("replace", "e", "е"), ("replace", 'му в "Държавен вестник".', "му.")]
    assert diffs[0]["our_line"] == 3 and diffs[0]["before"].endswith("Пробата") and diffs[0]["after"].startswith("публична")
    assert diffs[1]["n"] == 2 and diffs[1]["our_line"] == 4 and diffs[1]["witness_line"] == 4
    # the comparison is at the block level: a line the witness adds, a line we lack, two alineas joined into one
    ours = ["Чл. 1. Едно.", "(1) а б в", "(2) г д е", "Чл. 2. Две."]
    theirs = ["Чл. 1. Едно.", "(Изм. - ДВ, бр. 1 от 2020 г.)", "(1) а б в (2) г д е"]
    diffs = W.compare(ours, theirs)
    assert [(d["kind"], d["ours"], d["witness"]) for d in diffs] == [
        ("insert", "", "(Изм. - ДВ, бр. 1 от 2020 г.)"),
        ("delete", "Чл. 2. Две.", ""),
        ("structure", "(1) а б в | (2) г д е | Чл. 2. Две.", "(Изм. - ДВ, бр. 1 от 2020 г.) | (1) а б в (2) г д е")]
    assert diffs[2]["after"].startswith("3 line(s) of ours against 2")
    assert W.compare(["а", "б в", "г"], ["а", "б", "в", "г"]) == [{"n": 1, "kind": "structure", "ours": "б в", "witness": "б | в", "before": "", "after": "1 line(s) of ours against 2 of the witness, the same words", "our_line": 1, "witness_line": 1}]


def test_diff_task_record_and_the_refusal_of_an_incomplete_answer(tmp_path):
    raw = PAGE.encode("cp1251")
    p = W.write_diff(tmp_path, BODY, [{"name": "lexbg", "raw": raw, "page_sha256": hashlib.sha256(raw).hexdigest(), "fetched_at": "t"},
                                      {"name": "moj", "absent": "the portal answers 500 for this act"}])
    diff = json.loads(p.read_text(encoding="utf-8"))
    assert [w["count"] for w in diff["witnesses"]] == [2, 0] and diff["normalisation"] == list(W.NORMALISATION)
    sha = W.diff_sha256(tmp_path)
    task = W.task_text(diff, "zakon-za-probata", tmp_path / "witness-answer.json", sha)
    assert "## witness lexbg" in task and "### 1 (replace" in task and "(absent: the portal answers 500" in task and "source_error" in task and sha in task
    with pytest.raises(ValueError, match="for another diff"):
        W.record(tmp_path, {"lexbg": {"1": {"verdict": "source_error", "note": "x"}, "2": {"verdict": "timing", "note": "y"}}})
    with pytest.raises(ValueError, match="difference 2 has no verdict"):
        W.record(tmp_path, {"diff_sha256": sha, "lexbg": {"1": {"verdict": "source_error", "note": "Latin e in the Gazette"}}})
    with pytest.raises(ValueError, match="difference 1 has no verdict"):
        W.record(tmp_path, {"diff_sha256": sha, "lexbg": {"1": {"verdict": "nonsense"}, "2": {"verdict": "timing"}}})
    with pytest.raises(ValueError, match="other: not a witness.*difference 9 is not in the diff.*moj: absent, nothing to settle, yet answered"):
        W.record(tmp_path, {"diff_sha256": sha, "lexbg": {"1": {"verdict": "timing", "note": ""}, "2": {"verdict": "timing", "note": ""}, "9": {"verdict": "timing"}},
                            "other": {}, "moj": {"1": {"verdict": "timing"}}})
    assert not (tmp_path / "witness-record.json").exists()
    rec_path = W.record(tmp_path, {"diff_sha256": sha, "lexbg": {"1": {"verdict": "source_error", "note": "Latin e"}, "2": {"verdict": "witness_error", "note": "lex.bg adds words"}}})
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    assert rec["witnesses"][0]["counts"] == {"source_error": 1, "witness_error": 1} and rec["witnesses"][0]["verdicts"]["1"]["ours"] == "e"
    assert rec["witnesses"][1]["absent"] and rec["diff_sha256"] == sha and rec["stops"] == []
    assert W.summary(tmp_path) == "lexbg: 2 difference(s), settled source_error 1, witness_error 1; moj: absent (the portal answers 500 for this act)"
    rec = json.loads(W.record(tmp_path, {"diff_sha256": sha, "lexbg": {"1": {"verdict": "reading_error", "note": "our split"}, "2": {"verdict": "timing", "note": ""}}}).read_text(encoding="utf-8"))
    assert rec["stops"] == ["reading_error"]   # our own reading's error stops the write


@pytest.mark.skipif(not (REPO / "data" / "raw" / "lexbg" / "2137259781.html").exists(), reason="raw store not on this machine")
def test_the_committed_transport_law_matches_its_own_lexbg_page():
    from refresh import _split_frontmatter
    _, body = _split_frontmatter((REPO / "laws" / "zakon-za-obshtestveniya-transport.md").read_text(encoding="utf-8"))
    theirs, _ = W.witness_lines((REPO / "data" / "raw" / "lexbg" / "2137259781.html").read_bytes())
    assert W.compare(W.body_lines(body), theirs) == []


class FakeResponse:
    def __init__(self, status, body):
        self.status_code, self.content = status, body


class FakeSession:
    def __init__(self, answers):
        self.answers, self.calls = answers, []

    def get(self, url, headers=None, timeout=None):
        self.calls.append(url)
        return self.answers[url.rsplit("/", 1)[1]]


def test_the_portal_fetch_keeps_bodies_hashes_and_times_and_does_not_refetch(tmp_path):
    out = tmp_path / "moj"
    session = FakeSession({"1": FakeResponse(200, b"<html>" + b"x" * 2000 + b"</html>"), "2": FakeResponse(500, b"Error 500")})
    sleeps = []
    r1 = raw_fetch_moj.fetch_one("1", out, session=session, sleep=sleeps.append)
    r2 = raw_fetch_moj.fetch_one("2", out, session=session, sleep=sleeps.append)
    assert r1["outcome"] == "ok" and r1["sha256"] == hashlib.sha256(b"<html>" + b"x" * 2000 + b"</html>").hexdigest() and (out / "1.html").exists()
    assert r2["outcome"] == "absent" and r2["status"] == 500 and (out / "2.absent.html").read_bytes() == b"Error 500"
    assert sleeps == [1.0, 1.0] and len(raw_fetch_moj.manifest_rows(out)) == 2
    again = raw_fetch_moj.fetch_one("1", out, session=session, sleep=sleeps.append)
    assert again.get("cached") and session.calls == [raw_fetch_moj.URL.format(id="1"), raw_fetch_moj.URL.format(id="2")]
    again = raw_fetch_moj.fetch_one("2", out, session=session, sleep=sleeps.append)   # an absent page is the portal's settled answer: not asked again
    assert again.get("cached") and again["outcome"] == "absent" and len(session.calls) == 2
    session.answers["5"] = FakeResponse(503, b"down")
    raw_fetch_moj.fetch_one("5", out, session=session, sleep=sleeps.append)
    raw_fetch_moj.fetch_one("5", out, session=session, sleep=sleeps.append)   # an error is asked again
    assert session.calls.count(raw_fetch_moj.URL.format(id="5")) == 2


def test_a_certificate_error_falls_back_to_the_systems_curl(tmp_path, monkeypatch):
    import requests

    class Bad:
        def get(self, url, headers=None, timeout=None):
            raise requests.exceptions.SSLError("certificate verify failed")
    monkeypatch.setattr(raw_fetch_moj, "_curl", lambda url: (500, b"Error 500"))
    row = raw_fetch_moj.fetch_one("3", tmp_path / "moj", session=Bad(), sleep=lambda s: None)
    assert row["outcome"] == "absent" and row["via"] == "curl" and row["status"] == 500
    monkeypatch.setattr(raw_fetch_moj, "_curl", lambda url: (None, b""))
    row = raw_fetch_moj.fetch_one("4", tmp_path / "moj", session=Bad(), sleep=lambda s: None)
    assert row["outcome"] == "error" and "curl could not" in row["detail"]
