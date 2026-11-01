"""The real steps of the routes of the exceptions list (step S1 of the plan of 31 October 2026), for ``reading/routes.py``.

The route "whole act from its promulgation material" (an act never amended, read whole from the Gazette):

1. ``amendment_search``: a script searches the Gazette index after the act's promulgation issue for a material that
   amends it: by title (a law amending the act), and in the text of every law and corrigendum published since (an
   amendment made in another act's final provisions opens "В Закона за …"), fetching the bodies the cache lacks at
   one request per second; it also fetches the issues published after the index's last one and searches them. A
   hit stops the route: the act is not whole in its promulgation material and needs the history route.
2. ``fetch_material``: the material into the Gazette cache and its record (id, hash, time, issue) into the run folder.
3. ``prepare``: the material split by ``split_dv`` into blocks and round-0 tasks.
4. ``label``: round 0 through the run driver of D-070: the call files are written and the step waits (``pending``)
   until the labeller's answers are on disk; then the round is collected.
5. ``ladder``: rounds 1 and 2 the same way; a residue the labeller holds (``rule_needed``) is the step's own
   "changed nothing"; another residue is a stop.
6. ``content_check``: the last round's report; lost text (D-076) puts the act on the route "investigate" and stops.
7. ``witnesses``: the body against the lex.bg page and the portal page (fetch-only); the settler's answer is waited
   for; the record is written.
8. ``write``: ``reading/write.py`` through the gate, one commit with the four trailers.

The route "investigate": ``investigate`` gathers the texts a defect needs and waits for the investigator's answer in
the fixed form; ``route_decision`` loads it onto the list and stops, since the act then goes through its new route in
a new run. The engine (F1) and the source decision (S4) are not defined, so those routes stop at once.

The model calls themselves are made by the session through the lean project agents (``labeller``, ``settler``,
``investigator``); a step that needs one writes the task and reports ``pending`` with the call to make. Nothing here
writes a corpus file: the write step goes through ``reading/write.py`` and the gate.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import raw_fetch_moj  # noqa: E402
import source_exceptions as sx  # noqa: E402
from fetcher.dv.client import DvSession  # noqa: E402
from fetcher.dv.issues import enumerate_issues  # noqa: E402
from fetcher.dv.materials import _content_div, fetch_material, fetch_materials, parse_material_header  # noqa: E402
from reading import run as run_driver  # noqa: E402
from reading import ladder, witnesses  # noqa: E402
from reading.routes import Context, StepResult  # noqa: E402
from reading.splitter import split_dv, split_lexbg  # noqa: E402
from reading.write import CorpusIntegrityError, WriteRefused, corpus_file, write_staged  # noqa: E402
from refresh import _split_frontmatter  # noqa: E402

DV_CACHE = ROOT / "data" / "dv" / "cache"
DV_INDEX = ROOT / "data" / "dv" / "materials.jsonl"
DV_ISSUES = ROOT / "data" / "dv" / "issues.jsonl"
RAW_LEXBG = ROOT / "data" / "raw" / "lexbg"
RAW_MOJ = ROOT / "data" / "raw" / "moj"
LAW_TITLE = re.compile(r"^(Закон|Кодекс|Поправка|Решение|Указ)")
SECTIONS = ("Народно събрание", "Конституционен съд", "Президент на Републиката")   # the bodies whose materials can change a law
NEW_ISSUE_PAGES = 1   # the newest ten issues; the step stops when they do not reach the index's last issue
# an amending or repealing instruction near the act's name: "В Закона за …", "Законът за … се отменя", "… от Закона за … се изменя"
AMENDING_VERBS = r"(изменя|допълва|отменя|заменя|създава|заличава|правят следните изменения|обявява за противоконституцион)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _rel(ctx: Context, p: Path) -> str:
    return ctx.rel(p)


def _material_id(ctx: Context) -> int:
    if ctx.entry is None or not str(ctx.entry.address).isdigit():
        raise ValueError(f"{ctx.slug}: the entry's address is not a material id")
    return int(ctx.entry.address)


def _doc_id(ctx: Context) -> str:
    fm, _ = _split_frontmatter(corpus_file(ctx.root, ctx.slug).read_text(encoding="utf-8"))
    return str(fm.get("identificador", "")).strip()


def _title_parts(ctx: Context) -> tuple[str, str, str]:
    """(kind, preposition, name) of the act's title: ("закон", "за", "обществения транспорт"), ("кодекс", "на", "труда")."""
    title = (ctx.entry.title if ctx.entry else ctx.slug).strip()
    m = re.match(r"^(Закон|Кодекс)\s+(за|на)\s+(.+)$", title, re.I)
    if not m:
        return "", "", title.lower()
    return m.group(1).lower(), m.group(2).lower(), m.group(3).strip().lower()


def _title_words(ctx: Context) -> str:
    """The act's name as other acts cite it: the title without its leading 'Закон за' or 'Кодекс на'."""
    return _title_parts(ctx)[2]


def _amending_pattern(ctx: Context) -> re.Pattern:
    """The act's name in any case ("закона за …", "законът за …", "кодекса на …") within 200 characters of an amending or repealing verb."""
    kind, prep, name = _title_parts(ctx)
    cited = (re.escape(kind) + r"[аът]*\s+" + re.escape(prep) + r"\s+" if kind else "") + re.escape(name)
    return re.compile(cited + r".{0,200}?" + AMENDING_VERBS + "|" + AMENDING_VERBS + r".{0,200}?" + cited, re.S)


def _next_issue(latest: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
    """The two issues that can follow the latest known one: the next number of its year, or the first of the next year."""
    return (latest[0], latest[1] + 1), (latest[0] + 1, 1)


def _index_rows() -> list[dict]:
    return [json.loads(l) for l in DV_INDEX.read_text(encoding="utf-8").splitlines() if l.strip()]


def _material_text(html: str) -> str:
    return re.sub(r"\s+", " ", _content_div(BeautifulSoup(html, "lxml")).get_text(" ")).lower()


# --- the steps of the whole-act route --------------------------------------------------------------------

class AmendmentSearch:
    name = "amendment_search"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        return [DV_INDEX, DV_ISSUES]

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "amendments.json", ctx.act_dir / "later-materials.jsonl"]

    def run(self, ctx: Context) -> StepResult:
        id_mat = _material_id(ctx)
        rows = _index_rows()
        own = next((r for r in rows if r.get("id_mat") == id_mat), None)
        if own is None:
            return StepResult("stop", f"the index has no material {id_mat}")
        since = (own["issue_year"], own["issue_number"])
        latest = max((r["issue_year"], r["issue_number"]) for r in rows)
        session = DvSession()
        later: list[dict] = []
        fetched_issues = list(enumerate_issues(session, max_pages=NEW_ISSUE_PAGES))
        for issue in fetched_issues:
            if (issue.year, issue.number) > latest:
                for m in fetch_materials(session, issue.id_obj):
                    later.append({"id_obj": issue.id_obj, "issue_year": issue.year, "issue_number": issue.number, "issue_date": issue.date,
                                  "status": "ok", "position": m.position, "id_mat": m.id_mat, "section": m.section, "title": m.title, "start_page": m.start_page})
        ctx.act_dir.mkdir(parents=True, exist_ok=True)
        (ctx.act_dir / "later-materials.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in later), encoding="utf-8")
        newest = max(((i.year, i.number) for i in fetched_issues), default=latest)
        oldest_new = min(((i.year, i.number) for i in fetched_issues), default=latest)
        name = _title_words(ctx)
        candidates = [r for r in rows + later if r.get("status") == "ok" and (r["issue_year"], r["issue_number"]) > since
                      and r.get("section") in SECTIONS and LAW_TITLE.match(r.get("title") or "") and r["id_mat"] != id_mat]
        title_hits = [r for r in candidates if name in (r.get("title") or "").lower()]
        amending = _amending_pattern(ctx)
        amending_hits, mentions, fetched = [], [], 0
        for r in candidates:
            cached = (DV_CACHE / f"{r['id_mat']}.html").exists()
            html = fetch_material(session, r["id_mat"], cache_dir=DV_CACHE)
            fetched += 0 if cached else 1
            text = _material_text(html)
            if amending.search(text):
                amending_hits.append(r)
            elif name in text:
                mentions.append(r)
        out = {"act": ctx.slug, "material": id_mat, "promulgation_issue": f"{since[1]}/{since[0]}", "index_through": f"{latest[1]}/{latest[0]}",
               "newest_issue_seen": f"{newest[1]}/{newest[0]}", "oldest_issue_fetched": f"{oldest_new[1]}/{oldest_new[0]}",
               "later_issues": sorted({f"{r['issue_number']}/{r['issue_year']}" for r in later}), "searched_for": name, "sections": list(SECTIONS),
               "candidates": len(candidates), "bodies_fetched": fetched, "title_hits": title_hits, "amending_hits": amending_hits,
               "mentions": [{k: r[k] for k in ("issue_year", "issue_number", "id_mat", "title")} for r in mentions], "searched_at": _now()}
        (ctx.act_dir / "amendments.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        evidence = [_rel(ctx, ctx.act_dir / "amendments.json")]
        fetched_keys = {(i.year, i.number) for i in fetched_issues}
        if not fetched_keys or not any(k <= _next_issue(latest)[0] or k == _next_issue(latest)[1] for k in fetched_keys):
            return StepResult("stop", f"the issues fetched ({'none' if not fetched_keys else f'from бр. {oldest_new[1]}/{oldest_new[0]}'}) do not reach the issue "
                              f"after the index's last one (бр. {latest[1]}/{latest[0]}): a gap no search covered; extend the index first", evidence)
        if title_hits or amending_hits:
            hits = [f"{r['issue_number']}/{r['issue_year']} material {r['id_mat']}: {r['title'][:80]}" for r in title_hits + amending_hits]
            return StepResult("stop", "a later material amends the act, so its promulgation material is not the whole act "
                              f"(the history route of F1 is needed): {'; '.join(hits)}", evidence)
        return StepResult("done", f"no amendment of the act in {len(candidates)} laws and corrigenda after бр. {since[1]}/{since[0]} "
                          f"(index through {latest[1]}/{latest[0]}, later issues {out['later_issues'] or 'none'}; {len(mentions)} mention(s) that are not amendments)", evidence)


class FetchMaterial:
    name = "fetch_material"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        try:
            return [DV_CACHE / f"{_material_id(ctx)}.html"]   # the cached page, when there is one, is what the step records
        except ValueError:
            return []

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "material.json"]

    def run(self, ctx: Context) -> StepResult:
        id_mat = _material_id(ctx)
        path = DV_CACHE / f"{id_mat}.html"
        cached = path.exists()
        html = fetch_material(DvSession(), id_mat, cache_dir=DV_CACHE)
        head = parse_material_header(html)
        raw = path.read_bytes()
        fetched_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds") if cached else _now()
        rec = {"id_mat": id_mat, "sha256": _sha(raw), "bytes": len(raw), "fetched_at": fetched_at, "cached": cached,
               "issue_number": head.issue_number, "issue_year": int(head.issue_date[:4]), "issue_date": head.issue_date,
               "section_path": head.section_path, "start_page": head.start_page, "body_org": head.body_org, "cache": _rel(ctx, path)}
        ctx.act_dir.mkdir(parents=True, exist_ok=True)
        (ctx.act_dir / "material.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        return StepResult("done", f"material {id_mat} of бр. {head.issue_number}/{rec['issue_year']} ({'cached' if cached else 'fetched'}), sha256 {rec['sha256'][:12]}",
                          [_rel(ctx, ctx.act_dir / "material.json")])


class Prepare:
    name = "prepare"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        rec = ctx.act_dir / "material.json"
        paths = [rec]
        if rec.exists():
            paths.append(DV_CACHE / f"{json.loads(rec.read_text(encoding='utf-8'))['id_mat']}.html")
        return paths

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "blocks.json", ctx.act_dir / "source.txt", ctx.act_dir / "tasks" / "round0"]

    def run(self, ctx: Context) -> StepResult:
        rec = json.loads((ctx.act_dir / "material.json").read_text(encoding="utf-8"))
        html = (DV_CACHE / f"{rec['id_mat']}.html").read_bytes()
        if _sha(html) != rec["sha256"]:
            return StepResult("stop", f"the cached material {rec['id_mat']} no longer hashes as material.json recorded it")
        act = split_dv(html)
        if not act.has_spine:
            return StepResult("stop", f"the material {rec['id_mat']} holds no article or § block")
        run_driver.prepare_act(ctx.act_dir, ctx.slug, act, str(rec["id_mat"]))
        return StepResult("done", f"{len(act.blocks)} blocks, {len(act.sections)} sections", [_rel(ctx, ctx.act_dir / "blocks.json")])


def _round_state(ctx: Context, rnd: int) -> tuple[int, int]:
    """(tasks of the round, answered tasks of the round)."""
    tdir = ctx.act_dir / "tasks" / f"round{rnd}"
    mdir = ctx.act_dir / "maps" / f"round{rnd}"
    tasks = sorted(tdir.glob("*.json")) if tdir.exists() else []
    run_driver._split_call_answers(ctx.act_dir, rnd)
    answered = [t for t in tasks if (mdir / t.name).exists()]
    return len(tasks), len(answered)


def _dispatch_or_collect(ctx: Context, rnd: int) -> tuple[str, str, dict | None]:
    """Write the round's call files and wait, or collect the round: ("pending"|"collected", detail, report)."""
    n_tasks, n_answered = _round_state(ctx, rnd)
    if n_tasks == 0:
        return "collected", f"round {rnd}: no tasks", None
    if n_answered < n_tasks:
        listed, remaining = run_driver.dispatch(ctx.run_root, [ctx.slug], rnd, relist=True)
        calls = "; ".join(f"{c['name']} ({c['tasks']} tasks): read {c['call_file']}, write {c['answer_file']}" for c in listed)
        return "pending", f"round {rnd}: {remaining} of {n_tasks} tasks unanswered; {len(listed)} labeller call(s) to make: {calls}", None
    report = run_driver.collect(ctx.act_dir, ctx.slug, rnd)
    return "collected", f"round {rnd} collected: {len(report['exceptions'])} exception(s), {len(report['source_findings'])} source finding(s)", report


def _call_answers(ctx: Context, rnd: int) -> list[Path]:
    """The labeller's own answer files of a round (one per call), without the per-task files and sidecars the split writes."""
    mdir = ctx.act_dir / "maps" / f"round{rnd}"
    return sorted(p for p in mdir.glob("*.json") if run_driver.calls.CALL_NAME.fullmatch(p.stem)) if mdir.exists() else []


class Label:
    name = "label"
    version = "2"

    def inputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "tasks" / "round0", *_call_answers(ctx, 0)]

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "report-round0.json", ctx.act_dir / "tasks" / "round1"]

    def run(self, ctx: Context) -> StepResult:
        state, detail, report = _dispatch_or_collect(ctx, 0)
        if state == "pending":
            return StepResult("pending", detail)
        return StepResult("done", detail, [_rel(ctx, ctx.act_dir / "report-round0.json")])


class Ladder:
    name = "ladder"
    version = "2"

    def inputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "report-round0.json", ctx.act_dir / "tasks" / "round1", *_call_answers(ctx, 1),
                ctx.act_dir / "tasks" / "round2", *_call_answers(ctx, 2)]

    def outputs(self, ctx: Context) -> list[Path]:
        # the map, the staged body and the diff are written by every collect; the ladder is the last step that collects
        return [ctx.act_dir / "report-round1.json", ctx.act_dir / "report-round2.json", ctx.act_dir / "ladder.json",
                ctx.act_dir / "map.json", ctx.act_dir / "staged.md", ctx.act_dir / "diff.txt"]

    def run(self, ctx: Context) -> StepResult:
        report = json.loads((ctx.act_dir / "report-round0.json").read_text(encoding="utf-8"))
        rnd = 0
        while report.get("next_round_tasks", 0) and rnd < ladder.MAX_ROUNDS:
            rnd += 1
            state, detail, rep = _dispatch_or_collect(ctx, rnd)
            if state == "pending":
                return StepResult("pending", detail)
            report = rep or report
        residue = report.get("residue", [])
        classes = report.get("residue_classes", {})
        summary = {"rounds": rnd, "residue": residue, "residue_classes": classes, "exceptions": len(report.get("exceptions", [])),
                   "source_finding_kinds": report.get("source_finding_kinds", {}), "last_report": f"report-round{report['round']}.json"}
        (ctx.act_dir / "ladder.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        evidence = [_rel(ctx, ctx.act_dir / "ladder.json"), _rel(ctx, ctx.act_dir / summary["last_report"])]
        if residue and classes.get("rule_needed"):
            return StepResult("unchanged", f"after round {rnd} the residue is {len(residue)} block(s), {classes.get('rule_needed')} of them a reading the "
                              f"labeller holds and the checks refuse (rule_needed); a rule, not a round, is needed", evidence)
        if residue:
            return StepResult("stop", f"after round {rnd} the residue is {len(residue)} block(s) of the labeller's doubt; a whole-act read is needed", evidence)
        return StepResult("done", f"no residue after round {rnd}", evidence)


class ContentCheck:
    name = "content_check"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "ladder.json", *sorted(ctx.act_dir.glob("report-round*.json"))]

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "content-check.json"]

    def run(self, ctx: Context) -> StepResult:
        summary = json.loads((ctx.act_dir / "ladder.json").read_text(encoding="utf-8"))
        report = json.loads((ctx.act_dir / summary["last_report"]).read_text(encoding="utf-8"))
        lost = [e for e in report.get("source_findings", []) if e["kind"] in ladder.LOST_TEXT]
        out = {"lost_text": lost, "exceptions": len(report.get("exceptions", [])), "source_findings": report.get("source_finding_kinds", {}),
               "report": summary["last_report"], "checked_at": _now()}
        (ctx.act_dir / "content-check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        evidence = [_rel(ctx, ctx.act_dir / "content-check.json")]
        if lost:
            kinds = sorted({e["kind"] for e in lost})
            if ctx.entry is not None and ctx.entry.route != "investigate":
                ctx.entry = sx.update(ctx.list_path, ctx.slug, route="investigate")
            return StepResult("stop", f"lost text ({', '.join(kinds)}), first at block {lost[0]['block']}: {lost[0]['detail']}; "
                              f"the act is on the list with the route investigate (D-076)", evidence)
        if report.get("exceptions"):
            return StepResult("stop", f"{len(report['exceptions'])} exception(s) remain", evidence)
        return StepResult("done", f"no lost text, no exception; source findings {out['source_findings'] or 'none'}", evidence)


class Witnesses:
    name = "witnesses"
    version = "3"   # the record carries the hash of the body as written; a witness without a page is recorded absent

    def inputs(self, ctx: Context) -> list[Path]:
        paths = [ctx.act_dir / "staged.md", ctx.act_dir / "witness-answer.json"]
        try:
            doc_id = _doc_id(ctx)
            paths += [RAW_LEXBG / f"{doc_id}.html", RAW_MOJ / f"{doc_id}.html", RAW_MOJ / f"{doc_id}.absent.html"]
        except Exception:  # no corpus file: the step itself refuses
            pass
        return paths

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "witness-diff.json", ctx.act_dir / "witness-task.md", ctx.act_dir / "witness-record.json"]

    def run(self, ctx: Context) -> StepResult:
        doc_id = _doc_id(ctx)
        body = (ctx.act_dir / "staged.md").read_text(encoding="utf-8")
        page = RAW_LEXBG / f"{doc_id}.html"
        if not page.exists():
            return StepResult("stop", f"the raw store holds no lex.bg page {doc_id}")
        raw = page.read_bytes()
        row = None
        for line in (RAW_LEXBG / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line) if line.strip() else {}
            if str(r.get("doc_id")) == doc_id and r.get("status") == "ok":
                row = r
        lexbg = {"name": "lexbg", "raw": raw, "page_sha256": _sha(raw), "fetched_at": (row or {}).get("fetched_at", "unknown")}
        m = raw_fetch_moj.fetch_one(doc_id, RAW_MOJ)
        if m["outcome"] == "ok":
            moj = {"name": "moj", "raw": (RAW_MOJ / m["file"]).read_bytes(), "page_sha256": m["sha256"], "fetched_at": m["fetched_at"]}
        else:
            moj = {"name": "moj", "absent": f"the portal answers {m.get('status')} for {m['url']} ({m['outcome']}, {m['fetched_at']})"}
        diff_path = witnesses.write_diff(ctx.act_dir, body, [lexbg, moj])
        diff = json.loads(diff_path.read_text(encoding="utf-8"))
        answer_path = ctx.act_dir / "witness-answer.json"
        evidence = [_rel(ctx, diff_path)]
        if sum(w["count"] for w in diff["witnesses"]) == 0:
            witnesses.record(ctx.act_dir, {})
            return StepResult("done", "no difference from any witness; " + witnesses.summary(ctx.act_dir), evidence + [_rel(ctx, ctx.act_dir / "witness-record.json")])
        task_path = ctx.act_dir / "witness-task.md"
        sha = witnesses.diff_sha256(ctx.act_dir)
        task_path.write_text(witnesses.task_text(diff, ctx.slug, answer_path, sha), encoding="utf-8")
        counts = ", ".join(f"{w['witness']} {w['count']}" for w in diff["witnesses"])
        if not answer_path.exists():
            return StepResult("pending", f"differences to settle ({counts}); one settler call: read {task_path}, write {answer_path}", evidence)
        try:
            answer = json.loads(answer_path.read_text(encoding="utf-8"))
            if isinstance(answer, dict) and answer.get("diff_sha256") != sha:
                # the answer settles another diff (the body or a witness changed since): the settler reads the new task
                return StepResult("pending", f"the settler's answer is for another diff; differences to settle again ({counts}); "
                                  f"one settler call: read {task_path}, write {answer_path}", evidence)
            witnesses.record(ctx.act_dir, answer)
        except (ValueError, json.JSONDecodeError) as exc:
            return StepResult("stop", f"the settler's answer does not settle the differences: {exc}", evidence)
        rec = json.loads((ctx.act_dir / "witness-record.json").read_text(encoding="utf-8"))
        if rec.get("stops"):
            return StepResult("stop", f"the settler found our reading wrong ({', '.join(rec['stops'])}): " + witnesses.summary(ctx.act_dir),
                              evidence + [_rel(ctx, ctx.act_dir / "witness-record.json")])
        return StepResult("done", witnesses.summary(ctx.act_dir), evidence + [_rel(ctx, ctx.act_dir / "witness-record.json")])


class Write:
    name = "write"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        paths = [ctx.act_dir / "staged.md", ctx.act_dir / "map.json", ctx.act_dir / "material.json", ctx.act_dir / "witness-record.json"]
        try:
            paths.append(corpus_file(ctx.root, ctx.slug))
        except WriteRefused:
            pass
        return paths

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "written.json"]

    def run(self, ctx: Context) -> StepResult:
        try:
            w = write_staged(ctx.slug, ctx.act_dir, root=ctx.root)
        except CorpusIntegrityError as exc:
            return StepResult("stop", f"the gate refused the act: {len(exc.violations)} violation(s): " + "; ".join(f"{v.check}@{v.locator}: {v.detail}" for v in exc.violations[:5]))
        except WriteRefused as exc:
            return StepResult("stop", f"the write path refused the act: {exc}")
        if w.commit_type == "unchanged":
            head = subprocess.run(["git", "log", "-1", "--format=%h", "--", str(corpus_file(ctx.root, ctx.slug))], cwd=ctx.root, capture_output=True, text=True).stdout.strip()
            return StepResult("done", f"the corpus already holds this text (Record-Id {w.record_id})", committed=head or "unchanged")
        out = {"slug": ctx.slug, "commit": w.commit, "commit_type": w.commit_type, "record_id": w.record_id, "written_at": _now()}
        (ctx.act_dir / "written.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        return StepResult("done", f"[{w.commit_type}] {w.commit} Record-Id {w.record_id}", [_rel(ctx, ctx.act_dir / "written.json")], committed=w.commit)


# --- the investigation ---------------------------------------------------------------------------------------

ANSWER_FORM = """# The investigator's answer: one YAML document with exactly these keys
defect: <one of {defects}>
source: <one of {sources}>
address: <a material id or a URL, or unknown>
route: <one of {routes}>
evidence:
  defect: <the lines you relied on>
  source: <the lines you relied on>
  route: <the lines you relied on>
"""


class Investigate:
    name = "investigate"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "investigate-answer.yaml"]

    def outputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "investigate-task.md", ctx.act_dir / "texts", ctx.act_dir / "investigate-result.json"]

    def run(self, ctx: Context) -> StepResult:
        texts = ctx.act_dir / "texts"
        texts.mkdir(parents=True, exist_ok=True)
        gathered: list[str] = []
        doc_id = _doc_id(ctx)
        page = RAW_LEXBG / f"{doc_id}.html"
        if page.exists():
            (texts / "lexbg.txt").write_text(split_lexbg(page.read_bytes()).source_text + "\n", encoding="utf-8")
            gathered.append(f"lex.bg page {doc_id}: {texts / 'lexbg.txt'}")
        if ctx.entry is not None and ctx.entry.source == "dv_html" and str(ctx.entry.address).isdigit():
            html = fetch_material(DvSession(), int(ctx.entry.address), cache_dir=DV_CACHE)
            (texts / f"dv-{ctx.entry.address}.txt").write_text(split_dv(html).source_text + "\n", encoding="utf-8")
            gathered.append(f"Gazette material {ctx.entry.address}: {texts / f'dv-{ctx.entry.address}.txt'}")
        m = raw_fetch_moj.fetch_one(doc_id, RAW_MOJ)
        if m["outcome"] == "ok":
            (texts / "moj.txt").write_text(split_lexbg((RAW_MOJ / m["file"]).read_bytes()).source_text + "\n", encoding="utf-8")
            gathered.append(f"Ministry of Justice portal page {doc_id}: {texts / 'moj.txt'}")
        else:
            gathered.append(f"Ministry of Justice portal: no page for {doc_id} ({m['outcome']}, status {m.get('status')})")
        answer = ctx.act_dir / "investigate-answer.yaml"
        task = ctx.act_dir / "investigate-task.md"
        task.write_text("\n".join([
            f"# Investigate {ctx.slug}", "",
            f"The act: {ctx.entry.title if ctx.entry else ctx.slug}. Listed with the defect `{ctx.entry.defect if ctx.entry else '?'}`, "
            f"the note: {ctx.entry.note if ctx.entry else ''}", "",
            "Read only these texts:", *[f"- {g}" for g in gathered], "",
            "Decide from the texts alone: what the act's defect is, which source holds the act right and at which address, and which route brings it to a correct commit.",
            "Closed sets: " + "; ".join(f"defect `{k}`: {v}" for k, v in sx.DEFECTS.items()) + ". " + "; ".join(f"source `{k}`: {v}" for k, v in sx.SOURCES.items())
            + ". " + "; ".join(f"route `{k}`: {v}" for k, v in sx.ROUTES.items()) + ".",
            f"Write exactly one file, `{answer}`, in this form and nothing else:", "",
            "```yaml", ANSWER_FORM.format(defects=sorted(sx.DEFECTS), sources=sorted(sx.SOURCES), routes=sorted(sx.ROUTES)).strip(), "```", ""]), encoding="utf-8")
        if not answer.exists():
            return StepResult("pending", f"one investigator call: read {task}, write {answer}", [_rel(ctx, task)])
        try:
            got = yaml.safe_load(answer.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            return StepResult("stop", f"the investigator's answer is not YAML: {exc}")
        problems = []
        if not isinstance(got, dict):
            problems.append("not a mapping")
        else:
            for key, allowed in (("defect", sx.DEFECTS), ("source", sx.SOURCES), ("route", sx.ROUTES)):
                if got.get(key) not in allowed:
                    problems.append(f"{key} {got.get(key)!r} is not one of {sorted(allowed)}")
            address = got.get("address")
            if not isinstance(address, str) or not address.strip():
                problems.append("address missing")
            elif got.get("source") in ("dv_html", "dv_pdf") and not address.strip().isdigit():
                problems.append(f"address {address!r} is not a material id, as the source {got.get('source')} needs")
            elif got.get("source") in ("moj_portal", "strategy_bg", "paid_service") and address.strip() != "unknown" and not address.strip().startswith(("http://", "https://")):
                problems.append(f"address {address!r} is not a URL, as the source {got.get('source')} needs")
            ev = got.get("evidence")
            if not isinstance(ev, dict) or not all(isinstance(ev.get(k), str) and ev[k].strip() for k in ("defect", "source", "route")):
                problems.append("evidence notes missing or empty")
            if set(got) - {"defect", "source", "address", "route", "evidence"}:
                problems.append(f"keys outside the form: {sorted(set(got) - {'defect', 'source', 'address', 'route', 'evidence'})}")
        if problems:
            return StepResult("stop", "the investigator's answer is outside the form: " + "; ".join(problems), [_rel(ctx, answer)])
        kept = {k: got[k] for k in ("defect", "source", "address", "route", "evidence")}
        (ctx.act_dir / "investigate-result.json").write_text(json.dumps({**kept, "answered_at": _now()}, ensure_ascii=False, indent=1), encoding="utf-8")
        return StepResult("done", f"defect {got['defect']}, source {got['source']} at {got['address']}, route {got['route']}", [_rel(ctx, answer)])


class RouteDecision:
    name = "route_decision"
    version = "1"

    def inputs(self, ctx: Context) -> list[Path]:
        return [ctx.act_dir / "investigate-result.json"]

    def outputs(self, ctx: Context) -> list[Path]:
        return []

    def run(self, ctx: Context) -> StepResult:
        got = json.loads((ctx.act_dir / "investigate-result.json").read_text(encoding="utf-8"))
        ctx.entry = sx.update(ctx.list_path, ctx.slug, defect=got["defect"], source=got["source"], address=got["address"], route=got["route"],
                              state="investigated", evidence=(ctx.entry.evidence if ctx.entry else []) + [{"kind": "case_file", "ref": f"investigated in run {ctx.run}: {_rel(ctx, ctx.act_dir / 'investigate-result.json')}"}])
        return StepResult("stop", f"investigated: the list now names the route {got['route']} from {got['source']} at {got['address']}; the act goes through it in a new run",
                          [_rel(ctx, ctx.act_dir / "investigate-result.json")])


STEPS = {s.name: s for s in (AmendmentSearch(), FetchMaterial(), Prepare(), Label(), Ladder(), ContentCheck(), Witnesses(), Write(), Investigate(), RouteDecision())}
