"""Export self-check (spec §Exporter `--verify`):

1. recount rows vs catalog.db (laws / law_versions / amendments vs
   manifest counts + on-disk acts/versions file counts),
2. FTS row count == laws row count,
3. re-hash every manifest `files` entry + the acts/versions class
   aggregates,
4. sample N=25 acts (deterministic: sorted law_ids, even stride) and
   assert the R2 JSON articles match live `provisions` lookups (text +
   text_hash for article-as-whole rows, text for alinea rows).

Raises VerifyError with a full failure list; returns a report dict.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from export_cf.manifest import _sha256_file, class_aggregate
from export_cf.scan import max_statement_bytes
from export_cf.sqlgen import STATEMENT_MAX_BYTES

DEFAULT_SAMPLE_N = 25


class VerifyError(AssertionError):
    def __init__(self, failures: list[str]):
        super().__init__("export verification failed:\n- "
                         + "\n- ".join(failures))
        self.failures = failures


def _sample(ids: list[str], n: int) -> list[str]:
    ids = sorted(ids)
    if len(ids) <= n:
        return ids
    stride = len(ids) / n
    return [ids[int(i * stride)] for i in range(n)]


def _check_act_articles(conn: sqlite3.Connection, out_dir: Path,
                        law_id: str, failures: list[str]) -> None:
    path = out_dir / "r2" / "acts" / f"{law_id}.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        failures.append(f"acts/{law_id}.json unreadable: {e}")
        return
    arts = doc.get("articles", {})
    # FIRST-wins (rowid order), mirroring article_lookup's rows[0]
    # semantics and export_cf.acts.articles_map — see its docstring.
    rows = conn.execute(
        "SELECT article, paragraph, text, text_hash FROM provisions "
        "WHERE law_id = ? ORDER BY rowid", (law_id,)).fetchall()
    whole: dict = {}
    alineas: dict = {}
    for r in rows:
        if r["paragraph"] is None:
            whole.setdefault(r["article"], r)
        else:
            alineas.setdefault((r["article"], r["paragraph"]), r)
    if set(arts) != set(whole):
        failures.append(
            f"{law_id}: article keys diverge (json={len(arts)}, "
            f"provisions={len(whole)})")
        return
    for art_id, art in arts.items():
        row = whole[art_id]
        if art["text"] != row["text"] or art["text_hash"] != row["text_hash"]:
            failures.append(f"{law_id} чл.{art_id}: text/text_hash mismatch")
        expected_paras = {p: r["text"] for (a, p), r in alineas.items()
                          if a == art_id}
        if art["paragraphs"] != expected_paras:
            failures.append(f"{law_id} чл.{art_id}: paragraphs diverge")


def verify_export(db_path: str, out_dir: Path,
                  sample_n: int = DEFAULT_SAMPLE_N) -> dict:
    out_dir = Path(out_dir)
    failures: list[str] = []
    manifest = json.loads((out_dir / "manifest.json")
                          .read_text(encoding="utf-8"))
    counts = manifest["counts"]

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        db_counts = {
            t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in ("laws", "law_versions", "amendments", "laws_fts")}

        # 1. row counts vs catalog.db + on-disk object counts
        for t, n in db_counts.items():
            if counts.get(t) != n:
                failures.append(f"count mismatch {t}: manifest="
                                f"{counts.get(t)} db={n}")
        acts_on_disk = len(list((out_dir / "r2" / "acts").glob("*.json")))
        versions_on_disk = len(list(
            (out_dir / "r2" / "versions").rglob("*.json")))
        if acts_on_disk != db_counts["laws"]:
            failures.append(f"acts/ objects={acts_on_disk} != laws rows="
                            f"{db_counts['laws']}")
        if versions_on_disk != db_counts["law_versions"]:
            failures.append(f"versions/ objects={versions_on_disk} != "
                            f"law_versions rows={db_counts['law_versions']}")

        # 2. FTS row count == laws row count
        if db_counts["laws_fts"] != db_counts["laws"]:
            failures.append(f"laws_fts rows={db_counts['laws_fts']} != "
                            f"laws rows={db_counts['laws']}")

        # 3. artifact hashes
        for rel, sha in manifest["files"].items():
            f = out_dir / rel
            if not f.is_file():
                failures.append(f"missing artifact: {rel}")
            elif _sha256_file(f) != sha:
                failures.append(f"sha256 mismatch: {rel}")
        for cls, subdir in (("acts", "r2/acts"), ("versions", "r2/versions")):
            if class_aggregate(out_dir, subdir) != manifest["classes"][cls]:
                failures.append(f"class aggregate mismatch: {cls}")

        # 4. v1.3 statement-budget self-check: rescan every emitted SQL
        # file quote-aware and assert no statement exceeds the D1 cap.
        max_seen = 0
        for f in sorted(out_dir.glob("d1-*.sql")):
            max_seen = max(max_seen, max_statement_bytes(str(f)))
        if max_seen > STATEMENT_MAX_BYTES:
            failures.append(
                f"statement budget exceeded: longest emitted statement "
                f"{max_seen} bytes > {STATEMENT_MAX_BYTES}")

        # 5. sampled acts vs provisions
        law_ids = [r[0] for r in conn.execute("SELECT law_id FROM laws")]
        sampled = _sample(law_ids, sample_n)
        for law_id in sampled:
            _check_act_articles(conn, out_dir, law_id, failures)
    finally:
        conn.close()

    if failures:
        raise VerifyError(failures)
    return {
        "ok": True,
        "laws_rows": db_counts["laws"],
        "fts_rows": db_counts["laws_fts"],
        "law_versions_rows": db_counts["law_versions"],
        "sampled_acts": len(sampled),
    }
