# F1, the engine: read-back, measurement and budget

Who this is for: the owner, who gives the go for the model runs of step F1 of the implementation plan of 31 October 2026 (`docs/plans/2026-10-31-starting-state-implementation-plan.md`, section 4, "F1: the engine"). Written on 1 November 2026 in the F1 session (worktree `jolly-wright-479586`, draft pull request onto `main`). The plan said the budget of F1 is unknown until the splitter and the attribution step exist; both exist now, measured with no model call, and this document states the budget from that measurement and asks for the go.

## 1. The plan's words, read back

Each item is the plan's text for F1 (section 4) or the task given to this session by the planning session, tagged with its source. Everything marked "my addition" is a how this session decided under the owner's standing word of 31 October 2026 that the hows are the sessions' to decide and record.

1. **Five parts.** "The material splitter for the Gazette's HTML materials, from S1. The attribution step: which act a material changes, from the title and opening blocks, recorded as data. The instruction step: each amending instruction turned into an operation on the act's addressed provision, recorded as data. The apply-and-check step: the operation applied by script, the result through the checks and the write gate. The witness comparison with its settlement." (The plan, F1, "What is built".)
2. **Where the model is.** "The engine is a reasoning run on the lean agents; what it cannot apply with certainty stops with a case file." (The plan, F1.) The model returns, for an amendment, "an operation (address, kind, old string cited from the provision, new string cited from the Gazette material); a script assembles or applies, then checks: … an edit's old string occurs once at its address and is gone afterwards" (decision D-069).
3. **The proof.** "It is verified first on the representative acts of each kind that the owner agrees from S3's profiles: their history is rebuilt from the Gazette and every difference from the witnesses settled; that is the evidence of whether the engine can be built." (The plan, F1.) The eleven acts are those of `docs/plans/2026-10-31-f1-representative-acts-proposal.md`, which the owner let stand (the task of 1 November 2026).
4. **Done when.** "The representative acts of every kind are committed with their history rebuilt, every difference settled and the engine's errors counted per kind, and the kinds it cannot do stop with case files." (The plan, F1.) The session prints as evidence: the eleven acts' commits with trailers or their case files, the per-kind error counts, the settled-difference counts per act, the distance line over the eleven and over the 18 listed acts, the attribution measurement, the token report against the budget, and the local gate passing. (The task.)
5. **Budget.** "Unknown until the splitter and the attribution step exist. The catch-up materials of бр. 63 to 96/2026 (151 bodies on disk, 55 of them in scope by title) are the first measured batch, estimated before it runs." (The plan, F1.) The budget is stated with a unit cost per material and per representative act, and work past it waits for the owner's go. (The task.)
6. **Then the 18 listed acts** on the history route, "if the budget allows, else say what it would cost." (The task.)
7. **Reviews.** "Fresh Opus review after each part, findings fixed with tests, stop when majors do not fall for two rounds or at the owner's ruling, three rounds at most; keep each reviewer's scope to the diff and the tests so a round stays well under the measured 0.5 million." (The task.)
8. **Standing rules.** Corpus files only through the gate; the lex.bg refresh path never runs; no API key; protected surfaces are the owner's; only the owner merges; the pull request stays a draft until its review passed and the local gate passed on its last commit; only a correctly committed act counts. (The task; `.claude/CLAUDE.md`.)

## 2. What is built, with my additions marked

**Part 1, the material splitter (built).** `split_dv` of S1 cuts a material into blocks. My addition: `reading/material.py` reads the material's *skeleton* mechanically, as the owner's rule of 21 October 2026 keeps for structured text: the header (a law's promulgation decree, a ministry's issuing body, the title lines, the cited history line whose first issue is the amended act's promulgation), the instructions (`§ N.` nodes with `N.`, `а)` and `аа)` under them), the quoted text that hangs under each instruction (a run opens on a block that starts with a quotation mark and does not close it; the Gazette closes a nested quotation with one mark, so where the marks' parity fails the amending act's own sequence resumes the instructions and the parser records it), the cross-act target a § opens with („В Закона за … (обн., ДВ, бр. …)“), the provisions headings, an act a decree adopts after its signatures, a whole act's own final provisions, and the tail. Every block gets one role; what the grammar cannot place is a finding, recorded, never hidden. A material with a finding is still attributed by its title; the instruction step refuses it until the finding is read (by the model's block ranges, section 3, or by the owner).

**Part 2, the attribution step (built).** My addition: `reading/attribution.py` resolves each cited title to a corpus act by the resolver's normalised title, then requires the corpus act to have been promulgated in the issue the material cites; that is what tells a same-named predecessor from the act the corpus holds (FR-043). Statuses form a closed set (`attributed`, `ambiguous`, `not_in_corpus`, `predecessor_or_other`), the result is one JSON record per material with a mechanical form check, and **no model is called**: an ambiguous title is a stop for the owner, since a fixed form leaves no reading to make. A corrigendum („Поправка в …“) is classified; its target is resolved through the amending act it corrects (to build). A court decision is classified and not applied: a kind the engine does not do, recorded as such.

**Part 3, the instruction step (to build; my additions).** The route's chain step gathers an act's materials: the index's title hits plus every law, decree, ordinance, regulation and instruction of the issues lex.bg's history line names, fetched at one request per second; lex.bg points at where to look, the Gazette's own text attributes (D-061). One lean-agent call per attributed material reads the parsed instructions with their quoted blocks and the current text of the provisions the addresses name, and answers operations in a fixed JSON form: instruction id, a kind from a closed set, the address, the old string as a reference to a quoted segment the parser numbered, the new string as a reference to quoted blocks, and where the parser's quoted extents were wrong, the block range. The closed set the materials show so far: `replace_provision`, `replace_words`, `delete_words`, `insert_words`, `insert_provision`, `repeal`, `renumber`, `replace_heading`, `insert_annex`, `replace_annex`, `repeal_annex`, `corrigendum`, `no_text_change` (an entry-into-force or transitional rule that changes no text); a kind outside it, an amendment of an amending act's own provisions, or a court decision stops the act with a case file. A script checks the form (D-069): the kind is in the set, the references exist, the address resolves in the act, the old string occurs exactly once at its address, a new text begins with a quotation mark in the material; the wording is copied symbol for symbol from the material's blocks, never retyped by the model. The agent's instructions travel in the task file and the call goes to the `labeller` type, because the session's agents load from the main checkout (follow-up of 31 October); an `applier` agent definition is added for later sessions.

**Part 4, apply and check (to build; my additions).** The act's text is a tree of lines built from the Markdown body by the assembler's own conventions; an operation edits the addressed lines; after each material the body is re-derived into blocks and labels and `reading/checks.py` runs (numbering, nesting, addresses, reassembly), and a failed check stops the act with a case file, never a retry on the same inputs (S0's bound). The amendment marker is written in the corpus's convention, which is lex.bg's, so that the corpus stays uniform and the witness comparison compares text, not form: „(Изм. - ДВ, бр. N от YYYY г.)“, „(Нова - …)“, „(Доп. - …)“, „(Отм. - …)“, after the provision's number, without the entry-into-force clause, which the Gazette states only in the amending act's final provisions and the engine does not infer. The write path gains the engine's mode: the body is rebuilt deterministically from the committed records (the promulgation reading plus each material's operations in order) and must equal the staged body; the provenance base says `source: dv, state: consolidated`, names the promulgation material and the chain of applied materials with their hashes; `amendment_history` is rebuilt from the Gazette's chain (promulgation plus one row per applied material, issue and date); the commit is `[reforma]` with `Source-Id: dv-<last material>` and the four trailers. My reading: this stays inside the preflight the owner signed on 31 October (the same fields, more rows; the provenance block is an optional extension under D-071); section 6 asks the owner to confirm the reading.

**Part 5, the witnesses (built in S1; one addition).** The witness normalisation gains one rule: the entry-into-force clause inside an amendment marker („, в сила от 22.12.2023 г.“) is removed on both sides before the comparison, since the engine does not write it; every other difference is settled by the settler as before, one call per act.

**The eleven acts enter the exceptions list** (my addition) with the route `history` and a new value of the list's own closed defect set, `representative` ("no lex.bg defect known; rebuilt from the Gazette as a representative of its kind for the engine's verification, D-074 (3)"), because once committed from the Gazette their text is not taken from lex.bg, which is what the list records. The route's steps replace the placeholder `engine` of S0 (`chain`, `fetch_material`, `prepare`, `label`, `ladder`, `content_check`, `apply`, `witnesses`, `write`); the 18 case files of S2 that stopped at `engine` stay valid, their step name accepted as the historic stop.

## 3. The measurement, with no model call

**The catch-up materials of бр. 63 to 96/2026** (the plan's first measured batch; `data/runs/f1-attribution-2026-11-01/catchup-63-96/summary.json`):

| Measure | Count |
|---|---|
| materials on disk | 151 |
| amending materials | 42 |
| of them amending a corpus act | 33 |
| cited targets | 83 |
| attributed to a corpus act | 62 |
| not in the corpus (18 by type: tariffs, decrees, rules, an amending act's own provisions; 3 acts the corpus does not hold) | 21 |
| a same-named predecessor or other act | 0 |
| ambiguous | 0 |
| cross-act targets inside other acts' provisions, and attributed | 43, 28 |
| materials with a parse finding (a quoted list the grammar cannot place, a text printed without quotation marks) | 7 |
| instructions in the amending materials | 1,168 |
| tokens of instruction and quoted text in them | 122,330 |
| model calls | 0 |

Of the 55 materials the session of 21 October triaged as in scope by title, 33 amend a corpus act, 4 amend acts outside the corpus (tariffs and decrees), 4 carry a parse finding, 13 are whole new acts or court decisions (read by the labeller route or recorded as a kind the engine does not do), and 1 names no target. The figures are those after the review of parts 1 and 2 (3 blocking, 5 major, all fixed with tests); the summary's form check now fails on a wrong promulgation and found and fixed 18 missed attributions in the chains.

**The eleven acts' chains** (`…/eleven-chains/`): 598 candidate materials (the title hits and every law, decree, ordinance and regulation of the 100 issues lex.bg's histories name), 203 of them amending a corpus act; 93 attributed to one of the eleven acts, in 88 distinct materials (five amend two of the eleven at once), with 5,849 instructions; about 350,000 tokens of instruction and quoted text fall to the eleven acts, 677,000 for the 88 materials whole. Of lex.bg's 100 amendment events, 96 are located in the Gazette; the four not located are: two that ride in the promulgation materials of new codes (the Penal Procedure Code of бр. 86/2005 for the extradition law, the Civil Procedure Code of бр. 59/2007 for the private international law code), which the fetch filter of this measurement skipped and the chain step will fetch; one amendment of an amending act's entry-into-force clause (Семеен кодекс, бр. 101/2019), a kind the engine stops on; one corrigendum (Наредба № 1 от 2015 г., бр. 81/2021), whose target the attribution will resolve through the act it corrects. Eleven of the 88 materials carry a parse finding (a new text printed without quotation marks, a quoted list the grammar cannot tell from the instructions, a quotation the Gazette closes item by item), which the instruction step resolves by the model's block ranges or stops on. The promulgation materials of the eleven acts hold 5,058 blocks in 154 labelling sections.

## 4. The budget

Counted once, from the measured figures of D-070 (7,700 tokens of plan usage per labelling section on the lean driver) and S1 (the transport law: three round-0 calls and at most two ladder calls for 17 sections).

| Part | Unit | Count | Tokens |
|---|---|---|---|
| promulgation reading, round 0 (labeller) | 7,700 per section | 154 sections | 1.19 M |
| ladder rounds 1 and 2 | 40 % of round 0 | | 0.45 M |
| instruction step (one lean call per material: the instructions and quoted text, about 3,800 tokens measured; the addressed provisions' current text; the answer; the agent's fixed context) | 10,000 per material | 93 | 0.93 M |
| witness settlement (settler) | 40,000 per act | 11 | 0.44 M |
| three fresh Opus review rounds, scoped to the diff and the tests | under 0.5 M each | 3 | 1.0 M |
| **total, eleven acts** | | | **4.0 M** |

Unit costs: about **280,000 tokens per representative act** of model calls (promulgation reading, instructions and settlement), and about **10,000 tokens per amending material** for the instruction step, which is also F2's per-material figure (the 33 catch-up materials in scope would cost about 0.33 M to apply, plus their settlement). The budget asked for is **5.0 million tokens** of plan usage, calls and reviews, a fifth above the estimate. The costs by token type and cache type cannot be split before a call is made; the first act run, Наредба № 8121з-310 (96 blocks, 7 amendments, the smallest chain), measures them and the per-material figure before the other ten run, and the token report gives every call by type and cache type.

**The 18 listed acts** on the history route (68 lex.bg events; their lex.bg pages hold about 29,400 blocks, one act, the Наредбата за качеството на социалните услуги, 16,700 of them in annexes): about 11 M tokens at the same units, or about 5.6 M without that one act. They are not inside the 5.0 M; the owner decides a raise now or a later goal line, after the eleven acts have measured the engine.

## 5. The goal line

Objective: the engine of F1 in five parts on the lean agents, proven on the eleven representative acts.

Done-condition, printed as evidence: the eleven acts' commits with the four trailers, or their case files; the engine's errors counted per kind; the settled-difference counts per act; the distance line over the eleven and over the 18 listed acts; the attribution measurement of section 3; the token report against the budget by token type and cache type; the local gate passing on the last commit.

Non-goals: no change to the roles of script and model (D-069); no act outside the eleven written unless the owner raises the budget; no change to a protected surface beyond the reading of section 6, item 2; no API key; no corpus file written outside the gate; no lex.bg refresh.

Where state lives: the branch `claude/jolly-wright-479586` and its draft pull request onto `main`; the run folder `data/runs/f1-engine-2026-11-01/`; each committed act's chain, operations and witness records beside it in git (D-073); case files in `docs/cases/`; decisions in `docs/sync/DECISIONS.md`.

Offered: `/goal F1 of docs/plans/2026-10-31-starting-state-implementation-plan.md: the engine in five parts on the lean agents, proven on the eleven representative acts of docs/plans/2026-10-31-f1-representative-acts-proposal.md; done when the evidence of docs/plans/2026-11-01-f1-engine-read-back.md section 5 is printed; budget 5.0 million tokens counted once, calls and reviews; past it the session waits for the owner's go; reviews stop when majors do not fall for two rounds or at the owner's ruling, three rounds at most.`

## 6. The owner's decisions, in one batch

1. **The go and the budget of 5.0 million tokens** for the eleven acts. Recommendation: go.
2. **The frontmatter of an engine-rebuilt act** (Surface 2): the source field `dv.parliament.bg` as signed on 31 October; the provenance base `state: consolidated` with the promulgation material and the chain of applied materials; `amendment_history` rebuilt from the Gazette's chain. My reading is that this stays inside the signed preflight (the same fields, more rows, an optional extension block). Options: (a) confirm the reading; (b) a second short preflight before the first write. Recommendation: (a).
3. **The eleven acts on the exceptions list** under the new defect value `representative`, so that their text is recorded as taken from the Gazette and the lex.bg path is refused for them by name. Recommendation: yes.
4. **The 18 listed acts:** about 11 M tokens (5.6 M without the social-services ordinance). Options: (a) a raise now to 16 M; (b) a later goal line after the eleven acts have measured the engine. Recommendation: (b).

## Provenance

The measurement scripts and records: `reading/material.py`, `reading/attribution.py`, their tests, `data/runs/f1-attribution-2026-11-01/` (the summaries are committed; the per-material records are rebuilt by `python -m reading.attribution measure`). The per-section labelling figure is D-070's; the per-act ladder ratio is S1's run of the transport law (`data/runs/starting-state-2026-10-31/`). No model was called for anything in this document.
