# Pre-UI Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix every verified defect from the 2026-07-02 comprehensive review (`docs/research/2026-07-02-pre-ui-code-review.md`) so the backend is trustworthy for daily MCP use and consumable by the Phase-7 web UI, whose REST API (7.1) is the follow-on plan.

**Architecture:** Five independent hardening batches over existing modules — A: index data correctness; B: MCP wire contract; E: acquisition-gate soundness; C: search performance (FR-027, measurement-gated); D: operability (CI, metrics, docs). No new subsystems except the CI workflow. The REST API is deliberately NOT in this plan (own plan, after Batch B lands, since it reuses the same query layer and error taxonomy).

**Tech Stack:** Python 3.12, sqlite3 + FTS5, FastMCP (installed 3.2.4; pyproject `>=2,<4`), pytest, GitHub Actions.

## Global Constraints

- Run `.venv/bin/python -m pytest -q --ignore=tests/perf` after every task; must stay green (437+ passing at baseline).
- Protected surfaces (`.ahelia/protected-surfaces.yaml`) — Batch B touches **MCP tool signatures / error taxonomy** (Surface 3): Task 5 Step 1 writes ONE preflight doc covering all of Batch B's additive contract deltas. SQLite schema, frontmatter schema, fetcher/bg interfaces, commit format: NOT touched by this plan (Batch E changes are internal logic only).
- Additive-only contract changes: new error code `INVALID_DATE`, JSON wire format for errors, real output schemas. `tools.json` version 1.2.0 → 1.3.0 exactly once (Task 8).
- Corpus `.md` files are data — never modified, except the single `git mv` in Task 3.
- Pipeline-code commits use conventional messages (delivery-contract §Pipeline Code Commits). No corpus-format commits in this plan except Task 3's relocation (also conventional — a file move is repo maintenance, not a legislative event).
- `catalog.db` full rebuild (~40 s) required after Tasks 2, 3, 4 — the plan batches it once in Task 4.
- Bulgarian text in tests: always UTF-8 literals, never escaped.

## Execution order

Tasks are numbered in recommended order: **1–4 (Batch A) → 5–8 (Batch B) → 9–11 (Batch E) → 12–14 (Batch C) → 15–17 (Batch D) → 18 (close-out)**. Batches are independent; within a batch, order matters (Task 8 regenerates tools.json and must be last in B).

---

### Task 1: Atomic full rebuild (P0-3)

**Files:**
- Modify: `index/build.py:78-84` (`_drop_content_rows`)
- Create: `tests/index/test_build_atomicity.py`

**Interfaces:**
- Consumes: `index.build.build(corpus_root, db_path)` (unchanged signature).
- Produces: no interface change — behavioral guarantee: a failed full rebuild leaves the previous catalog intact.

Background: `sqlite3` (default `isolation_level=""`) opens an implicit transaction on the first DML and holds it until an explicit `commit()`. `migrate()` runs (and commits) BEFORE `_drop_content_rows`, so removing the premature commit makes DELETE + all re-INSERTs one transaction, committed only by the existing `conn.commit()` at the end of `build()`'s full path. On exception, `conn.close()` in the `finally` discards everything → prior state survives.

- [ ] **Step 1: Write the failing test**

```python
# tests/index/test_build_atomicity.py
"""Full rebuild must never destroy the previous catalog on failure
(P0-3, review 2026-07-02): the DELETE of all content tables and the
re-INSERT loop must share ONE transaction so a crash mid-rebuild rolls
back to the prior good state when the connection closes."""

import sqlite3
import subprocess

import pytest

import index.build as build_mod
from index.build import build


def _write_act(corpus, cat, slug, title, doc_id):
    d = corpus / cat
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{slug}.md").write_text(
        "---\n"
        f"titulo: {title}\n"
        f"identificador: {doc_id}\n"
        "fecha_publicacion: 2020-01-01\n"
        "---\n\n"
        f"**Чл. 1.** (1) Текст на {title}.\n",
        encoding="utf-8",
    )


@pytest.fixture
def git_corpus(tmp_path):
    corpus = tmp_path / "corpus"
    _write_act(corpus, "laws", "zakon-a", "Закон А", 111)
    _write_act(corpus, "laws", "zakon-b", "Закон Б", 222)
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] fixture"],
        cwd=corpus, check=True)
    return corpus


def test_failed_full_rebuild_preserves_previous_catalog(
        git_corpus, tmp_path, monkeypatch):
    db = str(tmp_path / "catalog.db")
    assert build(git_corpus, db) == 2  # good build first

    real = build_mod._reindex_act
    calls = {"n": 0}

    def boom(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RuntimeError("simulated crash mid-rebuild")
        return real(*args, **kwargs)

    monkeypatch.setattr(build_mod, "_reindex_act", boom)
    with pytest.raises(RuntimeError):
        build(git_corpus, db)

    conn = sqlite3.connect(db)
    try:
        n_laws = conn.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
        n_fts = conn.execute("SELECT COUNT(*) FROM laws_fts").fetchone()[0]
    finally:
        conn.close()
    assert n_laws == 2, "previous catalog must survive a failed rebuild"
    assert n_fts == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/index/test_build_atomicity.py -v`
Expected: FAIL — `assert 0 == 2` (the premature commit made the DELETE durable).

- [ ] **Step 3: Remove the premature commit**

In `index/build.py`, change `_drop_content_rows` to:

```python
def _drop_content_rows(conn: sqlite3.Connection) -> None:
    """Idempotency: remove all rows from content tables before
    re-inserting. Schema (managed by migrations.py) stays intact.
    Order matters for FK-style constraints: dependent tables first.

    Deliberately does NOT commit: the DELETE and the full re-INSERT
    loop must be one transaction (committed at the end of build()'s
    full path), so a crash mid-rebuild rolls back to the previous
    catalog instead of leaving it durably empty (P0-3, review
    2026-07-02)."""
    for table in _CONTENT_TABLES:
        conn.execute(f"DELETE FROM {table}")
```

- [ ] **Step 4: Run the new test + the index suite**

Run: `.venv/bin/python -m pytest tests/index -q`
Expected: all PASS (including the new test).

- [ ] **Step 5: Commit**

```bash
git add index/build.py tests/index/test_build_atomicity.py
git commit -m "fix(index): full rebuild is one transaction — crash no longer empties catalog (P0-3)"
```

---

### Task 2: Alinea-marker false positives (P0-2)

**Files:**
- Modify: `index/provisions.py:66,139-175` (`_ALINEA_CONTINUATION_RE`, `_ALINEA_MARKER_RE`, `_split_alineas`)
- Create: `tests/index/test_alinea_markers.py`

**Interfaces:**
- Consumes: `index.provisions.parse(markdown, law_id)` (unchanged).
- Produces: `_split_alineas(body) -> list[tuple[str, str]]` (same signature) plus new helper `_is_alinea_boundary(prefix: str) -> bool` used only within the module.

Two independent filters (defense in depth): (a) a marker must open a clause — start of body or after a sentence/anchor boundary character; (b) alinea numbers are 1–3 digits (parenthesised years `(1969)`/`(2003)` are 4-digit — the dominant live corruption).

- [ ] **Step 1: Write the failing tests**

```python
# tests/index/test_alinea_markers.py
"""P0-2 (review 2026-07-02): parenthesised years/citation numbers were
parsed as alinea boundaries, truncating real alineas and minting bogus
paragraph rows (116 rows / 22 acts live, e.g. paragraph='1969')."""

from index.provisions import _split_alineas, parse


def test_year_in_parens_is_not_an_alinea_boundary():
    # Naredba № 3/2004 (ship tonnage) pattern — the live corruption case.
    body = ("Чл. 10. (1) При придобиване на кораб в чужбина, за който има "
            "издадено валидно Международно свидетелство за тонажа (1969), "
            "срокът за подаване на заявление за измерване е 3 месеца от "
            "датата на придобиване. (2) Срокът се удължава с 4 седмици.")
    pairs = _split_alineas(body)
    assert [p for p, _ in pairs] == ["1", "2"]
    assert "срокът за подаване" in pairs[0][1]      # not truncated at (1969)
    assert "(1969)" in pairs[0][1]                   # year stays in the text


def test_midtext_citation_number_is_not_a_boundary():
    # ЗРТ чл. 19 pattern: "(2003)" / "(2020)" citations inside running text.
    body = ("Чл. 19. (1) Прилагат се препоръките от Регламента (2003) и "
            "изменението (2020) по отношение на доставчиците. "
            "(2) Друго правило.")
    pairs = _split_alineas(body)
    assert [p for p, _ in pairs] == ["1", "2"]
    assert "(2003)" in pairs[0][1] and "(2020)" in pairs[0][1]


def test_inline_and_suffixed_markers_still_split():
    body = "Чл. 1. (1) Първа. (2) Втора. (2а) Втора-а. (3) Трета."
    assert [p for p, _ in _split_alineas(body)] == ["1", "2", "2а", "3"]


def test_marker_at_start_of_body_and_after_bold_anchor():
    assert [p for p, _ in _split_alineas("(1) Направо алинея. (2) Втора.")] \
        == ["1", "2"]
    assert [p for p, _ in _split_alineas("**Чл. 5.** (1) Първа. (2) Втора.")] \
        == ["1", "2"]


def test_parse_emits_no_bogus_year_paragraph_rows():
    md = ("**Чл. 10.** (1) Свидетелство за тонажа (1969), срокът е 3 "
          "месеца. (2) Удължава се.")
    rows = parse(md, law_id="x")
    paragraphs = [r.paragraph for r in rows if r.paragraph is not None]
    assert paragraphs == ["1", "2"]
```

- [ ] **Step 2: Run to verify the year tests fail**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_markers.py -v`
Expected: the two year/citation tests FAIL (bogus `'1969'`/`'2003'` ids in the list); the others PASS.

- [ ] **Step 3: Implement the boundary + digit-cap filters**

In `index/provisions.py`, replace the `_ALINEA_MARKER_RE` definition block (keep the existing comment about non-digit parentheticals, append the new rationale) and `_split_alineas`; tighten `_ALINEA_CONTINUATION_RE`:

```python
# 1-3 digits only: no article has 1,000+ alineas, while parenthesised
# YEARS — "(1969)", "(2003)" — are always 4-digit and were the dominant
# false positive (P0-2, review 2026-07-02: 116 bogus paragraph rows in
# 22 live acts, truncating real alinea text).
_ALINEA_MARKER_RE = re.compile(r"\(\s*(\d{1,3}[а-я]?)\s*\)")

# Characters that legitimately end the text preceding a real alinea
# marker: sentence enders, the article anchor's '.', bold '**', a
# closing paren/quote. A '(N)' following a LETTER — "тонажа (1969)",
# "изменението (2020)" — is a citation inside running text, never an
# alinea boundary.
_BOUNDARY_CHARS = '.;:!?*)»"“”’'


def _is_alinea_boundary(prefix: str) -> bool:
    """True when a '(N)' candidate at position len(prefix) opens a
    clause: start of the article body, or right after a sentence/anchor
    boundary character (ignoring intervening whitespace)."""
    trimmed = prefix.rstrip()
    if not trimmed:
        return True
    return trimmed[-1] in _BOUNDARY_CHARS


def _split_alineas(body: str) -> list[tuple[str, str]]:
    """Split an article body into (paragraph_id, text) pairs.
    Returns [] if the article has no '(N)' alinea markers.

    The text for each alinea spans from after the marker to the next
    marker (or end of body), with leading/trailing whitespace stripped.
    Candidates that don't open a clause (see _is_alinea_boundary) are
    citations, not boundaries, and are left inside the running text.
    """
    matches = [m for m in _ALINEA_MARKER_RE.finditer(body)
               if _is_alinea_boundary(body[:m.start()])]
    if not matches:
        return []
    out: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        paragraph_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        # Strip leading punctuation/whitespace artifacts left by adjacent
        # markers (e.g., ". " between "(1) Първа." and "(2) Втора.")
        text = re.sub(r"^[\s\.,]+", "", text)
        out.append((paragraph_id, text))
    return out
```

And change line 66 to match the digit cap:

```python
_ALINEA_CONTINUATION_RE = re.compile(r"^\s*\(\s*\d{1,3}[а-я]?\s*\)")
```

- [ ] **Step 4: Run the new tests + existing provisions/index suites**

Run: `.venv/bin/python -m pytest tests/index/test_alinea_markers.py tests/index/test_provisions.py tests/index -q`
Expected: all PASS. If an existing lock-test pins a case where a real marker follows a letter (unlikely — inspect any failure), the failing fixture is the arbiter: adjust `_BOUNDARY_CHARS`, never the test.

- [ ] **Step 5: Commit**

```bash
git add index/provisions.py tests/index/test_alinea_markers.py
git commit -m "fix(index): '(1969)'-style citations no longer split alineas (P0-2)"
```

(The live-catalog rebuild + sweep happens once, in Task 4 Step 5.)

---

### Task 3: Category-drift guard + relocate the invisible ПМС act

**Files:**
- Modify: `index/build.py` (new `_check_category_drift`, called from `build()`)
- Move: `postanovleniya/postanovlenie-46-ot-21-mart-2005-g-za-priemane-na-natsionalni-schetovodni-standa.md` → `regulations/`
- Create: `tests/index/test_category_drift.py`

**Interfaces:**
- Produces: `index.build._check_category_drift(corpus_root: Path) -> None` — raises `ValueError` when a top-level dir outside `CATEGORY_DIRS` holds corpus-shaped acts. Called at the top of `build()` for both full and incremental paths.

- [ ] **Step 1: Relocate the misfiled act (its own frontmatter says `category: regulations`)**

```bash
git mv "postanovleniya/postanovlenie-46-ot-21-mart-2005-g-za-priemane-na-natsionalni-schetovodni-standa.md" regulations/
git commit -m "fix(corpus): relocate ПМС 46/2005 to regulations/ — postanovleniya/ was invisible to the index and every MCP tool (review 2026-07-02); first-class ПМС category arrives with FR-025"
```

Note: the act's pre-move git history stays under the old path (no `--follow` in FR-020), so it will index with a single fresh version — acceptable, it had zero index presence before.

- [ ] **Step 2: Write the failing guard test**

```python
# tests/index/test_category_drift.py
"""A top-level directory holding corpus-shaped acts but absent from
CATEGORY_DIRS must fail the build loudly instead of being silently
invisible (review 2026-07-02: postanovleniya/ had 0 catalog rows)."""

import subprocess

import pytest

from index.build import _check_category_drift, build


def _init_git(corpus):
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] fixture"],
        cwd=corpus, check=True)


def _act(text_dir, slug, doc_id):
    text_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / f"{slug}.md").write_text(
        "---\ntitulo: Тест\n"
        f"identificador: {doc_id}\n"
        "fecha_publicacion: 2020-01-01\n---\n\nЧл. 1. Текст.\n",
        encoding="utf-8")


def test_rogue_corpus_dir_fails_build(tmp_path):
    corpus = tmp_path / "corpus"
    _act(corpus / "laws", "zakon-a", 1)
    _act(corpus / "postanovleniya", "pms-1", 2)   # rogue, corpus-shaped
    _init_git(corpus)
    with pytest.raises(ValueError, match="postanovleniya"):
        build(corpus, str(tmp_path / "c.db"))


def test_non_corpus_dirs_are_ignored(tmp_path):
    corpus = tmp_path / "corpus"
    _act(corpus / "laws", "zakon-a", 1)
    docs = corpus / "docs"
    docs.mkdir()
    (docs / "notes.md").write_text("# just docs\n", encoding="utf-8")
    _init_git(corpus)
    _check_category_drift(corpus)  # must not raise
    assert build(corpus, str(tmp_path / "c.db")) == 1
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/index/test_category_drift.py -v`
Expected: FAIL — `ImportError: cannot import name '_check_category_drift'`.

- [ ] **Step 4: Implement the guard**

In `index/build.py`, add after `_iter_corpus_files`:

```python
def _check_category_drift(corpus_root: Path) -> None:
    """Fail loudly when a top-level directory outside CATEGORY_DIRS holds
    corpus-shaped acts (review 2026-07-02: postanovleniya/ was invisible
    to every build and every MCP tool). A dir is corpus-shaped when any
    immediate *.md child starts with YAML frontmatter carrying an
    `identificador` key. docs/, research/ etc. don't match."""
    known = set(CATEGORY_DIRS.values())
    offenders: list[str] = []
    for d in sorted(corpus_root.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in known:
            continue
        for f in sorted(d.glob("*.md")):
            head = f.read_text(encoding="utf-8", errors="replace")[:2048]
            if head.startswith("---\n") and "\nidentificador:" in head:
                offenders.append(f"{d.name}/ (e.g. {f.name})")
                break
    if offenders:
        raise ValueError(
            "corpus-shaped directories not indexed (missing from "
            f"CATEGORY_DIRS): {', '.join(offenders)} — relocate the acts "
            "into a known category dir, or register the category in "
            "fetcher/bg/discovery.py CATEGORY_DIRS (protected surface — "
            "IMPLEMENTATION-PREFLIGHT required)."
        )
```

And in `build()`, right after `corpus_root = Path(corpus_root)`:

```python
    _check_category_drift(corpus_root)
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/index/test_category_drift.py tests/index -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add index/build.py tests/index/test_category_drift.py
git commit -m "feat(index): fail build loudly on corpus dirs invisible to CATEGORY_DIRS (review 2026-07-02)"
```

---

### Task 4: Pre-1970 `valid_from` clamp repair + live rebuild & sweep

**Files:**
- Modify: `index/build.py:229-243` (`_reindex_act` version loop)
- Create: `tests/index/test_pre1970_valid_from.py`

**Interfaces:**
- Consumes: `_reindex_act`'s `effective` local (ISO string, frontmatter-derived) and `git_versions` list.
- Produces: earliest `law_versions.valid_from` = frontmatter date when the git author-date carries the D-017 `1970-01-01` clamp.

- [ ] **Step 1: Write the failing test**

```python
# tests/index/test_pre1970_valid_from.py
"""D-017 clamps pre-1970 GIT_AUTHOR_DATEs to 1970-01-01 (git rejects
negative epochs). The version map must repair the EARLIEST version's
valid_from from frontmatter so pre-1970 history isn't denied (review
2026-07-02: Inheritance Act 1949 reported earliest_available=1970-01-01)."""

import os
import sqlite3
import subprocess

from index.build import build


def test_earliest_valid_from_prefers_frontmatter_over_epoch_clamp(tmp_path):
    corpus = tmp_path / "corpus"
    d = corpus / "laws"
    d.mkdir(parents=True)
    (d / "zakon-star.md").write_text(
        "---\ntitulo: Закон за наследството\nidentificador: 999\n"
        "fecha_publicacion: 1949-01-29\n---\n\nЧл. 1. Текст.\n",
        encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    env = dict(os.environ,
               GIT_AUTHOR_DATE="1970-01-01T00:00:00+00:00",
               GIT_COMMITTER_DATE="1970-01-01T00:00:00+00:00")
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "[bootstrap] Закон за наследството"],
        cwd=corpus, check=True, env=env)

    db = str(tmp_path / "c.db")
    build(corpus, db)
    conn = sqlite3.connect(db)
    try:
        vf = conn.execute(
            "SELECT MIN(valid_from) FROM law_versions "
            "WHERE law_id='zakon-star'").fetchone()[0]
    finally:
        conn.close()
    assert vf == "1949-01-29"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/index/test_pre1970_valid_from.py -v`
Expected: FAIL — `assert '1970-01-01' == '1949-01-29'`.

- [ ] **Step 3: Implement the repair**

In `index/build.py` `_reindex_act`, inside the `if git_versions:` loop, insert before the `if is_latest:` branch:

```python
        for i, (valid_from, commit_hash) in enumerate(git_versions):
            # D-017/D-018 clamp repair: pre-1970 publication dates commit
            # with GIT_AUTHOR_DATE clamped to 1970-01-01 (git rejects
            # negative epochs). For the act's EARLIEST version, prefer the
            # frontmatter date when it is genuinely earlier, so
            # version_at_date() doesn't deny pre-1970 history (review
            # 2026-07-02: Inheritance Act 1949 → earliest=1970-01-01).
            if i == 0 and valid_from == "1970-01-01" and effective < "1970-01-01":
                valid_from = effective
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/index/test_pre1970_valid_from.py tests/index -q`
Expected: all PASS.

- [ ] **Step 5: Rebuild the live catalog and sweep for Batch-A regressions**

```bash
.venv/bin/python -m index.build --corpus . --db catalog.db
.venv/bin/python - <<'EOF'
import sqlite3
conn = sqlite3.connect("file:catalog.db?mode=ro", uri=True)
c = conn.cursor()
four = c.execute("SELECT COUNT(*) FROM provisions WHERE paragraph GLOB '[0-9][0-9][0-9][0-9]*'").fetchone()[0]
three = c.execute("SELECT DISTINCT paragraph FROM provisions WHERE paragraph GLOB '[0-9][0-9][0-9]'").fetchall()
pms = c.execute("SELECT COUNT(*) FROM laws WHERE law_id LIKE 'postanovlenie-46%'").fetchone()[0]
old = c.execute("SELECT MIN(valid_from) FROM law_versions WHERE law_id='zakon-za-nasledstvoto'").fetchone()[0]
total = c.execute("SELECT COUNT(*) FROM laws").fetchone()[0]
print(f"4-digit paragraphs: {four} (expect 0)")
print(f"3-digit paragraphs to eyeball: {three} (expect [] or justified)")
print(f"ПМС 46 indexed: {pms} (expect 1)")
print(f"Inheritance Act earliest: {old} (expect 1949-01-29)")
print(f"total acts: {total} (expect 3600)")
EOF
```

Expected: the printed expectations hold. Eyeball any 3-digit paragraph survivors against their source `.md` (`grep -n "(NNN)" <file>`); a real 3-digit alinea is fine, a citation is a new failing test case for Task 2.

- [ ] **Step 6: Commit**

```bash
git add index/build.py tests/index/test_pre1970_valid_from.py
git commit -m "fix(index): earliest valid_from prefers frontmatter over the 1970-01-01 git clamp (review 2026-07-02)"
```

---

### Task 5: Errors reach the wire as JSON (P0-1) — with Batch-B preflight

**Files:**
- Create: `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-wire-contract.md`
- Modify: `mcp_server/errors.py`
- Modify: `tests/mcp_server/test_tools_e2e.py` (rewrite the substring-only error test; add per-family structured assertions)
- Modify: `docs/api/error-codes.md`, `docs/api/error-codes.json` (wire-format section; version 1.0.0 → 1.1.0)

**Interfaces:**
- Consumes: `fastmcp.exceptions.ToolError` (FastMCP's own class; its `call_tool` passes `FastMCPError` subclasses through unwrapped).
- Produces: `mcp_server.errors.ToolError(code, payload)` — same constructor, same `.code`/`.payload`/`.to_dict()`, but now subclassing FastMCP's `ToolError`, and `str(e)` == `json.dumps({"code": ..., **payload}, ensure_ascii=False)`. Every later task's error assertions may rely on `json.loads(str(e))`.

- [ ] **Step 1: Write the Batch-B preflight doc** (Surface 3 — MCP tool signatures / error taxonomy; all changes additive)

Create `docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-wire-contract.md` following the checklist format of `docs/process/IMPLEMENTATION-PREFLIGHT.md` (mirror the structure of `IMPLEMENTATION-PREFLIGHT-2026-06-21-fr018.md`), covering, as one batch: (a) error wire format becomes JSON (behavioral, additive — same codes, same payloads, machine-parseable message); (b) `INDEX_STALE`/`INDEX_MISSING` become genuinely tool-raised (Task 6) and the docs' `raised_by` is corrected; (c) new additive error code `INVALID_DATE` (Task 7); (d) real field-level `output_schema` for all tools via TypedDict annotations, `tools.json` 1.2.0 → 1.3.0 (Task 8). State explicitly: no field removed, no required input added, no tool renamed → additive per Surface 3; owner sign-off = the review-session approval of 2026-07-02 (D-050).

- [ ] **Step 2: Write the failing structured-error e2e test**

In `tests/mcp_server/test_tools_e2e.py`, replace the body of `test_invalid_article_spec_surfaces_through_mcp` (keep the name; ~line 252) and add a helper + parametrized family test alongside it:

```python
import json


def _error_payload(exc_value) -> dict:
    """Parse the structured JSON error a real MCP client receives.
    Tolerates a host-added text prefix by slicing at the first '{'."""
    text = str(exc_value)
    start = text.find("{")
    assert start != -1, f"no JSON object in error text: {text!r}"
    return json.loads(text[start:])


@pytest.mark.anyio
async def test_invalid_article_spec_surfaces_through_mcp(handle):
    """The structured payload must reach a REAL MCP client as parseable
    JSON — not Python dict-repr prose (P0-1, review 2026-07-02)."""
    async with Client(handle.mcp) as client:
        with pytest.raises(Exception) as exc:
            await client.call_tool(
                "get_article", {"law": "закон-тест", "article": "garbage!!"})
    payload = _error_payload(exc.value)
    assert payload["code"] == "INVALID_ARTICLE_SPEC"
    assert isinstance(payload["examples"], list) and payload["examples"]


@pytest.mark.anyio
async def test_law_not_found_carries_structured_suggestions(handle):
    async with Client(handle.mcp) as client:
        with pytest.raises(Exception) as exc:
            await client.call_tool("get_law", {"name": "несъществуващ акт"})
    payload = _error_payload(exc.value)
    assert payload["code"] == "LAW_NOT_FOUND"
    assert isinstance(payload["suggestions"], list)
```

(Match the module's existing async/client conventions — it already drives `fastmcp.Client(handle.mcp)`; reuse its fixture names and the same `pytest.raises` exception type the module already imports.)

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_tools_e2e.py -v -k "invalid_article_spec or law_not_found_carries"`
Expected: FAIL — `json.loads` chokes on dict-repr (`{'spec': ...}` single quotes).

- [ ] **Step 4: Rewrite `mcp_server/errors.py`**

```python
"""Tool error taxonomy. Per D-026, errors are first-class structured outputs.

Each ToolError carries a stable `code` (one of ERROR_CODES) and a payload
dict with model/UI-actionable structured data (suggestions, candidates,
available_articles, etc.).

The class SUBCLASSES fastmcp.exceptions.ToolError so FastMCP's call_tool
passes it through unwrapped (`except FastMCPError: raise`), and its
message is compact JSON — every MCP client (LLM host or web UI) receives
machine-parseable structure, not Python repr prose. (P0-1, review
2026-07-02: a plain-Exception ToolError was wrapped and flattened to
dict-repr text on the wire, making the taxonomy invisible to non-LLM
callers.)
"""

import json

from fastmcp.exceptions import ToolError as _FastMCPToolError

ERROR_CODES = frozenset({
    "LAW_NOT_FOUND",
    "AMBIGUOUS_NAME",
    "NO_VERSION_AT_DATE",
    "DATE_UNCERTAIN",     # warning, rides in successful response
    "INVALID_ARTICLE_SPEC",
    "ARTICLE_NOT_FOUND",
    "INDEX_STALE",
    "INDEX_MISSING",
    "QUERY_TOO_BROAD",    # FR-016: single-word category queries (e.g. "наредба")
    "INVALID_DATE_RANGE",  # Phase 2: diff/amendments_in_period with from > to
    "DIFF_FAILED",         # Phase 2: underlying git diff invocation failed
})


class ToolError(_FastMCPToolError):
    """Structured tool failure surfaced through the MCP response envelope.

    str(e) — and therefore the error text an MCP client receives — is
    json.dumps({"code": ..., **payload}, ensure_ascii=False).
    """

    def __init__(self, code: str, payload: dict):
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code {code!r}; "
                             f"must be one of {sorted(ERROR_CODES)}")
        self.code = code
        self.payload = payload
        super().__init__(json.dumps(self.to_dict(), ensure_ascii=False,
                                    default=str))

    def to_dict(self) -> dict:
        """JSON-serializable form for FastMCP."""
        return {"code": self.code, **self.payload}
```

- [ ] **Step 5: Run the full mcp_server suite**

Run: `.venv/bin/python -m pytest tests/mcp_server -q`
Expected: all PASS. `tests/mcp_server/test_errors.py` asserts on `.code`/`.payload`/`to_dict()` which are unchanged; any test asserting the old `"CODE: {...}"` message format must be updated to `json.loads(str(e))["code"] == ...` (the JSON message is the contract now).

- [ ] **Step 6: Update the error-codes contract docs**

In `docs/api/error-codes.md`: bump `version` to `1.1.0`; add a short **Wire format** section: "The MCP error text is a single JSON object: `{"code": "<CODE>", ...payload}` (UTF-8, `ensure_ascii=False`). Clients parse it with `JSON.parse`/`json.loads`; the `code` key is always present." Mirror the version bump in `docs/api/error-codes.json`. Run the parity test: `.venv/bin/python -m pytest tests/mcp_server/test_error_codes_doc.py -q` — adjust the doc edits (not the runtime) until green.

- [ ] **Step 7: Commit**

```bash
git add mcp_server/errors.py tests/mcp_server/test_tools_e2e.py docs/api/error-codes.md docs/api/error-codes.json docs/process/IMPLEMENTATION-PREFLIGHT-2026-07-02-wire-contract.md
git commit -m "fix(mcp): ToolError subclasses FastMCP's — structured errors reach the wire as JSON (P0-1)"
```

---

### Task 6: Historical-read hardening + real INDEX_STALE/INDEX_MISSING (P1)

**Files:**
- Modify: `mcp_server/server.py:47-64` (`_read_law_markdown`), `191-231` (`_register`)
- Create: `tests/mcp_server/test_historical_reads.py`
- Modify: `docs/api/error-codes.md` + `.json` (`raised_by` corrections)

**Interfaces:**
- Consumes: `queries.version_with_warnings` (unchanged), the Task-5 `ToolError`.
- Produces: `_read_law_markdown` raises `ToolError("INDEX_STALE", {...})` instead of leaking `OSError`/`CalledProcessError`; `_register` maps catalog-level `sqlite3.OperationalError` to `ToolError("INDEX_MISSING", {...})`. FTS5 user-input `OperationalError`s are NOT remapped (they're already suppressed inside `index/fts.py:_run_match` / `queries.resolve_name_to_law_id`).

- [ ] **Step 1: Write the failing tests (real 2-commit git fixture — also closes the "git show path untested" and "real diff() untested" gaps)**

```python
# tests/mcp_server/test_historical_reads.py
"""FR-020 historical reads via `git show` and real two-version diff()
had zero coverage (review 2026-07-02); failures leaked raw
CalledProcessError. These tests use a REAL 2-commit corpus."""

import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from index.build import build
from mcp_server.errors import ToolError
from mcp_server.server import build_app


def _commit(corpus, msg, date):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{date}T00:00:00+00:00",
               GIT_COMMITTER_DATE=f"{date}T00:00:00+00:00")
    subprocess.run(["git", "add", "-A"], cwd=corpus, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", msg], cwd=corpus, check=True, env=env)


@pytest.fixture
def two_version_app(tmp_path):
    corpus = tmp_path / "corpus"
    law = corpus / "laws" / "zakon-vremeto.md"
    law.parent.mkdir(parents=True)
    fm = ("---\ntitulo: Закон за времето\nidentificador: 777\n"
          "fecha_publicacion: 2020-01-01\n---\n\n")
    law.write_text(fm + "Чл. 1. СТАРА редакция.\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
    _commit(corpus, "[bootstrap] Закон за времето", "2020-01-01")
    law.write_text(fm + "Чл. 1. НОВА редакция.\n", encoding="utf-8")
    _commit(corpus, "[reforma] Закон за времето", "2021-06-15")

    db = str(tmp_path / "c.db")
    build(corpus, db)
    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    handle = build_app(conn, corpus_root=Path(corpus))
    yield handle, conn
    conn.close()


def test_get_law_historical_returns_v1_text(two_version_app):
    handle, _ = two_version_app
    out = handle.call_tool_sync(
        "get_law", {"name": "zakon-vremeto", "date": "2020-06-01"})
    assert "СТАРА редакция" in out["body_markdown"]
    current = handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert "НОВА редакция" in current["body_markdown"]
    assert out["commit_hash"] != current["commit_hash"]


def test_diff_returns_real_two_version_diff(two_version_app):
    handle, _ = two_version_app
    out = handle.call_tool_sync(
        "diff", {"law": "zakon-vremeto",
                 "date1": "2020-06-01", "date2": "2021-12-31"})
    assert "-Чл. 1. СТАРА редакция." in out
    assert "+Чл. 1. НОВА редакция." in out


def test_unreachable_commit_surfaces_index_stale(two_version_app):
    handle, conn = two_version_app
    conn.execute("UPDATE law_versions SET commit_hash = ? "
                 "WHERE valid_to IS NOT NULL", ("0" * 40,))
    conn.commit()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync(
            "get_law", {"name": "zakon-vremeto", "date": "2020-06-01"})
    assert exc.value.code == "INDEX_STALE"
    assert "hint" in exc.value.payload


def test_missing_working_tree_file_surfaces_index_stale(two_version_app, tmp_path):
    handle, _ = two_version_app
    (tmp_path / "corpus" / "laws" / "zakon-vremeto.md").unlink()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert exc.value.code == "INDEX_STALE"


def test_dropped_table_surfaces_index_missing(two_version_app):
    handle, conn = two_version_app
    conn.execute("ALTER TABLE laws RENAME TO laws_gone")
    conn.commit()
    with pytest.raises(ToolError) as exc:
        handle.call_tool_sync("get_law", {"name": "zakon-vremeto"})
    assert exc.value.code == "INDEX_MISSING"
```

- [ ] **Step 2: Run to verify failures**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_historical_reads.py -v`
Expected: the two positive tests PASS already (they lock the untested paths); the three error tests FAIL with raw `CalledProcessError` / `FileNotFoundError` / `sqlite3.OperationalError`.

- [ ] **Step 3: Harden `_read_law_markdown`**

Replace the function in `mcp_server/server.py`:

```python
def _read_law_markdown(corpus_root: Path, law_id: str, category: str,
                       commit_hash: str, current_commit: str) -> str:
    """Return the full Markdown (frontmatter + body) for the law at the
    given commit. Working-tree fast path when commit_hash ==
    current_commit; historical versions go through `git show`.

    Read failures surface as INDEX_STALE (structured, actionable): a
    missing working-tree file or an unreachable commit both mean the
    catalog no longer matches the corpus — re-run `python -m index.build`
    (review 2026-07-02; previously leaked OSError/CalledProcessError).
    """
    rel_path = f"{category}/{law_id}.md"
    rebuild_hint = ("catalog and corpus have diverged — re-run "
                    "`python -m index.build` against this corpus")
    if commit_hash == current_commit:
        path = corpus_root / rel_path
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            raise ToolError("INDEX_STALE", {
                "law_id": law_id,
                "detail": f"indexed file unreadable: {rel_path} ({e})",
                "hint": rebuild_hint,
            })
    try:
        out = subprocess.run(
            ["git", "show", f"{commit_hash}:{rel_path}"],
            cwd=corpus_root, check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        stderr = (getattr(e, "stderr", "") or "").strip()
        raise ToolError("INDEX_STALE", {
            "law_id": law_id,
            "commit_hash": commit_hash,
            "detail": stderr[:300] or str(e),
            "hint": rebuild_hint,
        })
    return out.stdout
```

- [ ] **Step 4: Map catalog-level sqlite errors in `_register`**

In `mcp_server/server.py`, add a module-level helper after `_law_meta` and extend the wrapper's `except` chain:

```python
_SQLITE_CATALOG_ERRORS = ("no such table", "no such column",
                          "unable to open database",
                          "database disk image is malformed",
                          "file is not a database")


def _is_catalog_error(e: sqlite3.OperationalError) -> bool:
    """Catalog-level OperationalErrors (schema missing/corrupt) — as
    opposed to FTS5 user-input syntax errors, which queries/index.fts
    already suppress before reaching the tool wrapper."""
    msg = str(e).lower()
    return any(marker in msg for marker in _SQLITE_CATALOG_ERRORS)
```

In `_register`'s `wrapper`, before the generic `except Exception:` clause:

```python
                except sqlite3.OperationalError as e:
                    if _is_catalog_error(e):
                        ok, code = False, "INDEX_MISSING"
                        raise ToolError("INDEX_MISSING", {
                            "detail": str(e)[:300],
                            "hint": ("catalog.db is missing tables or "
                                     "corrupt — re-run `python -m "
                                     "index.build`"),
                        })
                    ok, code = False, "UNEXPECTED"
                    raise
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_historical_reads.py tests/mcp_server -q`
Expected: all PASS.

- [ ] **Step 6: Correct the contract docs**

In `docs/api/error-codes.md` + `.json`: `INDEX_STALE.raised_by` = `["get_law", "get_article", "get_articles"]` (read-path failures) — keep the startup-preflight note; `INDEX_MISSING.raised_by` = all seven tools (wrapper-level). Run `.venv/bin/python -m pytest tests/mcp_server/test_error_codes_doc.py -q` until green.

- [ ] **Step 7: Commit**

```bash
git add mcp_server/server.py tests/mcp_server/test_historical_reads.py docs/api/error-codes.md docs/api/error-codes.json
git commit -m "fix(mcp): historical reads + catalog errors surface structured INDEX_STALE/INDEX_MISSING; first real git-show/diff tests (review 2026-07-02)"
```

---

### Task 7: Date validation (`INVALID_DATE`) + input-length caps (P2s)

**Files:**
- Modify: `mcp_server/errors.py` (add code), `mcp_server/queries.py` (`_validate_date`, caps), `mcp_server/server.py` (docstrings mention INVALID_DATE)
- Create: `tests/mcp_server/test_input_validation.py`
- Modify: `docs/api/error-codes.md` + `.json` (new code)

**Interfaces:**
- Produces: `queries._validate_date(date: str | None, param: str) -> str | None` — returns the trimmed date or None; raises `ToolError("INVALID_DATE", {"param": ..., "value": ..., "expected": "YYYY-MM-DD"})` on malformed/empty-string input. Applied in `version_at_date`, `diff_law_versions`, `amendments_in_period`. New cap constants: `_MAX_QUERY_LEN = 512` (search), `_MAX_NAME_LEN = 512` (resolver).

- [ ] **Step 1: Write the failing tests**

```python
# tests/mcp_server/test_input_validation.py
"""Empty-string dates were silently treated as 'today' (truthiness) and
malformed dates fell through to string comparison; free-text params had
no length bound (review 2026-07-02 P2s)."""

import pytest

from mcp_server.errors import ToolError
from mcp_server import queries


@pytest.mark.parametrize("bad", ["", "  ", "2020-13-45", "vinagi", "2020/01/01"])
def test_malformed_date_raises_invalid_date(conn, bad):
    with pytest.raises(ToolError) as exc:
        queries.version_at_date(conn, "zakon-test", bad)
    assert exc.value.code == "INVALID_DATE"
    assert exc.value.payload["expected"] == "YYYY-MM-DD"


def test_none_date_still_means_today(conn):
    assert queries.version_at_date(conn, "zakon-test", None)


def test_overlong_query_rejected_as_too_broad(conn):
    with pytest.raises(ToolError) as exc:
        queries.full_text_search(conn, "закон " * 200)
    assert exc.value.code == "QUERY_TOO_BROAD"


def test_overlong_name_raises_law_not_found(conn):
    with pytest.raises(queries.LawNotFound):
        queries.resolve_name_to_law_id(conn, "х" * 1000)
```

(Reuse the existing `conn` fixture from `tests/mcp_server/conftest.py` — it seeds `zakon-test`-style acts; adapt the law_id literals to the fixture's actual seeded slugs, visible at the top of that conftest.)

- [ ] **Step 2: Run to verify failures**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_input_validation.py -v`
Expected: FAIL — `""` returns today's version; malformed dates raise `NoVersionAtDate` or pass; long inputs run unbounded.

- [ ] **Step 3: Implement**

`mcp_server/errors.py`: add `"INVALID_DATE",  # malformed/empty date parameter (YYYY-MM-DD required)` to `ERROR_CODES`.

`mcp_server/queries.py` — add near the top:

```python
_MAX_QUERY_LEN = 512   # defensive cap: a pasted multi-MB string must not
_MAX_NAME_LEN = 512    # run through normalization/FTS5 under the DB lock

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value: str | None, param: str) -> str | None:
    """Strict ISO-8601 date validation for tool date parameters.
    None → None (meaning 'today'); anything else must be YYYY-MM-DD.
    Empty strings are INVALID (previously truthiness silently mapped
    them to 'today' — review 2026-07-02)."""
    if value is None:
        return None
    v = value.strip() if isinstance(value, str) else ""
    if not _ISO_DATE_RE.match(v):
        raise ToolError("INVALID_DATE", {
            "param": param, "value": str(value)[:50],
            "expected": "YYYY-MM-DD",
        })
    try:
        _date.fromisoformat(v)
    except ValueError:
        raise ToolError("INVALID_DATE", {
            "param": param, "value": v, "expected": "YYYY-MM-DD",
        })
    return v
```

Wire it in:
- `version_at_date`: first line becomes `date = _validate_date(date, "date")` (then `target = date or _date.today().isoformat()` unchanged). This covers `get_law`/`get_article`/`get_articles`/`diff` via their shared version resolution, and `article_lookup`/`articles_lookup` get it via their callers passing the already-validated value — additionally add the same first line to `article_lookup` and `articles_lookup` for direct-call safety.
- `diff_law_versions`: validate both (`date1 = _validate_date(date1, "date1")`, `date2 = _validate_date(date2, "date2")`) BEFORE the reversed-range check; the reversed check then uses `if date1 and date2 and date1 > date2` unchanged.
- `amendments_in_period`: `from_date = _validate_date(from_date, "from_date")`, `to_date = _validate_date(to_date, "to_date")`; then `if from_date is None or to_date is None: raise ToolError("INVALID_DATE", {"param": "from_date/to_date", "value": "null", "expected": "YYYY-MM-DD"})` (both are required for this tool).
- `full_text_search`: before tokenization — `if isinstance(query, str) and len(query) > _MAX_QUERY_LEN: raise ToolError("QUERY_TOO_BROAD", {"query": query[:200], "hint": f"query longer than {_MAX_QUERY_LEN} chars — send a focused query"})`.
- `resolve_name_to_law_id`: after the emptiness check — `if len(name) > _MAX_NAME_LEN: raise LawNotFound(name=name[:100] + "…")`.

`mcp_server/server.py`: add `INVALID_DATE` to the Raises sections of the `get_law`, `get_article`, `get_articles`, `diff`, `amendments_in_period` docstrings (one line each: `INVALID_DATE: a date parameter is not a valid YYYY-MM-DD string.`).

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/mcp_server -q`
Expected: all PASS. If an existing test passed `""` or a malformed date expecting old behavior, update it — the new contract is the arbiter.

- [ ] **Step 5: Update contract docs**

Add `INVALID_DATE` to `docs/api/error-codes.md` + `.json` (raised_by: get_law, get_article, get_articles, diff, amendments_in_period). Parity test green: `.venv/bin/python -m pytest tests/mcp_server/test_error_codes_doc.py -q`.

- [ ] **Step 6: Commit**

```bash
git add mcp_server/errors.py mcp_server/queries.py mcp_server/server.py tests/mcp_server/test_input_validation.py docs/api/error-codes.md docs/api/error-codes.json
git commit -m "feat(mcp): INVALID_DATE validation + input-length caps (review 2026-07-02)"
```

---

### Task 8: Real output schemas in tools.json (P1) — closes Batch B

**Files:**
- Modify: `mcp_server/schemas.py` (TypedDict mirrors), `mcp_server/server.py` (return annotations), `mcp_server/export_tools.py` (version bump), `tools.json` (regenerated)
- Modify: `tests/mcp_server/test_export_tools.py` (lock field-level schema presence)

**Interfaces:**
- Produces: TypedDicts in `mcp_server/schemas.py` — `GetLawResponseDict`, `SearchHitDict`, `GetArticleResponseDict`, `ArticleEntryDict`, `GetArticlesResponseDict`, `VersionEntryDict`, `AmendmentEntryDict` — field names/types mirroring the existing dataclasses exactly. Tool annotations change from `-> dict` / `-> list[dict]` to these types. Runtime return values (plain dicts from `.to_dict()`) are unchanged.

- [ ] **Step 1: Write the failing schema-presence test**

Append to `tests/mcp_server/test_export_tools.py`:

```python
def test_core_read_tools_export_field_level_output_schemas():
    """get_law/get_article/get_articles carried
    {"additionalProperties": true} — nothing for UI codegen
    (review 2026-07-02 P1)."""
    from mcp_server.export_tools import export_tool_schemas
    tools = {t["name"]: t for t in export_tool_schemas()["tools"]}
    assert "body_markdown" in tools["get_law"]["output_schema"]["properties"]
    assert "text_hash" in tools["get_article"]["output_schema"]["properties"]
    assert "articles" in tools["get_articles"]["output_schema"]["properties"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_export_tools.py -v -k field_level`
Expected: FAIL — `KeyError: 'properties'`.

- [ ] **Step 3: Add TypedDict mirrors to `mcp_server/schemas.py`**

Append (imports: `from typing import TypedDict`):

```python
# ── Wire-shape mirrors (review 2026-07-02) ─────────────────────────────
# TypedDicts mirroring the dataclasses above, used ONLY as tool return
# annotations so FastMCP derives field-level output_schema for
# tools.json / UI codegen. Runtime values stay the .to_dict() dicts —
# keep every field list in lockstep with its dataclass.


class SearchHitDict(TypedDict):
    law_id: str
    identificador: str
    title: str
    category: str
    title_snippet: str
    body_snippet: str
    relevance: float


class GetLawResponseDict(TypedDict):
    law_id: str
    identificador: str
    titulo: str
    category: str
    fecha_publicacion: str | None
    ultima_actualizacion: str | None
    dv_issue: str | None
    dv_year: int | None
    effective_date: str | None
    eli: str | None
    amendment_history: list[dict]
    commit_hash: str
    body_markdown: str
    warnings: list[dict]


class GetArticleResponseDict(TypedDict):
    law_id: str
    article: str
    paragraph: str | None
    text: str
    text_hash: str
    commit_hash: str
    warnings: list[dict]


class ArticleEntryDict(TypedDict):
    article: str
    paragraph: str | None
    text: str
    text_hash: str


class GetArticlesResponseDict(TypedDict):
    law_id: str
    articles: list[ArticleEntryDict]
    commit_hash: str
    warnings: list[dict]


class VersionEntryDict(TypedDict):
    date: str | None
    dv_issue: str | None
    operation: str
    commit_hash: str | None


class AmendmentEntryDict(TypedDict):
    law_id: str
    title: str
    date: str | None
    dv_issue: str | None
```

- [ ] **Step 4: Annotate the tools**

In `mcp_server/server.py`, import the TypedDicts and change signatures only (bodies untouched): `get_law(...) -> GetLawResponseDict`, `search(...) -> list[SearchHitDict]`, `get_article(...) -> GetArticleResponseDict`, `get_articles(...) -> GetArticlesResponseDict`, `history(law: str) -> list[VersionEntryDict]`, `amendments_in_period(...) -> list[AmendmentEntryDict]` (`diff -> str` already accurate).

- [ ] **Step 5: Run e2e + live smoke — FastMCP validates returns against these schemas**

Run: `.venv/bin/python -m pytest tests/mcp_server -q` — must PASS.
Then a live-catalog smoke (all 7 tools through a real client):

```bash
.venv/bin/python - <<'EOF'
import asyncio, sqlite3
from pathlib import Path
from fastmcp import Client
from mcp_server.server import build_app

conn = sqlite3.connect("catalog.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
handle = build_app(conn, corpus_root=Path("."))

async def smoke():
    async with Client(handle.mcp) as c:
        await c.call_tool("search", {"query": "обществени поръчки", "limit": 3})
        await c.call_tool("get_law", {"name": "zakon-za-obshtestvenite-porachki"})
        await c.call_tool("get_article", {"law": "zakon-za-obshtestvenite-porachki", "article": "чл. 2"})
        await c.call_tool("get_articles", {"law": "zakon-za-obshtestvenite-porachki", "articles": "чл. 2-4"})
        await c.call_tool("history", {"law": "zakon-za-obshtestvenite-porachki"})
        await c.call_tool("amendments_in_period", {"from_date": "2024-01-01", "to_date": "2024-12-31"})
        await c.call_tool("diff", {"law": "zakon-za-obshtestvenite-porachki", "date1": "2020-01-01", "date2": "2025-01-01"})
        print("SMOKE OK — all 7 tools returned")

asyncio.run(smoke())
EOF
```

Expected: `SMOKE OK`. **Contingency:** if FastMCP output validation rejects a live field (e.g. `dv_year` arriving as a string in some acts), loosen THAT field in the TypedDict to the union actually observed (`int | str | None`), note it in the preflight doc, and re-run — do not silence validation globally.

- [ ] **Step 6: Bump version + regenerate tools.json**

In `mcp_server/export_tools.py`: `TOOLS_JSON_VERSION = "1.3.0"` and extend the comment: `# 1.2.0 → 1.3.0: field-level output schemas (TypedDict annotations), INVALID_DATE code, JSON error wire format — all additive.`

```bash
.venv/bin/python -m mcp_server.export_tools --output tools.json
.venv/bin/python -m mcp_server.export_tools --check
.venv/bin/python -m pytest tests/mcp_server/test_export_tools.py -q
```

Expected: `OK: tools.json matches live schemas (version=1.3.0).`; tests PASS.

- [ ] **Step 7: Commit**

```bash
git add mcp_server/schemas.py mcp_server/server.py mcp_server/export_tools.py tools.json tests/mcp_server/test_export_tools.py
git commit -m "feat(mcp): field-level output schemas for all tools; tools.json 1.3.0 (review 2026-07-02)"
```

---

### Task 9: Coverage gate — full-substring match at any length (P0-4)

**Files:**
- Modify: `fetcher/bg/coverage.py:224-235`
- Modify: `tests/fetcher/bg/test_coverage.py` (add the middle-truncation regression)

**Interfaces:**
- Consumes/Produces: `uncovered_legal_text(soup, markdown, chrome)` — same signature/return shape; stricter semantics.

- [ ] **Step 1: Write the failing test**

Append to `tests/fetcher/bg/test_coverage.py` (reuse its existing soup-building helpers/imports):

```python
def test_middle_truncation_of_long_node_is_uncovered():
    """>200-char nodes were only head/tail-anchored: a parser bug
    dropping text from the MIDDLE passed the gate with 0 uncovered
    chars (P0-4, review 2026-07-02) — the exact D-047 failure class."""
    sentence = ("Възложителят провежда процедурата при условията и по реда "
                "на този закон и приложимите подзаконови нормативни актове, "
                "като осигурява публичност и прозрачност на всички етапи. ")
    full_text = sentence * 4                      # ~640 normalized chars
    html = f'<div class="boxi"><p class="Article">{full_text}</p></div>'
    soup = BeautifulSoup(html, "lxml")
    truncated = full_text[:200] + full_text[-200:]   # middle dropped
    result = uncovered_legal_text(soup, truncated)
    assert result["uncovered_chars"] > 0


def test_trailing_punctuation_variance_still_passes():
    text = ("Министерският съвет приема наредба за прилагането на този "
            "закон в тримесечен срок от обнародването му в Държавен "
            "вестник, като определя реда и условията за нейното изпълнение "
            "и контролните органи по прилагането ѝ. ") * 2
    html = f'<div class="boxi"><p class="Article">{text}</p></div>'
    soup = BeautifulSoup(html, "lxml")
    markdown = text.strip().rstrip(".")           # trailing '.' lost only
    result = uncovered_legal_text(soup, markdown)
    assert result["uncovered_chars"] == 0
```

(If the module's existing tests build soups differently — e.g. wrap in the fixture page skeleton so `content_region()` resolves — mirror that construction; the assertion pair is the contract.)

- [ ] **Step 2: Run to verify the truncation test fails**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_coverage.py -v -k "middle_truncation or trailing_punctuation"`
Expected: `middle_truncation` FAILS (`0 > 0`); `trailing_punctuation` may pass already.

- [ ] **Step 3: Implement full-match with explicit trailing-punct tolerance**

In `fetcher/bg/coverage.py`, replace the length-branched check (lines ~224-235) with:

```python
        # Full-text coverage check at ANY length. The old >200-char rule
        # anchored only the first/last 100 chars, leaving the middle
        # unchecked — a parser bug dropping text from the middle of a
        # long node passed the gate silently (P0-4, review 2026-07-02:
        # the exact D-047 failure class). The head/tail rule existed to
        # tolerate minor trailing-punctuation variance; that tolerance
        # is now explicit and bounded: retry with trailing punctuation
        # stripped, never with the middle unchecked.
        covered = t in M
        if not covered:
            t2 = t.rstrip(" .,;:")
            covered = bool(t2) and t2 in M
```

- [ ] **Step 4: Run the full fetcher suite (fixture regression = the false-positive guard)**

Run: `.venv/bin/python -m pytest tests/fetcher -q`
Expected: all PASS. The 6 act fixtures exercised by existing coverage tests are the guard against the stricter rule flagging good parses; a failure there means a real normalization mismatch — fix `_normalize` (e.g. extend the tolerance), never re-widen the blind spot.

- [ ] **Step 5: Commit**

```bash
git add fetcher/bg/coverage.py tests/fetcher/bg/test_coverage.py
git commit -m "fix(fetcher): coverage gate full-substring match at any length — middle truncation now trips it (P0-4)"
```

---

### Task 10: CF-challenge-on-200 detection + titulo precondition (P0-5)

**Files:**
- Modify: `fetcher/bg/client.py:36-41`, `refresh.py` (nova + existing branches), `bootstrap.py` (per-doc loop, same site as its gate check)
- Modify: `tests/fetcher/bg/test_client.py`, `tests/refresh/test_gate.py`

**Interfaces:**
- Produces: `is_cloudflare_challenge(resp) -> bool` — status-agnostic (markers decide). New refresh/bootstrap behavior: an act parsing to empty `titulo` is recorded as a gate failure (`buckets: {"<missing-titulo>": <body length>}`) and never written.

- [ ] **Step 1: Write the failing tests**

Append to `tests/fetcher/bg/test_client.py` (mirror its existing fake-response helper):

```python
def test_challenge_served_with_http_200_is_detected():
    """CF managed challenges can arrive with HTTP 200; status-gating let
    them pass as act content (P0-5, review 2026-07-02)."""
    resp = _FakeResponse(status_code=200, content=(
        b"<html><title>Just a moment...</title>"
        b"<script src='/cdn-cgi/challenge-platform/x.js'></script></html>"))
    assert is_cloudflare_challenge(resp) is True


def test_normal_act_page_is_not_flagged():
    resp = _FakeResponse(status_code=200,
                         content="<html><p class='Article'>Чл. 1. Текст."
                                 "</p></html>".encode("utf-8"))
    assert is_cloudflare_challenge(resp) is False
```

Append to `tests/refresh/test_gate.py` (reuse its orchestrator-fixture pattern — the module already fakes `_fetch_assemble` results):

```python
def test_empty_titulo_is_a_gate_failure_and_skips_write():
    """A page parsing to no titulo is never a legal act — record a gate
    failure instead of committing a near-empty file (P0-5)."""
    meta = {"titulo": "", "identificador": "123", "estado": "vigente"}
    # drive the EXISTING branch with this meta via the module's fake
    # _fetch_assemble; assert: report.gate_failures grows by one with
    # bucket "<missing-titulo>", no file write, state[doc_id]=="gate-fail".
```

(Complete the body against the module's actual fixture names — it already has gate-failure tests to copy the harness from; the three assertions above are the contract.)

- [ ] **Step 2: Run to verify failures**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_client.py tests/refresh/test_gate.py -q`
Expected: the new tests FAIL (200-challenge returns False; empty titulo writes).

- [ ] **Step 3: Implement**

`fetcher/bg/client.py`:

```python
def is_cloudflare_challenge(resp) -> bool:
    """Detect a Cloudflare bot challenge by body markers. 403/503 is the
    classic signature, but managed/JS challenges can arrive with HTTP
    200 (P0-5, review 2026-07-02) — the markers alone are decisive; no
    real lex.bg act body contains them."""
    body = (resp.content or b"")[:20000].lower()
    return any(m in body for m in _CF_MARKERS)
```

`refresh.py` — in BOTH the nova branch and the existing branch, immediately after `_fetch_assemble(...)` returns and before the threshold check, insert:

```python
            if not (meta.get("titulo") or "").strip():
                # A page with no parseable titulo is not a legal act —
                # blank/challenge/soft-404 pages must never be written
                # (P0-5, review 2026-07-02). FR-011's 7 known empty-titulo
                # stubs will re-fail here on refresh: intended — they are
                # content-less and stay frozen as committed.
                report.gate_failures.append(make_gate_record(
                    doc_id, ce.slug if doc_id in corpus else str(doc_id),
                    "<no titulo>",
                    {"uncovered_chars": len(body),
                     "buckets": {"<missing-titulo>": len(body)}}))
                state[doc_id] = "gate-fail"
                save_state(state_path, state)
                log.warning("titulo precondition FAIL doc_id=%d — skipping write",
                            doc_id)
                continue
```

(In the nova branch use `str(doc_id)` for the slug argument; in the existing branch use `ce.slug`.)

`bootstrap.py` — same precondition at its per-doc gate-check site (before its write/commit), recording into its gate-report structure exactly as its existing `uncovered_chars > threshold` branch does.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/fetcher tests/refresh tests/test_bootstrap.py -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add fetcher/bg/client.py refresh.py bootstrap.py tests/fetcher/bg/test_client.py tests/refresh/test_gate.py
git commit -m "fix(fetcher): detect CF challenges on any HTTP status; empty-titulo pages gate-fail instead of committing (P0-5)"
```

---

### Task 11: `estado: derogado` preservation on re-scrape (P0-6)

**Files:**
- Modify: `refresh.py` (EXISTING branch)
- Modify: `tests/refresh/test_orchestrator.py` (or `test_gate.py` — whichever hosts the EXISTING-branch harness)

**Interfaces:**
- Produces: in the EXISTING branch, a committed `estado: derogado` survives re-scrape (metadata.parse hardcodes `vigente` and has no repeal detection).

- [ ] **Step 1: Write the failing test**

```python
def test_derogado_estado_survives_existing_rescrape():
    """metadata.parse() hardcodes estado: vigente; without preservation a
    repealed act still listed on lex.bg gets silently un-repealed on its
    next re-scrape and committed as [popravka] (P0-6, review 2026-07-02)."""
    # corpus fixture entry: frontmatter estado: derogado
    # fake _fetch_assemble returns meta with estado: "vigente" and an
    # otherwise-identical body
    # run the EXISTING branch; assert:
    #   1) the written/candidate frontmatter still says "estado: derogado"
    #   2) when nothing else changed, classification is "unchanged"
    #      (no spurious [popravka] commit)
```

(Complete against the module's existing EXISTING-branch harness — it already builds `CorpusEntry`-style fixtures; the two assertions are the contract.)

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/refresh -q -k derogado`
Expected: FAIL — candidate carries `estado: vigente`.

- [ ] **Step 3: Implement**

In `refresh.py`'s EXISTING branch, right after the titulo precondition (Task 10) and before `candidate = assemble_file(meta, body)`:

```python
            # P0-6 (review 2026-07-02): never silently un-repeal.
            # metadata.parse() hardcodes estado: vigente (no repeal
            # detection), so a committed derogado act still listed on
            # lex.bg would flip back on re-scrape. Preserve derogado
            # unless an explicit un-repeal signal exists (none is parsed
            # today — revisit with the ДВ layer, FR-024/FR-025).
            if ce.frontmatter.get("estado") == "derogado":
                meta["estado"] = "derogado"
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/refresh -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add refresh.py tests/refresh/
git commit -m "fix(refresh): estado derogado survives EXISTING re-scrape — no silent un-repeal (P0-6)"
```

---

### Task 12: FR-027 search perf — probe harness + baseline record

**Files:**
- Create: `scripts/perf_probe.py`
- Create: `docs/research/2026-07-02-fr027-search-perf.md` (baseline numbers — skeleton below, executor fills measured values)

**Interfaces:**
- Produces: `python scripts/perf_probe.py [db]` printing per-query cold (fresh connection) and warm p50 latency for a fixed 10-query set. Baseline doc other tasks reference.

- [ ] **Step 1: Write the probe**

```python
# scripts/perf_probe.py
"""FR-027 search-latency probe. Cold = fresh read-only connection (OS
page cache NOT controlled — true cold needs a reboot/purge; the fresh-
connection number is still the operative regression signal). Run on a
quiet machine."""

import sqlite3
import statistics
import sys
import time

sys.path.insert(0, ".")
from index.fts import search_fts  # noqa: E402

QUERIES = [
    "обществени поръчки", "данък добавена стойност", "лични данни",
    "трудов договор", "движение по пътищата", "енергийна ефективност",
    "ЗОП", "касови апарати", "административни нарушения",
    "защита на потребителите",
]


def probe(db: str = "catalog.db", runs: int = 5) -> None:
    for q in QUERIES:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        t0 = time.perf_counter()
        search_fts(cur, q, limit=10)
        cold = time.perf_counter() - t0
        warm = []
        for _ in range(runs):
            t0 = time.perf_counter()
            search_fts(cur, q, limit=10)
            warm.append(time.perf_counter() - t0)
        conn.close()
        print(f"{q!r}: cold={cold * 1000:7.0f}ms "
              f"warm_p50={statistics.median(warm) * 1000:7.0f}ms")


if __name__ == "__main__":
    probe(*sys.argv[1:2])
```

- [ ] **Step 2: Run it, record the baseline**

Run: `.venv/bin/python scripts/perf_probe.py` (quiet machine, nothing else running).
Create `docs/research/2026-07-02-fr027-search-perf.md` with sections: **Context** (223 M FTS chars post-D-047; budgets: contract 100 ms warm / 250 ms cold, web PRD 300 ms p95; measured 2026-07-02 orientation: cold 1.2–3.7 s, "лични данни" 4.9 s warm), **Baseline** (paste the probe output verbatim + machine/date), **Experiments** (filled by Task 13), **Decision** (filled by Task 14).

- [ ] **Step 3: Commit**

```bash
git add scripts/perf_probe.py docs/research/2026-07-02-fr027-search-perf.md
git commit -m "perf(fr-027): search-latency probe + baseline record"
```

---

### Task 13: FR-027 — measured cheap wins

**Files:**
- Modify: `index/build.py` (FTS optimize after full build), `mcp_server/__main__.py` (connection pragmas), `docs/research/2026-07-02-fr027-search-perf.md` (experiment log)

**Interfaces:**
- Produces: build-time `INSERT INTO laws_fts(laws_fts) VALUES('optimize')`; runtime pragmas `mmap_size`/`cache_size` on the server connection. Each kept ONLY if the probe shows improvement — the experiment log records keep/drop per item.

- [ ] **Step 1: Experiment A — FTS segment optimize.** In `index/build.py` `build()` full path, after the reindex loop and before `conn.commit()`:

```python
        # FR-027: merge FTS5 b-tree segments so MATCH reads fewer,
        # larger doclists (a 3,600-act bulk insert leaves many segments).
        conn.execute("INSERT INTO laws_fts(laws_fts) VALUES('optimize')")
```

Rebuild + probe: `.venv/bin/python -m index.build --corpus . --db catalog.db && .venv/bin/python scripts/perf_probe.py`. Log the delta in the experiments section.

- [ ] **Step 2: Experiment B — server connection pragmas.** In `mcp_server/__main__.py:main()` after `conn.row_factory = sqlite3.Row`:

```python
    # FR-027: the 1.2 GB catalog is read-only at serve time — memory-map
    # it (page-cache reads without syscalls) and give SQLite a 64 MB
    # page cache. Both are per-connection and harmless on small DBs.
    conn.execute("PRAGMA mmap_size = 1073741824")
    conn.execute("PRAGMA cache_size = -65536")
```

Probe cold-call effect through the server path: `.venv/bin/python -m pytest tests/perf/test_cold_calls.py -q` (still expected to fail budgets — record the numbers, compare to Task 12 baseline).

- [ ] **Step 3: Experiment C — quantify where the time goes** (informs Task 14): run the probe with the two-tier split instrumented — temporarily time tier-1 (title-only MATCH) vs tier-2 (body MATCH) inside `search_fts` via `time.perf_counter()` prints, on the three slowest queries. Record: if tier-2 dominates (expected), the Task-14 options are body-index restructuring or tier-2 gating; if tier-1 dominates, it's segment/IO tuning. Remove the instrumentation after recording.

- [ ] **Step 4: Log every experiment** (numbers, kept/dropped) in the research doc; keep only the winners in code.

- [ ] **Step 5: Commit**

```bash
git add index/build.py mcp_server/__main__.py docs/research/2026-07-02-fr027-search-perf.md
git commit -m "perf(fr-027): measured cheap wins — FTS optimize + ro-connection pragmas"
```

---

### Task 14: FR-027 — decision gate, structural fix, budget re-lock ⚠️ OWNER CHECKPOINT

**Files:**
- Modify: depends on chosen option (below); `tests/perf/test_budgets.py`, `tests/perf/test_cold_calls.py`, `tests/perf/conftest.py`; `pyproject.toml` (perf marker); `docs/research/2026-07-02-fr027-search-perf.md` (decision); `docs/sync/DECISIONS.md` (D-051)

**Interfaces:**
- Consumes: Task 12/13 measurements.
- Produces: ratified budgets that PASS deterministically on the reference machine; `perf` pytest marker excludable in CI.

- [ ] **Step 1: Present the owner a one-page decision** (in-session): baseline vs post-Task-13 numbers + the options with measured/estimated effect:
  - **(a) Title-first gating:** run tier-2 (body MATCH) only when tier-1 yields < 3 hits — most real queries are title-shaped; body-only queries stay slow. No schema change.
  - **(b) Split body index:** separate `laws_fts_body` FTS table with `detail=column`-reduced options, keep title FTS small — **SQLite schema = protected surface → needs its own preflight**; biggest win, most work.
  - **(c) Re-baseline only:** accept measured reality, set budgets to post-Task-13 p95 × 1.5, document that a UI needs its own caching layer (REST API plan).
  Recommendation to present: (a) now + (c) for body-only queries; (b) deferred into the REST-API-era if (a) misses the web PRD's 300 ms p95 for the query mix.

- [ ] **Step 2: Implement the ratified option.** For (a), in `index/fts.py:search_fts` replace the unconditional tier-2 block:

```python
    # FR-027 (D-051): tier 2 (full-corpus body MATCH over 223M chars) is
    # the latency driver — run it only when the title tier can't serve
    # the query (title-shaped queries are the dominant real traffic).
    _TIER2_MIN_TITLE_HITS = 3
    if len(title_rows) >= min(limit, _TIER2_MIN_TITLE_HITS):
        return _rang_tier_sort(list(title_rows))[:limit]
```

(keeping the existing `len(title_rows) >= limit` early-return semantics — this widens it; body-only queries still fall through to tier 2). Locked ranking tests (`tests/index/test_fts.py`, `test_fts_regression.py`, FR-015 adversarial fixture) are the behavioral guard — all must stay green; any that assert tier-2 results for title-served queries get inspected against the D-051 decision text, not blindly edited.

- [ ] **Step 3: Add the `perf` marker + re-lock budgets.** `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "perf: latency budgets against the live catalog (excluded in CI; run locally on a quiet machine)",
]
```

Top of `tests/perf/test_budgets.py` and `tests/perf/test_cold_calls.py`:

```python
pytestmark = pytest.mark.perf
```

Update `BUDGETS`/`COLD_BUDGETS` to the D-051-ratified values (from measurements). Run `.venv/bin/python -m pytest tests/perf -q` on a quiet machine: **6/6 PASS** is the exit criterion.

- [ ] **Step 4: Record D-051** in `docs/sync/DECISIONS.md` (chosen option, measured before/after, ratified budgets, delivery-contract §Phase-1b budget table pointer updated in the same commit) and fill the research doc's Decision section.

- [ ] **Step 5: Commit**

```bash
git add index/fts.py tests/perf/ pyproject.toml docs/research/2026-07-02-fr027-search-perf.md docs/sync/DECISIONS.md docs/process/delivery-contract.md
git commit -m "perf(fr-027): <ratified option> — perf suite green on ratified budgets (D-051)"
```

---

### Task 15: CI (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the `perf` marker (Task 14), `export_tools --check`, the packaging entry point.
- Produces: CI on every push/PR — suite minus perf, parity checks, clean-venv install smoke.

- [ ] **Step 1: Write the workflow**

```yaml
# .github/workflows/ci.yml
name: ci
on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install -e ".[dev]"
      # catalog.db is not in CI — real-corpus/perf tests self-skip;
      # perf is excluded explicitly (hard wall-clock budgets need a
      # quiet reference machine, not a shared runner).
      - run: python -m pytest -q -m "not perf"
      - run: python -m mcp_server.export_tools --check
  install-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m venv /tmp/smoke && /tmp/smoke/bin/pip install .
      - run: /tmp/smoke/bin/legalize-bg-mcp --help
      - name: INDEX_MISSING preflight exits 2
        run: |
          set +e
          /tmp/smoke/bin/legalize-bg-mcp --db /tmp/nope.db --corpus /tmp
          rc=$?
          set -e
          test "$rc" -eq 2
```

- [ ] **Step 2: Verify locally what CI will run**

Run: `.venv/bin/python -m pytest -q -m "not perf"` → all pass, perf deselected.
Run: `.venv/bin/python -m mcp_server.export_tools --check` → `OK`.

- [ ] **Step 3: Commit, push, watch the first run**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: pytest (not perf) + tools.json parity + clean-venv install smoke (review 2026-07-02 P0: no CI existed)"
git push
gh run watch --exit-status
```

Expected: both jobs green. Fix-forward any runner-only failure (e.g. a test accidentally requiring the live catalog without a skip guard — add the skip, don't weaken the test).

---

### Task 16: Metrics reachability + metrics out of the DB lock

**Files:**
- Modify: `mcp_server/__main__.py` (SIGUSR1 dump), `mcp_server/server.py` (`_metrics_lock`)
- Create: `tests/mcp_server/test_metrics_signal.py`

**Interfaces:**
- Produces: `kill -USR1 <pid>` logs a JSON `metrics_snapshot` line (the only runtime observability channel over stdio); `handle._record` synchronized by its own `_metrics_lock` and executed OUTSIDE `_db_lock` (log I/O no longer holds the DB lock).

- [ ] **Step 1: Write the failing tests**

```python
# tests/mcp_server/test_metrics_signal.py
"""metrics_snapshot() was unreachable in production (never a tool, no
signal handler) — an operator had NO runtime observability over stdio
(review 2026-07-02 P1)."""

import json
import logging
import signal
import sqlite3
from pathlib import Path

from mcp_server.__main__ import _install_metrics_signal_handler
from mcp_server.server import build_app


def test_sigusr1_handler_logs_metrics_json(caplog):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    handle = build_app(conn, corpus_root=Path("."))
    handler = _install_metrics_signal_handler(handle)
    with caplog.at_level(logging.INFO, logger="mcp_server"):
        handler(signal.SIGUSR1, None)   # invoke directly — no real signal
    line = next(r for r in caplog.records if "metrics_snapshot" in r.message)
    payload = json.loads(line.message.split("metrics_snapshot: ", 1)[1])
    assert isinstance(payload, dict)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_metrics_signal.py -v`
Expected: FAIL — `ImportError: cannot import name '_install_metrics_signal_handler'`.

- [ ] **Step 3: Implement**

`mcp_server/__main__.py` — add:

```python
import json
import signal


def _install_metrics_signal_handler(handle):
    """SIGUSR1 → log the metrics snapshot as one JSON line. The stdio
    transport has no side channel, so a signal is the only way an
    operator can pull runtime metrics without killing the process
    (review 2026-07-02). Returns the handler for direct-call tests."""
    def _dump(signum, frame):
        log.info("metrics_snapshot: %s",
                 json.dumps(handle.metrics_snapshot(), ensure_ascii=False))
    try:
        signal.signal(signal.SIGUSR1, _dump)
    except (ValueError, OSError, AttributeError):
        pass  # non-main thread, or platform without SIGUSR1 (Windows)
    return _dump
```

and call it in `main()` right after `handle = build_app(...)`: `_install_metrics_signal_handler(handle)`.

`mcp_server/server.py` — give metrics their own lock and move recording/logging OUT of `_db_lock`: in `_AppHandle.__init__` add `self._metrics_lock = threading.Lock()`; in `_record` wrap the mutation in `with self._metrics_lock:`; in `_register`'s wrapper move the `finally:` block outside the `with _db_lock:` scope (structure: `t0 = ...` / `try:` / `with _db_lock: return fn(...)` / `except ... raise` / `finally: <record + log>`), and update both docstrings that currently claim metrics run inside `_db_lock`. Also import `threading` is already present.

- [ ] **Step 4: Run tests (incl. the concurrency stress + metrics suites)**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_metrics_signal.py tests/mcp_server/test_metrics.py tests/mcp_server/test_tools_e2e.py -q`
Expected: all PASS (the 16×20 concurrency test now also exercises the metrics lock).

- [ ] **Step 5: Commit**

```bash
git add mcp_server/__main__.py mcp_server/server.py tests/mcp_server/test_metrics_signal.py
git commit -m "feat(mcp): SIGUSR1 metrics dump; metrics move off the DB lock (review 2026-07-02)"
```

---

### Task 17: Operator docs truth + runbook parity test + repo hygiene

**Files:**
- Modify: `docs/runbook/2026-05-09-phase1b1-operator-setup.md`, `README.md`
- Create: `tests/mcp_server/test_runbook_parity.py`
- Delete: `HANDOVER.md`

**Interfaces:**
- Produces: runbook/README describing the REAL server (7 tools + Docker + guards); a parity test that fails when the runbook's tool table drifts from the live tool set (that's exactly how it went stale).

- [ ] **Step 1: Write the failing parity test**

```python
# tests/mcp_server/test_runbook_parity.py
"""The runbook's tool table drifted to 3 tools while the server grew to
7 (review 2026-07-02 P1) — lock it to the live tool set the same way
tools.json is locked."""

import re
from pathlib import Path

from mcp_server.export_tools import export_tool_schemas

RUNBOOK = Path("docs/runbook/2026-05-09-phase1b1-operator-setup.md")


def test_runbook_tool_table_matches_live_tools():
    live = {t["name"] for t in export_tool_schemas()["tools"]}
    text = RUNBOOK.read_text(encoding="utf-8")
    documented = set(re.findall(r"^\|\s*`(\w+)`", text, flags=re.M))
    assert documented == live, (
        f"runbook tool table out of date: documented={sorted(documented)} "
        f"live={sorted(live)}")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_runbook_parity.py -v`
Expected: FAIL — documented set has 3 entries, live has 7.

- [ ] **Step 3: Rewrite the runbook**

Update `docs/runbook/2026-05-09-phase1b1-operator-setup.md`: (a) tool table → all 7 tools, one `| \`name\` | one-line purpose |` row each (the parity test's regex keys on the backticked first column); (b) delete the stale "Phase 2+ deferred" claims — history/diff/amendments_in_period are live, `diff()`/`get_law(date)` return real history for multi-version acts; (c) add sections: Docker quick-start (copy the Dockerfile header's three commands), deploy-guard env vars (`LEGALIZE_CORPUS_DEFECTIVE` / `LEGALIZE_ALLOW_DEFECTIVE`), `--strict` staleness mode, incremental rebuild (`python -m index.build --incremental`), SIGUSR1 metrics dump (Task 16), and a "zero-downtime rebuild" note (rebuild to a temp DB path, `mv` over `catalog.db`, restart the server; a crashed in-place rebuild no longer empties the catalog per Task 1 but a *successful* in-place rebuild still races live readers). Update `README.md`'s tool list to all 7 + a one-line pointer to the runbook and Docker usage.

- [ ] **Step 4: Delete the stale stub**

```bash
git rm HANDOVER.md
```

(9-line redirect stub to ACTIVE.md, itself stale — ACTIVE.md is the session-startup entry per CLAUDE.md; the stub is noise.)

- [ ] **Step 5: Run tests + commit**

Run: `.venv/bin/python -m pytest tests/mcp_server/test_runbook_parity.py -q` → PASS.

```bash
git add docs/runbook/2026-05-09-phase1b1-operator-setup.md README.md tests/mcp_server/test_runbook_parity.py
git commit -m "docs(runbook): describe the real 7-tool/Docker server + parity test; drop stale HANDOVER stub (review 2026-07-02)"
```

---

### Task 18: Close-out — full verification + governance

**Files:**
- Modify: `docs/sync/ACTIVE.md`, `docs/sync/DECISIONS.md` (D-050 outcome note), `docs/frs/INDEX.md` (FR-027 → Done, FR-029 unchanged), `docs/research/2026-07-02-pre-ui-code-review.md` (disposition footnote)

- [ ] **Step 1: Full gates**

```bash
.venv/bin/python -m pytest -q -m "not perf"        # expect: all pass
.venv/bin/python -m pytest -q tests/perf            # quiet machine: 6/6 pass (post-D-051 budgets)
.venv/bin/python -m mcp_server.export_tools --check # OK, version=1.3.0
.venv/bin/python -m index.build --corpus . --db catalog.db && .venv/bin/python scripts/perf_probe.py
gh run watch --exit-status                          # CI green on the final push
```

- [ ] **Step 2: Live end-to-end smoke** — rerun the Task 8 Step 5 seven-tool client smoke against the rebuilt catalog; additionally call `get_article` with a paragraph on a Task-2-repaired act and eyeball the text: `get_article(law="naredba-3-ot-6-april-2004-g-za-izmervane-tonazha-na-morskite-korabi", article="чл. 10, ал. 1")` must contain the full sentence through "3 месеца" (previously truncated at "(1969)").

- [ ] **Step 3: Governance updates** — ACTIVE.md: hardening banner → done, next action = REST API plan (FR-028, Phase 7.1); DECISIONS: D-050 outcome note (all batches landed, D-051 cross-ref); FRS INDEX: FR-027 → Done with a one-line resolution + D-051 link.

- [ ] **Step 4: Commit**

```bash
git add docs/sync/ACTIVE.md docs/sync/DECISIONS.md docs/frs/INDEX.md docs/research/2026-07-02-pre-ui-code-review.md
git commit -m "docs(sync): pre-UI hardening complete — next: FR-028 REST API plan (D-050)"
```

---

## Deferred out of this plan (recorded, do NOT implement here)

- **FR-028 REST API (Phase 7.1)** — own plan, written after Batch B lands (design already exists: `docs/plans/2026-05-11-phase7-legislation-browser-design.md`). Reuses the query layer + error taxonomy this plan fixes; owns per-request connections, CORS, caching, `/metrics`.
- **FR-029 MCP per-call connection model** — replaces the global lock for true parallel MCP reads; only justified when a concurrent MCP fronting appears (the REST API does NOT reuse the MCP lock).
- **Acquisition robustness P1s** (bootstrap resume/idempotent-commit guard, dirty-tree preflight, `history_grew` shrinkage detection, bare-text `_walk` capture, probe-cap distinguishability) — attach to the FR-025 kickoff preflight; recorded in the review doc §4-5.
- **Batch C option (b)** (split body FTS index) — only if D-051's chosen option misses the web PRD 300 ms p95; needs a schema preflight.

## Self-review (skill checklist)

- **Spec coverage:** every P0 from the review doc → Tasks 1, 2, 5, 9, 10, 11; P0-3→1, P0-2→2, P0-1→5, P0-4→9, P0-5→10, P0-6→11; perf regression → 12-14; P1s: git-show/diff untested+unhandled → 6, dead codes → 6, output schemas → 8, invisible dir → 3, pre-1970 → 4, no CI → 15, metrics → 16, runbook/README → 17, lock scope → FR-029 (deferred, D-050), acquisition P1s → deferred (FR-025). P2s: input caps/dates → 7, HANDOVER.md → 17; remaining P2s recorded in review doc §5 only — deliberate.
- **Placeholder scan:** Tasks 10/11 contain two test bodies specified as contract-assertions against existing fixtures (the harness names live in the test modules; inventing them here would be wrong-by-construction). All other steps carry complete code/commands.
- **Type consistency:** `ToolError(code, payload)` used identically in Tasks 5-7; `_validate_date` signature consistent between definition (Task 7) and call sites; TypedDict names in Task 8 Step 3 = Step 4 annotations; `_install_metrics_signal_handler` defined (16 Step 3) = imported (16 Step 1).
