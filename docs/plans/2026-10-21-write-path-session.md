# The write path: from a staged text to an act committed in git

Who this is for: the owner, who starts the session, and the session that builds the write path. Written 21 October 2026 on the owner's word that the only success criterion of this stage is an act correctly read, properly parsed and committed in git. The prompt for the session is in section 5. The owner pastes it into a new session started in this worktree.

## 1. What exists and what is missing

What exists. The single write gate `corpus_gate.write_act` (merged 6 September 2026): it serialises frontmatter and body, runs the registered integrity checks (tag remnants, site chrome) against the waiver file, refuses with every violation named, has no force flag, and fails the build if any other module writes a corpus path. The lex.bg refresh path, which builds an act's frontmatter from its page (title, amendment list, dates) and commits with the three trailers, deciding `[reforma]` when the amendment history grew and `[popravka]` when only the body changed. The reading pipeline of decision D-069: for each of the 50 acts read so far (16 of the test set, 34 of batch 1), a run folder with the page's blocks, the structure map, the staged Markdown body, the reassembly check and the residue.

What is missing, between the staged body and a commit:

1. The rulings on the forms the residue turned up (section 2), decided by the session under decision D-069 and recorded as D-072, applied as rules in the assembler, the checks or the labeller's instructions, so that no reviewer reads per act.
2. Three check gaps found in batch 1: a doubled letter on a numbered item (27аа), a superscript on a bare article number (Чл. 166¹), and footnote asterisks that the reassembly check strips as bold markup.
3. The write path itself: a module that takes a run folder, builds the frontmatter the refresh path would build from the same page, puts the staged body under it, records provenance, calls the gate, and commits.
4. The two additions to protected surfaces need no preflight and no signature: the frontmatter gains an optional `provenance` block (Surface 2, optional extension fields are within the allowed scope; decision D-071 of 21 October 2026 struck the earlier preflight requirement) and the commit gains a `Record-Id` trailer (Surface 5, an added optional trailer within the allowed scope).

## 2. The rulings, decided by the session and recorded as D-072

Each line is a form met in the test set or batch 1 and the rule the session applies. Judged against the first principles as a whole, these are the agent's to decide: each is a reading of lex.bg's formatting under decision D-069, written to git, reversible, recorded per act in the omissions list, and guarded by the reassembly check. They are recorded as the session's readings with their evidence, and the owner corrects any line read differently; none is put to the owner as a question.

1. **A superseded heading printed again by lex.bg** (the old number line and old title after the current heading, with or without a „Загл. изм.“ note): dropped from the body and recorded in the act's omissions list as `superseded_heading` with its block index. Not an editorial note, because the note would become an addressable line of the act.
2. **Headings printed on two lines** (number line, then title): joined into one heading line, as the assembler does now.
3. **Bold on article heads, § openers, „Член единствен“ and „Параграф единствен“**: the staged convention stands (bold), and the older plain form in corpus files is replaced.
4. **Heading levels**: chapter and section headings at the levels the assembler gives them; pre-1974 acts with parts above chapters take four levels. The corpus file's levels are replaced.
5. **A numbered list inside a definition item** (items under an item that ends with a colon): each line is an `item` whose address nests under the parent item. Letters that restart after a paragraph of prose inside a definition start a new lettered list under that paragraph.
6. **Duplicate numbers the page itself carries** (two alineas (11), item 58 twice): both lines keep their label and number; the second gets the address suffix `-2`, and the act's omissions list records `duplicate_number` with both block indices. The number grammar accepts a doubled letter on a numbered item (27аа) and a superscript digit on a bare article number (166¹ addressed as `166-1`, ordered after 166 and before 166а).
7. **Irregular heads the page carries** (a § without its sign, an article number without „Чл.“, an item without its dot, an alinea „(2“ without its bracket): the label the labeller gave stands, the text stays as the page has it, and the check records a source finding instead of an exception.
8. **The dashed separator before the adoption formula** and lex.bg's dotted elision line: editorial notes, kept.
9. **lex.bg's list of related EU acts, the add-to-my-acts button, the correspondence-table link**: dropped as chrome, not recorded (defect class FR-036 closes for the acts written).
10. **The corpus body is replaced wholesale by the staged body** when the reassembly check holds (every block of the page in the body, symbol for symbol, except the lines dropped under rules 1 and 9). The diff against the old corpus file is not read line by line; it is kept in the run folder.
11. **A page newer than the corpus file** (its amendment list has entries the frontmatter lacks): the commit is `[reforma]` with `Source-Date` of the newest entry, `ultima_actualizacion` moves to it, and `amendment_history` is rebuilt from the page, as the refresh path does. Otherwise the commit is `[popravka]`.
12. **Provenance**: the act's `fuente` stays `lex.bg`, its grade stays what the coverage floor derives for a snapshot base; the `provenance` block carries `base: {source: lexbg, state: snapshot, page_sha256, fetched_at}`, `record: {run, map_sha256, blocks_sha256}` and `omissions: [...]` (rules 1 and 6). Nothing else of the September design's block is filled in this session.

## 3. The work of the session, in order

1. **The decision record.** Record the rulings of section 2 as decision D-072 in `docs/sync/DECISIONS.md`, each line with its evidence and marked as the session's reading. Add the `provenance` block to `docs/data/schema-reference.md` as an optional extension (D-071) and the `Record-Id` trailer to the commit format section of `docs/process/delivery-contract.md` as an optional trailer. Done when the three documents carry the entries and the owner has the twelve rulings in one line each.
2. **The rules.** Apply rulings 1 and 5 to 9 in `reading/assembler.py`, `reading/checks.py` and `reading/labels.py`, with a test per ruling in the reading package's tests; fix the three check gaps the same way. Re-collect the 34 acts of batch 1 and the 16 of the test set (no labeller call, except the three energy items of round 1, which re-run through `dispatch`). Done when the residue of the 50 acts is zero, or every remaining block is listed with the rule it still needs.
3. **The write path.** A new module `reading/write.py` with one entry point, `write_staged(slug, run_dir)`: reads the page from the raw store, builds the frontmatter as the refresh path does, through `MetadataParser.parse` over the page and `merge_preserved` over the committed frontmatter (the text parser is not called for the body: its role is reduced to the lister the plan of record names), takes the staged body, checks reassembly once more against the page, fills the `provenance` block of ruling 12, calls `corpus_gate.write_act` with `SourceRef("lexbg", doc_id)`, and commits with the three trailers and `Record-Id: <run>/<slug>/<map_sha256 prefix>`. The commit type follows ruling 11. The gate's AST scan must list no new writer: the module writes only through the gate. Tests: the frontmatter equals what the refresh path builds for the same page; a body that fails reassembly is refused before the gate; a gate refusal leaves no file changed. Done when the first act is committed on this branch and its file passes `corpus_integrity` and the frontmatter checks.
4. **The first act.** The public finance law (no residue, 25 diff lines), then the municipal property law. Done when both commits are on the branch with their trailers, and the files re-read through the MCP server's `get_law` return the staged structure.
5. **The 50 acts.** `write_staged` over every act of the test set and batch 1 whose residue is zero after step 2, one commit per act, in a single pass; the acts the gate refuses are listed with the violation. Done when the pass prints the written and refused lists.
6. **Review and the owner.** One fresh-subagent review of the module and the decision record on a different model from the session's, findings fixed, then the pull request onto the plan branch stays a draft until the owner merges. The owner's go is needed to merge; the session does not merge.

Non-goals: no Gazette material, no change to the labeller's vocabulary beyond ruling 5, no index rebuild beyond what the gate already triggers, no municipal acts, no re-read of acts outside the 50, no API key.

Budget: this is session work, not a labeller run. Estimate 2 to 3 million session tokens for the six steps including two review rounds; the only model calls outside the session are the three energy re-labels and the review. Stop and report if the gate refuses more than five of the 50 acts for the same cause, or the session passes 4 million tokens.

## 4. The goal line

```
/goal Write path (docs/plans/2026-10-21-write-path-session.md): done when the public finance law and the municipal property law are committed on this branch through corpus_gate.write_act with the three trailers and Record-Id, the rulings are in DECISIONS.md as D-072 and applied with a test each, and the pass over the 50 read acts prints its written and refused lists. Budget: 3 million session tokens; stop and report if the gate refuses more than five acts for one cause or tokens pass 4 million. Non-goals: no merge, no Gazette material, no vocabulary change beyond ruling 5, no acts outside the 50.
```

## 5. The prompt for the session

Start a new session in the worktree `/Users/ekimir/swprj/legalize-bg/.claude/worktrees/run-design-ab4d70` on branch `claude/run-design-ab4d70` and paste:

```
Read docs/plans/2026-10-21-write-path-session.md. Build the write path by its section 3, in order, with the done-condition of each step printed as evidence before the next starts. The rulings of section 2 are yours to record as D-072, not to ask me about; tell me in one line each what you recorded after step 1, then continue. Then continue through step 6. Commit on this branch only; do not merge. Report after each step in plain words: what is committed, what the gate refused and why, and the distance left to an act in git.
```

## Glossary

- **Staged body**: the Markdown body the reading pipeline assembled from the page's blocks under the labeller's map, kept in the act's run folder and not yet in the corpus.
- **Run folder**: the folder per act under the run of 22 October 2026 holding its blocks, map, staged body, checks and reports.
- **The gate**: the single sanctioned writer of a corpus file, which runs the integrity checks and refuses with every violation named.
- **Residue**: the blocks the two re-label rounds left for a reviewer.
- **Omissions list**: the per-act list in the provenance block of what the pipeline dropped or marked on purpose, with block indices.
- **Surface 2, Surface 5**: the protected surfaces for the frontmatter schema and the commit message format; both additions here fall within their allowed scope.
- **D-069, D-070, D-071, D-072**: decisions in the decision log: the reading architecture, the run driver, the provenance block as an optional field without a preflight, and the rulings of section 2 once recorded.
- **FR-036**: the future-requirement entry for site chrome in act bodies.
- **Reassembly check**: the check that the staged body contains every block of the page, symbol for symbol, in order.

## References

- The plan of record: `docs/plans/2026-10-21-reasoning-driven-corpus.md`, 21 October 2026, stage 1 step 4.
- The graded source design: `docs/plans/2026-09-05-dv-graded-source-design.md`, section 4.3, the provenance block.
- The two results documents the rulings answer: `docs/testing/2026-10-22-structure-map-results.md` and `docs/testing/2026-10-21-structure-map-batch-1.md`.
- The Legalize specification the commit format and the mandatory frontmatter fields follow: `legalize-dev/legalize/SPEC.md`, as cited by the preflight document.

## Provenance

- The gate: `corpus_gate.py` in this repository (`write_act`, `SourceRef`, `find_corpus_writers`). The refresh path: `refresh.py` (`_git_commit_typed`, `history_grew`, `merge_preserved`) and `fetcher/bg/metadata.py` (`MetadataParser`). The reading pipeline: `reading/` and its run folders under `data/runs/structure-map-2026-10-22/`.
- The plan of record and its step 4: `docs/plans/2026-10-21-reasoning-driven-corpus.md`; the provenance block's design: `docs/plans/2026-09-05-dv-graded-source-design.md`, section 4.3; the protected surfaces: `docs/process/IMPLEMENTATION-PREFLIGHT.md`; the commit format: `docs/process/delivery-contract.md`.
- The residue the rulings answer: `docs/testing/2026-10-22-structure-map-results.md` and `docs/testing/2026-10-21-structure-map-batch-1.md`.
