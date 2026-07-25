"""Export self-check (spec §Exporter `--verify`):

1. recount rows vs catalog.db (laws / law_versions / amendments /
   laws_fts / articles_fts vs manifest counts + on-disk acts/versions
   file counts),
2. FTS title-row count == laws row count; every articles_fts body
   respects the SEG_MAX_BYTES contract (and D1's 2MB value cap),
3. re-hash every manifest `files` entry + the acts/versions class
   aggregates,
4. rescan every emitted SQL file quote-aware: statement budget +
   per-statement idempotency guards in BOTH fts series; then reimport
   the fts series into a scratch SQLite, check row-count parity and
   spot-hash sampled segment bodies against the live catalog,
5. sample N=25 acts (deterministic: sorted law_ids, even stride) and
   assert the R2 JSON articles match live `provisions` lookups (text +
   text_hash for article-as-whole rows, text for alinea rows).

Raises VerifyError with a full failure list; returns a report dict.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from index.segments import SEG_MAX_BYTES

from export_cf.d1 import D1_VALUE_MAX_BYTES
from export_cf.manifest import _sha256_file, class_aggregate
from export_cf.scan import iter_statements, max_statement_bytes
from export_cf.sqlgen import STATEMENT_MAX_BYTES

DEFAULT_SAMPLE_N = 25


class VerifyError(AssertionError):
    def __init__(self, failures: list[str]):
        super().__init__("export verification failed:\n- "
                         + "\n- ".join(failures))
        self.failures = failures


def _sample(ids: list, n: int) -> list:
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


def _check_fts_guards(out_dir: Path, failures: list[str]) -> None:
    """Every statement in BOTH fts series must carry a retry guard
    (WHERE NOT EXISTS for INSERTs — keyed on law_id, plus seg_no for
    articles_fts — byte-offset length() guard for append UPDATEs)."""
    for f in sorted(out_dir.glob("d1-fts-laws-*.sql")):
        for stmt in iter_statements(str(f)):
            if not (stmt.startswith(b"INSERT INTO laws_fts")
                    and b"WHERE NOT EXISTS (SELECT 1 FROM laws_fts" in stmt):
                failures.append(
                    f"unguarded fts statement in {f.name}: {stmt[:100]!r}")
                return
    for f in sorted(out_dir.glob("d1-fts-articles-*.sql")):
        for stmt in iter_statements(str(f)):
            if stmt.startswith(b"INSERT INTO articles_fts"):
                ok = (b"WHERE NOT EXISTS (SELECT 1 FROM articles_fts"
                      in stmt and b"AND seg_no = " in stmt)
            elif stmt.startswith(b"UPDATE articles_fts"):
                ok = (b"AND length(CAST(body AS BLOB)) = " in stmt
                      and b"AND seg_no = " in stmt)
            else:
                ok = False
            if not ok:
                failures.append(
                    f"unguarded fts statement in {f.name}: {stmt[:100]!r}")
                return


# All segment rows above this byte floor are unconditionally hashed by
# the reimport check — see the sliced-rows comment inside. Kept below
# d1.py's effective per-statement body budget so every sliced row
# qualifies.
SLICED_HASH_FLOOR_BYTES = 80_000


def _check_fts_reimport(conn: sqlite3.Connection, out_dir: Path,
                        sample_n: int, failures: list[str]) -> int:
    """Reimport d1-schema.sql + both fts series into a scratch SQLite
    file (RAM-safe at live scale, ~385MB of normalized text) and check
    (a) row-count parity per FTS table and (b) sampled segment rows —
    kind/label equality + sha256(body) — against the live catalog. This
    is the end-to-end proof that the guarded INSERT+UPDATE slicing
    reassembles bodies byte-exactly. Returns the sampled-segment count."""
    with tempfile.TemporaryDirectory(prefix="cf-verify-") as tmp:
        scratch = sqlite3.connect(str(Path(tmp) / "reimport.db"))
        try:
            # Throwaway db: durability off. Without these the live-scale
            # reimport (385MB of fts SQL) measured 3.5 HOURS wall clock
            # (fsync per autocommit statement); with them it is minutes.
            scratch.execute("PRAGMA journal_mode = OFF")
            scratch.execute("PRAGMA synchronous = OFF")
            scratch.executescript(
                (out_dir / "d1-schema.sql").read_text(encoding="utf-8"))
            for series in ("d1-fts-laws-*.sql", "d1-fts-articles-*.sql"):
                for chunk in sorted(out_dir.glob(series)):
                    scratch.executescript(
                        chunk.read_text(encoding="utf-8"))
            for table in ("laws_fts", "articles_fts"):
                got = scratch.execute(
                    f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                want = conn.execute(
                    f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                if got != want:
                    failures.append(f"reimported {table} rows={got} != "
                                    f"catalog rows={want}")
            keys = [(r[0], r[1]) for r in conn.execute(
                "SELECT law_id, seg_no FROM articles_fts")]
            # Review 2026-07-24 (FR-032): sliced rows (INSERT prefix +
            # append UPDATEs) are the ONLY rows that can arrive torn
            # while row counts stay intact, and a uniform stride
            # sample covers ~0.06% of the 182K-row corpus. Hash ALL
            # rows above the slice floor (safely below the ~89.7KB
            # effective statement budget, so a superset of sliced
            # rows — ~456 live, cheap), plus the uniform sample.
            sliced = [(r[0], r[1]) for r in conn.execute(
                "SELECT law_id, seg_no FROM articles_fts"
                " WHERE length(CAST(body AS BLOB)) > ?",
                (SLICED_HASH_FLOOR_BYTES,))]
            sampled = list(dict.fromkeys(
                sliced + _sample(keys, sample_n)))
            for law_id, seg_no in sampled:
                q = ("SELECT kind, label, body FROM articles_fts "
                     "WHERE law_id = ? AND seg_no = ?")
                src = conn.execute(q, (law_id, seg_no)).fetchone()
                got = scratch.execute(q, (law_id, seg_no)).fetchone()
                if got is None:
                    failures.append(
                        f"segment ({law_id}, {seg_no}) missing on reimport")
                    continue
                if (got[0], got[1]) != (src[0], src[1]):
                    failures.append(
                        f"segment ({law_id}, {seg_no}) kind/label diverge")
                src_hash = hashlib.sha256(
                    src[2].encode("utf-8")).hexdigest()
                got_hash = hashlib.sha256(
                    got[2].encode("utf-8")).hexdigest()
                if src_hash != got_hash:
                    failures.append(
                        f"segment ({law_id}, {seg_no}) body hash mismatch")
            return len(sampled)
        finally:
            scratch.close()


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
            for t in ("laws", "law_versions", "amendments", "laws_fts",
                      "articles_fts")}

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

        # 2. FTS title-row count == laws row count
        if db_counts["laws_fts"] != db_counts["laws"]:
            failures.append(f"laws_fts rows={db_counts['laws_fts']} != "
                            f"laws rows={db_counts['laws']}")

        # 2b. v2.0 body-size contract (replaces the retired v1.2
        # truncation check): no articles_fts body over SEG_MAX_BYTES,
        # therefore nothing near D1's 2MB value cap; the manifest must
        # agree with the catalog.
        max_body = conn.execute(
            "SELECT COALESCE(MAX(length(CAST(body AS BLOB))), 0) "
            "FROM articles_fts").fetchone()[0]
        if max_body > SEG_MAX_BYTES:
            failures.append(
                f"articles_fts body {max_body} bytes > SEG_MAX_BYTES="
                f"{SEG_MAX_BYTES} (mis-built catalog)")
        if max_body >= D1_VALUE_MAX_BYTES:
            failures.append(
                f"articles_fts body {max_body} bytes >= D1 value cap "
                f"{D1_VALUE_MAX_BYTES}")
        if manifest.get("max_fts_body_bytes") != max_body:
            failures.append(
                f"max_fts_body_bytes: manifest="
                f"{manifest.get('max_fts_body_bytes')} db={max_body}")

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

        # 4b. idempotency guards in both fts series
        _check_fts_guards(out_dir, failures)

        # 4c. fts reimport: row-count parity + segment spot-hash
        sampled_segments = _check_fts_reimport(conn, out_dir, sample_n,
                                               failures)

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
        "articles_fts_rows": db_counts["articles_fts"],
        "law_versions_rows": db_counts["law_versions"],
        "sampled_acts": len(sampled),
        "sampled_segments": sampled_segments,
    }
