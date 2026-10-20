# The reasoning-driven corpus: direction of 21 October 2026 and the plan of work

Who this is for: the repository owner, who set this direction on the night of 21 October 2026 and will read this again to check the daily loop and the backfill against it.

## 1. The decision

From 21 October 2026 the corpus is kept by two kinds of worker with a fixed division of labour. Scripts acquire: they enumerate the State [Gazette](#glossary), fetch its [materials](#glossary), re-photograph lex.bg, and write files through the single [write gate](#glossary). A reasoning run decides: what each Gazette material does to which act, how the amended text reads after it, whether a lex.bg divergence is a lex.bg error or ours, and which suspected structural defects in the Markdown are real. The reasoning run is the consolidation engine that the September design left for a later phase. Mechanical checks keep their place wherever the text has a strict structure, and they keep blocking there. Over free prose they only list places to look, and the reasoning run decides each one.

The owner also fixed the first priority: a corpus that is current, a daily update procedure that keeps it current from the Gazette, and a clear picture of how far the Gazette-side chain reaches back. The end of this stage is the day lex.bg is no longer needed as a source. Municipal sources and court practice come after that stage and are not planned here.

## 2. The owner's words, read back

The read-back was shown in the session and the owner approved it item by item, with two corrections. Each item below names its source.

1. "Scripts are not the tools to decode the corpus, the reasoning model is." Scripts fetch, enumerate, diff and write through the gate. Every judgement about legal text is made by a reasoning run and recorded as data before the gate writes. (Owner, 21 October 2026.)
2. "No mechanical check can work for free text." The correctness plan of 11 August 2026 is refactored: its reading classes become "detector lists, model decides, gate records". Fixed-structure checks keep blocking. (Owner, 21 October 2026, agreeing the split, and the owner's rule of 20 October 2026 in the skills repository.) The owner's correction: the rule is not absolute. Code, code-like text and the structural skeleton of an act keep mechanical checks. The split is by what the judgement needs, form or meaning, and section 4 lists both sides.
3. "Phase one: a loop that checks the authoritative sources daily and updates the corpus via a reasoning run plus scripts." (Owner, 21 October 2026.) The owner's correction: the loop is a declared, scheduled loop in the form of the oversight catalogue's compliance auditor and registry keeper ([LC-03 and LC-04](#glossary)), not a goal-driven session.
4. "Reasoning is the authoritative decision maker." The reasoning run is the engine: it consolidates the amended text, the lex.bg snapshot is the [witness](#glossary), divergences are adjudicated and recorded, and the gate commits. This reopens item 5 of decision D-064, an entry in the repository's [decision log](#glossary) of 5 September 2026, which parked amendment commits until an engine existed. The owner's words of 21 October set this; the read-back item stands unless the owner corrects it. (Owner, 21 October 2026; the reading is the session's.)
5. "Later, when we publish, a simple harness for model calls." This belongs to stage 2, the later work listed at the end of section 5, and is not planned here. (Owner, 21 October 2026.)
6. "Simplify the word searches in the MCP server and the web with a similar approach." Also stage 2. (Owner, 21 October 2026.)
7. "End goal of this stage: stop using lex.bg and run entirely on the Gazette." The exit condition of stage 1 is in section 5. (Owner, 21 October 2026.)
8. Court practice: a placeholder in stage 2, no work. (Owner, 21 October 2026.)
9. Tonight: the lex.bg refresh runs, the Gazette catch-up with a reasoning read runs, the nine-hour body fetch waits for the next night. (Owner, 21 October 2026.)
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

Tonight at 02:15 Sofia time lex.bg served act pages to a plain client with no Cloudflare challenge, so a full refresh was started on its own branch.

## 4. What changes in the repository

The direction is recorded where this repository keeps direction, so that no session reads the August and September plans as they stand and builds the per-class ladders.

1. **Owner directives.** Directive 15 says that machines check form and the reasoning run decides meaning, with the owner's qualification. Directive 16 says that scripts acquire and the reasoning run decides, and that every decision is recorded as data before the gate writes.
2. **Decisions.** Four new decision-log entries. D-065 records the split of checks by form and meaning and rescopes the correctness plan. D-066 records that the reasoning run is the consolidation engine and reopens item 5 of D-064. D-067 records the daily update as a declared loop. D-068 records the exit condition of stage 1 and the lex.bg refresh of tonight as the last run of lex.bg as a base.
3. **The correctness plan of 11 August 2026** carries an amendment note at its head. Its phases 1 to 6 are rewritten in principle, not in text: each reading class gets a lister, a reasoning pass with a verdicts file, and a gate step that applies the verdicts. The exit gate of each reading class becomes "zero items without a verdict". The fixed-structure checks keep "detector zero".
4. **The implementation plan of 5 September 2026** (phases P0 and P1 of the graded source model) carries an amendment note. Its segmenter, its material parser and its reasoning pass remain as named tasks but their decision part moves to the reasoning run. Its provenance block, its § addressing and its consumer exposure stand.
5. **Future requirements.** Three entries of the future-requirements register change. FR-002 (the Gazette monitor) becomes the daily loop. FR-003 (the amendment grammar parser) is redirected: the reasoning run consolidates, no grammar kernel is built. FR-008 (a model as a fallback for hard patterns) is superseded: the model is the primary, not the fallback.
6. **The loop spec** is committed in status `proposed`, with its ledger file; the Provenance section names both files.

The form side and the meaning side, as the owner agreed them:

- **Form, checked by a machine, blocking.** The eight mandatory frontmatter fields and their types. Declared counts against files on disk. The paragraph topology of an article. The provenance derivation. Site chrome and tag remnants. Address uniqueness, one key and one row. Heading sequence. The article and paragraph numbering grammar. Commit trailers.
- **Meaning, listed by a machine, decided by the reasoning run, recorded by the gate.** Whether a quoted passage is a real heading, whether a bracket is a citation or a numbering, why a duplicate address arose, whether an unnumbered line is a heading, where an annex begins, and what a cross-reference points to. Also all Gazette reading: what a material amends, how to consolidate it, and how a lex.bg divergence is adjudicated into a [lane](#glossary).

## 5. The plan of work

### Stage 1: a current corpus and a daily loop

1. **Decisions batch.** The owner confirms item 4 of the read-back if not yet, and chooses the form of the enumeration tables in git. The session's recommendation is gzipped tables on the main branch under the data directory, about five megabytes. The owner also approves the catch-up's model and budget (section 6). Done when each is recorded in the decision log.
2. **Refactor of the checks.** One pull request: the amendment notes on the two plans, the directives, the decisions, the future-requirement rows, the loop spec. No code changes beyond the two live checks staying as they are. Done when merged.
3. **Catch-up run (tonight).** The 15 new issues' materials are read by the reasoning run. For each material it records: the act or acts touched, the kind of event (amendment, repeal, new act, corrigendum, entry into force), the Gazette citation, the instructions in plain words, and, where the material amends a corpus act, the consolidated text of the changed provisions. The lex.bg refresh of the same night serves as witness for every touched act, and each divergence is adjudicated into a lane and recorded. The gate writes the touched acts. Done when every material of the 15 issues has a findings record and every touched act is written or carries a recorded reason why not.
4. **The daily loop.** The loop spec moves from `proposed` to `supervised`. Its entry point is a checked-in command that runs step 3 for the issues after the last ledger mark, opens one pull request per run with the corpus commits, and appends a ledger row. After two weeks of supervised runs with no proposal the owner would have rejected, it moves to `active`. Done when it has run three days with a printed ledger row each and zero unrecorded materials.
5. **Backfill of the [chain](#glossary), 2003 to 2026.** The body fetch of all 32,117 HTML-era materials runs on the next night: about nine hours at the Gazette's rate limit of one request per second, resumable. Then the reasoning run works issue by issue from the most recent backwards, attributing each material to its acts and confirming or correcting each act's recorded chain. The 9,873 unconfirmed events and the 314 near misses are closed by this reading. Done when every event of every act since бр. 1 of 2003 is confirmed from a Gazette material, corrected, or marked as a Gazette-side gap with its reason.

**Exit of stage 1.** Every act's chain from 2003 onward is established from the Gazette by the reasoning run, the daily loop keeps it current, and lex.bg is no longer fetched as a source. Pre-2003 events stay as inherited from the base snapshot and are stated as inherited, as the graded source model already provides.

### Stage 2, later and not planned here

A model-call harness outside Claude Code for the loop's reading step. The simplification of word search in the Model Context Protocol server and the web. Vision reading of the Gazette issues of 1989 to 2002, which exist only as scanned PDF files. Municipal sources. Court practice.

## 6. Tonight's runs, with the estimate the owner asked for

**The lex.bg refresh** started at 02:15 Sofia time on its own branch, `refresh/2026-10-21`, in a separate checkout. It takes 75 to 90 minutes at one request per second. It writes only through the gate and keeps every act's file name. It classifies each changed act as an amendment or a corrigendum, and commits on its branch only. The guards that stopped earlier runs are in place. A Cloudflare challenge halts the run. A stub page or a page with no title is refused. A connection failure is retried with backoff. A page that fails the chrome or remnant check is refused and listed. What this refresh does not do: it does not repair lex.bg's own omissions of promulgated sections, which is exactly why the Gazette is the target source.

**The Gazette catch-up** started at the same time: 15 new issues were enumerated and their materials are being listed. The reasoning read follows the owner's approval of the budget.

**The estimate for the reasoning read.** Tonight's enumeration found 151 materials in the 15 new issues. The same six weeks of 2025, 5 September to 21 October, held 16 issues and 166 materials in the sections the loop reads (National Assembly, Council of Ministers, ministries, the President). After leaving out the President's promulgation decrees, the election commission's and the courts' decisions, about 125 materials need reading, and about 50 of them are expected to amend a corpus act. A material averages 12,000 tokens of text.

| Leg | Model | Calls | Input tokens | Output tokens | Cost at list price |
|---|---|---|---|---|---|
| Reading and findings record | Claude Opus 5.5 | 110 | 2.0 million | 0.7 million | 22 dollars |
| Consolidation of touched provisions | Claude Opus 5.5 | 50 | 1.6 million | 0.6 million | 18 dollars |
| Adjudication of divergences and final check | Claude Fable 5.1 (this session) | 1 | 0.6 million | 0.1 million | 11 dollars |
| Total | | | 4.2 million | 1.4 million | about 50 dollars, a range of 35 to 90 |

The prices are the first-party list prices of 6 October 2026: Opus 5.5 at 4 dollars per million input tokens and 20 per million output, Fable 5.1 at 10 and 50. Thinking tokens are counted in the output columns. When the legs run as subagents of this Claude Code session, the same tokens count against the session's plan rather than being billed per token; the dollar figures are what the stage 2 harness would pay. The session recommends Opus 5.5 for the two bulk legs, following the owner's tiering rule of 5 September 2026, and this session's model for adjudication. Sonnet 5.5 would halve the bulk cost and is not recommended for consolidation, where a missed word is a wrong law.

## 7. Open owner items

1. Item 4 of the read-back, if the owner wants to correct it.
2. The form of the enumeration tables in git (pull request 37 holds them).
3. The budget and model for tonight's reasoning read.
4. The required status check on the main branch for the corpus-integrity job (open since 6 September).
5. Whether repealed predecessor acts enter the corpus (future-requirements entry FR-043, open since 5 September).

## Glossary

- **Gazette**: Държавен вестник, the State Gazette of Bulgaria, the official publication of every act and amendment.
- **Material**: one item published in a Gazette issue, such as an act, an amending act, a decree or a decision, served as one page on the Gazette's website.
- **Chain**: the sequence of Gazette events (promulgation and every amendment) that the corpus records for one act.
- **Title pass**: the coverage-map run of 6 September 2026 that matched Gazette materials to acts by title only.
- **Body scan**: the planned reading of each material's text to find amendments to other acts carried inside it.
- **Near miss**: a material whose title scored high against an act but was refused by the resolver's guards.
- **Write gate**: the single function through which every corpus file is written, which runs the registered checks and refuses a file that fails one.
- **Witness**: a consolidated text (lex.bg, the Ministry of Justice portal) that the corpus is compared against and never deferred to.
- **Lane**: the category a divergence is adjudicated into: a source error on the witness side, a defect on our side, a risk signal, or an editorial difference.
- **Decision log**: the dated register of decisions in this repository; **D-047** (1 July 2026) is the parser data-loss remediation, **D-064** (5 September 2026) the owner's answers to the graded-source design, **D-065** to **D-068** (21 October 2026) the four decisions of this document.
- **Future-requirements register**: the backlog of registered requirements and defect classes; **FR-043** is the open question whether repealed predecessor acts enter the corpus.
- **P0, P1**: the first two phases of the graded source model's implementation plan of 5 September 2026 (the coverage map; the provenance block and the pilot).
- **Stage 1, stage 2**: the two stages of this document's plan (section 5).
- **LC-03, LC-04**: the compliance-auditor and registry-keeper loops of the oversight catalogue, the model for the daily loop.

## Provenance

The counts in section 3 come from the files on disk, the decision log, the coverage-map research note of 6 September 2026 and the enumeration run of 21 October 2026, all in this repository. The lex.bg reachability was checked with a plain client at 02:00 Sofia time on 21 October 2026. The price table comes from the Claude API reference bundled with Claude Code, cached on 6 October 2026. The loop spec is `.ahelia/loops/dv-daily-sync.yaml` and its ledger `.ahelia/loops/ledger/dv-daily-sync.md`; the refresh log is `data/runs/refresh-2026-10-21.log` and the catch-up logs `data/runs/dv-catchup-2026-10-21.log` and `data/runs/dv-bodies-catchup-2026-10-21.log`. The material size average comes from the 16 cached bodies, measured as characters of text divided by three.
