# The reasoning-driven corpus: direction of 21 October 2026 and the plan of work

Who this is for: the repository owner, who set this direction on the night of 21 October 2026 and will read this again to check the daily loop and the backfill against it.

## 1. The direction the owner set, and what it asks of the owner now

This document records a direction the owner set on 21 October 2026 (sections 1 to 5) and asks the owner for four decisions that the direction leaves open (section 7). From 21 October 2026 the corpus is kept by two kinds of worker with a fixed division of labour. Scripts acquire: they enumerate the State [Gazette](#glossary), fetch its [materials](#glossary), re-photograph lex.bg, and write files through the single [write gate](#glossary). A reasoning run decides: what each Gazette material does to which act, how the amended text reads after it, whether a lex.bg divergence is a lex.bg error or ours, and which suspected structural defects in the Markdown are real. The reasoning run is the consolidation engine that the September design left for a later phase. Mechanical checks keep their place wherever the text has a strict structure, and they keep blocking there. Over free prose they only list places to look, and the reasoning run decides each one.

The owner also set the first priority: a current corpus, a daily update procedure that keeps it current from the Gazette, and a clear picture of how far back the Gazette-side chain reaches. This stage ends on the day lex.bg is no longer needed as a source. Municipal sources and court practice come after that stage and are not planned here.

## 2. The owner's words, read back

The read-back was shown in the session and the owner approved it item by item, with two corrections. Each item below names its source.

1. "Scripts are not the tools to decode the corpus, the reasoning model is." Scripts fetch, enumerate, diff and write through the gate. Every judgement about legal text is made by a reasoning run and recorded as data before the gate writes. (Owner, 21 October 2026.)
2. "No mechanical check can work for free text." The correctness plan of 11 August 2026 is refactored: its reading classes become "detector lists, model decides, gate records". Fixed-structure checks keep blocking. (Owner, 21 October 2026, agreeing the split, and the owner's rule of 20 October 2026 in the skills repository.) The owner's correction: the rule is not absolute. Code, code-like text and the structural skeleton of an act keep mechanical checks. The split is by what the judgement needs, form or meaning, and section 4 lists both sides.
3. "Phase one: a loop that checks the authoritative sources daily and updates the corpus via a reasoning run plus scripts." (Owner, 21 October 2026.) The owner's correction: the loop is a declared, scheduled loop in the form of the oversight catalogue's compliance auditor and registry keeper ([LC-03 and LC-04](#glossary)), not a goal-driven session.
4. "Reasoning is the authoritative decision maker." The reasoning run is the engine: it consolidates the amended text, the lex.bg snapshot is the [witness](#glossary), divergences are adjudicated and recorded, and the gate commits. This reopens item 5 of decision D-064, an entry in the repository's [decision log](#glossary) of 5 September 2026, which parked amendment commits until an engine existed. This item is the session's reading of the owner's words, and the owner has not yet confirmed it in so many words. Until the owner confirms it, the catch-up records findings and consolidated texts as data and writes no amendment commit. (Owner's words, 21 October 2026; reading by the session.)
5. "Later, when we publish, a simple harness for model calls." This belongs to stage 2, the later work listed at the end of section 5, and is not planned here. (Owner, 21 October 2026.)
6. "Simplify the word searches in the MCP server and the web with a similar approach." Also stage 2. (Owner, 21 October 2026.)
7. "End goal of this stage: stop using lex.bg and run entirely on the Gazette." The exit condition of stage 1 is in section 5. (Owner, 21 October 2026.)
8. Court practice: a placeholder in stage 2, no work. (Owner, 21 October 2026.)
9. On the night of 21 October 2026 the lex.bg refresh runs and the Gazette catch-up with a reasoning read runs; the nine-hour body fetch waits for the night of 22 October. (Owner, 21 October 2026.)
10. The session's addition: the Gazette enumeration tables must live in git in some form, because the daily loop's state is "the last issue enumerated", and that lives in those tables.

## 3. Where the corpus stands on 21 October 2026

| Fact | Value | How it was measured |
|---|---|---|
| Acts in the corpus | 3,624 | files on disk, the same count as the status file |
| Last lex.bg re-photograph | 1 July 2026 | decision-log entry D-047 of 1 July 2026 |
| Newest amendment the corpus records | 31 July 2026 | the largest `ultima_actualizacion` value over all acts |
| Last Gazette issue enumerated before tonight | бр. 81 of 4 September 2026 | the issues table of 5 September |
| Gazette issues enumerated tonight | 15 new issues, бр. 82 to бр. 96 | the enumeration run of 21 October, 02:15 |
| Gazette materials enumerated | 32,117 before tonight | the materials table of 5 September |
| Material bodies fetched | 16 | the cache directory |
| Events the [title pass](#glossary) could not locate | 10,319 events over 3,624 acts | the coverage map of 6 September |
| Of those, the [body-scan](#glossary) cases | 9,873 | the same map |
| [Near misses](#glossary) queued for a reasoning pass | 314 | the same map |

The pieces that exist and work: the Gazette acquisition layer (issue list, materials list with pagination, body fetch with resume), the lex.bg refresh runner with resume and the write gate, and the coverage map with its title resolver. Also live: the corpus-integrity package with two checks (tag remnants, site chrome), the single write gate, and the two consumer surfaces over the index, the Model Context Protocol server used by Claude Code and the web interface.

The pieces that were planned and not built: the instruction segmenter for transitional provisions, the Gazette material parser, the provenance block, the reasoning pass over the near misses, and every per-class ladder of the correctness plan beyond the two live checks.

At 02:00 Sofia time on 21 October 2026 lex.bg served act pages to a plain client with no Cloudflare challenge, so a full refresh was started at 02:15 on its own branch.

## 4. What changes in the repository

The direction is recorded in the files this repository treats as authoritative, so that a later session does not read the August and September plans as they stand and build the per-class [ladders](#glossary) they describe.

1. **Owner directives.** Directive 15 says that machines check form and the reasoning run decides meaning, with the owner's qualification. Directive 16 says that scripts acquire and the reasoning run decides, and that every decision is recorded as data before the gate writes.
2. **Decisions.** Four new decision-log entries. D-065 records the split of checks by form and meaning and rescopes the correctness plan. D-066 records that the reasoning run is the consolidation engine and reopens item 5 of D-064. D-067 records the daily update as a declared loop. D-068 records the exit condition of stage 1 and the lex.bg refresh of tonight as the last run of lex.bg as a base.
3. **The correctness plan of 11 August 2026** carries an amendment note at its head; its body is left as written for its evidence and definitions. The note changes what each [reading class](#glossary) gets: a lister that prints suspected places, a reasoning pass that records a verdict per place, and a gate step that applies the verdicts. The exit gate of each reading class becomes "zero items without a verdict". The fixed-structure checks keep "detector zero".
4. **The implementation plan of 5 September 2026** (phases P0 and P1 of the graded source model) carries an amendment note. Its segmenter, its material parser and its reasoning pass remain as named tasks but their decision part moves to the reasoning run. Its [provenance block](#glossary), its addressing of paragraphs marked with the section sign, and its exposure of the grade on the consumer surfaces stand as written.
5. **Future requirements.** Three entries of the future-requirements register change. FR-002 (the Gazette monitor) becomes the daily loop. FR-003 (the amendment grammar parser) is redirected: the reasoning run consolidates, no grammar kernel is built. FR-008 (a model as a fallback for hard patterns) is superseded: the model is the primary, not the fallback.
6. **The loop spec** of the [declared loop](#glossary) is committed on the plan branch in status `proposed`, with its [ledger](#glossary) file; the Provenance section names both files. It reaches the main branch with step 2 of stage 1.

The form side and the meaning side, as the owner agreed them:

- **Blocking, mechanical, only on fixed parts of the built file.** The eight mandatory frontmatter fields and their types. The file's link to its findings record, and the record's hash of the raw source. Declared counts against files on disk. Commit trailers. The provenance grade as the pure function of the recorded events. Literal code fragments that no law contains, in text the reasoning run rendered. The string equalities the reading architecture makes total: the cited spans re-assemble the whole source, and an edit's old string occurs exactly once at its address and is gone after the edit. When one of these fails, the writer script is fixed; the model's text is never re-rendered to satisfy a check.
- **Index only, never blocking, over the text.** Article numbering, paragraph nesting, headings, duplicate addresses, quoted passages that look like headings, brackets that look like numbering, annex boundaries, cross-references, and the disagreement between the model's labelling and the deterministic parser's. Each run produces its index once; the reasoning run records one verdict per item; a later reader sees the index and the verdicts beside the text. No count has to reach zero for a write to happen.
- **The existing chrome and remnant checks** with their waivers move to the index side for text inherited from the old parser, and stay blocking only for text the model rendered, where they cannot occur unless copied.

The reading architecture that makes the string equalities possible (one provision per call, cited pointers and edit operations instead of retyped text, the cheapest model that passes the check carrying the bulk) is the subject of the research run of 21 October 2026 in the knowledge base, `knowledge/references/2026-10-21-model-selection/`, and is a draft until the owner adopts it.

## 5. The plan of work

### Stage 1: a current corpus and a daily loop

The owner adopted the reading architecture on 21 October 2026 (decision D-069): the source's wording is copied symbol for symbol, the model judges only the formatting and returns a structure map or an edit operation, a script applies and checks it, and a failed check is an exception that two model rounds with neighbouring blocks try to settle before a whole-act read by a Fable model or the owner. Claude Opus 5.5 does the labelling and the operations. Each step below is one pull request the owner reviews, in this order.

1. **The direction (this document's pull request).** The directives, the decisions D-065 to D-069, the amendment notes on the two earlier plans, the redirected requirements, the loop spec in status proposed, the knowledge base with the research run. Done when merged, and the knowledge base is registered with oversight.
2. **Acquisition and the raw store.** A fetch command that keeps the raw page of an act or a Gazette material with its URL, time and hash, under the data directory, and does nothing else. Includes the owner's go for one fetch-only run over all 3,624 lex.bg act pages (about an hour at one request per second), which the audit needs as its wording source. Done when the raw store holds every act's page and every material of the catch-up issues, each with its hash.
3. **The structure map.** The splitter, the labelling call with custom content blocks, the assembler that copies blocks under labels, the two kinds of mechanical check (re-assembly equality; numbering and nesting), the exception ladder of two neighbour rounds, and the record format that ties every written file to its map and its source hash. No protected surface is touched: the output goes to a staging folder, never to the corpus. Done when ten acts of the owner's choice pass the ladder end to end with their exception counts printed.
4. **Protected surfaces, one pull request.** The provenance block with the record field and the per-act list of confirmed source omissions with Gazette locators; the commit trailer naming the record; the fetcher's text-parser role reduced to a lister; the preflight documents the directives require. Done when the preflights are signed and the write gate accepts a staged act.
5. **The Gazette path and the catch-up.** The material splitter, the attribution step (title and opening blocks), the instruction-to-operation step, the apply-and-check step, the witness diff against the current corpus text with its adjudication record; then the catch-up over бр. 63 to 96 of 2026 on Opus 5.5, its records and corpus commits on one branch, one pull request. Done when every material of those issues has a record and every touched act is written or carries a recorded reason.
6. **The call harness.** The audit of 3,624 acts is on the order of four hundred thousand small calls, which cannot run as subagents of a session, so a minimal harness that sends the labelling and operation calls through the API, in batch where the work is not urgent, comes forward from stage 2 into this step. It is a script with no logic of its own beyond retries and the ledger. Done when it has run step 3's ten acts and reported their cost.
7. **The audit of the existing corpus.** The ladder over every act through the harness: about 584 dollars at list price on Opus 5.5, half in batch; the owner approves the spend before the run. Every exception that survives two rounds goes to the whole-act read. Done when every act has a map, a record and a count of exceptions, and the dirty acts carry their omission list.
8. **The daily loop.** The entry command runs steps 2 and 5 for the issues after the last ledger mark, opens one pull request per run and appends a ledger row; the spec moves to supervised, and to active after two weeks without a rejected proposal. Done when it has run three days with a printed ledger row each and zero unrecorded materials.
9. **The backfill of the chain, 2003 to 2026.** The body fetch of all 32,117 HTML-era materials on the night of 22 October 2026 (about nine hours, resumable), then attribution and instructions through the harness from the most recent issue backwards, on the tier the owner chooses for that volume. Done when every event of every act since бр. 1 of 2003 is confirmed from a Gazette material, corrected, or marked as a Gazette-side gap with its reason.

**Exit of stage 1.** Every act's chain from 2003 onward is established from the Gazette by the reasoning run, the daily loop keeps it current, and lex.bg is no longer fetched at all. Until that day the daily loop still fetches lex.bg, but only to compare: the refresh of 21 October 2026 is the last run whose lex.bg text becomes corpus text. Events before 2003 stay as the corpus inherited them from lex.bg, and the provenance grade says so.

### Stage 2, later and not planned here

A model-call harness outside Claude Code for the loop's reading step. The simplification of word search in the Model Context Protocol server and the web. Vision reading of the Gazette issues of 1989 to 2002, which exist only as scanned PDF files. Municipal sources. Court practice.

## 6. Tonight's runs, with the estimate the owner asked for

**The lex.bg refresh** started at 02:15 Sofia time on 21 October 2026 on its own branch, `refresh/2026-10-21`, in a separate checkout. It takes 75 to 90 minutes at one request per second. It writes only through the gate and keeps every act's file name. It classifies each changed act as an amendment or a corrigendum, and commits on its branch only. Every guard that an earlier run needed is in place. A Cloudflare challenge halts the run. A stub page or a page with no title is refused. A connection failure is retried with backoff. A page that fails the chrome or remnant check is refused and listed. What this refresh does not do: it does not repair lex.bg's own omissions of promulgated sections, which is exactly why the Gazette is the target source.

**The Gazette catch-up** started at the same time: 15 new issues were enumerated, their 151 materials listed and all 151 bodies fetched by 02:23. The session then sorted the 151 by title. 55 are to be read: amending and new acts, and court decisions that can strike provisions. 14 are to be read with a scope question for the owner: ratification laws, and decrees of the Council of Ministers that have no act in the corpus. 82 are not read, each with a recorded reason: budget allocations, awards, appointments, election decisions, contracts, treaty texts. The reasoning read starts when the owner approves the budget below.

**The estimate for the reasoning read.** The 69 materials to read hold 344,000 tokens of text in all, about 5,000 each; about 35 of them are expected to amend a corpus act. The table counts one call per material for the reading leg, one per amended act for the consolidation leg, and one adjudication pass in this session.

| Leg | Model | Calls | Input tokens | Output tokens | Cost at list price |
|---|---|---|---|---|---|
| Reading and findings record | Claude Opus 5.5 | 69 | 0.6 million | 0.35 million | 10 dollars |
| Consolidation of touched provisions | Claude Opus 5.5 | 35 | 0.9 million | 0.35 million | 11 dollars |
| Adjudication of divergences and final check | Claude Fable 5.1 (this session) | 1 | 0.4 million | 0.1 million | 9 dollars |
| Total | | | 1.9 million | 0.8 million | about 30 dollars, a range of 20 to 45 |

The prices are the first-party list prices of 6 October 2026: Opus 5.5 at 4 dollars per million input tokens and 20 per million output, Fable 5.1 at 10 and 50. Thinking tokens are counted in the output columns. When the legs run as subagents of this Claude Code session, the same tokens count against the session's plan rather than being billed per token; the dollar figures are what the stage 2 harness would pay. The owner chose Opus 5.5 for labelling and operations on 21 October 2026 (D-069); under the adopted architecture the model writes no text, so this table's consolidation row no longer applies as estimated and the research run's cost table replaces it.

## 7. Open owner items

1. Item 4 of the read-back: confirm or correct it. The catch-up writes no amendment commit before this.
2. The form of the enumeration tables in git (pull request 37 holds them).
3. The budget and model for tonight's reasoning read.
4. The required status check on the main branch for the corpus-integrity job (open since 6 September; it is what makes the form checks of section 4 block on merge).
5. Whether repealed predecessor acts enter the corpus (future-requirements entry FR-043, open since 5 September; the backfill of stage 1 step 5 meets those acts in every Gazette issue it reads).
6. The scope question of the catch-up: whether ratification laws, and decrees of the Council of Ministers that are acts in their own right, belong in the corpus.

## Glossary

- **Gazette**: Държавен вестник, the State Gazette of Bulgaria, the official publication of every act and amendment.
- **Material**: one item published in a Gazette issue, such as an act, an amending act, a decree or a decision, served as one page on the Gazette's website.
- **Chain**: the sequence of Gazette events (promulgation and every amendment) that the corpus records for one act.
- **Title pass**: the coverage-map run of 6 September 2026 that matched Gazette materials to acts by title only.
- **Body scan**: the planned reading of each material's text to find amendments to other acts carried inside it.
- **Near miss**: a material whose title scored high against an act but was refused by the resolver's guards.
- **Reading class**: one of the kinds of structural defect of the correctness plan of 11 August 2026 whose judgement needs the meaning of the text (a quoted passage read as a heading, a citation read as a numbering, an annex read as articles, and the like).
- **Ladder**: the correctness plan's sequence for one defect class: a detector that counts every instance, a fixer that drives the count to zero, and the exit gate "detector zero".
- **Provenance block**: the part of an act's frontmatter that records where its text and each of its amendments came from (Gazette material or lex.bg snapshot) and the grade derived from that record.
- **Paragraph topology**: the nesting of an article's paragraphs, items and letters, which the Markdown must reproduce exactly.
- **Site chrome**: parts of the lex.bg web page that are not the act (menus, news, forum) and must not enter the corpus.
- **Tag remnants**: fragments of HTML markup left in the text, which break article addresses.
- **Declared loop**: a recurring agent workflow with a committed spec (trigger, entry point, permissions, budget) under the oversight loop-governance policy; its statuses are proposed, supervised and active.
- **Ledger**: the loop's log, one row per run with the time, the items processed, the actions taken, the tokens spent and the outcome; the "ledger mark" is the last Gazette issue a row records.
- **Write gate**: the single function through which every corpus file is written, which runs the registered checks and refuses a file that fails one.
- **Witness**: a consolidated text (lex.bg, the Ministry of Justice portal) that the corpus is compared against and never deferred to.
- **Lane**: the category a divergence is adjudicated into: a source error on the witness side, a defect on our side, a risk signal, or an editorial difference.
- **Decision log**: the dated register of decisions in this repository; **D-047** (1 July 2026) is the parser data-loss remediation, a full re-photograph of lex.bg, **D-064** (5 September 2026) the owner's answers to the graded-source design, **D-065** to **D-068** (21 October 2026) the four decisions of this document.
- **Future-requirements register**: the backlog of registered requirements and defect classes; **FR-043** is the open question whether repealed predecessor acts enter the corpus.
- **P0, P1**: the first two phases of the graded source model's implementation plan of 5 September 2026 (the coverage map; the provenance block and the pilot).
- **Stage 1, stage 2**: the two stages of this document's plan (section 5).
- **LC-03, LC-04**: the compliance-auditor and registry-keeper loops of the oversight catalogue, the model for the daily loop.

## Provenance

The counts in section 3 come from the files on disk, the decision log, the coverage-map research note of 6 September 2026 and the enumeration run of 21 October 2026, all in this repository. The lex.bg reachability was checked with a plain client at 02:00 Sofia time on 21 October 2026. The price table comes from the Claude API reference bundled with Claude Code, cached on 6 October 2026. The loop spec is `.ahelia/loops/dv-daily-sync.yaml` and its ledger `.ahelia/loops/ledger/dv-daily-sync.md`; the refresh log is `data/runs/refresh-2026-10-21.log` and the catch-up logs `data/runs/dv-catchup-2026-10-21.log` and `data/runs/dv-bodies-catchup-2026-10-21.log`. The material size average comes from the 16 cached bodies, measured as characters of text divided by three.
