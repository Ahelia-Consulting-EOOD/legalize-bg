"""The ``estado`` run of 1 November 2026: the field carries what lex.bg's own page says about the act's repeal.

The bootstrap wrote ``estado: vigente`` as a constant for every act (``fetcher/bg/metadata.py``), so the field said
nothing (D-077 (9), the follow-up of 2026-10-31). lex.bg's page of an act records its repeal in two places that are
read together: the history line (the element ``HistoryOfDocument``: „Обн. ДВ. бр. …, изм. ДВ. бр. …, отм. ДВ. бр. …“),
whose last entry „отм. ДВ. бр. N от <date>“ names the Gazette issue that carried the repeal, and the repeal note under
the title („Отменена с § 2 от преходните и заключителните разпоредби на Наредба № … - ДВ, бр. N от <date>, в сила от
<date>“), which names the repealing act and the day the repeal takes effect. The line alone is not enough: the issue
that carries a repeal is often months before its entry into force, and one page's note („Отменено основание“) says
that the act's legal basis was repealed, not the act. This module reads both with a fixed form and, through the single
corpus write gate, writes the repeal into the frontmatter.

The fixed form (the parser settles only what matches it; everything else is recorded unparsed, never guessed):

- the history line is a sequence of Gazette entries, each a verb and a reference „ДВ. бр. N от D Month YYYYг.“, as the
  bootstrap's ``DV_REF_PATTERN`` reads them; the verb of an entry is the text between the previous entry and the
  reference, stripped of the separators lex.bg prints („ , “);
- the line **carries the act's repeal** when the last entry's verb is exactly „отм.“ and the word „отм“ occurs nowhere
  else in the line (a repeal entry followed by an amendment, two repeal entries, or „отм“ inside another entry's verb
  would say that a part was repealed, or that the repeal did not hold, and the form does not settle that);
- the note is the paragraph beginning „Отменен с“ or „Отменена с“ (lex.bg prints a Latin letter in one of them), and
  carries the repealing provision and act, the same Gazette issue as the line's repeal entry, and „в сила от <date>“;
- the act is **repealed** when the line carries its repeal, the note matches it and the entry into force is on or
  before the run's date; its repeal is **pending** when that date is later (the act is in force today; listed, not
  written); it is **not repealed per lex.bg** when the word „отм“ occurs nowhere in the line and the page carries no
  note; the page is **unsettled** otherwise, with the reason: a note that names the repealed legal basis instead of the
  act, an entry into force that is not a fixed date („считано от момента на започване на функционирането на …“), a note
  without a repeal entry or a repeal entry without a note, a note whose issue differs from the line's; a page without
  the element has **no history line**.

The run (``python -m reading.estado report`` to count; ``write --commit`` to write) reads every corpus act's page from
the raw store, and for every act whose parsed status is ``repealed`` while the frontmatter says ``vigente`` writes
``estado: derogado`` through ``corpus_gate.write_act`` in one commit per act, ``[otmyana]``, author-dated at the repeal
(D-048), with the four trailers (``Source-Id`` the repealing issue as the history line gives it, ``Source-Date`` the
issue's date, ``Norm-Id`` the act, ``Record-Id`` the run record). The repeal's issue and date go into the fields the
schema already has: when the page's Gazette entries before the repeal are the committed amendment rows, the repeal's
row is added to ``amendment_history`` (as the bootstrap's parser puts every entry of the line there, the repeal
included) and ``ultima_actualizacion`` becomes the repeal's issue date; when the page carries entries the corpus has not
absorbed, only ``estado`` is written and the act is listed in the report. No field is added. A committed ``derogado``
act is never un-repealed (refresh P0-6): one whose page carries no repeal is reported, not written.

Usage::

    python -m reading.estado report [--today 2026-11-01]
    python -m reading.estado write [--commit] [--today 2026-11-01]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bootstrap import _format_author_date  # noqa: E402
from corpus_gate import CorpusIntegrityError, ListedActRefused, SourceRef, render_act, write_act  # noqa: E402
from corpus_integrity.loader import CATEGORY_DIRS  # noqa: E402
from fetcher.bg.metadata import BG_MONTHS, DV_REF_PATTERN, MetadataParser  # noqa: E402
from reading.splitter import decode  # noqa: E402
from refresh import _split_frontmatter  # noqa: E402

RAW = ROOT / "data" / "raw" / "lexbg"
RUNS = ROOT / "data" / "runs"
RUN_NAME = "estado-lexbg-2026-11-01"

STATUSES = ("repealed", "repeal_pending", "not_repealed", "unsettled", "no_history")

_REPEAL_WORD = re.compile(r"отм", re.IGNORECASE)
_REPEAL_VERB = re.compile(r"отм\.", re.IGNORECASE)
_SEPARATORS = " ,; "   # the verb keeps its full stop: „отм.“ is the form, „отм“ is not
_NOTE_ACT = re.compile(r"^Отменен[аa]?\s+с\s+", re.IGNORECASE)      # „Отменена с …“, „Отменен с …“; lex.bg prints a Latin a in one
_NOTE_BASIS = re.compile(r"^Отменено\s+основание", re.IGNORECASE)   # the act's legal basis was repealed, not the act
_NOTE_ANY = re.compile(r"^Отменен", re.IGNORECASE)
_NOTE_ISSUE = re.compile(r"\s+-\s+ДВ,\s*бр\.\s*(\d+)\s+от\s+(\d{1,2})\s+([А-Яа-я]+)\s+(\d{4})\s*г\.", re.IGNORECASE)
_IN_FORCE = re.compile(r"^\s*,?\s*в\s+сила\s+(?:от\s+)?(?:(\d{1,2})\.(\d{1,2})\.(\d{4})|(\d{1,2})\s+([А-Яа-я]+)\s+(\d{4}))\s*г\.", re.IGNORECASE)
_IN_FORCE_WORDS = re.compile(r"в\s+сила", re.IGNORECASE)
_ISSUE_WORDS = re.compile(r"ДВ,\s*бр\.", re.IGNORECASE)


def _ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class Entry:
    """One Gazette entry of the history line: its verb as printed, the issue „N/YYYY“ and the ISO date (None without a full date)."""
    verb: str
    issue: str
    date: str | None
    text: str


@dataclass
class Reading:
    status: str                      # one of STATUSES
    history: str                     # the line, whitespace-normalised
    entries: list[Entry] = field(default_factory=list)
    repeal_issue: str | None = None  # „64/2000“, the line's repeal entry
    repeal_date: str | None = None   # the issue's date, „2000-08-04“
    marker: str | None = None        # the repeal entry as printed
    reason: str | None = None        # why the page is unsettled or pending
    note: str | None = None          # the repeal note under the title, where the page carries one
    repealing_act: str | None = None  # the provision and act the note names („§ 2 от … на Наредба № 10 от 16 юли 2026 г. за …“)
    note_issue: str | None = None    # the issue the note names, „67/2026“
    in_force: str | None = None      # the day the repeal takes effect, ISO; None when the note gives no fixed date

    def to_dict(self) -> dict:
        d = asdict(self)
        d["entries"] = [asdict(e) for e in self.entries]
        return d


def _iso(day: str, month: str, year: str) -> str | None:
    m = int(month) if month.isdigit() else BG_MONTHS.get(month.lower())
    try:
        return date(int(year), m, int(day)).isoformat() if m else None
    except ValueError:
        return None


def _entry_date(m: re.Match) -> str | None:
    if m.group(2) and m.group(3) and m.group(4):
        return _iso(m.group(2), m.group(3), m.group(4))
    if m.group(5) and m.group(6) and m.group(7):
        return _iso(m.group(5), m.group(6), m.group(7))
    return None


def entries_of(history: str) -> list[Entry]:
    """The Gazette entries of a history line, in order, each with the verb printed before its reference."""
    out, last = [], 0
    for m in DV_REF_PATTERN.finditer(history):
        verb = history[last:m.start()].strip(_SEPARATORS + "\t\n")
        year = m.group(4) or m.group(7)
        issue = f"{m.group(1)}/{year}" if year else m.group(1)
        out.append(Entry(verb=verb, issue=issue, date=_entry_date(m), text=_ws(history[last:m.end()].strip(" ,; "))))
        last = m.end()
    return out


def parse_history(history: str | None) -> Reading:
    """Read one history line with the fixed form: whether it carries the act's repeal, or why it does not settle that."""
    text = _ws(history or "")
    if not text:
        return Reading(status="no_history", history="")
    entries = entries_of(text)
    if not _REPEAL_WORD.search(text):
        return Reading(status="not_repealed", history=text, entries=entries)
    repeal_entries = [i for i, e in enumerate(entries) if _REPEAL_WORD.search(e.verb)]
    matches = list(DV_REF_PATTERN.finditer(text))
    tail = text[matches[-1].end():] if matches else text
    if not entries:
        reason = "the line carries „отм“ but no Gazette entry at all"
    elif _REPEAL_WORD.search(tail):
        reason = "„отм“ stands after the last Gazette entry, outside the form"
    elif len(repeal_entries) == 0:
        reason = "„отм“ occurs outside every entry's verb (a reference the form does not read)"
    elif len(repeal_entries) > 1:
        reason = f"{len(repeal_entries)} entries carry „отм“; one repeal of the act is one entry"
    elif repeal_entries[0] != len(entries) - 1:
        after = len(entries) - 1 - repeal_entries[0]
        reason = f"{after} Gazette entr{'y' if after == 1 else 'ies'} follow the repeal entry (a repeal of a part, or one that did not hold)"
    elif not _REPEAL_VERB.fullmatch(entries[-1].verb):
        reason = f"the repeal entry's verb is „{entries[-1].verb}“, not „отм.“ alone"
    elif entries[-1].date is None:
        reason = "the repeal entry carries no full date"
    else:
        last = entries[-1]
        return Reading(status="repealed", history=text, entries=entries, repeal_issue=last.issue, repeal_date=last.date, marker=last.text)
    return Reading(status="unsettled", history=text, entries=entries, reason=reason)


def history_of(soup: BeautifulSoup) -> str | None:
    """The history line's text, read as ``MetadataParser`` reads it (so the entries are the rows the bootstrap wrote)."""
    el = soup.find(class_="HistoryOfDocument")
    return _ws(el.get_text()) if el else None


_PROVISION_START = re.compile(r"^(Чл\.|§|Глава|Раздел|Част|Преамбюл|Приложение)", re.IGNORECASE)


def note_of(soup: BeautifulSoup) -> str | None:
    """The repeal note under the title, where the page carries one: the innermost paragraph beginning „Отменен…“ that stands
    before the act's first provision (lex.bg prints the note in an ``Article`` element above the text, after lines such as
    „Публикуван: …“ on municipal pages); a provision that starts with the word is the act's text, not the note."""
    for el in soup.find_all(["div", "p"]):
        text = _ws(el.get_text(" "))
        if "Article" in (el.get("class") or []) and _PROVISION_START.match(text):
            return None   # the act's text begins
        if _NOTE_ANY.match(text) and not any(_NOTE_ANY.match(_ws(c.get_text(" "))) for c in el.find_all(["div", "p"])):
            return text
    return None


def parse_note(note: str | None) -> dict:
    """The parts of a repeal note: kind (act, basis or other), the repealing provision and act, the issue „N/YYYY“ and the entry into force.

    The entry into force is read only where the form puts it, right after the issue („- ДВ, бр. N от <date> г., в сила от
    <date> г.“): the repealing act's title may carry a date of its own („(загл. изм. - ДВ, бр. 60 от 2025 г., в сила от
    25.07.2025 г.)“), and a note with more than one issue or more than one entry into force is not read (``kind`` other).
    """
    out = {"kind": None, "repealing_act": None, "note_issue": None, "in_force": None}
    if not note:
        return out
    if _NOTE_BASIS.match(note):
        out["kind"] = "basis"
        return out
    if not _NOTE_ACT.match(note):
        out["kind"] = "other"
        return out
    if len(_ISSUE_WORDS.findall(note)) > 1 or len(_IN_FORCE_WORDS.findall(note)) > 1:
        out["kind"] = "other"
        return out
    out["kind"] = "act"
    issue = _NOTE_ISSUE.search(note)
    if issue:
        out["repealing_act"] = _ws(_NOTE_ACT.sub("", note[:issue.start()]))
        out["note_issue"] = f"{issue.group(1)}/{issue.group(4)}"
        m = _IN_FORCE.match(note[issue.end():])
        if m:
            out["in_force"] = _iso(m.group(1), m.group(2), m.group(3)) if m.group(1) else _iso(m.group(4), m.group(5), m.group(6))
    return out


def read_page(raw: bytes | None, today: str | None = None) -> Reading:
    """The reading of one raw page: the history line and the repeal note read together against the run's date."""
    today = today or date.today().isoformat()
    if not raw:
        return Reading(status="no_history", history="", reason="no page in the raw store")
    soup = BeautifulSoup(decode(raw), "lxml")
    history = history_of(soup)
    r = parse_history(history)
    if r.status == "no_history":
        r.reason = "the page carries no HistoryOfDocument element" if history is None else "the page's HistoryOfDocument element is empty"
    r.note = note_of(soup)
    parts = parse_note(r.note)
    r.repealing_act, r.note_issue, r.in_force = parts["repealing_act"], parts["note_issue"], parts["in_force"]
    if r.status == "unsettled":
        return r
    if parts["kind"] == "basis":
        r.status, r.reason = "unsettled", "the note says the act's legal basis was repealed („Отменено основание“), not the act"
    elif parts["kind"] == "other":
        r.status, r.reason = "unsettled", "the page carries a note beginning „Отменен…“ in a form the parser does not read"
    elif r.status == "repealed":
        if parts["kind"] != "act":
            r.status, r.reason = "unsettled", "the line's last entry is a repeal but the page carries no note „Отменен(а) с …“"
        elif r.note_issue != r.repeal_issue:
            r.status, r.reason = "unsettled", f"the note names ДВ бр. {r.note_issue or '?'} and the line's repeal entry ДВ бр. {r.repeal_issue}"
        elif r.in_force is None:
            r.status, r.reason = "unsettled", "the note's entry into force is not a fixed date"
        elif r.in_force > today:
            r.status, r.reason = "repeal_pending", f"the repeal takes effect on {r.in_force}, after the run's date {today}"
    elif parts["kind"] == "act":
        r.status, r.reason = "unsettled", "the page carries a repeal note but the line carries no repeal entry"
    return r


# --- the run ------------------------------------------------------------------


def corpus_acts(root: Path) -> list[tuple[str, str, Path]]:
    out = []
    for cat in CATEGORY_DIRS:
        for p in sorted((root / cat).glob("*.md")):
            out.append((p.stem, cat, p))
    return out


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _page_rows(raw: bytes, doc_id: str, category: str) -> list[dict]:
    """The page's amendment rows as the bootstrap's parser reads them."""
    meta = MetadataParser().parse(BeautifulSoup(decode(raw), "lxml"), doc_id=int(doc_id), category=category)
    return list(meta.get("amendment_history") or [])


def decide(slug: str, category: str, path: Path, raw: bytes | None, today: str | None = None) -> dict:
    """One act against its page: the reading, the committed state and the outcome of the run for it.

    Outcomes: ``change`` (repealed per lex.bg, committed vigente); ``agree`` (both say the same); ``pending`` (the repeal
    takes effect after the run's date, the act stays as committed); ``kept_derogado`` (committed derogado, the page does
    not read as a repeal in force: never un-repealed); ``unsettled`` and ``no_history`` (not written, listed).
    """
    fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
    doc_id = str(fm.get("identificador", "")).strip()
    reading = read_page(raw, today)
    committed = str(fm.get("estado") or "")
    rows = [r for r in (fm.get("amendment_history") or []) if isinstance(r, dict)]
    row = {"slug": slug, "category": category, "doc_id": doc_id, "titulo": fm.get("titulo"), "estado": committed,
           "ultima_actualizacion": fm.get("ultima_actualizacion"), "reading": reading.to_dict(), "outcome": None,
           "repeal_row_in_history": None, "history_matches_page": None, "page_sha256": _sha256(raw) if raw else None}
    if reading.status == "repealed":
        repeal_row = {"dv": reading.repeal_issue, "date": reading.repeal_date}
        row["repeal_row_in_history"] = repeal_row in rows
        if raw and doc_id.lstrip("-").isdigit():
            # the page's entries, as the bootstrap's parser reads them, are the committed rows plus the repeal row at most
            page_rows = _page_rows(raw, doc_id, category)
            row["history_matches_page"] = page_rows == (rows if repeal_row in rows else [*rows, repeal_row])
        row["outcome"] = "agree" if committed == "derogado" else "change"
    elif committed == "derogado":
        row["outcome"] = "kept_derogado"
    elif reading.status == "not_repealed":
        row["outcome"] = "agree"
    elif reading.status == "repeal_pending":
        row["outcome"] = "pending"
    else:
        row["outcome"] = reading.status
    return row


def survey(root: Path = ROOT, raw_dir: Path = RAW, today: str | None = None) -> list[dict]:
    rows = []
    for slug, cat, path in corpus_acts(root):
        fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        doc_id = str(fm.get("identificador", "")).strip()
        page = raw_dir / f"{doc_id}.html"
        rows.append(decide(slug, cat, path, page.read_bytes() if page.exists() else None, today))
    return rows


def report_of(rows: list[dict], run: str = RUN_NAME, today: str | None = None) -> dict:
    by = lambda outcome: [r for r in rows if r["outcome"] == outcome]  # noqa: E731
    status = lambda s: [r for r in rows if r["reading"]["status"] == s]  # noqa: E731
    line = lambda r: {"slug": r["slug"], "doc_id": r["doc_id"], "estado": r["estado"], "reason": r["reading"]["reason"],  # noqa: E731
                      "history": r["reading"]["history"], "note": r["reading"]["note"]}
    return {
        "run": run,
        "today": today or date.today().isoformat(),
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "acts": len(rows),
        "pages_with_history": sum(1 for r in rows if r["reading"]["status"] != "no_history"),
        "parsed": sum(1 for r in rows if r["reading"]["status"] in ("repealed", "repeal_pending", "not_repealed")),
        "repealed_per_lexbg": len(status("repealed")),
        "already_derogado": sum(1 for r in by("agree") if r["reading"]["status"] == "repealed"),
        "to_change": len(by("change")),
        "repeal_pending": len(status("repeal_pending")),
        "unsettled": len(status("unsettled")),
        "no_history": len(status("no_history")),
        "kept_derogado_without_repeal": [line(r) for r in by("kept_derogado")],
        "pending_acts": [{**line(r), "in_force": r["reading"]["in_force"], "repeal_issue": r["reading"]["repeal_issue"]} for r in status("repeal_pending")],
        "unsettled_acts": [line(r) for r in status("unsettled")],
        "no_history_acts": [{"slug": r["slug"], "doc_id": r["doc_id"], "reason": r["reading"]["reason"]} for r in status("no_history")],
        "changes": [{"slug": r["slug"], "doc_id": r["doc_id"], "repeal_issue": r["reading"]["repeal_issue"], "repeal_date": r["reading"]["repeal_date"],
                     "in_force": r["reading"]["in_force"], "repeal_row_in_history": r["repeal_row_in_history"],
                     "history_matches_page": r["history_matches_page"], "repealing_act": r["reading"]["repealing_act"]} for r in by("change")],
    }


def compact(row: dict) -> dict:
    """One survey line per act: the reading's status and outcome, the line and note only where they decide something."""
    r = row["reading"]
    keep = r["status"] in ("repealed", "repeal_pending", "unsettled") or row["outcome"] == "kept_derogado"
    return {"slug": row["slug"], "doc_id": row["doc_id"], "estado": row["estado"], "status": r["status"], "outcome": row["outcome"],
            "repeal_issue": r["repeal_issue"], "repeal_date": r["repeal_date"], "in_force": r["in_force"], "reason": r["reason"],
            "repeal_row_in_history": row["repeal_row_in_history"], "history_matches_page": row["history_matches_page"],
            "history": r["history"] if keep else None, "note": r["note"] if keep else None}


# --- the write ----------------------------------------------------------------


class WriteRefused(Exception):
    """The act is not written; the reason names what stands in the way."""


@dataclass
class Written:
    slug: str
    record_id: str
    commit: str | None
    fields: list[str]


def _git(root: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, env=env).stdout.strip()


def frontmatter_after(committed: dict, row: dict) -> tuple[dict, list[str]]:
    """The frontmatter with the repeal written into the fields the schema has, and the names of the fields changed."""
    reading = row["reading"]
    if reading["status"] != "repealed":
        raise WriteRefused(f"{row['slug']}: the reading is {reading['status']}, not repealed")
    if committed.get("estado") == "derogado":
        raise WriteRefused(f"{row['slug']}: already derogado")
    meta = dict(committed)
    meta["estado"] = "derogado"
    changed = ["estado"]
    repeal_row = {"dv": reading["repeal_issue"], "date": reading["repeal_date"]}
    rows = [r for r in (committed.get("amendment_history") or []) if isinstance(r, dict)]
    if repeal_row not in rows and row.get("history_matches_page"):
        meta["amendment_history"] = [*rows, repeal_row]
        changed.append("amendment_history")
        if str(committed.get("ultima_actualizacion") or "") < reading["repeal_date"]:
            meta["ultima_actualizacion"] = reading["repeal_date"]
            changed.append("ultima_actualizacion")
    return meta, changed


def write_change(row: dict, *, root: Path = ROOT, run_dir: Path | None = None, waivers_path: Path | None = None,
                 exceptions_path: Path | None = None, commit: bool = True) -> Written:
    """Write one act's repeal through the gate and commit it with its run record."""
    root = Path(root)
    run_dir = Path(run_dir) if run_dir else RUNS / RUN_NAME
    path = root / row["category"] / f"{row['slug']}.md"
    rel = str(path.relative_to(root))
    if _git(root, "status", "--porcelain", "--", rel):   # in both modes: the rollback puts the act back from HEAD
        raise WriteRefused(f"{row['slug']}: uncommitted changes in {rel}; commit or restore them first")
    committed_raw = path.read_text(encoding="utf-8")
    committed, body = _split_frontmatter(committed_raw)
    if render_act(committed, body) != committed_raw:
        raise WriteRefused(f"{row['slug']}: the gate's render does not reproduce the committed file byte for byte; the write would churn it")
    meta, changed = frontmatter_after(committed, row)
    reading = row["reading"]

    record = {"run": run_dir.name, "slug": row["slug"], "doc_id": row["doc_id"], "page_sha256": row["page_sha256"],
              "history": reading["history"], "marker": reading["marker"], "repeal_issue": reading["repeal_issue"],
              "repeal_date": reading["repeal_date"], "note": reading["note"], "repealing_act": reading["repealing_act"],
              "in_force": reading["in_force"],
              "before": {k: committed.get(k) for k in ("estado", "ultima_actualizacion", "amendment_history")},
              "after": {k: meta.get(k) for k in ("estado", "ultima_actualizacion", "amendment_history")},
              "fields_changed": changed, "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    record_bytes = (json.dumps(record, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    record_id = f"{run_dir.name}/{row['slug']}/{_sha256(record_bytes)[:12]}"
    record_path = run_dir / "acts" / f"{row['slug']}.json"

    source = SourceRef("lexbg", row["doc_id"])   # the page the fact is read from; the exceptions list is checked by name at the gate
    files = [rel, str(record_path.relative_to(root))]
    written = recorded = False
    try:
        write_act(path, meta, body, source=source, waivers_path=waivers_path, exceptions_path=exceptions_path)
        written = True
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_bytes(record_bytes)   # after the gate, so a refusal leaves no record of a write that did not happen
        recorded = True
        if not commit:
            return Written(row["slug"], record_id, None, changed)
        _git(root, "add", "--", *files)
        message = (f"[otmyana] {meta['titulo']}\n\n"
                   f"lex.bg's history line of page {row['doc_id']} ends „{reading['marker']}“ and its note reads „{reading['note']}“: "
                   f"the act is repealed by ДВ бр. {reading['repeal_issue']} of {reading['repeal_date']}, in force from {reading['in_force']}. "
                   f"Fields written: {', '.join(changed)}. The run {run_dir.name} (reading/estado.py), the record beside the act.\n\n"
                   f"Source-Id: dv-{reading['repeal_issue']}\n"
                   f"Source-Date: {reading['repeal_date']}\n"
                   f"Norm-Id: {row['doc_id']}\n"
                   f"Record-Id: {record_id}\n")
        env = os.environ.copy()
        author_date = _format_author_date(reading["repeal_date"])
        if author_date:
            env["GIT_AUTHOR_DATE"] = author_date  # the repeal's date; the committer date stays real (D-048)
        _git(root, "commit", "-q", "-m", message, "--", *files, env=env)
    except BaseException:
        if commit:
            subprocess.run(["git", "reset", "-q", "--", *files], cwd=root, capture_output=True)
        if written:
            _git(root, "checkout", "HEAD", "--", rel)   # the committed act, as the check above found it
        if recorded:
            record_path.unlink(missing_ok=True)   # no orphan record of a write that was put back
        raise
    return Written(row["slug"], record_id, _git(root, "rev-parse", "--short", "HEAD"), changed)


def run_write(rows: list[dict], *, root: Path = ROOT, run_dir: Path | None = None, commit: bool = True,
              waivers_path: Path | None = None, exceptions_path: Path | None = None) -> tuple[list[Written], list[dict]]:
    written, refused = [], []
    for row in rows:
        if row["outcome"] != "change":
            continue
        try:
            written.append(write_change(row, root=root, run_dir=run_dir, commit=commit, waivers_path=waivers_path, exceptions_path=exceptions_path))
        except CorpusIntegrityError as exc:
            refused.append({"slug": row["slug"], "by": "gate", "detail": [f"{v.check}@{v.locator}: {v.detail}" for v in exc.violations]})
        except (WriteRefused, ListedActRefused) as exc:
            refused.append({"slug": row["slug"], "by": "run", "detail": [str(exc)]})
        except subprocess.CalledProcessError as exc:   # a git failure is rolled back and reported; the run and its report go on
            refused.append({"slug": row["slug"], "by": "git", "detail": [f"{exc.cmd}: exit {exc.returncode}: {(exc.stderr or '').strip()[:300]}"]})
    return written, refused


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("step", choices=["report", "write"])
    ap.add_argument("--run", default=RUN_NAME)
    ap.add_argument("--commit", action="store_true", help="commit each written act (write only)")
    ap.add_argument("--today", default=None, help="the run's date (ISO); a repeal in force after it is pending, not written")
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--raw", type=Path, default=RAW)
    args = ap.parse_args(argv)
    today = args.today or date.today().isoformat()
    run_dir = Path(args.root) / "data" / "runs" / args.run
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = survey(args.root, args.raw, today)
    report = report_of(rows, args.run, today)
    if args.step == "write":
        written, refused = run_write(rows, root=args.root, run_dir=run_dir, commit=args.commit)
        done = {w.slug for w in written}
        for row in rows:   # the survey line of a written act says what the corpus now says
            if row["slug"] in done:
                row["outcome"], row["estado"] = "agree", "derogado"
        report["written"] = [{"slug": w.slug, "commit": w.commit, "record_id": w.record_id, "fields": w.fields} for w in written]
        report["refused"] = refused
        for w in written:
            print(f"written  {w.slug}: {w.commit or '-'} {', '.join(w.fields)} Record-Id {w.record_id}")
        for r in refused:
            print(f"refused  {r['slug']}: {r['detail'][0]}")
    (run_dir / "survey.json").write_text(json.dumps([compact(r) for r in rows], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (run_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if not isinstance(v, list)}, ensure_ascii=False, indent=1))
    for u in report["pending_acts"]:
        print(f"pending   {u['slug']} ({u['doc_id']}): in force from {u['in_force']}")
    for u in report["unsettled_acts"]:
        print(f"unsettled {u['slug']} ({u['doc_id']}): {u['reason']}")
    return 1 if report.get("refused") else 0


if __name__ == "__main__":
    raise SystemExit(main())
