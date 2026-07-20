"""R2 act payload builders + exporters.

`acts/{law_id}.json` and `versions/{law_id}/{date}.json` share one
payload shape (spec §R2):

    {"meta": {...}, "preamble_raw": "...", "body_markdown": "...",
     "articles": {"<art>": {"text": ..., "text_hash": ...,
                            "paragraphs": {"<n>": "<text>", ...}}}}

- `meta` mirrors the REST API's get_law composition (api/routes/laws.py)
  plus `rango`/`estado` from frontmatter (spec lists them explicitly).
- `articles` is baked with index.provisions.parse — the SAME extraction
  logic that populates the `provisions` table (imported, not
  reimplemented). Keys are what GET /laws/{slug}/articles/{art} accepts
  (single articles, e.g. "5", "14а"); paragraphs are plain strings and
  `text_hash` is article-level only (cf-worker interface agreement
  2026-07-21 — the Worker recomputes alinea hashes with the same
  sha256[:16] recipe when needed).
- `preamble_raw` (cf-worker interface agreement 2026-07-21): the raw
  file prefix such that `preamble_raw + body_markdown` == the .md file
  byte-exactly — lets the Worker reproduce FastAPI's whole-file
  git-diff hunks on /diff.

JSON is minified UTF-8 with a trailing-free, insertion-ordered key
layout — deterministic for identical inputs.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from index.provisions import parse as parse_provisions
from mcp_server.queries import (
    iso_date,
    read_law_markdown,
    split_frontmatter,
    version_with_warnings,
)


def _json_default(v: Any):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    raise TypeError(f"not JSON serializable: {type(v)!r}")


def dump_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"),
                   default=_json_default),
        encoding="utf-8", newline="\n")


def articles_map(body_markdown: str, law_id: str) -> dict[str, dict]:
    """Bake the articles map from the same parser that fills
    `provisions` (article-as-whole rows carry text_hash; alinea rows
    become plain paragraph strings).

    FIRST-wins on duplicates — exact FastAPI parity: the corpus has 457
    (law, article) pairs where quoted amendment text (typically inside
    ПЗР) re-anchors "Чл. N." and yields a second provisions block for
    the same article id. `article_lookup` serves rows[0] (first inserted
    row) for each (article, paragraph) key, so the article text/hash
    keep the FIRST block and each paragraph key keeps its FIRST
    occurrence — while a paragraph that exists only in a later block is
    still included (FastAPI would return it too)."""
    arts: dict[str, dict] = {}
    for prov in parse_provisions(body_markdown, law_id=law_id):
        if prov.paragraph is None:
            if prov.article not in arts:
                arts[prov.article] = {
                    "text": prov.text,
                    "text_hash": prov.text_hash,
                    "paragraphs": {},
                }
        else:
            entry = arts.setdefault(prov.article, {
                "text": "", "text_hash": "", "paragraphs": {},
            })
            entry["paragraphs"].setdefault(prov.paragraph, prov.text)
    return arts


def build_act_payload(law_id: str, doc_id: int, category: str,
                      raw_markdown: str, commit_hash: str,
                      warnings: list[dict]) -> dict:
    fm, body = split_frontmatter(raw_markdown)
    preamble = raw_markdown[: len(raw_markdown) - len(body)] if body \
        else raw_markdown
    meta = {
        "law_id": law_id,
        "identificador": str(doc_id),
        "titulo": fm.get("titulo") or "",
        "category": category,
        "rango": fm.get("rango"),
        "estado": fm.get("estado"),
        "fecha_publicacion": iso_date(fm.get("fecha_publicacion")),
        "ultima_actualizacion": iso_date(fm.get("ultima_actualizacion")),
        "dv_issue": fm.get("dv_issue"),
        "dv_year": fm.get("dv_year"),
        "effective_date": iso_date(fm.get("effective_date")),
        "eli": fm.get("eli"),
        "amendment_history": fm.get("amendment_history") or [],
        "commit_hash": commit_hash,
        "warnings": warnings,
    }
    return {
        "meta": meta,
        "preamble_raw": preamble,
        "body_markdown": body,
        "articles": articles_map(body, law_id),
    }


def export_acts(conn: sqlite3.Connection, corpus_root: Path,
                r2_dir: Path) -> int:
    """Write acts/{law_id}.json for every law (current consolidated
    text, working-tree fast path). Streams act-by-act."""
    acts_dir = Path(r2_dir) / "acts"
    n = 0
    rows = conn.execute(
        "SELECT law_id, doc_id, category, current_commit FROM laws "
        "ORDER BY law_id").fetchall()
    for row in rows:
        law_id = row["law_id"]
        commit, warnings = version_with_warnings(conn, law_id, None)
        raw = read_law_markdown(Path(corpus_root), law_id,
                                row["category"], commit,
                                row["current_commit"])
        payload = build_act_payload(law_id, row["doc_id"],
                                    row["category"], raw, commit, warnings)
        dump_json(payload, acts_dir / f"{law_id}.json")
        n += 1
    return n


def export_versions(conn: sqlite3.Connection, corpus_root: Path,
                    r2_dir: Path) -> int:
    """Write versions/{law_id}/{valid_from}.json for EVERY law_versions
    row (spec §R2). Historical rows resolve body via `git show
    {commit}:{path}` inside read_law_markdown; the latest row takes the
    working-tree fast path. {date} == the row's valid_from exactly as
    stored in D1 (cf-worker interface agreement 2026-07-21)."""
    versions_dir = Path(r2_dir) / "versions"
    n = 0
    rows = conn.execute(
        """SELECT v.law_id, v.valid_from, l.doc_id, l.category,
                  l.current_commit
             FROM law_versions v JOIN laws l ON l.law_id = v.law_id
            ORDER BY v.law_id, v.valid_from""").fetchall()
    for row in rows:
        law_id = row["law_id"]
        commit, warnings = version_with_warnings(conn, law_id,
                                                 row["valid_from"])
        raw = read_law_markdown(Path(corpus_root), law_id,
                                row["category"], commit,
                                row["current_commit"])
        payload = build_act_payload(law_id, row["doc_id"],
                                    row["category"], raw, commit, warnings)
        dump_json(payload,
                  versions_dir / law_id / f"{row['valid_from']}.json")
        n += 1
    return n
