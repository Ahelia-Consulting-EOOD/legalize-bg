# FR-034 Unnumbered-Alinea Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore intra-article paragraph structure for pre-Указ-883 (1974) acts (ЗЗД class), make their unnumbered алинеи addressable via `get_article("чл. X, ал. N")`, and add a structural gate so paragraph-topology loss can never again pass silently.

**Architecture:** Three code changes on one feature branch (parser child-div fix → implicit-alinea extraction + wire-through → structural gate in report mode), then a full-corpus refetch sweep with `refresh.py` (per-act `[popravka]` commits), catalog rebuild, verification, governance. Evidence base: `docs/research/2026-07-31-unnumbered-alinea-structure-loss.md`.

**Tech Stack:** Python 3.12 (`.venv/bin/python`), BeautifulSoup, SQLite, pytest, FastMCP, FastAPI.

## Global Constraints

- Branch: all work on `fix/fr034-unnumbered-alineas` off `main`. NEVER commit to `main`.
- Test runner: `.venv/bin/python -m pytest` (system python3 is 3.9 and cannot import the code).
- Full gate per task: `.venv/bin/python -m pytest -m "not perf" -q` must be green before commit.
- Protected surfaces (preflight filed in §Preflight below): Surface 6 (index builder — additive column via migration, allowed), Surface 4 (SQLite — additive, no waiver), Surface 3 (MCP — additive response field + additive warning code only; tools.json `1.4.0` → `1.5.0`).
- Commit conventions: code commits use conventional prefixes (`fix:`, `feat:`, `test:`, `docs:`); corpus commits are produced by `refresh.py` (`[popravka]`/`[reforma]` with `Source-Id`/`Source-Date`/`Norm-Id` trailers) — never hand-write corpus commits.
- Bulgarian text in docs/messages uses „…“ quotes (U+201E/U+201C). No em-dashes in Bulgarian doc output.
- `catalog.db` is NOT tracked — rebuild locally, never `git add` it.
- Do not touch `docs/sync/SYNC-NOTICE-2026-07-07.md` or `.claude/CLAUDE.md` (separate owner-gated process).

---

## Preflight (IMPLEMENTATION-PREFLIGHT.md template, filled)

```
## Preflight: FR-034 unnumbered-alinea remediation

- protected surface: 3 (MCP), 4 (SQLite), 6 (index builder), plus fetcher/bg/text_parser.py (Surface 1 file)
- authoritative source: docs/process/IMPLEMENTATION-PREFLIGHT.md; design docs cited there
- hard constraint confirmed: yes — all changes additive: new provisions column via
  index/migrations.py (D-025 pattern), new optional response field `implicit` +
  new warning code IMPLICIT_ALINEA (additive per D-026), no signature changes,
  no field removals/renames; text_parser change alters OUTPUT fidelity only,
  interfaces unchanged (TextParser.convert signature intact)
- violation risk: regression of D-023 alinea rows (mitigated: baseline-vs-post
  rebuild-diff in Task 5 asserts no numbered-alinea rows lost); FTS asymmetry
  N/A (bg_normalize untouched)
- allowed scope confirmed: yes (additive column, additive field, additive warning)
- waiver required: no
- owner confirmation: ekimir / 2026-08-02 ("Perform all as planned")
- implementation may proceed: yes
```

---

### Task 1: Parser — child-div алинеи become Markdown paragraphs (Defect A)

**Files:**
- Modify: `fetcher/bg/text_parser.py:209-239` (`_extract_article_text`)
- Test: `tests/fetcher/bg/test_text_parser.py`

**Interfaces:**
- Consumes: existing `HtmlToMarkdown._block_text` (text_parser.py:155-182) — already implements the correct semantics (breaks on `<br>` AND `div/p/li/tr`, recursive walk, whitespace-normalized, `\n\n`-joined).
- Produces: `_extract_article_text(element) -> str` with identical signature; multi-child-div Article elements now yield blank-line-separated paragraphs. Tasks 2–6 rely on this output shape.

- [ ] **Step 1: Write the failing test** (append to `tests/fetcher/bg/test_text_parser.py`; mirror the style of `test_preserves_paragraph_structure` at line 77):

```python
def test_child_div_alineas_become_paragraphs():
    """Pre-Указ-883 acts (ЗЗД, ЗС, ЗН, ЗЛС) have unnumbered алинеи, each
    in its own child <div> of the Article element (verified against live
    lex.bg HTML for doc_id 2121934337, чл. 36 ЗЗД, 2026-07-31). They must
    become separate Markdown paragraphs, not be glued with spaces."""
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Едно лице може да представлява друго по разпоредба на закона или по волята на представлявания.</div>
        <div>Последиците от правните действия, които представителят извършва, възникват направо за представлявания.</div>
        <br/>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert blocks[0].startswith("**Чл. 36.**")
    assert blocks[0].endswith("представлявания.")
    assert "Последиците" not in blocks[0], "алинеи glued into one paragraph"
    assert blocks[1].startswith("Последиците")


def test_mixed_layout_br_inside_child_div():
    """A child div that itself contains <br>-separated runs must split on
    those too (belt-and-braces for mixed layouts)."""
    html = '''
    <div class="Article">
        <div><b>Чл. 5.</b> Първа алинея.<br/>Втора алинея.</div>
        <div>Трета алинея.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    md = HtmlToMarkdown().convert(soup)
    blocks = [b.strip() for b in md.split("\n\n") if b.strip()]
    assert len(blocks) == 3
    assert blocks[1] == "Втора алинея."
    assert blocks[2] == "Трета алинея."
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_text_parser.py -q`
Expected: the two new tests FAIL (glued output); all pre-existing tests PASS.

- [ ] **Step 3: Implement — delegate `_extract_article_text` to `_block_text`**

Replace the entire body of `_extract_article_text` (keep the method — external references and readability) with:

```python
    def _extract_article_text(self, element: Tag) -> str:
        """Extract article text, treating <br> AND child block elements as
        paragraph breaks.

        lex.bg uses two article layouts:
        - modern (post-Указ-883/1974) acts: numbered alineas ((1), (2), …)
          separated by <br> inside one Article element;
        - pre-1974 acts (ЗЗД, ЗС, ЗН, ЗЛС): unnumbered alineas, each its
          own child <div> of the Article element (FR-034 — the old code
          honored only <br>, silently gluing those алинеи into one flowed
          paragraph).
        `_block_text` already implements exactly these semantics for
        §-provisions (recursive walk, breaks on <br> and div/p/li/tr,
        blank-line-joined) — delegate to it so the rule lives in one place.
        """
        return self._block_text(element)
```

- [ ] **Step 4: Run the parser test file, then the full suite**

Run: `.venv/bin/python -m pytest tests/fetcher/bg/test_text_parser.py -q` → all PASS.
Run: `.venv/bin/python -m pytest -m "not perf" -q` → all PASS. If any coverage/cross-category test fails, READ the failure — `_block_text` normalizes NBSP runs; a fixture asserting the old space-glued output must be updated to the new (correct) paragraph-split expectation, with a comment referencing FR-034.

- [ ] **Step 5: Commit**

```bash
git add fetcher/bg/text_parser.py tests/fetcher/bg/test_text_parser.py
git commit -m "fix(parser): child-div алинеи become Markdown paragraphs (FR-034 Defect A)"
```

---

### Task 2: Provisions — accept unnumbered continuation paragraphs + implicit alinea rows (Defect B)

**Files:**
- Modify: `index/provisions.py` (dataclass, `_extract_article_blocks`, new `_split_implicit_alineas`, `parse`)
- Test: `tests/index/test_provisions.py`

**Interfaces:**
- Consumes: Task 1's markdown shape (unnumbered алинеи as separate paragraphs).
- Produces: `Provision` gains field `implicit: bool = False` (keyword-default; `export_cf/acts.py` imports `parse` — additive field must not break it). `parse()` emits, for marker-less multi-paragraph articles: the usual article-as-whole row PLUS one row per implicit alinea (`paragraph='1'`, `'2'`, …, `implicit=True`). Tasks 3–4 rely on `implicit` existing on every Provision.

**AMENDED 2026-08-02 after Task-1 execution evidence:** modern acts ALSO render точки/букви as child `<div>`s, so post-Task-1 markdown contains digit-leading (`1.`) and letter-leading paragraphs inside articles corpus-wide. A Cyrillic-only continuation rule recovers ~1% (measured on ЗОП). Tasks 1+2 are folded into ONE commit (the green-gate Global Constraint forbids committing Task 1 alone — it drops ЗОП indexed article text 425K→171K chars). Modern-act parity is the acceptance bar (see Step 4a).

**Design rules (encode exactly):**
1. While an article is open, EVERY no-anchor paragraph continues it EXCEPT the closers: structural headers (`#…`), PreHistory italics (`*…`), standalone gazette banners `^\(ОБН`, and annex starts (`^Приложение\s*№` or `^ПРИЛОЖЕНИЕ`) — without the annex closer, default-continue swallows appendix forms into the last article (measured: ППЗ-акцизи чл. 102б absorbed 86,503 chars of annexes). This default-continue rule restores pre-Task-1 article-body parity (точки `1.`/`2)`, букви `а)`, `(Изм. …)`-prefixed алинеи, and unnumbered алинеи all rejoin their article as separate paragraphs). Headings and the next `Чл. N.` anchor are the natural closers.
1a. Title-preamble glue (text_parser): article title preambles are separate child divs preceding the anchor div; post-fix they'd become separate paragraphs that `_extract_article_blocks` routes to the WRONG article (previous article's tail). In `_extract_article_text`, when the extracted lines have ≥2 entries, the FIRST line contains no `Чл. N.` anchor and the SECOND starts with `Чл.` — join them with a single space, reproducing the documented pre-FR-034 form („Title preamble Чл. N. …" in one paragraph; ЗОП has 261 such articles, ГПК 715).
2. Implicit splitting applies ONLY when `_split_alineas` found zero `(N)` markers AND the body has ≥ 2 paragraphs after merging: a paragraph starting with a sub-point marker — letter `а)`, `б)` … or digit `1.`/`1)` (max 2 digits) — belongs to the PRECEDING alinea (точки/букви are sub-units of an алинея, not new алинеи).
3. Implicit ал. 1 text = first paragraph with the `**Чл. N.**` anchor prefix stripped (mirrors numbered-alinea semantics: text after the marker).
4. `_block_text` purity (review round 1, Critical; second clause corrected by implementer bisect): the raw-string fallback must emit ONLY plain `NavigableString` — skip `Comment`, `Script`, `Stylesheet` bs4 subclasses (HEAD's `get_text()` excluded script/style; the `Script` skip alone zeroes the AdOcean payload). Tag skipping is restricted to `_INLINE_CHROME = {"buttons"}`: the other `CHROME_DENYLIST` classes are INLINE CITATION WRAPPERS inside Article elements (`NewDocReference` carries text in 2,212/2,214 occurrences and wraps the article anchor; `SameDocReference` 1,662/1,662; `contextads` 94/94) — skipping them deleted 485/745 ГПК articles in measurement. `CHROME_DENYLIST` remains correct at the `_walk` level only.
5. Implicit ал. 1 anchor strip must use the anchor MATCH END (search, not `^`-anchored sub) so it works for titled articles where rule 1a glued a preamble before `Чл. N.` (`„Предмет Чл. 1. Този кодекс…“` → ал. 1 text `„Този кодекс…“`).
6. Golden fixtures must include a REAL pre-1974 act: a trimmed ЗЗД HTML fixture (source: live-fetched lex.bg HTML, e.g. first ~40 articles incl. чл. 36) with explicit_rows=0, implicit_rows pinned, and a text spot-assert that чл. 36 ал. 2 starts with „Последиците“. Every fixture golden test also asserts NO provision text contains `ado.`, `javascript`, `function(`, or `<` (pollution tripwire).

- [ ] **Step 1: Write the failing tests** (append to `tests/index/test_provisions.py`):

```python
ZZD_STYLE_MD = """\
**Чл. 36.** Едно лице може да представлява друго по разпоредба на закона или по волята на представлявания.

Последиците от правните действия, които представителят извършва, възникват направо за представлявания.

**Чл. 37.** Еднолинейна разпоредба без втора алинея.

## ПРЕХОДНИ РАЗПОРЕДБИ

(ОБН. - ДВ, БР. 2 ОТ 1950 Г.)
"""


def test_implicit_alineas_for_markerless_multiparagraph_article():
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art36 = [r for r in rows if r.article == "36"]
    whole = [r for r in art36 if r.paragraph is None]
    alineas = [r for r in art36 if r.paragraph is not None]
    # article-as-whole keeps BOTH paragraphs (continuation accepted)
    assert len(whole) == 1
    assert "Последиците" in whole[0].text
    assert whole[0].implicit is False
    # two implicit alinea rows, position-numbered
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", True), ("2", True)]
    assert alineas[0].text.startswith("Едно лице")   # anchor stripped
    assert alineas[1].text.startswith("Последиците")


def test_single_paragraph_article_gets_no_implicit_rows():
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art37 = [r for r in rows if r.article == "37"]
    assert len(art37) == 1 and art37[0].paragraph is None


def test_obn_banner_not_swallowed_as_continuation():
    """Both closers must hold: the ## heading closes чл. 37, and a bare
    ^(ОБН banner with no intervening heading also closes an open article."""
    rows = parse(ZZD_STYLE_MD, law_id="zzd")
    art37 = [r for r in rows if r.article == "37"]
    assert "ОБН" not in art37[0].text
    md = ("**Чл. 5.** Първа алинея.\n\n"
          "(ОБН. - ДВ, БР. 2 ОТ 1950 Г.)\n")
    rows2 = parse(md, law_id="x")
    art5 = [r for r in rows2 if r.article == "5"]
    assert "ОБН" not in art5[0].text


def test_digit_tochki_continue_the_open_article():
    """Modern acts: точки arrive as their own paragraphs post-Task-1;
    they must stay in the article body and inside the right alinea."""
    md = ("**Чл. 12.** (1) Изисквания:\n\n"
          "1. първо изискване;\n\n"
          "2. второ изискване.\n\n"
          "(2) Втора алинея.\n")
    rows = parse(md, law_id="x")
    whole = [r for r in rows if r.article == "12" and r.paragraph is None]
    assert "второ изискване" in whole[0].text
    al1 = [r for r in rows if r.article == "12" and r.paragraph == "1"]
    assert "второ изискване" in al1[0].text and al1[0].implicit is False


def test_letter_points_merge_into_preceding_implicit_alinea():
    md = ("**Чл. 363.** Дружеството се прекратява:\n\n"
          "а) с постигане целта на дружеството;\n\n"
          "б) с изтичането на времето.\n\n"
          "Втора алинея след буквите.\n")
    rows = parse(md, law_id="zzd")
    alineas = [r for r in rows if r.article == "363" and r.paragraph is not None]
    assert [r.paragraph for r in alineas] == ["1", "2"]
    assert "б) с изтичането" in alineas[0].text
    assert alineas[1].text.startswith("Втора алинея")


def test_numbered_articles_unchanged_and_not_implicit():
    md = "**Чл. 1.** (1) Първа. (2) Втора.\n"
    rows = parse(md, law_id="x")
    alineas = [r for r in rows if r.paragraph is not None]
    assert [(r.paragraph, r.implicit) for r in alineas] == [("1", False), ("2", False)]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/index/test_provisions.py -q`
Expected: new tests FAIL (`implicit` attribute missing / rows absent); existing PASS.

- [ ] **Step 3: Implement in `index/provisions.py`**

(a) Dataclass — add the field with a default (last position, so existing positional constructions stay valid):

```python
@dataclass(frozen=True)
class Provision:
    law_id: str
    article: str
    paragraph: str | None
    text: str
    text_hash: str
    implicit: bool = False
```

(b) Continuation rule — replace `_looks_like_alinea_continuation` usage. Add below `_ALINEA_CONTINUATION_RE`:

```python
# FR-034: after the Task-1 parser fix, article content that lex.bg
# renders as child <div>s — unnumbered алинеи (pre-Указ-883 acts),
# точки ("1."), букви ("а)"), "(Изм. …)"-prefixed алинеи — arrives as
# separate plain paragraphs. While an article is open, everything
# continues it EXCEPT the named closers: '#' structural headers,
# '*' PreHistory italics, and standalone '(ОБН' gazette banners.
# Default-continue restores pre-FR-034 article-body parity (measured on
# ЗОП: the Cyrillic-only alternative lost 60% of indexed article text).
# High-recall by design (D-055 lesson) — corpus-wide validation via the
# structural gate + fr034_verify rebuild-diff.
_CONTINUATION_CLOSER_RE = re.compile(r"^(?:#|\*|\(ОБН|Приложение\s*№|ПРИЛОЖЕНИЕ)")
```

and in `_extract_article_blocks`, change the `n == 0` branch to:

```python
        elif n == 0:
            if pending_id is not None and not _CONTINUATION_CLOSER_RE.match(para):
                pending_parts.append(para)
            else:
                flush()
```

(the `_is_structural_header` early-continue at the top of the loop already
handles `#`; keep it — `_CONTINUATION_CLOSER_RE` makes the closure explicit
for `*` and `(ОБН` too).)

(c) Implicit splitter — add after `_split_alineas`:

```python
_SUBPOINT_RE = re.compile(r"^(?:[а-я]\)|\d{1,2}[а-я]?[\.\)])\s")  # 1. / 1) / 1а. / 57д.
_ANCHOR_PREFIX_RE = re.compile(r"^(?:\*\*)?Чл\.\s+\d+[а-я]?\.(?:\*\*)?\s*")


def _split_implicit_alineas(body: str) -> list[tuple[str, str]]:
    """Position-derived alineas for marker-less multi-paragraph articles
    (pre-Указ-883 acts: ЗЗД, ЗС, ЗН, ЗЛС…). ВКС cites their алинеи by
    paragraph position („чл. 36, ал. 2 ЗЗД“) even though the source text
    carries no (N) markers. Sub-points (букви а), б)… and точки 1., 2)…)
    merge into the preceding alinea — they subdivide an алинея, they do
    not start one.
    Returns [] for single-paragraph articles (no implicit ал. 1 row —
    mirrors numbered acts, where a marker-less article gets no rows)."""
    paras = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(body) if p.strip()]
    if len(paras) < 2:
        return []
    merged: list[str] = []
    for p in paras:
        if merged and _SUBPOINT_RE.match(p):
            merged[-1] = merged[-1] + "\n\n" + p
        else:
            merged.append(p)
    if len(merged) < 2:
        return []
    out: list[tuple[str, str]] = []
    for i, text in enumerate(merged, start=1):
        if i == 1:
            text = _ANCHOR_PREFIX_RE.sub("", text, count=1)
        out.append((str(i), text))
    return out
```

(d) Wire into `parse()` — replace the alinea loop:

```python
        explicit = _split_alineas(body)
        implicit_rows = [] if explicit else _split_implicit_alineas(body)
        for paragraph_id, alinea_text in explicit or implicit_rows:
            rows.append(Provision(
                law_id=law_id,
                article=article_id,
                paragraph=paragraph_id,
                text=alinea_text,
                text_hash=_hash(alinea_text),
                implicit=not explicit,
            ))
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/index/test_provisions.py tests/index/test_alinea_markers.py -q` → PASS. Golden fixtures policy (amended): UPDATE the golden shape to split `explicit_rows` / `implicit_rows`; `explicit_rows` is pinned at pre-FR-034 HEAD values EXACTLY except itemized verified recoveries (see 4a); `implicit_rows` are the new by-design values. Never fold explicit and implicit into one count — that is how silent loss gets ratified.
Run: `.venv/bin/python -m pytest -m "not perf" -q` → PASS (this also proves `export_cf/acts.py` consumers survive the additive field).

- [ ] **Step 4a: Modern-act parity check (acceptance bar for the fold).** Using the measurement method from the Task-1 report (parse fixture acts through the new pipeline), confirm on ЗОП, ГПК and ППЗ-акцизи: explicit alinea row counts ≥ pre-FR-034 HEAD (ЗОП 1,156 exactly; ГПК 1,486 / ППЗ 824 as floor), with EVERY excess row itemized in the report and individually verified as a recovery of text HEAD had lost (e.g. ППЗ чл. 102а/102б broken-markup drop, ГПК чл. 22а truncation); per-act summed article text within ±2% of HEAD once title-preamble glue (rule 1a) and the annex closer (rule 1) are in place. Record the numbers in the report.

- [ ] **Step 5: Commit (Tasks 1+2 folded — a lone Task-1 commit cannot pass the green gate)**

```bash
git add fetcher/bg/text_parser.py tests/fetcher/bg/test_text_parser.py index/provisions.py tests/index/test_provisions.py
git commit -m "fix(parser,provisions): preserve child-div paragraph structure + implicit alineas for pre-1974 acts (FR-034 A+B)"
```

---

### Task 3: Wire `implicit` through DB → MCP → REST (additive)

**Files:**
- Modify: `index/migrations.py` (migration 006), `index/build.py:322-329` (INSERT), `mcp_server/queries.py:513-537` (SELECT + row dict), `mcp_server/schemas.py:93-104,216-224` (dataclass + TypedDict), `mcp_server/server.py` (get_article response construction + IMPLICIT_ALINEA warning), `mcp_server/export_tools.py:46` (version `1.5.0` + changelog comment), `api/routes/laws.py:71-80` (response key)
- Regenerate: `tools.json`, `docs/api/openapi-rest.json`
- Test: `tests/index/test_migrations.py`, `tests/mcp_server/` (find the get_article test file via `grep -rln "get_article" tests/mcp_server/`), `tests/api/` equivalent

**Interfaces:**
- Consumes: `Provision.implicit` from Task 2.
- Produces: `provisions.implicit INTEGER NOT NULL DEFAULT 0` column; `GetArticleResponse.implicit: bool = False`; warning `{code: "IMPLICIT_ALINEA"}` on implicit-alinea responses; REST article payload gains `"implicit"`. Task 4's gate and Task 5's sweep queries rely on the column.

- [ ] **Step 1: Failing tests.** (1) In `tests/index/test_migrations.py`, mirror an existing migration test: apply migrations to a fresh DB, assert `implicit` in `PRAGMA table_info(provisions)` names. (2) In the mcp get_article test file: build a catalog from `ZZD_STYLE_MD` (reuse that file's fixture pattern for making a test catalog), call `get_article("zzd", "чл. 36, ал. 2")`, assert `paragraph == "2"`, `implicit is True`, and `any(w["code"] == "IMPLICIT_ALINEA" for w in warnings)`; call `чл. 36` whole → `implicit is False`, no such warning. Run: expected FAIL.

- [ ] **Step 2: Migration 006** — append to `MIGRATIONS` following the existing entries' exact shape:

```python
    Migration(
        version=6,
        name="provisions_implicit_column",
        sql="ALTER TABLE provisions ADD COLUMN implicit INTEGER NOT NULL DEFAULT 0;",
    ),
```

(Also add `implicit INTEGER NOT NULL DEFAULT 0` to the CREATE TABLE in `index/catalog.py:41` area so fresh DBs match migrated ones — mirror how the `text` column (migration 001) is handled there; follow whichever pattern `catalog.py` already uses for it.)

- [ ] **Step 3: INSERT** in `index/build.py`:

```python
        conn.execute(
            """INSERT INTO provisions
               (law_id, article, paragraph, valid_from, text, text_hash, implicit)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (prov.law_id, prov.article, prov.paragraph,
             effective, prov.text, prov.text_hash, int(prov.implicit)),
        )
```

- [ ] **Step 4: Query + schemas + server + REST.**
  - `queries.py` article_lookup SELECT: `SELECT article, paragraph, text, text_hash, valid_from, valid_to, implicit FROM provisions …` (leave the `articles_lookup` SELECT (ranges) untouched — it serves whole-article rows where implicit is always 0). AMENDED (review round 1): `get_articles`' single-alinea path reuses `article_lookup` and MUST carry the same signal — add `implicit: bool = False` to `ArticleEntry` (dataclass + TypedDict), populate via `bool(r.get("implicit", 0))`, and append the IMPLICIT_ALINEA warning on that path too; the REST article route also appends the same warning dict (peer-of-MCP parity).
  - `schemas.py`: add `implicit: bool = False` to `GetArticleResponse` (after `commit_hash`, before `warnings`) and `implicit: bool` to `GetArticleResponseDict`.
  - `server.py` get_article: pass `implicit=bool(row.get("implicit", 0))` when building the response; when true, append to warnings:

```python
            warnings.append({
                "code": "IMPLICIT_ALINEA",
                "message": ("Алинеята е изведена по позиция: актът е отпреди "
                            "Указ № 883/1974 и алинеите му не са номерирани в "
                            "оригиналния текст. / Alinea number derived from "
                            "paragraph position: pre-1974 act, alineas are "
                            "unnumbered in the source text."),
            })
```

  - `api/routes/laws.py`: add `"implicit": bool(row["implicit"]),` next to the existing `"paragraph"` key.
  - `export_tools.py`: bump `TOOLS_JSON_VERSION = "1.5.0"` and add a changelog comment line `# 1.4.0 → 1.5.0: ADDITIVE get_article field `implicit` + warning code IMPLICIT_ALINEA (FR-034)`.

- [ ] **Step 5: Regenerate contracts and run everything.**

```bash
.venv/bin/python -m mcp_server.export_tools
.venv/bin/python -m api.export_openapi
.venv/bin/python -m pytest -m "not perf" -q
```

All green, including the `--check` parity tests. If `api.export_openapi` has a `--check` flag pattern in CI, regenerate the committed artifact the same way the FR-032 session did (see `.github/workflows/ci.yml` for the exact check commands and satisfy them).

- [ ] **Step 6: Commit**

```bash
git add index/migrations.py index/catalog.py index/build.py mcp_server/ api/ tools.json docs/api/openapi-rest.json tests/
git commit -m "feat(mcp,rest): additive implicit-alinea surface — migration 006, get_article implicit flag + IMPLICIT_ALINEA warning, tools.json 1.5.0 (FR-034)"
```

---

### Task 4: Structural gate — paragraph-topology check (report mode)

**Files:**
- Modify: `fetcher/bg/coverage.py` (new function `structure_mismatches`), `bootstrap.py` + `refresh.py` (record results into the gate record; consult `make_gate_record` signature in coverage.py and extend additively)
- Test: `tests/fetcher/bg/test_coverage.py`

**Interfaces:**
- Consumes: `content_region`, `CLASS_MAP` conventions from text_parser/coverage.
- Produces: `structure_mismatches(soup, markdown) -> list[dict]` — one dict `{"article": str, "expected_blocks": int, "got_blocks": int}` per Article element whose source block count exceeds its markdown paragraph count. REPORT mode only this cycle: results recorded in `gate-report.json` under key `structure_mismatches`; enforcement (hard-fail) is a deliberate flip AFTER the Task-6 sweep proves corpus-wide cleanliness (gate-first discipline: run the check continuously before making it strict).

- [ ] **Step 1: Failing tests** (append to `tests/fetcher/bg/test_coverage.py`):

```python
def test_structure_mismatch_detects_flattened_alineas():
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    flattened_md = "**Чл. 36.** Първа алинея текст. Втора алинея текст.\n"
    mismatches = structure_mismatches(soup, flattened_md)
    assert mismatches == [
        {"article": "36", "expected_blocks": 2, "got_blocks": 1}]


def test_structure_mismatch_clean_when_paragraphs_preserved():
    html = '''
    <div class="Article">
        <div><b>Чл. 36.</b> Първа алинея текст.</div>
        <div>Втора алинея текст.</div>
    </div>
    '''
    soup = BeautifulSoup(html, "lxml")
    good_md = "**Чл. 36.** Първа алинея текст.\n\nВтора алинея текст.\n"
    assert structure_mismatches(soup, good_md) == []
```

- [ ] **Step 2: Implement** in `fetcher/bg/coverage.py` (self-contained — coverage.py must NOT import from `index/` (Ahelia-private vs upstream-PR layering); duplicate the tiny anchor regex with a cross-reference comment):

```python
# Article anchor, duplicated from index/provisions.py by design —
# fetcher/bg/ ships upstream without the Ahelia-private index/ package.
_STRUCT_ARTICLE_RE = re.compile(r"(?:\*\*)?Чл\.\s+(\d+[а-я]?)\.")

_BLOCK_CHILD_TAGS = ("div", "p")


def structure_mismatches(soup: BeautifulSoup, markdown: str) -> list[dict]:
    """Paragraph-topology check (FR-034): every Article element whose
    source has N>=2 Cyrillic-bearing child block elements must map to a
    markdown article block with at least N blank-line-separated
    paragraphs. Text-presence coverage (uncovered_legal_text) is
    structure-blind — flattened алинеи preserve every character; this
    check closes that blind spot. REPORT mode: callers record the list;
    enforcement is a separate, later decision (D-058)."""
    region, _ = content_region(soup)

    # Markdown side: article number -> paragraph count of its block
    # (anchor paragraph up to the next anchored/header paragraph).
    md_counts: dict[str, int] = {}
    current: str | None = None
    for para in re.split(r"\n\n+", markdown):
        para = para.strip()
        if not para:
            continue
        m = _STRUCT_ARTICLE_RE.match(para)
        if para.startswith("#"):
            current = None
            continue
        if m:
            current = m.group(1)
            # first occurrence wins — quoted anchors in ПЗР (FR-030
            # family) must not overwrite the real article's count
            if current in md_counts:
                current = None
                continue
            md_counts[current] = 1
        elif current is not None:
            md_counts[current] += 1

    out: list[dict] = []
    for el in region.find_all("div", class_="Article"):
        blocks = [
            c for c in el.children
            if isinstance(c, Tag) and c.name in _BLOCK_CHILD_TAGS
            and _CYR.search(c.get_text())
        ]
        if len(blocks) < 2:
            continue
        m = _STRUCT_ARTICLE_RE.search(el.get_text())
        if not m:
            continue
        art = m.group(1)
        got = md_counts.get(art, 0)
        if got < len(blocks):
            out.append({"article": art,
                        "expected_blocks": len(blocks),
                        "got_blocks": got})
    return out
```

- [ ] **Step 3: Record in the gate report.** In `bootstrap.py` and `refresh.py`, at the point where `uncovered_legal_text(soup, body)` is called, also compute `structure_mismatches(soup, body)` and attach it to the per-act gate record (extend `make_gate_record` additively or add the key next to where the gate dict is assembled — follow the existing shape in the code; REPORT only, never block the write on it this cycle).

- [ ] **Step 4: Run tests**

`.venv/bin/python -m pytest tests/fetcher/bg/ -q` then full `-m "not perf"` → PASS.

- [ ] **Step 5: Commit**

```bash
git add fetcher/bg/coverage.py bootstrap.py refresh.py tests/fetcher/bg/test_coverage.py
git commit -m "feat(gate): structural paragraph-topology check, report mode (FR-034)"
```

---

### Task 5: Pre-sweep baseline + verification script

**Files:**
- Create: `scripts/fr034_verify.py`
- Test: manual run (script is itself the verifier; it must exit non-zero on failure)

**Interfaces:**
- Consumes: `catalog.db` (pre-sweep state), rebuilt catalog (post-sweep).
- Produces: `scripts/fr034_verify.py baseline` writes `.fr034-baseline.json` (git-ignored path is fine — do NOT commit it); `scripts/fr034_verify.py check` exits 0/1. Task 6's sweep agent runs both.

- [ ] **Step 1: Write the script:**

```python
"""FR-034 sweep verification.

`baseline`: snapshot per-law numbered-alinea row counts + article counts
from the CURRENT catalog.db (pre-sweep).
`check`: after the sweep + rebuild, assert:
  R1  no law lost numbered (explicit) alinea rows vs baseline
      (implicit=0, paragraph NOT NULL counts per law_id, current rows only);
  R2  no law lost articles vs baseline (current article-as-whole rows);
  R3  ЗЗД spot-checks: чл. 36 has implicit rows ал.1+ал.2; ал.2 text
      starts with 'Последиците'; чл. 36 whole text contains BOTH a
      blank-line separator and 'Последиците' (structure preserved);
  R4  зakon-za-sobstvenostta has >0 implicit rows;
  R5  corpus-wide: no provisions row has implicit=1 AND a paragraph value
      that also exists with implicit=0 for the same (law_id, article)
      at the same valid_from (explicit/implicit never mix in one article).
Failures print a per-law diff and exit 1.
"""
import json, sqlite3, sys

DB = "catalog.db"
BASELINE = ".fr034-baseline.json"

CURRENT = "valid_to IS NULL"


def _counts(conn):
    q = f"""SELECT law_id,
                   SUM(paragraph IS NOT NULL AND implicit = 0) AS explicit_alineas,
                   SUM(paragraph IS NULL) AS articles
              FROM provisions WHERE {CURRENT} GROUP BY law_id"""
    return {r[0]: {"explicit_alineas": r[1] or 0, "articles": r[2] or 0}
            for r in conn.execute(q)}


def baseline():
    conn = sqlite3.connect(DB)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(provisions)")]
    if "implicit" not in cols:  # pre-migration baseline: all rows explicit
        q = f"""SELECT law_id, SUM(paragraph IS NOT NULL), SUM(paragraph IS NULL)
                  FROM provisions WHERE {CURRENT} GROUP BY law_id"""
        data = {r[0]: {"explicit_alineas": r[1] or 0, "articles": r[2] or 0}
                for r in conn.execute(q)}
    else:
        data = _counts(conn)
    json.dump(data, open(BASELINE, "w"))
    print(f"baseline: {len(data)} laws -> {BASELINE}")


def check():
    base = json.load(open(BASELINE))
    conn = sqlite3.connect(DB)
    now = _counts(conn)
    failures = []
    for law, b in base.items():
        n = now.get(law)
        if n is None:
            failures.append(f"R2 {law}: law vanished from catalog")
            continue
        if n["explicit_alineas"] < b["explicit_alineas"]:
            failures.append(
                f"R1 {law}: explicit alineas {b['explicit_alineas']} -> "
                f"{n['explicit_alineas']}")
        if n["articles"] < b["articles"]:
            failures.append(
                f"R2 {law}: articles {b['articles']} -> {n['articles']}")
    zzd = "zakon-za-zadalzheniyata-i-dogovorite"
    rows = conn.execute(
        f"""SELECT paragraph, implicit, text FROM provisions
            WHERE law_id=? AND article='36' AND {CURRENT}
            ORDER BY paragraph IS NULL DESC, paragraph""", (zzd,)).fetchall()
    al = {p: (i, t) for p, i, t in rows if p is not None}
    whole = [t for p, i, t in rows if p is None]
    if set(al) != {"1", "2"} or not all(i for i, _ in al.values()):
        failures.append(f"R3 ЗЗД чл.36 alinea rows wrong: {sorted(al)}")
    elif not al["2"][1].startswith("Последиците"):
        failures.append("R3 ЗЗД чл.36 ал.2 text wrong")
    if not whole or "\n\n" not in whole[0] or "Последиците" not in whole[0]:
        failures.append("R3 ЗЗД чл.36 whole-article structure not preserved")
    zs = conn.execute(
        f"""SELECT COUNT(*) FROM provisions
            WHERE law_id='zakon-za-sobstvenostta' AND implicit=1
            AND {CURRENT}""").fetchone()[0]
    if zs == 0:
        failures.append("R4 ЗС has no implicit alinea rows")
    # R5 scope (review round 1): restrict to single-anchor articles. Laws
    # carrying a quoted ПЗР copy of an article (FR-030 family, e.g.
    # zakon-za-patishtata чл. 8) legitimately produce explicit rows from
    # the real block and implicit rows from the quoted block — 277 such
    # collisions exist corpus-wide and are FR-030's remit, not FR-034's.
    # With the duplicate-anchor exclusion the residual is exactly 0.
    mixed = conn.execute(
        f"""SELECT COUNT(*) FROM provisions a JOIN provisions b
            ON a.law_id=b.law_id AND a.article=b.article
            AND a.valid_from=b.valid_from AND a.paragraph=b.paragraph
            WHERE a.implicit=1 AND b.implicit=0
            AND (SELECT COUNT(*) FROM provisions w
                 WHERE w.law_id=a.law_id AND w.article=a.article
                   AND w.valid_from=a.valid_from
                   AND w.paragraph IS NULL) = 1""").fetchone()[0]
    if mixed:
        failures.append(f"R5 {mixed} mixed explicit/implicit paragraph pairs")
    if failures:
        print("FR-034 VERIFY FAIL:")
        for f in failures[:50]:
            print(" -", f)
        sys.exit(1)
    print(f"FR-034 VERIFY OK ({len(now)} laws)")


if __name__ == "__main__":
    {"baseline": baseline, "check": check}[sys.argv[1]]()
```

- [ ] **Step 2: Run `baseline` NOW (against the pre-sweep catalog.db) and confirm it writes the JSON.** `.venv/bin/python scripts/fr034_verify.py baseline`

- [ ] **Step 3: Commit the script (not the baseline JSON):**

```bash
git add scripts/fr034_verify.py
git commit -m "test(fr034): sweep verification script — baseline/check for alinea-row invariants"
```

---

### Task 6: Full-corpus refetch sweep + rebuild + verification (SONNET agent, background)

**Owner constraint: this task runs on a Sonnet (or Opus) subagent — NOT Fable — to save tokens. It is deliberately mechanical: every judgment call routes back to the orchestrator.**

**Files:** corpus `.md` files (via `refresh.py` only — never hand-edit), `catalog.db` (untracked rebuild), `docs/research/2026-08-02-fr034-sweep-report.md` (new).

**Interfaces:**
- Consumes: Tasks 1–5 committed on `fix/fr034-unnumbered-alineas`.
- Produces: per-act `[popravka]`/`[reforma]` commits from refresh.py; rebuilt catalog; sweep report with quantification (acts changed, structure mismatches before/after, implicit-row counts per act); `fr034_verify.py check` green.

- [ ] **Step 1:** Confirm on branch `fix/fr034-unnumbered-alineas`, working tree clean, `.fr034-baseline.json` exists.
- [ ] **Step 2:** Run the sweep: `.venv/bin/python refresh.py --output . 2>&1 | tee refresh-fr034.log` (all categories; the resume checkpoint `.refresh-state.json` makes re-runs safe). On a Cloudflare halt: STOP and report to the orchestrator — cookie minting is interactive and happens in the main session (D-047 path: `--cookie-file` + Playwright-minted `cf_clearance`); do not improvise fetch workarounds.
- [ ] **Step 3:** On DNS/socket errors for individual acts (D-047 precedent): delete the `error` entries from `.refresh-state.json` and re-run the same command once; if errors persist, report the act list instead of retrying further.
- [ ] **Step 4:** Rebuild the catalog: find the exact rebuild command with `.venv/bin/python -m index.build --help` (full rebuild mode) and run it against `catalog.db`; then `.venv/bin/python -m pytest -m "not perf" -q` → must be green.
- [ ] **Step 5:** `.venv/bin/python scripts/fr034_verify.py check` → must print OK. If it fails: report the failure list verbatim; do NOT attempt fixes.
- [ ] **Step 6:** Quantify and write `docs/research/2026-08-02-fr034-sweep-report.md`: number of acts with commits this sweep (from `git log --oneline` since the sweep started, split by `[popravka]`/`[reforma]`); `structure_mismatches` totals from `gate-report.json` (should be ~0 — any non-zero rows listed verbatim); SQL: `SELECT COUNT(DISTINCT law_id), COUNT(*) FROM provisions WHERE implicit=1;` and top-10 acts by implicit rows; ЗЗД/ЗС/ЗН/ЗЛС per-act implicit counts vs the research doc's predictions (184/…, 49/97, 17/166).
- [ ] **Step 7:** Commit the report: `git add docs/research/2026-08-02-fr034-sweep-report.md && git commit -m "docs(fr034): sweep quantification report"`.

---

### Task 6b: Structure-aware change classifier + targeted re-sweep (ADDED 2026-08-03 after sweep run 1)

**Root cause (verified):** `refresh.py:238` `normalize_for_compare` collapses ALL whitespace → structure-only improvements classify as `unchanged` and are never written. ЗЗД (byte-identical skip, R3 red), ЗН (implicit 0), ЗС (2) are in this class; the 496+99 written acts carry the new structure (207 laws / 18,488 implicit rows).

**Files:** Modify `refresh.py` (`normalize_for_compare`), test `tests/` (find refresh classifier tests via `grep -rln classify_change tests/`).

- [ ] TDD: failing test — two texts differing only by `"a b"` vs `"a\n\nb"` must classify as `popravka`; texts differing only by space RUNS or quote variants stay `unchanged`.
- [ ] Implement: preserve paragraph boundaries in `normalize_for_compare` — collapse horizontal whitespace runs to one space, collapse `\n{2,}` (with optional surrounding spaces) to a canonical `\n\n` token, single `\n` to space, quotes as today. Docstring: cite FR-034 sweep run 1 (ЗЗД skipped as `unchanged` because the classifier was structure-blind — the third instance of the text-presence blind-spot class).
- [ ] Full gate green; commit `fix(refresh): structure-aware change classification — paragraph breaks are real changes (FR-034)`.
- [ ] Re-sweep: back up CURRENT `.refresh-state.json` (sweep run 1) into the SDD workspace, clear it, re-run `refresh.py --output .` (run 2, background, same CF/DNS protocol). Already-restructured acts byte-match → `unchanged`; the skipped class now lands as `[popravka]`. Rebuild catalog; `pytest -m "not perf"`; `fr034_verify.py check`.
- [ ] Expected: R3 green (ЗЗД чл. 36 → implicit ал. 1+2); ЗЗД implicit ≈ 400+ (184 multi-div articles), ЗН/ЗС substantial; re-run the Task-6 census + write the sweep report (both runs described, both state backups named).

### Task 6c: Verify-red adjudication + implicit-row sampling (ADDED 2026-08-03)

- [ ] R1 false-positive check (Наредба № 69, ЗФСАКМ — both `[reforma]`): confirm via `git show` of their sweep commits + amendment_history that removed alineas correspond to real ДВ amendments (whitespace-normalize before grepping quotes — line-wrapped citations produce false refutations). If yes: record as baseline-vs-amendment false positives; note in the sweep report; `fr034_verify.py` needs no change (baseline refresh post-merge resolves).
- [ ] R1/R2 `[popravka]` suspects (ЗЖТ 425→424 explicit; Наредба № 5/1999 44→43 articles): `git show` their sweep diffs; determine parser-artifact vs genuine lex.bg change. Parser artifact → fix round; genuine → document.
- [ ] Sample the 18,488 implicit rows: SQL stratified sample (~30 rows across ≥15 laws, mix of categories) + read each against its act; classify real-алинея vs artifact (точки shapes `_SUBPOINT_RE` misses, ДР definitions, quoted-ЗИД). >10% artifacts → fix round before Task 7; else document rate in sweep report.
- [ ] 51 post-sweep structure mismatches (from run-2 census): list the acts, classify layouts, register residuals in the sweep report (fix in FR-030/FR-034 follow-up, not this branch).

### Task 7: Governance + PR

**Files:**
- Modify: `docs/frs/INDEX.md` (FR-034 row; FR-030 row annotation for Defect C), `docs/sync/DECISIONS.md` (D-058), `docs/sync/ACTIVE.md` (banner), `docs/data/schema-reference.md` (provisions.implicit column row + paragraph-semantics note)
- Commit: `docs/research/2026-07-31-unnumbered-alinea-structure-loss.md`, `docs/plans/2026-08-02-fr034-unnumbered-alinea-remediation.md`

- [ ] **Step 1:** FR-034 row (follow the table's exact column format): unnumbered-alinea structure loss — Defects A/B fixed this cycle (parser child-div flush; implicit position-based rows, D-058), structural gate in REPORT mode, sweep executed; link both research docs. FR-030 row: append one sentence — „FR-034's ЗЗД sweep confirmed the article-level variant: quoted ПЗР insertions (чл. 1001а–г от стария ЗГС) adopted as ЗЗД articles; fold article-anchor discrimination into this FR's reasoning pipeline."
- [ ] **Step 2:** D-058 row: implicit-alinea model (position-derived, `implicit` column + IMPLICIT_ALINEA warning, letter-point merge rule, single-paragraph articles get no rows); structural gate lands REPORT-mode first, hard-fail flip is a follow-up decision once the sweep shows clean corpus (gate-first); tools.json 1.5.0.
- [ ] **Step 3:** ACTIVE.md: new top banner (✅ FR-034 …) following the existing banner style, including the sweep numbers from the Task-6 report.
- [ ] **Step 4:** `docs/data/schema-reference.md`: add `implicit` row to the provisions column table; amend the `paragraph` row: „NULL if the provision is the entire article. For pre-1974 acts alinea numbers are position-derived (implicit=1, D-058)."
- [ ] **Step 5:** Full suite one last time; commit docs; push; open PR:

```bash
.venv/bin/python -m pytest -m "not perf" -q
git add docs/
git commit -m "docs(fr034): governance — FR-034/D-058, FR-030 annex, schema reference, research + plan docs"
git push -u origin fix/fr034-unnumbered-alineas
gh pr create --title "FR-034: unnumbered-alinea structure restoration (ЗЗД class) + implicit alinea rows + structural gate + corpus sweep" --body "..."
```

PR body: summary of the three defects, the fix architecture, sweep numbers, verification evidence (fr034_verify OK, suite green, structural mismatches 0), preflight note (all additive), per-area diff framing (~525 code lines to review; corpus commits machine-generated + gate-validated), and the standard generated-with footer.

**MERGE MODE (owner-confirmed 2026-08-03): merge commit of the whole branch — NEVER squash.** D-047 precedent: the per-act `[popravka]`/`[reforma]` commits carry `Source-Id`/`Source-Date`/`Norm-Id` trailers and `GIT_AUTHOR_DATE`, which the FR-020 time-machine derives version boundaries from; a squash collapses 617 provenance commits and breaks version derivation. State this in the PR body so it isn't merged wrong from the GitHub UI (default UI button may be squash).

---

## Self-Review Notes

- Spec coverage: Defect A → Task 1; Defect B (both halves: continuation acceptance + implicit numbering) → Task 2; wire-through → Task 3; structural gate → Task 4 (report-mode, flip deferred by design); sweep + quantification → Tasks 5–6; Defect C → governance annotation only (Task 7, by design — FR-030 reasoning track owns it); governance → Task 7. ✔
- Type consistency: `Provision.implicit: bool` (Task 2) ↔ `int(prov.implicit)` INSERT (Task 3) ↔ `implicit INTEGER` column ↔ `bool(row["implicit"])` at the API edges. ✔
- Known intentional deferrals: structural-gate hard-fail flip (post-sweep decision, D-058); `get_articles`/range responses unchanged; implicit rows for single-paragraph articles deliberately NOT emitted.
