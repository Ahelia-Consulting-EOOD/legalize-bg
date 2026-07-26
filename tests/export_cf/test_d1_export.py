"""D1 dump (spec v2.0): d1-schema.sql + d1-meta-NNNN.sql (plain
multi-row INSERTs — NOT idempotent, empty-tables-only) + TWO fully
idempotent guarded FTS series: d1-fts-laws-NNNN.sql (title-only rows,
keyed on law_id) and d1-fts-articles-NNNN.sql (one row per body
segment, keyed on law_id + seg_no, oversized bodies sliced into
INSERT + guarded UPDATE appends). All chunks ≤12MB, broken only at
statement boundaries, every statement ≤90,000 bytes; no articles_fts
body may exceed the 400,000-byte SEG_MAX_BYTES contract."""

import sqlite3

import pytest

from export_cf.d1 import export_d1

LAWS_Q = "SELECT law_id, title, category FROM laws_fts ORDER BY law_id"
ARTS_Q = ("SELECT law_id, seg_no, kind, label, body, category "
          "FROM articles_fts ORDER BY law_id, CAST(seg_no AS INTEGER)")


def _reimport(out, fresh):
    fresh.executescript((out / "d1-schema.sql").read_text(encoding="utf-8"))
    for series in ("d1-meta-*.sql", "d1-fts-laws-*.sql",
                   "d1-fts-articles-*.sql"):
        for chunk in sorted(out.glob(series)):
            fresh.executescript(chunk.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def d1_out(export_corpus, tmp_path_factory):
    _, db = export_corpus
    out = tmp_path_factory.mktemp("d1-out")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    result = export_d1(conn, out)
    conn.close()
    return db, out, result


@pytest.fixture(scope="module")
def reimported(d1_out):
    db, out, _ = d1_out
    fresh = sqlite3.connect(":memory:")
    _reimport(out, fresh)
    yield db, fresh
    fresh.close()


def test_series_files_exist(d1_out):
    _, out, result = d1_out
    assert (out / "d1-schema.sql").is_file()
    assert sorted(out.glob("d1-meta-*.sql"))[0].name == "d1-meta-0001.sql"
    assert sorted(out.glob("d1-fts-laws-*.sql"))[0].name \
        == "d1-fts-laws-0001.sql"
    assert sorted(out.glob("d1-fts-articles-*.sql"))[0].name \
        == "d1-fts-articles-0001.sql"
    assert not list(out.glob("d1-data-*.sql"))  # pre-v1.3.2 series gone
    assert not list(out.glob("d1-fts-0*.sql"))  # v1.x single-series gone
    assert result["counts"]["laws"] > 0
    assert result["counts"]["laws_fts"] == result["counts"]["laws"]
    assert result["counts"]["articles_fts"] > result["counts"]["laws"]


def test_chunk_default_is_12mb():
    """v1.3.1: 50MB chunks keep D1's import long-poll open too long
    (transient 'fetch failed'); 12MB imports reliably."""
    from export_cf.d1 import CHUNK_MAX_BYTES
    assert CHUNK_MAX_BYTES == 12_000_000


def test_tables_copied_1_to_1(reimported):
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for table, order in (("laws", "law_id"), ("law_versions", "id"),
                         ("amendments", "id"), ("schema_version", "version")):
        cols = [r[1] for r in src.execute(f"PRAGMA table_info({table})")]
        q = f"SELECT {', '.join(cols)} FROM {table} ORDER BY {order}"
        assert fresh.execute(q).fetchall() == src.execute(q).fetchall(), table
    src.close()


def test_no_provisions_in_d1(reimported):
    _, fresh = reimported
    names = {r[0] for r in fresh.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "provisions" not in names


def test_fts_rebuilt_with_same_source_text(reimported):
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    for q in (LAWS_Q, ARTS_Q):
        assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    src.close()


def test_fts_indexes_are_queryable(reimported):
    _, fresh = reimported
    hits = fresh.execute(
        "SELECT law_id FROM laws_fts WHERE laws_fts MATCH 'време'"
    ).fetchall()
    assert ("zakon-vremeto",) in hits
    seg_hits = fresh.execute(
        "SELECT DISTINCT law_id FROM articles_fts "
        "WHERE articles_fts MATCH 'редакция'").fetchall()
    assert ("zakon-vremeto",) in seg_hits


def test_segment_rows_cover_all_kinds(reimported):
    """The fixture's multi-anchor act must land one articles_fts row per
    segment kind — proof the exporter carries kind/label through."""
    _, fresh = reimported
    kinds = {r[0] for r in fresh.execute(
        "SELECT kind FROM articles_fts WHERE law_id = 'zakon-segmenti'")}
    assert {"article", "para", "annex"} <= kinds
    labels = {r[0] for r in fresh.execute(
        "SELECT label FROM articles_fts WHERE law_id = 'zakon-segmenti'")}
    assert "чл. 1" in labels and "§ 1" in labels


def test_laws_dumped_in_rowid_order(reimported):
    """Parity: FastAPI's AMBIGUOUS_NAME candidates and no-ORDER-BY scans
    follow insertion (rowid) order — the reimported D1 must preserve it."""
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    src_order = [r[0] for r in src.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    # insertion order (laws/ before ordinances/), NOT sorted law_id order
    assert src_order != sorted(src_order)
    assert src_order[0].startswith("zakon-")
    fresh_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    assert fresh_order == src_order
    fts_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws_fts ORDER BY rowid")]
    assert fts_order == src_order
    # articles_fts rowid order == source rowid order (per-act seg_no runs)
    seg_order = [tuple(r) for r in fresh.execute(
        "SELECT law_id, seg_no FROM articles_fts ORDER BY rowid")]
    src_seg_order = [tuple(r) for r in src.execute(
        "SELECT law_id, seg_no FROM articles_fts ORDER BY rowid")]
    assert seg_order == src_seg_order
    src.close()


# ──────────── v2.0 segment-size guard (replaces the v1.2 cap) ────────────


def test_seg_max_bytes_guard_rejects_oversized_bodies(export_corpus,
                                                      tmp_path):
    """Spec v2.0: the exporter TRUSTS the index's SEG_MAX_BYTES chunking
    and never truncates — but it must refuse to emit if the invariant is
    broken upstream (a >400KB body would mean a mis-built catalog)."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    with pytest.raises(ValueError, match="seg_max_bytes|SEG_MAX_BYTES"):
        export_d1(src, tmp_path, seg_max_bytes=40)
    src.close()


def test_max_fts_body_bytes_reported_within_contract(d1_out):
    from index.segments import SEG_MAX_BYTES
    _, _, result = d1_out
    assert 0 < result["max_fts_body_bytes"] <= SEG_MAX_BYTES
    assert result["max_fts_body_bytes"] < 2_000_000  # D1 value cap


# ─────────────── v1.3 statement budget + scanner ───────────────


def test_statement_scanner_quote_aware(tmp_path):
    """The chunk self-check must split statements SQL-aware: ';' and
    quote characters INSIDE string literals (escaped as '') must not be
    seen as statement terminators."""
    from export_cf.scan import max_statement_bytes
    sql = ("INSERT INTO t (a) VALUES ('x;y');\n"
           "INSERT INTO t (a) VALUES ('it''s; tricky');\n"
           "UPDATE t SET a = a || ';;''' WHERE b = 'q';\n")
    p = tmp_path / "scan.sql"
    p.write_text(sql, encoding="utf-8")
    expected = max(len(line.encode("utf-8"))
                   for line in sql.split("\n") if line)
    assert max_statement_bytes(str(p)) == expected


def test_scanner_iter_statements_reconstructs(tmp_path):
    from export_cf.scan import iter_statements
    sql = ("INSERT INTO t (a) VALUES ('multi\nline; ''x''');\n"
           "UPDATE t SET a = 'y' WHERE b = 1;\n")
    p = tmp_path / "scan.sql"
    p.write_text(sql, encoding="utf-8")
    stmts = list(iter_statements(str(p)))
    assert len(stmts) == 2
    assert stmts[0] == \
        "INSERT INTO t (a) VALUES ('multi\nline; ''x''');".encode()
    assert stmts[1] == b"UPDATE t SET a = 'y' WHERE b = 1;"


def test_oversized_segment_sliced_into_insert_plus_updates(
        export_corpus, tmp_path):
    """Slicing under idempotency guards: INSERT(first slice) + guarded
    UPDATE appends keyed on (law_id, seg_no); reassembled body equals
    the source EXACTLY, every statement within budget."""
    from export_cf.scan import max_statement_bytes
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    result = export_d1(src, tmp_path, stmt_max_bytes=1000)
    assert result["max_statement_bytes"] <= 1000
    assert result["fts_guards"]["updates"] > 0
    chunks = sorted(tmp_path.glob("d1-*.sql"))
    for c in chunks:
        if c.name != "d1-schema.sql":
            assert max_statement_bytes(str(c)) <= 1000, c.name
    joined = "".join(c.read_text("utf-8")
                     for c in sorted(tmp_path.glob("d1-fts-articles-*.sql")))
    assert "UPDATE articles_fts SET body = body || '" in joined
    fresh = sqlite3.connect(":memory:")
    _reimport(tmp_path, fresh)
    for q in (LAWS_Q, ARTS_Q):
        assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    hits = fresh.execute("SELECT law_id FROM laws_fts WHERE laws_fts "
                         "MATCH 'време'").fetchall()
    assert ("zakon-vremeto",) in hits
    fresh.close()
    src.close()


def test_default_budget_slices_the_big_annex(d1_out):
    """The fixture's >90KB annex segment must slice at PRODUCTION
    settings — this is the live-corpus path (hundreds of segments exceed
    the statement budget), not just a small-budget test artifact."""
    from export_cf.scan import max_statement_bytes
    _, out, result = d1_out
    assert result["fts_guards"]["updates"] > 0
    for f in sorted(out.glob("d1-*.sql")):
        assert max_statement_bytes(str(f)) <= 90_000, f.name


def test_chunks_break_only_at_statement_boundaries(export_corpus, tmp_path):
    """String literals contain raw newlines (legal text), so chunk files
    are only splittable at statement ends: every chunk must end with a
    complete ';\\n'-terminated statement and be independently
    executescript-able in sequence."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    export_d1(src, tmp_path, chunk_max_bytes=2_000, stmt_max_bytes=1_000)
    chunks = sorted(tmp_path.glob("d1-meta-*.sql")) \
        + sorted(tmp_path.glob("d1-fts-laws-*.sql")) \
        + sorted(tmp_path.glob("d1-fts-articles-*.sql"))
    assert len(chunks) > 2  # tiny budget → many files
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((tmp_path / "d1-schema.sql").read_text("utf-8"))
    for c in chunks:
        text = c.read_text("utf-8")
        assert text.endswith(";\n"), c.name
        fresh.executescript(text)  # would raise if a stmt were split
    q = "SELECT law_id, body FROM articles_fts ORDER BY rowid"
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    fresh.close()
    src.close()


# ─────────────── idempotent import guards (both fts series) ───────────────


def test_every_fts_statement_carries_a_guard(d1_out):
    """Self-check contract: every statement in BOTH fts series is
    idempotent — laws_fts INSERTs via WHERE NOT EXISTS(law_id),
    articles_fts INSERTs via WHERE NOT EXISTS(law_id AND seg_no),
    appends via the length(CAST(body AS BLOB)) byte-offset guard."""
    from export_cf.scan import iter_statements
    _, out, result = d1_out
    inserts = updates = 0
    for f in sorted(out.glob("d1-fts-laws-*.sql")):
        for stmt in iter_statements(str(f)):
            assert stmt.startswith(b"INSERT INTO laws_fts"), stmt[:80]
            assert (b"WHERE NOT EXISTS (SELECT 1 FROM laws_fts "
                    b"WHERE law_id = ") in stmt
            inserts += 1
    for f in sorted(out.glob("d1-fts-articles-*.sql")):
        for stmt in iter_statements(str(f)):
            if stmt.startswith(b"INSERT INTO articles_fts"):
                assert (b"WHERE NOT EXISTS (SELECT 1 FROM articles_fts "
                        b"WHERE law_id = ") in stmt
                assert b"AND seg_no = " in stmt
                inserts += 1
            elif stmt.startswith(b"UPDATE articles_fts"):
                assert b"AND length(CAST(body AS BLOB)) = " in stmt
                assert b"AND seg_no = " in stmt
                updates += 1
            else:
                raise AssertionError(f"unexpected stmt: {stmt[:80]!r}")
    assert inserts == (result["counts"]["laws_fts"]
                       + result["counts"]["articles_fts"])
    assert inserts == result["fts_guards"]["inserts"]
    assert updates == result["fts_guards"]["updates"]


def test_fts_series_reimport_is_idempotent(export_corpus, tmp_path):
    """The double-application incident: a 'fetch failed' import may have
    committed server-side. Importing BOTH fts series a second (and
    third) time must be a byte-exact no-op — including sliced rows,
    where an unguarded retry would double-append body slices."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    export_d1(src, tmp_path, stmt_max_bytes=1000)  # forces slicing
    fresh = sqlite3.connect(":memory:")
    _reimport(tmp_path, fresh)
    first = {q: fresh.execute(q).fetchall() for q in (LAWS_Q, ARTS_Q)}
    for _ in range(2):  # blind retries of both fts series
        for series in ("d1-fts-laws-*.sql", "d1-fts-articles-*.sql"):
            for chunk in sorted(tmp_path.glob(series)):
                fresh.executescript(chunk.read_text(encoding="utf-8"))
    for q in (LAWS_Q, ARTS_Q):
        assert fresh.execute(q).fetchall() == first[q]
        assert first[q] == src.execute(q).fetchall()
    fresh.close()
    src.close()


def test_partial_append_retry_completes(export_corpus, tmp_path):
    """Mid-series crash recovery: if only a PREFIX of the fts statements
    was applied (e.g. INSERT + first append committed, rest lost), re-
    running the whole series must complete the row without corruption."""
    from export_cf.scan import iter_statements
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    export_d1(src, tmp_path, stmt_max_bytes=1000)
    stmts = []
    for series in ("d1-fts-laws-*.sql", "d1-fts-articles-*.sql"):
        for f in sorted(tmp_path.glob(series)):
            stmts.extend(s.decode("utf-8") for s in iter_statements(str(f)))
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((tmp_path / "d1-schema.sql").read_text("utf-8"))
    cut = len(stmts) // 2
    for s in stmts[:cut]:          # partial first attempt
        fresh.executescript(s)
    for s in stmts:                # full blind retry
        fresh.executescript(s)
    q = "SELECT law_id, seg_no, body FROM articles_fts ORDER BY rowid"
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    fresh.close()
    src.close()
