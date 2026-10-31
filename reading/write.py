"""The write path, step 3 of the plan of 2026-10-21 (``docs/plans/2026-10-21-write-path-session.md``).

``write_staged(slug, run_dir)`` takes one act a reading run has read to no
exception and commits it to the corpus through the single write gate:

1. the page is read again from the raw store, its SHA-256 checked against the
   store's manifest, and split again; the blocks must equal the run's
   ``blocks.json``;
2. the body is assembled again from those blocks and the run's ``map.json``,
   with the rulings of D-072 applied, and checked again; a label exception, or
   a body that differs from the run's ``staged.md``, refuses the write before
   the gate is called;
3. the frontmatter is built as the refresh path builds it (``MetadataParser.parse``
   over the page, ``merge_preserved`` over the committed frontmatter, a repealed
   act kept repealed), and the ``provenance`` block of ruling 12 is filled;
4. ``corpus_gate.write_act`` writes the file or refuses it, leaving it unchanged;

An act read from a Gazette material (a run whose ``blocks.json`` says ``source: dv``,
step S1 of the plan of 31 October 2026) goes the same way: the material is read again
from the cache, its hash checked against the run's ``material.json``, split again with
``split_dv``; the frontmatter keeps every committed field and sets the source field to
the Gazette, the publication and issue fields and the one amendment row from the
material's header (``build_frontmatter_dv``, the Surface 2 preflight); the provenance
base names the material with its hash; the commit's ``Source-Id`` is ``dv-<material>``.
Before any of it, an act on the exceptions list is refused on the lex.bg path by name,
and lost text (an empty section, a first § above 1: D-076 (3)) refuses the write.
5. the act, its run record (``map.json``, the round reports, D-073, and the witness
   record when the witnesses were compared) and any waiver count the repair lowers go into one commit, ``[reforma]`` when
   the amendment list grew and ``[popravka]`` otherwise (ruling 11), with the
   three trailers and ``Record-Id``.

The act and the waiver file must carry no uncommitted change when a commit is
asked for, so a failure anywhere after the waiver is lowered puts both back as
git holds them: the waiver file from its text before, the act by ``git checkout``
of its committed version, never by writing it here.

The text parser is not called: the body is the reading run's. This module writes
the corpus only through the gate.

Usage::

    python reading/write.py --run structure-map-2026-10-22 SLUG [SLUG ...]
    python reading/write.py --run structure-map-2026-10-22 --all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import source_exceptions as sx  # noqa: E402
from bootstrap import _format_author_date  # noqa: E402
from corpus_gate import DEFAULT_WAIVERS, CorpusIntegrityError, SourceRef, render_act, write_act  # noqa: E402
from corpus_integrity.__main__ import CHECKS  # noqa: E402
from corpus_integrity.loader import CATEGORY_DIRS, act_from_text  # noqa: E402
from fetcher.bg.discovery import ENCODING  # noqa: E402
from fetcher.bg.metadata import MetadataParser  # noqa: E402
from reading import ladder, waiver_count  # noqa: E402
from reading.splitter import SplitAct, split_dv, split_lexbg  # noqa: E402
from refresh import _split_frontmatter, classify_change, history_grew, latest_amendment_date, merge_preserved  # noqa: E402

RAW = ROOT / "data" / "raw" / "lexbg"
DV_CACHE = ROOT / "data" / "dv" / "cache"
RUNS = ROOT / "data" / "runs"
WAIVERS = DEFAULT_WAIVERS.relative_to(ROOT)
EXCEPTIONS = sx.DEFAULT_PATH.relative_to(ROOT)
DV_FUENTE = "dv.parliament.bg"   # the schema reference's value of `fuente` for a Gazette-sourced act (Surface 2 preflight of 31 October 2026)


class WriteRefused(Exception):
    """The reading does not hold up against the page; nothing was written."""


class LostText(WriteRefused):
    """The content check of D-076 (3): an empty section or a first § above 1; the act is listed for investigation."""


def date_today() -> str:
    from datetime import date
    return date.today().isoformat()


def _issue_key(dv: str | None) -> tuple[int, int] | None:
    """(year, number) of an amendment row's "32/2026"; None for a row that does not read as one (the caller refuses it)."""
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d{4})\s*", str(dv or ""))
    return (int(m.group(2)), int(m.group(1))) if m else None


def _check_witness_record(slug: str, run_dir: Path, body: str) -> dict:
    """A Gazette-read act is written only with its witness record, made for this body, with no stopping verdict."""
    from reading import witnesses
    p = run_dir / "witness-record.json"
    if not p.exists():
        raise WriteRefused(f"{slug}: no witness-record.json in the run folder; the witnesses are compared and settled before the write")
    rec = json.loads(p.read_text(encoding="utf-8"))
    if rec.get("body_sha256") != witnesses.body_sha256(body):
        raise WriteRefused(f"{slug}: the witness record was made for another body than the one written; compare the witnesses again")
    if rec.get("stops"):
        raise WriteRefused(f"{slug}: the witness record carries a stopping verdict ({', '.join(rec['stops'])}); the reading is wrong somewhere")
    return rec


@dataclass
class Written:
    slug: str
    commit_type: str  # "reforma", "popravka" or "unchanged"
    record_id: str
    commit: str | None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest_row(raw_dir: Path, doc_id: str) -> dict:
    """The raw store's last manifest line for the page."""
    row = None
    with (raw_dir / "manifest.jsonl").open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if str(r.get("doc_id")) == doc_id and r.get("status") == "ok":
                row = r
    if row is None:
        raise WriteRefused(f"the raw store's manifest has no fetched page {doc_id}")
    return row


def corpus_file(root: Path, slug: str) -> Path:
    found = [root / cat / f"{slug}.md" for cat in CATEGORY_DIRS if (root / cat / f"{slug}.md").exists()]
    if len(found) != 1:
        raise WriteRefused(f"{slug}: {len(found)} corpus files carry this slug")
    return found[0]


def build_frontmatter(raw: bytes, doc_id: str, category: str, committed: dict) -> dict:
    """The frontmatter the refresh path writes for this page over this committed frontmatter."""
    soup = BeautifulSoup(raw.decode(ENCODING), "lxml")
    meta = MetadataParser().parse(soup, doc_id=int(doc_id), category=category)
    if not (meta.get("titulo") or "").strip():
        raise WriteRefused(f"the page {doc_id} carries no title")
    # never un-repeal: the parser reads no repeal, so a committed derogado act stays derogado (refresh P0-6)
    if committed.get("estado") == "derogado":
        meta["estado"] = "derogado"
    return merge_preserved(committed, meta)


def _check_reading(slug: str, run_dir: Path, act: SplitAct, what: str) -> tuple[str, list[dict], dict]:
    """The blocks, the map and the body of the run against the source split again: (body, omissions, the record block)."""
    blocks_bytes = (run_dir / "blocks.json").read_bytes()
    if act.to_dict() != json.loads(blocks_bytes):
        raise WriteRefused(f"{slug}: the {what} splits into other blocks than the run's blocks.json")
    map_bytes = (run_dir / "map.json").read_bytes()
    smap = {int(k): v for k, v in json.loads(map_bytes).items()}
    body, exceptions, omissions, _ = ladder.evaluate(act, smap, [], slug)
    # the content check of D-076 (3): lost text (an empty section, a first § above 1) stops the write like a label exception
    lost = [e for e in exceptions if e["kind"] in ladder.LOST_TEXT]
    if lost:
        kinds = sorted({e["kind"] for e in lost})
        raise LostText(f"{slug}: lost text on the {what} ({', '.join(kinds)}), first at block {lost[0]['block']}: "
                       f"{lost[0]['detail']}; the act goes to the exceptions list with the route investigate (D-076)")
    blocking = [e for e in exceptions if e["kind"] not in ladder.SOURCE_FINDINGS]
    if blocking:
        kinds = sorted({e["kind"] for e in blocking})
        raise WriteRefused(f"{slug}: {len(blocking)} exception(s) on the {what} ({', '.join(kinds)}), first at block {blocking[0]['block']}")
    if body != (run_dir / "staged.md").read_text(encoding="utf-8"):
        raise WriteRefused(f"{slug}: the body assembled from the {what} differs from the run's staged.md")
    record = {"run": run_dir.parent.name, "map_sha256": _sha256(map_bytes), "blocks_sha256": _sha256(blocks_bytes)}
    return body, omissions, record


def reread(slug: str, run_dir: Path, raw_dir: Path, doc_id: str) -> tuple[str, list[dict], dict]:
    """Assemble and check the body again from the page: (body, omissions, the provenance block without omissions)."""
    raw = (raw_dir / f"{doc_id}.html").read_bytes()
    row = _manifest_row(raw_dir, doc_id)
    if _sha256(raw) != row["sha256"]:
        raise WriteRefused(f"{slug}: the page {doc_id} in the raw store differs from its manifest line")
    body, omissions, record = _check_reading(slug, run_dir, split_lexbg(raw), "page")
    provenance = {
        "base": {"source": "lexbg", "state": "snapshot", "page_sha256": row["sha256"], "fetched_at": row["fetched_at"]},
        "record": record,
    }
    return body, omissions, provenance


def material_record(run_dir: Path) -> dict:
    """The run's record of the Gazette material it was read from (written by the route's fetch step)."""
    p = run_dir / "material.json"
    if not p.exists():
        raise WriteRefused(f"{run_dir.name}: no material.json in the run folder; the route's fetch step writes it")
    rec = json.loads(p.read_text(encoding="utf-8"))
    for key in ("id_mat", "sha256", "fetched_at", "issue_number", "issue_year", "issue_date"):
        if key not in rec:
            raise WriteRefused(f"{run_dir.name}: material.json lacks {key}")
    return rec


def reread_dv(slug: str, run_dir: Path, cache_dir: Path) -> tuple[str, list[dict], dict, dict]:
    """The same for a Gazette material: (body, omissions, provenance without omissions, the material record)."""
    rec = material_record(run_dir)
    html = (cache_dir / f"{rec['id_mat']}.html").read_bytes()
    if _sha256(html) != rec["sha256"]:
        raise WriteRefused(f"{slug}: the material {rec['id_mat']} in the cache differs from the run's material.json")
    body, omissions, record = _check_reading(slug, run_dir, split_dv(html), "material")
    provenance = {
        "base": {"source": "dv", "state": "promulgated", "material": int(rec["id_mat"]), "issue": f"{rec['issue_number']}/{rec['issue_year']}",
                 "issue_date": rec["issue_date"], "material_sha256": rec["sha256"], "fetched_at": rec["fetched_at"]},
        "record": record,
    }
    return body, omissions, provenance, rec


def build_frontmatter_dv(committed: dict, rec: dict) -> dict:
    """The frontmatter of an act read whole from its promulgation material (the Surface 2 preflight of 31 October 2026).

    Every committed field is kept, the identifier included, since the act's key does not change with its source.
    The source field names the Gazette; the publication, the issue and the one amendment row come from the material's
    header; the state stays as committed (the material promulgates, it never repeals).
    """
    meta = {k: v for k, v in committed.items() if k != "provenance"}
    issue = f"{rec['issue_number']}/{rec['issue_year']}"
    rows = [r for r in (committed.get("amendment_history") or []) if isinstance(r, dict) and r.get("dv") == issue]
    row = {**(rows[0] if rows else {}), "dv": issue, "date": rec["issue_date"]}
    meta.update({"fuente": DV_FUENTE, "fecha_publicacion": rec["issue_date"], "ultima_actualizacion": rec["issue_date"],
                 "dv_issue": str(rec["issue_number"]), "dv_year": int(rec["issue_year"]), "amendment_history": [row]})
    return meta


def _lower_waivers(waivers_path: Path, slug: str, path: Path, text: str) -> str | None:
    """Lower the act's count under every gated check to what the new text carries; the file's text before, or None."""
    act = act_from_text(path, text, category=path.parent.name)
    before = None
    for check in CHECKS:
        prior = waiver_count.lower_count(waivers_path, check.name, slug, len(check.run([act])))
        before = before if before is not None else prior
    return before


def _git(root: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, env=env).stdout.strip()


def _rel(root: Path, f: Path) -> str:
    try:
        return str(f.relative_to(root))
    except ValueError:
        raise WriteRefused(f"{f} lies outside the repository {root}") from None


def run_source(run_dir: Path) -> str:
    """The source the run's blocks were cut from: ``lexbg`` (the raw store) or ``dv`` (a Gazette material).

    A run folder without its blocks is taken as the lex.bg path, so a listed act is refused by name before anything
    else is read; the reread then refuses the folder itself.
    """
    p = Path(run_dir) / "blocks.json"
    if not p.exists():
        return "lexbg"
    return json.loads(p.read_text(encoding="utf-8")).get("source", "lexbg")


def write_staged(slug: str, run_dir: Path | str, *, root: Path | str = ROOT, raw_dir: Path | str = RAW,
                 cache_dir: Path | str = DV_CACHE, waivers_path: Path | str | None = None,
                 exceptions_path: Path | str | None = None, commit: bool = True) -> Written:
    """Write one read act through the gate and commit it with its run record."""
    root, run_dir, raw_dir, cache_dir = Path(root), Path(run_dir), Path(raw_dir), Path(cache_dir)
    waivers_path = Path(waivers_path) if waivers_path else root / WAIVERS
    exceptions_path = Path(exceptions_path) if exceptions_path else root / EXCEPTIONS
    own_list = exceptions_path.exists()   # only a list of this root is ever written to
    if not own_list:
        exceptions_path = sx.DEFAULT_PATH   # a root without a list (a test's) is still held to the repository's list, read only
    path = corpus_file(root, slug)
    source = run_source(run_dir)
    if source == "lexbg":
        # the exceptions list: an act whose text is not taken from lex.bg is refused on the lex.bg path by name
        entry = sx.listed(slug, exceptions_path)
        if entry is not None:
            raise WriteRefused(f"{slug}: on the exceptions list ({entry.defect}; source {entry.source}, route {entry.route}); "
                               f"the lex.bg path is refused for it")
    if commit:
        own = [_rel(root, path), _rel(root, waivers_path)]
        if _git(root, "status", "--porcelain", "--", *own):
            # a write left uncommitted (an earlier failure, a hand edit) would otherwise read as unchanged
            raise WriteRefused(f"{slug}: uncommitted changes in {' or '.join(own)}; commit or restore them first")
    committed_raw = path.read_text(encoding="utf-8")
    committed, _ = _split_frontmatter(committed_raw)
    doc_id = str(committed.get("identificador", "")).strip()
    if not re.fullmatch(r"-?\d+", doc_id):
        raise WriteRefused(f"{slug}: the committed frontmatter carries no lex.bg identificador")

    if source == "dv":
        rec = material_record(run_dir)
        entry = sx.listed(slug, exceptions_path)
        # the Gazette path writes an act whole from its promulgation material only when the list says so for that material
        if entry is None or entry.route != "whole_act_from_material":
            raise WriteRefused(f"{slug}: a Gazette material is written whole only for an act listed with the route whole_act_from_material "
                               f"(the list says {entry.route if entry else 'nothing'})")
        if str(entry.address).strip() != str(rec["id_mat"]):
            raise WriteRefused(f"{slug}: the run's material {rec['id_mat']} is not the entry's address {entry.address}")
        issue = (int(rec["issue_year"]), int(rec["issue_number"]))
        rows = [r for r in (committed.get("amendment_history") or []) if isinstance(r, dict)]
        unreadable = [r.get("dv") for r in rows if _issue_key(r.get("dv")) is None]
        if unreadable:
            raise WriteRefused(f"{slug}: the committed history holds rows that do not read as issue/year ({', '.join(map(str, unreadable))}); "
                               f"they are settled before a Gazette write")
        later = [r.get("dv") for r in rows if _issue_key(r.get("dv")) > issue]
        if later:
            raise WriteRefused(f"{slug}: the committed history holds {', '.join(map(str, later))} after the material's issue {issue[1]}/{issue[0]}; "
                               f"the act is not whole in that material (the history route is needed)")
        body, omissions, provenance, rec = reread_dv(slug, run_dir, cache_dir)
        _check_witness_record(slug, run_dir, body)
        meta = build_frontmatter_dv(committed, rec)
        source_ref = SourceRef("dv", str(rec["id_mat"]))
    else:
        try:
            body, omissions, provenance = reread(slug, run_dir, raw_dir, doc_id)
        except LostText as exc:
            # D-076 (3): the act goes to the exceptions list with the route investigate, through the list's own add
            if own_list and sx.listed(slug, exceptions_path) is None:
                sx.add(exceptions_path, sx.Entry(slug=slug, title=str(committed.get("titulo") or slug), defect="dropped_section", source="unknown",
                                                 address="unknown", route="investigate", state="listed", added=date_today(),
                                                 evidence=[{"kind": "audit", "ref": f"the content check on the lex.bg page {doc_id} in run {run_dir.parent.name}: {exc}"}],
                                                 note="listed by the content check of the write path; the investigator records the defect, the source and the route"))
            raise WriteRefused(str(exc)) from None
        raw = (raw_dir / f"{doc_id}.html").read_bytes()
        meta = build_frontmatter(raw, doc_id, path.parent.name, committed)
        source_ref = SourceRef("lexbg", doc_id)
    provenance["omissions"] = [{"kind": o["kind"], "blocks": list(o["blocks"])} for o in omissions]
    meta["provenance"] = provenance
    record_id = f"{provenance['record']['run']}/{slug}/{provenance['record']['map_sha256'][:12]}"

    # the refresh path's classification, over the text the gate will render
    text = render_act(meta, body)
    fresh_hist = meta.get("amendment_history") or []
    commit_type = classify_change(committed_raw, text, history_grew(committed.get("amendment_history") or [], fresh_hist))
    if commit_type == "unchanged":
        return Written(slug, "unchanged", record_id, None)

    record = [run_dir / "map.json", *sorted(run_dir.glob("report-round*.json")), *[p for p in [run_dir / "witness-record.json"] if p.exists()]]
    files = [_rel(root, f) for f in [path, *record]]
    before = waivers_path.read_text(encoding="utf-8")  # read once, so any failure below can put it back
    lowered = written = False
    try:
        lowered = _lower_waivers(waivers_path, slug, path, text) is not None
        write_act(path, meta, body, source=source_ref, waivers_path=waivers_path, exceptions_path=exceptions_path)
        written = True
        if not commit:
            return Written(slug, commit_type, record_id, None)
        files += [_rel(root, waivers_path)] if lowered else []
        _git(root, "add", "--", *files)
        date = latest_amendment_date(fresh_hist) or meta.get("fecha_publicacion")
        message = (f"[{commit_type}] {meta['titulo']}\n\n"
                   f"Source-Id: {source_ref.kind}-{source_ref.ident}\n"
                   f"Source-Date: {date or 'unknown'}\n"
                   f"Norm-Id: {doc_id}\n"
                   f"Record-Id: {record_id}\n")
        env = os.environ.copy()
        author_date = _format_author_date(date)
        if author_date:
            env["GIT_AUTHOR_DATE"] = author_date  # the legislative date; the committer date stays real (D-048)
        _git(root, "commit", "-m", message, "--", *files, env=env)
    except BaseException:
        try:
            if commit:
                subprocess.run(["git", "reset", "-q", "--", *files], cwd=root, capture_output=True)
                if written:
                    _git(root, "checkout", "HEAD", "--", _rel(root, path))  # the committed act, as the check above found it
        finally:
            if waivers_path.read_text(encoding="utf-8") != before:  # also when a second check failed after a first lowered it
                waiver_count.restore(waivers_path, before)
        raise
    return Written(slug, commit_type, record_id, _git(root, "rev-parse", "--short", "HEAD"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--run", required=True, help="the run folder under data/runs/")
    ap.add_argument("--all", action="store_true", help="every act of the run")
    ap.add_argument("--no-commit", action="store_true", help="write through the gate, do not commit")
    ap.add_argument("slugs", nargs="*")
    args = ap.parse_args(argv)
    run_root = RUNS / args.run
    slugs = sorted(p.name for p in run_root.iterdir() if (p / "map.json").exists()) if args.all else args.slugs
    written, refused = [], []
    for slug in slugs:
        try:
            w = write_staged(slug, run_root / slug, commit=not args.no_commit)
            written.append(w)
            print(f"written  {slug}: [{w.commit_type}] {w.commit or '-'} Record-Id {w.record_id}")
        except CorpusIntegrityError as exc:
            refused.append((slug, "gate", [f"{v.check}@{v.locator}: {v.detail}" for v in exc.violations]))
            print(f"refused  {slug}: the gate, {len(exc.violations)} violation(s)")
        except WriteRefused as exc:
            refused.append((slug, "reading", [str(exc)]))
            print(f"refused  {slug}: {exc}")
        except Exception as exc:  # one broken run folder or git call stops that act, not the pass and its report
            refused.append((slug, "error", [f"{type(exc).__name__}: {exc}"]))
            print(f"refused  {slug}: {type(exc).__name__}: {exc}")
    print(json.dumps({"written": [{"slug": w.slug, "type": w.commit_type, "commit": w.commit} for w in written],
                      "refused": [{"slug": s, "by": by, "violations": v[:5], "count": len(v)} for s, by, v in refused]},
                     ensure_ascii=False, indent=1))
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
