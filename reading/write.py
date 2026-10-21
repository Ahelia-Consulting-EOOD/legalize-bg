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
5. the act, its run record (``map.json`` and the round reports, D-073) and any
   waiver count the repair lowers go into one commit, ``[reforma]`` when
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

from bootstrap import _format_author_date  # noqa: E402
from corpus_gate import DEFAULT_WAIVERS, CorpusIntegrityError, SourceRef, render_act, write_act  # noqa: E402
from corpus_integrity.__main__ import CHECKS  # noqa: E402
from corpus_integrity.loader import CATEGORY_DIRS, act_from_text  # noqa: E402
from fetcher.bg.discovery import ENCODING  # noqa: E402
from fetcher.bg.metadata import MetadataParser  # noqa: E402
from reading import ladder, waiver_count  # noqa: E402
from reading.splitter import split_lexbg  # noqa: E402
from refresh import _split_frontmatter, classify_change, history_grew, latest_amendment_date, merge_preserved  # noqa: E402

RAW = ROOT / "data" / "raw" / "lexbg"
RUNS = ROOT / "data" / "runs"
WAIVERS = DEFAULT_WAIVERS.relative_to(ROOT)


class WriteRefused(Exception):
    """The reading does not hold up against the page; nothing was written."""


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


def reread(slug: str, run_dir: Path, raw_dir: Path, doc_id: str) -> tuple[str, list[dict], dict]:
    """Assemble and check the body again from the page: (body, omissions, the provenance block without omissions)."""
    raw = (raw_dir / f"{doc_id}.html").read_bytes()
    row = _manifest_row(raw_dir, doc_id)
    if _sha256(raw) != row["sha256"]:
        raise WriteRefused(f"{slug}: the page {doc_id} in the raw store differs from its manifest line")
    act = split_lexbg(raw)
    blocks_bytes = (run_dir / "blocks.json").read_bytes()
    if act.to_dict() != json.loads(blocks_bytes):
        raise WriteRefused(f"{slug}: the page splits into other blocks than the run's blocks.json")
    map_bytes = (run_dir / "map.json").read_bytes()
    smap = {int(k): v for k, v in json.loads(map_bytes).items()}
    body, exceptions, omissions, _ = ladder.evaluate(act, smap, [], slug)
    blocking = [e for e in exceptions if e["kind"] not in ladder.SOURCE_FINDINGS]
    if blocking:
        kinds = sorted({e["kind"] for e in blocking})
        raise WriteRefused(f"{slug}: {len(blocking)} exception(s) on the page ({', '.join(kinds)}), first at block {blocking[0]['block']}")
    if body != (run_dir / "staged.md").read_text(encoding="utf-8"):
        raise WriteRefused(f"{slug}: the body assembled from the page differs from the run's staged.md")
    provenance = {
        "base": {"source": "lexbg", "state": "snapshot", "page_sha256": row["sha256"], "fetched_at": row["fetched_at"]},
        "record": {"run": run_dir.parent.name, "map_sha256": _sha256(map_bytes), "blocks_sha256": _sha256(blocks_bytes)},
    }
    return body, omissions, provenance


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


def write_staged(slug: str, run_dir: Path | str, *, root: Path | str = ROOT, raw_dir: Path | str = RAW,
                 waivers_path: Path | str | None = None, commit: bool = True) -> Written:
    """Write one read act through the gate and commit it with its run record."""
    root, run_dir, raw_dir = Path(root), Path(run_dir), Path(raw_dir)
    waivers_path = Path(waivers_path) if waivers_path else root / WAIVERS
    path = corpus_file(root, slug)
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

    body, omissions, provenance = reread(slug, run_dir, raw_dir, doc_id)
    raw = (raw_dir / f"{doc_id}.html").read_bytes()
    meta = build_frontmatter(raw, doc_id, path.parent.name, committed)
    provenance["omissions"] = [{"kind": o["kind"], "blocks": list(o["blocks"])} for o in omissions]
    meta["provenance"] = provenance
    record_id = f"{provenance['record']['run']}/{slug}/{provenance['record']['map_sha256'][:12]}"

    # the refresh path's classification, over the text the gate will render
    text = render_act(meta, body)
    fresh_hist = meta.get("amendment_history") or []
    commit_type = classify_change(committed_raw, text, history_grew(committed.get("amendment_history") or [], fresh_hist))
    if commit_type == "unchanged":
        return Written(slug, "unchanged", record_id, None)

    record = [run_dir / "map.json", *sorted(run_dir.glob("report-round*.json"))]
    files = [_rel(root, f) for f in [path, *record]]
    before = _lower_waivers(waivers_path, slug, path, text)
    lowered = before is not None
    written = False
    try:
        write_act(path, meta, body, source=SourceRef("lexbg", doc_id), waivers_path=waivers_path)
        written = True
        if not commit:
            return Written(slug, commit_type, record_id, None)
        files += [_rel(root, waivers_path)] if lowered else []
        _git(root, "add", "--", *files)
        date = latest_amendment_date(fresh_hist) or meta.get("fecha_publicacion")
        message = (f"[{commit_type}] {meta['titulo']}\n\n"
                   f"Source-Id: lexbg-{doc_id}\n"
                   f"Source-Date: {date or 'unknown'}\n"
                   f"Norm-Id: {doc_id}\n"
                   f"Record-Id: {record_id}\n")
        env = os.environ.copy()
        author_date = _format_author_date(date)
        if author_date:
            env["GIT_AUTHOR_DATE"] = author_date  # the legislative date; the committer date stays real (D-048)
        _git(root, "commit", "-m", message, "--", *files, env=env)
    except BaseException:
        if commit:
            subprocess.run(["git", "reset", "-q", "--", *files], cwd=root, capture_output=True)
            if written:
                _git(root, "checkout", "HEAD", "--", _rel(root, path))  # the committed act, as the check above found it
        if lowered:
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
