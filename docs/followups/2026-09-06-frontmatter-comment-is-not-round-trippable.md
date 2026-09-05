# One act carries a YAML comment in its frontmatter, and no writer can preserve it

**Date:** 2026-09-06
**Status:** open — one act, no data loss yet, and a corpus-wide backfill would cause it
**Found by:** Part II Task 6, measuring the write gate's render against all 3 624 committed acts

## The finding

`implementing/pravilnik-za-sotsialno-podpomagane-na-chlenovete-na-sayuza-na-arhitektite-v-balg.md`
carries five lines of YAML comment between `ultima_actualizacion` and `estado`, recording that its
`derogado` status is a data-quality scope exclusion and not a Държавен вестник repeal, and pointing
at `docs/sync/HANDOFFS/2026-06-21-missing-acts-evaluation.md` §3.

A YAML comment is not data. Every writer in the repository loads the frontmatter with
`yaml.safe_load` and writes it back with `yaml.dump`, so the comment survives only for as long as
nothing rewrites the act. It is the **only** act of the 3 624 whose frontmatter does not round-trip
byte-identically through the gate's renderer; the other 3 623 round-trip exactly.

It is also evidence of a hand-edit: the note cannot have been produced by the pipeline, and
„corpus `.md` files are written only by the pipeline, never hand-edited“ is a Global Constraint.

## Why it matters later, not now

Nothing rewrites this act today. The first corpus-wide pass that does — the provenance backfill of
the Gazette plan writes every act through `corpus_gate.write_act` — deletes the note silently, and
the act then asserts `estado: derogado` with no trace of the adjudication behind it.

## The options, for whoever picks this up

1. **Move the note out of the file** into `docs/data/` next to the scope-exclusion record it cites,
   and let the act carry ordinary frontmatter. Cheapest, and it puts a governance record where
   governance records live.
2. **Promote it to a field**, e.g. an `estado_note` key. `corpus_gate.render_act` preserves
   frontmatter keys outside the assembler's whitelist, and `refresh.merge_preserved` carries every
   key the lex.bg metadata parser does not produce across a re-scrape, so such a field survives
   both. It costs a frontmatter-schema preflight (protected surface), and every other writer that
   builds frontmatter from scratch would have to preserve it too.
3. **Preserve comments in the renderer** by switching to a round-tripping YAML library. Rejected on
   sight for this: a new dependency and a changed dumper for one act, with a real risk of moving
   the bytes of the other 3 623.

Option 1 unless the note is wanted machine-readable.

## Verification

```
python - <<'PY'
from corpus_gate import render_act
from corpus_integrity.loader import iter_acts
from pathlib import Path
bad = [a.path for a in iter_acts(Path("."))
       if render_act(a.frontmatter, a.body) != a.path.read_text(encoding="utf-8")]
print(len(bad), bad)
PY
```

Expected today: `1` and this act. Expected after the fix: `0`.
