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
      NB чл. 36 currently has a single anchor; if ЗЗД ever gains a
      duplicate чл. 36 anchor the last-wins dict and whole[0] pick
      become order-fragile;
  R4  зakon-za-sobstvenostta has >0 implicit rows;
  R5  corpus-wide: no provisions row has implicit=1 AND a paragraph value
      that also exists with implicit=0 for the same (law_id, article)
      at the same valid_from (explicit/implicit never mix in one article),
      excluding duplicate-anchor articles (see the R5 comment below).
Failures print a per-law diff and exit 1.

`article-baseline` / `article-check`: the same pair keyed one level
finer, on (law_id, article) — D-058 (iv), mechanism 5 of the
anchor-integrity assurance chain. R1/R2 above are per-LAW aggregates,
so an article that LOSES rows is silently cancelled by another article
of the same act that GAINS them; a real defect hid exactly that way in
8 of the 9 acts it affected and surfaced only because the ninth had no
offsetting gain. Keyed per article, a loss cannot be offset:
  A1  an article lost explicit alinea rows vs baseline;
  A2  something in the baseline is ABSENT now — an article (or, in one
      summary line, a whole law) that the baseline recorded no longer
      exists in the catalog;
  A3  an article lost whole-article (anchor) rows vs baseline, i.e. it
      still exists but with fewer anchors than before.
A2 is the line the repair sweep's review step greps for: after the
sweep every removed phantom article shows up as an A2, and each one is
adjudicated by hand. A2 is therefore expected to be non-empty after a
repair — the net is there so nothing REAL vanishes unnoticed alongside
the phantoms, not to force the list to zero.

Both `baseline` and `article-baseline` REFUSE to overwrite an existing
baseline file (set `FR034_FORCE=1` to replace it deliberately): the
pre-sweep floor cannot be recomputed once the corpus has been swept and
the catalog rebuilt, and each is one habit-typo away from its `check`.

MUST be run from the repo root: DB and BASELINE are relative paths, so
elsewhere sqlite3 silently creates an empty db and check fails non-zero
but confusingly (mass R2 'law vanished' rather than a real regression).
"""
import json, os, sqlite3, sys

DB = "catalog.db"
BASELINE = ".fr034-baseline.json"
ARTICLE_BASELINE = ".article-baseline.json"

CURRENT = "valid_to IS NULL"


def _counts(conn):
    q = f"""SELECT law_id,
                   SUM(paragraph IS NOT NULL AND implicit = 0) AS explicit_alineas,
                   SUM(paragraph IS NULL) AS articles
              FROM provisions WHERE {CURRENT} GROUP BY law_id"""
    return {r[0]: {"explicit_alineas": r[1] or 0, "articles": r[2] or 0}
            for r in conn.execute(q)}


def _article_counts(conn):
    """`_counts` with (law_id, article) as the key instead of law_id —
    the SAME two quantities, one level finer. `explicit_alineas` stays
    'numbered alinea rows the parser marked explicit'; `articles` stays
    'whole-article rows' (paragraph IS NULL), which per article is that
    article's anchor multiplicity: 1 normally, >1 where the act carries
    a duplicate anchor. Returned nested, {law_id: {article: {...}}}, so
    it serialises to JSON as directly as `_counts` does."""
    q = f"""SELECT law_id, article,
                   SUM(paragraph IS NOT NULL AND implicit = 0) AS explicit_alineas,
                   SUM(paragraph IS NULL) AS articles
              FROM provisions WHERE {CURRENT} GROUP BY law_id, article"""
    out = {}
    for law, article, alineas, articles in conn.execute(q):
        out.setdefault(law, {})[article] = {
            "explicit_alineas": alineas or 0, "articles": articles or 0}
    return out


def baseline():
    # The baseline is the PRE-SWEEP floor: once the sweep has rewritten
    # the corpus and catalog.db has been rebuilt, it cannot be recomputed
    # from anything on disk. `baseline` is one habit-typo away from
    # `check`, so refuse to clobber an existing file.
    if os.path.exists(BASELINE) and os.environ.get("FR034_FORCE") != "1":
        sys.exit(
            f"refusing to overwrite the existing baseline {BASELINE} — it "
            "is the irreplaceable pre-sweep floor and cannot be recomputed "
            "after a rebuild. Did you mean `check`? To replace it "
            "deliberately: FR034_FORCE=1 python scripts/fr034_verify.py "
            "baseline")
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


def article_baseline():
    # Same irreplaceability, same habit-typo risk as `baseline` — see the
    # comment there. This one is the quantity regression net for the
    # repair sweep, so it must be captured from the corpus as it stands
    # PRE-repair.
    if os.path.exists(ARTICLE_BASELINE) and os.environ.get("FR034_FORCE") != "1":
        sys.exit(
            f"refusing to overwrite the existing baseline "
            f"{ARTICLE_BASELINE} — it is the irreplaceable pre-sweep "
            "per-article floor and cannot be recomputed after a rebuild. "
            "Did you mean `article-check`? To replace it deliberately: "
            "FR034_FORCE=1 python scripts/fr034_verify.py article-baseline")
    conn = sqlite3.connect(DB)
    data = _article_counts(conn)
    json.dump(data, open(ARTICLE_BASELINE, "w"))
    pairs = sum(len(a) for a in data.values())
    print(f"article baseline: {len(data)} laws, {pairs} articles -> "
          f"{ARTICLE_BASELINE}")


def article_check():
    base = json.load(open(ARTICLE_BASELINE))
    conn = sqlite3.connect(DB)
    now = _article_counts(conn)
    failures = []
    for law, arts in base.items():
        n_law = now.get(law)
        if n_law is None:
            # one summary line rather than an A2 per article — a whole
            # law vanishing would otherwise flood the report
            failures.append(f"A2 {law}: law vanished from catalog "
                            f"({len(arts)} baseline articles)")
            continue
        for art, b in arts.items():
            n = n_law.get(art)
            if n is None:
                failures.append(f"A2 {law} чл.{art}: article vanished "
                                "from catalog")
                continue
            if n["explicit_alineas"] < b["explicit_alineas"]:
                failures.append(
                    f"A1 {law} чл.{art}: explicit alineas "
                    f"{b['explicit_alineas']} -> {n['explicit_alineas']}")
            if n["articles"] < b["articles"]:
                failures.append(
                    f"A3 {law} чл.{art}: article rows "
                    f"{b['articles']} -> {n['articles']}")
    if failures:
        print(f"FR-034 ARTICLE VERIFY FAIL ({len(failures)} findings):")
        for f in failures[:50]:
            print(" -", f)
        sys.exit(1)
    pairs = sum(len(a) for a in now.values())
    print(f"FR-034 ARTICLE VERIFY OK ({len(now)} laws, {pairs} articles)")


if __name__ == "__main__":
    {"baseline": baseline, "check": check,
     "article-baseline": article_baseline,
     "article-check": article_check}[sys.argv[1]]()
