"""D1 dump (spec v1.3.2): d1-schema.sql + d1-meta-NNNN.sql (plain
multi-row INSERTs — NOT idempotent, empty-tables-only) + d1-fts-NNNN.sql
(fully idempotent guarded statements). All chunks ≤12MB, broken only at
statement boundaries, every statement ≤90,000 bytes."""

import sqlite3

import pytest

from export_cf.d1 import export_d1


def _reimport(out, fresh):
    fresh.executescript((out / "d1-schema.sql").read_text(encoding="utf-8"))
    for series in ("d1-meta-*.sql", "d1-fts-*.sql"):
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
    assert sorted(out.glob("d1-fts-*.sql"))[0].name == "d1-fts-0001.sql"
    assert not list(out.glob("d1-data-*.sql"))  # old series gone
    assert result["counts"]["laws"] > 0
    assert result["counts"]["laws_fts"] == result["counts"]["laws"]


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
    q = ("SELECT law_id, title, body, category FROM laws_fts "
         "ORDER BY law_id")
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    src.close()


def test_fts_index_is_queryable(reimported):
    _, fresh = reimported
    hits = fresh.execute(
        "SELECT law_id FROM laws_fts WHERE laws_fts MATCH 'време'"
    ).fetchall()
    assert ("zakon-vremeto",) in hits


def test_laws_dumped_in_rowid_order(reimported):
    """Parity: FastAPI's AMBIGUOUS_NAME candidates and no-ORDER-BY scans
    follow insertion (rowid) order — the reimported D1 must preserve it."""
    db, fresh = reimported
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    src_order = [r[0] for r in src.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    src.close()
    # insertion order (laws/ before ordinances/), NOT sorted law_id order
    assert src_order != sorted(src_order)
    assert src_order[0].startswith("zakon-")
    fresh_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws ORDER BY rowid")]
    assert fresh_order == src_order
    fts_order = [r[0] for r in fresh.execute(
        "SELECT law_id FROM laws_fts ORDER BY rowid")]
    assert fts_order == src_order


# ────────────────────────── v1.2 body cap ──────────────────────────


def test_fts_body_cap_truncates_oversized_bodies(export_corpus, tmp_path):
    """Spec v1.2: indexed FTS body = bg_normalize(body) truncated to a
    UTF-8 byte cap at a character boundary; truncated law_ids reported."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    result = export_d1(src, tmp_path, fts_body_max_bytes=40)
    src.close()
    assert set(result["fts_truncated"])  # fixture bodies exceed 40 bytes
    fresh = sqlite3.connect(":memory:")
    _reimport(tmp_path, fresh)
    for law_id, body in fresh.execute("SELECT law_id, body FROM laws_fts"):
        assert len(body.encode("utf-8")) <= 40, law_id
    fresh.close()


def test_fts_body_cap_cyrillic_char_boundary():
    """A cap landing mid-character must back off to the previous char
    boundary, never emit a broken UTF-8 tail (Cyrillic = 2 bytes/char)."""
    from export_cf.d1 import _cap_fts_body

    body = "я" * 60  # 120 UTF-8 bytes
    capped, cut = _cap_fts_body(body, 101)  # 101 splits the 51st 'я'
    assert cut is True
    assert capped == "я" * 50
    assert len(capped.encode("utf-8")) == 100
    uncut, not_cut = _cap_fts_body(body, 120)
    assert not_cut is False and uncut == body


def test_fts_body_cap_default_no_truncation_on_fixture(d1_out):
    _, _, result = d1_out
    assert result["fts_truncated"] == []


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


def test_oversized_fts_body_sliced_into_insert_plus_updates(
        export_corpus, tmp_path):
    """v1.3 slicing under v1.3.2 guards: INSERT(first slice) + guarded
    UPDATE appends; reassembled body equals the capped source EXACTLY,
    every statement within budget."""
    from export_cf.scan import max_statement_bytes
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    result = export_d1(src, tmp_path, stmt_max_bytes=1000)
    assert result["max_statement_bytes"] <= 1000
    assert result["fts_guards"]["updates"] > 0
    chunks = sorted(tmp_path.glob("d1-meta-*.sql")) \
        + sorted(tmp_path.glob("d1-fts-*.sql"))
    for c in chunks:
        assert max_statement_bytes(str(c)) <= 1000, c.name
    joined = "".join(c.read_text("utf-8")
                     for c in sorted(tmp_path.glob("d1-fts-*.sql")))
    assert "UPDATE laws_fts SET body = body || '" in joined
    fresh = sqlite3.connect(":memory:")
    _reimport(tmp_path, fresh)
    q = "SELECT law_id, title, body, category FROM laws_fts ORDER BY law_id"
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    hits = fresh.execute("SELECT law_id FROM laws_fts WHERE laws_fts "
                         "MATCH 'време'").fetchall()
    assert ("zakon-vremeto",) in hits
    fresh.close()
    src.close()


def test_default_budget_emits_no_statement_over_90k(d1_out):
    from export_cf.scan import max_statement_bytes
    _, out, _ = d1_out
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
        + sorted(tmp_path.glob("d1-fts-*.sql"))
    assert len(chunks) > 2  # tiny budget → many files
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((tmp_path / "d1-schema.sql").read_text("utf-8"))
    for c in chunks:
        text = c.read_text("utf-8")
        assert text.endswith(";\n"), c.name
        fresh.executescript(text)  # would raise if a stmt were split
    q = "SELECT law_id, body FROM laws_fts ORDER BY law_id"
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    fresh.close()
    src.close()


# ─────────────── v1.3.2 idempotent import guards ───────────────


def test_every_fts_statement_carries_a_guard(d1_out):
    """Self-check contract: every statement in the d1-fts series is
    idempotent — INSERTs via WHERE NOT EXISTS(law_id), appends via the
    length(CAST(body AS BLOB)) byte-offset guard."""
    from export_cf.scan import iter_statements
    _, out, result = d1_out
    inserts = updates = 0
    for f in sorted(out.glob("d1-fts-*.sql")):
        for stmt in iter_statements(str(f)):
            if stmt.startswith(b"INSERT INTO laws_fts"):
                assert (b"WHERE NOT EXISTS (SELECT 1 FROM laws_fts "
                        b"WHERE law_id = ") in stmt
                inserts += 1
            elif stmt.startswith(b"UPDATE laws_fts"):
                assert b"AND length(CAST(body AS BLOB)) = " in stmt
                updates += 1
            else:
                raise AssertionError(f"unexpected stmt: {stmt[:80]!r}")
    assert inserts == result["counts"]["laws_fts"]
    assert inserts == result["fts_guards"]["inserts"]
    assert updates == result["fts_guards"]["updates"]


def test_fts_series_reimport_is_idempotent(export_corpus, tmp_path):
    """The double-application incident: a 'fetch failed' import may have
    committed server-side. Importing the ENTIRE fts series a second (and
    third) time must be a byte-exact no-op — including sliced rows,
    where an unguarded retry would double-append body slices."""
    _, db = export_corpus
    src = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    export_d1(src, tmp_path, stmt_max_bytes=1000)  # forces slicing
    fresh = sqlite3.connect(":memory:")
    _reimport(tmp_path, fresh)
    q = "SELECT law_id, title, body, category FROM laws_fts ORDER BY law_id"
    first = fresh.execute(q).fetchall()
    for _ in range(2):  # blind retries of the whole fts series
        for chunk in sorted(tmp_path.glob("d1-fts-*.sql")):
            fresh.executescript(chunk.read_text(encoding="utf-8"))
    assert fresh.execute(q).fetchall() == first
    assert first == src.execute(q).fetchall()
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
    for f in sorted(tmp_path.glob("d1-fts-*.sql")):
        stmts.extend(s.decode("utf-8") for s in iter_statements(str(f)))
    fresh = sqlite3.connect(":memory:")
    fresh.executescript((tmp_path / "d1-schema.sql").read_text("utf-8"))
    cut = len(stmts) // 2
    for s in stmts[:cut]:          # partial first attempt
        fresh.executescript(s)
    for s in stmts:                # full blind retry
        fresh.executescript(s)
    q = "SELECT law_id, body FROM laws_fts ORDER BY law_id"
    assert fresh.execute(q).fetchall() == src.execute(q).fetchall()
    fresh.close()
    src.close()
