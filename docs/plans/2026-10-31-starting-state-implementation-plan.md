# The starting state, rebuilt forward: implementation plan

Who this is for: the owner, who on 31 October 2026 adopted the diagram "Corpus Way of Work" of 22 October 2026 as the working model of this corpus and asked for its implementation to be planned. This document is that plan, for the owner's approval and for the first goal line.

## 1. The decision this document asks for

Approve this plan as the plan of record for the working model, and give the go-ahead for its first session, which builds the diagram's steps S0 and S1 together (the diagram names its steps S0 to S5 for task 1 and F1 to F3 for task 2), under the goal line of section 6 and the budget stated there. The other decisions the work needs are gathered in section 7, with a recommendation each. Two of them, the preflight for a Gazette-sourced act's frontmatter and the amendment of one ruling, are needed inside the first session and are marked so; the rest can follow.

The plan builds the nine steps the diagram proposes, in the order the diagram gives and with the bounds the owner set on 22 October. Every step ends with acts correctly committed to git or with case files the owner reads. No route runs past its known steps. Every model call goes through a lean project agent under the owner's session plans. Nothing in it reopens a decision the owner recorded; where a step touches a recorded decision or a protected surface, section 7 asks.

## 2. The owner's words, read back

The owner's words of 31 October 2026, in this session: "based on that artifact, I agree with it to be our working model. please, plan its implementation accordingly", and before that, "without the artefact and confirmation we have it 100% no work is starting". The artifact was confirmed as the diagram file at commit 8aaf937cf on the branch `claude/run-design-ab4d70`, byte for byte apart from the viewer's wrapper lines, before any planning began.

Each item below is tagged with its source: the owner's words, the diagram (the artifact, by section), a recorded decision, an owner fact in `.claude/CLAUDE.md`, or "my addition".

1. **The working model is the diagram's two tasks.** Task 1 defines a starting state of sufficient quality: every act read from lex.bg except the acts on a maintained exceptions list, which are investigated and committed from the source the list names. Task 2 rebuilds that state forward with each Gazette issue and compares it with lex.bg from time to time as the quality measure. (The owner's words of 31 October; the diagram, section 1; decision D-074.)
2. **The steps are S0 to S5 for task 1 and F1 to F3 for task 2, in the diagram's order and dependencies.** F1 and F2 carry plan steps 5 and 8 of 21 October; F3 was the diagram's own addition, adopted with it. S0 and S1 come first, together. S2 and S3 run side by side after S1. S4 and S5 follow S3. F1 follows S3's profiles, F2 follows F1, and F3 follows F2. (The diagram, section 6.)
3. **Being on the list is not an outcome.** Every listed act has a route that ends with the act correctly committed to git. Only such acts count as done, and every report states first the distance left: the acts not yet correctly committed. (The diagram, section 1; owner facts of 21 and 22 October 2026.)
4. **Every route is bounded.** It stops when its known steps are used up, when a step changes nothing, or when the next step is not defined. It never runs a third round, never runs a step again on inputs it has already run on, and never edits text just to make a check pass. On a stop it writes a case file of fixed form. The owner reads a run's case files together at the run's end. (The diagram, sections 1 and 6, step S0; owner fact "Pipelines are bounded".)
5. **Every source goes through the same single reading step:** one labeller, one ladder, one write gate. What a source's text says, and whether a difference from a witness is the source's error or lex.bg's, is a reading of free text. A model run decides it and records the decision as data. Scripts fetch. (The diagram, section 1, figure caption; owner facts of 21 October on mechanical checks and on scripts and the reasoning run.)
6. **The engine is built, verified on a few representative acts of each kind, then used case by case; the backfill of every act's history is dropped.** (Decision D-074; the diagram, sections 1 and 6.)
7. **Every model call goes through a lean project agent under the owner's session plans, several tasks per call, never an API key and never a general-purpose subagent; costs are estimated from past transcripts and measured at the first batch of the real run.** They are reported by token type and cache type. (Owner facts of 21 and 22 October 2026; decision D-070.)
8. **The first entry of the exceptions list is the Закон за обществения транспорт**, fixed as an ordinary entry with no specification of its own, because the owner uses it daily. (Owner fact of 22 October; the diagram, step S1.)
9. **Protected surfaces are the owner's.** Setting the frontmatter of an act taken from the Gazette, in particular its source field (`fuente`) and its provenance base (the part of the provenance block that names the page or material the text came from, with its hash), changes Surface 2 and goes through the project's preflight before such an act is written. (The project's `CLAUDE.md`, Protected Surfaces; the record of 22 October, "Still open for the owner"; my addition that S1's first commit of the transport law waits on this.)
10. **The content check changes ruling 7 of decision D-072 for the lost-text finding.** Today that ruling lets an irregularity the page itself carries, such as a heading with nothing under it, be recorded as a source finding while the act is still written. Under the content check an empty section no longer passes through: it sends the act to the list. (The diagram, step S1; my addition that this is an amendment of a recorded decision and so needs the owner's word, asked in section 7.)
11. **My additions, marked as such throughout:** the file forms of the exceptions list, the case file and the act profiles; the two new lean agents (an investigator and a settler); a Gazette splitter beside the lex.bg one; a fetch-only script for the Ministry of Justice portal; the budgets; the order of the audit batches.

## 3. Where the work stands on 31 October 2026

- **The path of sections 2 to 5 of the diagram is built** on branch `claude/run-design-ab4d70`, in draft pull request #48 onto the plan branch `plan/2026-10-21-reasoning-driven-corpus` (draft pull request #47). Fifty acts, the 16 of the test set and the 34 of batch 1, went from their lex.bg page through the labeller, the ladder, the rulings of D-072, the write path and the single write gate into git. Each carries its run record (D-073). A rerun leaves all 50 unchanged. Only the owner merges either pull request. (Sources: the diagram, section 7; `docs/plans/2026-10-21-write-path-session.md`, section 1; the branch's commits.)
- **The run driver is the measured lean design of D-070:** the `labeller` agent without the instruction files, eight sections per call file, twenty-five re-labels per ladder call, answers as compact files. Its full-corpus estimate for round 0 over the 3,616 act pages that hold an act is 190 million tokens counted once, 360 million cost-weighted. The ladder adds about 36 million at the design's densities. Round 0 takes about eighteen hours of wall time at eight calls in flight. (Source: `docs/plans/2026-10-22-run-driver-design.md`, sections 10 and 11; its `step7/estimate.md`.)
- **The raw store holds 3,623 of the 3,624 lex.bg pages**, seven of them site chrome with no act; the Gazette index holds 4,160 issues and 35,363 materials through бр. 96/2026, with the bodies of 151 catch-up materials fetched. (Sources: `docs/testing/2026-10-22-structure-map-results.md`; the memory pointer of 22 October; `data/dv/`.)
- **Known on the exceptions side:** three acts need another source: the transport law and the Закон за прозрачност при представителство на интереси, whose § 1 lex.bg drops, and Указ № 883 от 1974, whose corpus text came from strategy.bg. The dropped-section detector of FR-042 flagged 103 acts with an empty section. In the corpus, 107 acts were promulgated before the Gazette's online archive begins, and 202 Gazette repeal titles were never attributed to an act. (Sources: the diagram's status figures; FR-042 in `docs/frs/INDEX.md`; `docs/research/2026-09-05-dv-coverage-map/README.md`.)
- **Nothing of task 1 or task 2 is built** beyond that path: no exceptions list, no route driver, no case-file form, no Gazette splitter, no engine. The loop spec `.ahelia/loops/dv-daily-sync.yaml` exists in status proposed. (Source: the diagram, section 7.)

## 4. The work, step by step

Each session's work is one pull request onto the branch of the one before it; S0 and S1 share one. A fresh-context reviewer on a model other than the one that did the work reviews it until no blocking or major finding remains, under the review rule's stopping condition (the number of major findings not dropping for two rounds) and a review budget named in each goal line. Each step's budget is an estimate from the transcripts of the runs so far; the first batch of each step measures it, and work past a budget waits for the owner's go. Tokens are reported by token type and cache type with the calls' durations.

### S0: bounds and case files, for every route (with S1, one session)

What is built. A route driver, `reading/routes.py`. A route is a named, ordered list of known steps with their inputs. The driver runs an act through its route and stops at a fixed point: the steps are used up, a step is reached again with inputs it has already run on (the hash of each step's inputs is kept, so running it again would change nothing), or the next step is not defined for this defect or era. The ladder's two rounds are the first route; the write path is the last step of every route. On a stop without a committed act the driver writes a case file, `docs/cases/<slug>.md`: a fixed YAML frontmatter (act, route, the step it stopped at, the exception, what was tried with the paths of its evidence, the run id, the date) and three short prose parts: lessons learnt, proposal, and the owner's ruling, empty until given. A run's report lists its case files together; the owner reads them at the run's end.

The checks that are mechanical and block are these: the case file's frontmatter against its schema, a stopped act without a case file, a route step run twice on the same input hash, and a third ladder round, which the ladder's round limit already refuses. What a case file's prose says is free text: the model writes it, the owner reads it.

Done when: the driver and the case-file form are in with tests (a route that stops at each of the three fixed points, a refused duplicate step, a refused stopped act without a case file), and the routes of S1 run through it. It commits no act itself. Budget: no model call beyond the reviews.

### S1: the exceptions list and its routes (with S0, one session)

What is built.

1. **The list,** `docs/data/source-exceptions.yaml`: per act its slug and its defect from a closed set (dropped section, wrong text, page without an act, server error, source before the archive). Then its source from a closed set (the Gazette's HTML materials, the Gazette's issue PDFs, the Ministry of Justice portal, strategy.bg, a paid service) and the source's address, a material id or a URL. Then its route from a closed set (whole act from its promulgation material, history through the engine, source before the archive, investigate), the evidence (a decision, an audit or a case file) and where it stands (listed, investigated, committed, stopped with a case file). Four mechanical checks: the file loads against its schema, every entry names a route, the write path refuses a listed act on the lex.bg path by name, and a report prints each entry's distance to its commit.
2. **The investigation,** a lean project agent `investigator` (Read and Write only, Opus, defined in `.claude/agents/`): scripts fetch what the act's defect needs (the lex.bg page text from the raw store, the Gazette material named by the coverage map or by a title search of the index, the Ministry of Justice portal's text), and the agent reads them and writes the entry's defect, source and route as data in a fixed answer form that the checks load. One run per act; a second only on new evidence; otherwise a case file.
3. **The content check,** in the reading path: the `empty_section` finding, and a first § above 1 in the act's own provisions, stop the write and put the act on the list with the route "investigate" instead of being carried as source findings. This amends ruling 7 of D-072 for those findings (section 7, decision 3).
4. **The witnesses,** `reading/witnesses.py`: for an act read from any source, its assembled body is compared with the lex.bg page text and with the Ministry of Justice portal's text (a fetch-only script `scripts/raw_fetch_moj.py` into `data/raw/moj/`, one request per second, hash and time kept, my addition); the comparison is a mechanical diff at the block level; each difference is settled by a lean agent `settler` as the source's error, the witness's error or a timing difference, recorded as data beside the act's run record. An act read from lex.bg cannot be witnessed by lex.bg itself; whether the portal is compared for such acts is decision 4 of section 7. For the transport law, read from the Gazette, both witnesses are compared.
5. **The Gazette as a source,** `reading/splitter.py` gains `split_dv` for a material's HTML from `dv.parliament.bg` (my addition): the same block contract (every character in exactly one block), the same labeller, ladder, rulings, checks and write path. The route "whole act from its promulgation material" fetches the material (`python -m fetcher.dv material`), splits it, labels it, writes it. The frontmatter of such an act carries the Gazette as its source field and a provenance base naming the material: Surface 2, preflight first (section 7, decision 2).
6. **The first entries.** The transport law (route: whole act from ДВ бр. 32/2026, material 242220; the index through бр. 96/2026 lists no amendment, and the route searches the materials after it before writing). The Закон за прозрачност при представителство на интереси (route: history; it stops with a case file until F1, since ДВ бр. 55/2026 amended it). Указ № 883 (route: source before the archive, S4).

Done when: the list is committed with its tests and every entry names its route. A write of the transport law from lex.bg is refused by name. The transport law is committed from the Gazette with § 1 and its twelve definitions, its witness differences settled and recorded. The other two entries stand at their bounded stops with case files. The distance left is printed: entries listed, entries committed.

Budget, estimated from the runs so far: the transport law is 572 blocks, 17 sections, so round 0 is three labeller calls and the ladder at most two. Three investigator runs and one settler run each read two or three texts of an act's size, under 40,000 tokens of content each. In all that is under 1 million tokens of calls, and about 450,000 for three fresh-context reviews at the measured 150,000 each. The first session's goal line states 1.5 million tokens; past that figure the session waits for the owner's go.

### S2: what lex.bg gets wrong (after S1, beside S3)

What is built. The dropped-section detector of FR-042 runs over every raw page (a script, no model). Each of its candidates is checked against the Gazette. A script fetches the act's promulgation material from the coverage map's attribution. The investigator reads the two texts and records whether the Gazette carries what lex.bg lacks, and what kind of error it is, from a closed set that grows only by the owner's word (dropped section, dropped provision, wrong number, wrong text, missing amendment). A register, `docs/data/lexbg-defect-kinds.yaml`, holds each kind with its evidence and, where the form allows one, its detector. After S3, a sample of acts per profile goes through the same comparison. Every act confirmed wrong enters the exceptions list with its route. Since most such acts were amended, most routes are "history" and stop with a case file until F1.

Done when: the register is committed, each of the 103 candidates carries a recorded verdict, and every act confirmed wrong is on the list with a route, correctly committed or stopped with a case file. Budget: 103 investigator runs at about 20,000 tokens of content each, about 2 million tokens counted once, plus the per-profile sample after S3, sized then; measured on the first ten candidates.

### S3: a profile of every act (after S1, beside S2)

What is built. A register, `docs/data/act-profiles.csv`, one row per act: kind (the frontmatter's rank field, `rango`), Gazette era from the publication date (HTML from 2003, PDF 1989 to 2002, before 1989), grade, layout features counted by script from the raw page's blocks (annex headings, table rows, images, unnumbered paragraphs, superscript numbers, repeated headings), known defects from S2, and source. For the 107 acts begun before the archive, whether each is still in force: a script pairs each with the Gazette's 202 unattributed repeal titles by title words, and the `investigator` reads each pairing and records in force, repealed by which title, or unknown. The register's form is fixed and checked; the model judges only the pairings.

Done when: the register covers all 3,624 corpus acts, the seven whose lex.bg page holds no act included, and the list of acts in force from before the archive is recorded with its evidence. Budget: 107 investigator runs at under 10,000 tokens of content each, about 1 million tokens counted once.

### S4: sources for the acts before the archive (after S3)

What is built. For each act on S3's list, the authoritative source is decided and recorded on the exceptions list: the Ministry of Justice portal, the Gazette's issue PDFs from 1989, strategy.bg or another state source. A PDF issue is read as images by the session's own model, which is the vision-based reading that the plan of record scheduled for stage 2; S4 brings forward only what these acts need (my addition). The route for a source before the archive fetches the text by script, reads it through the same labeller and write path, and settles the witnesses. The provenance of Указ № 883 is traced in the owner's legislation repositories and recorded, and ДВ бр. 39/1974 is looked for. A paid service is a spending decision (section 7, decision 6).

Done when: every act on S3's list is committed from its named source, or from lex.bg once checked against it, or stopped with a case file. Budget: sized from S3's count of acts in force and the sources found. A first batch of ten acts measures it. A PDF-era act read as images is the costly case and is counted separately.

### S5: the audit, by profile (after S3, in batches)

What is built. Nothing new: the run driver of D-070 and the routes of S0 and S1, over the 3,574 acts not yet read, in batches of one profile each, each batch agreed with the owner with its printed estimate. A new form met in a batch becomes a ruling and its test; an act with lost text goes to the list and into its route. Each batch ends with its acts committed or stopped with case files, and the owner reads the case files at the batch's end.

Done when: every act is correctly committed through the gate, from lex.bg or from its route, or stopped with a case file the owner has read. That is the starting state as the diagram defines it; the stopped acts are its distance left and are printed as such, since only a correctly committed act counts as done. The seven corpus acts whose lex.bg page holds no act are among the 3,574 and enter the list with the defect "page without an act". Budget: the design study's estimate over the whole corpus is 190 million tokens counted once for round 0 and about 36 million for the ladder (360 and 54 million cost-weighted), with about eighteen hours of wall time for round 0. The first batch measures the per-section figure before the next batch is agreed.

### F1: the engine (after S3's profiles; plan step 5)

What is built, in five parts. The material splitter for the Gazette's HTML materials, from S1. The attribution step: which act a material changes, from the title and opening blocks, recorded as data. The instruction step: each amending instruction turned into an operation on the act's addressed provision, recorded as data. The apply-and-check step: the operation applied by script, the result through the checks and the write gate. The witness comparison with its settlement. The engine is a reasoning run on the lean agents; what it cannot apply with certainty stops with a case file. It is verified first on the representative acts of each kind that the owner agrees from S3's profiles: their history is rebuilt from the Gazette and every difference from the witnesses settled; that is the evidence of whether the engine can be built. After that it runs on each new issue, and rebuilds a complete history only case by case.

Done when: the representative acts of every kind are committed with their history rebuilt, every difference settled and the engine's errors counted per kind, and the kinds it cannot do stop with case files. Budget: unknown until the splitter and the attribution step exist. The catch-up materials of бр. 63 to 96/2026 (151 bodies on disk, 55 of them in scope by title) are the first measured batch, estimated before it runs.

### F2: the daily loop (after F1; plan step 8)

What is built. The loop spec moves from proposed to supervised: the entry command fetches the issues after the last ledger mark, runs the engine, opens one pull request per run and appends a ledger row; the case files of the run are in the pull request. It becomes active once it has run for a period the owner sets without any proposal being rejected.

Done when: the loop has kept the corpus current for that period with its case files read. Budget: per run, the engine's measured per-material figure times the issue's materials in scope.

### F3: the periodic test against lex.bg (after F2; the diagram's addition)

What is built. On a schedule the owner sets, a script fetches every act the engine changed in the period from lex.bg and from the Ministry of Justice portal and compares it with the corpus by the witness diff. The settler settles each difference as the engine's error, the witness's error or a timing difference. The count of the engine's errors per period is the quality measure, recorded as data; an engine error is fixed in the engine and the act re-committed.

Done when: the first test is committed with its settled differences and its measure. Budget: one settler run per differing act, sized at the first test.

## 5. Order, pull requests and parallel sessions

The order is the diagram's. S0 and S1 run in one session. Then S2 and S3 run in two sessions side by side, each in its own worktree. Then come S4 and the first batches of S5, F1 once S3 has given the representative acts, and F2 and F3 after it. Each step's branch is cut from the step before it and merges only when the owner merges. Until pull requests #47 and #48 are merged, every branch stacks on the run-design branch.

What two writers may not share: the exceptions list and the case files are written by one session at a time; S2 and S3 write different files, the defect register and the profile register. Both add list entries only through the route driver, which refuses a second entry for the same act.

## 6. The first goal line: S0 and S1

Objective: the route driver with its bounds and case-file form, the exceptions list with its checks, the investigator and settler agents, the Gazette splitter and the portal fetcher, and the transport law committed from the Gazette with § 1 and its twelve definitions.

Done-condition, printed as evidence. The reading tests pass with the new tests named. The route report prints the list's entries with their distance: the transport law committed, the two others stopped with case files named. The write path, asked to write the transport law from the lex.bg path, prints the refusal by name. The commit of the transport law shows the four trailers and its provenance base naming material 242220. The witness record of the act lists its differences and their settlements. The token report gives every call by type and cache type.

Non-goals: no change to the roles of script and model (D-069), no engine, no act other than the transport law written, no change to a protected surface before its preflight is signed, no API key, and no corpus file written outside the gate.

Budget: 1.5 million tokens of plan usage in all, calls and reviews. Past it the session waits for the owner's go. Review clause: fresh-context review on a model other than the one that did the work, stopping when majors do not fall for two rounds or at the owner's ruling, three rounds at most.

Where state lives: the worktree of the session on its branch, the run folder of the transport law under the data folder, and the case files and the list in git.

Offered goal line: `/goal S0+S1 of docs/plans/2026-10-31-starting-state-implementation-plan.md: the route driver with bounds and case files, the exceptions list with its checks, and the transport law committed from ДВ бр. 32/2026 with § 1; done when the section 6 evidence is printed; budget 1.5 million tokens; reviews stop when majors do not fall for two rounds or at the owner's ruling, three rounds at most.`

## 7. The owner's decisions

Decision 1 is the approval itself. Decisions 2 and 3 are needed inside the first session: 2 before the transport law is written, 3 before the content check is built. The rest can follow.

1. **Approve this plan and the first goal line.** Recommendation: approve as written.
2. **The frontmatter of an act taken from the Gazette** (Surface 2): its source field set to the Gazette, its identifier field kept as the act's key, its provenance base naming the material. Options: (a) a preflight document signed before the transport law is written, in the first session; (b) the transport law stays stopped with a case file until the preflight is signed in a later step, and the first session's done-condition then ends at that case file. Recommendation: (a). The preflight is short, because the change is the value of one field and the content of one block.
3. **Amend ruling 7 of D-072:** an empty section, and a first § above 1 in the act's own provisions, stop the write and list the act. Recommendation: yes; it is what the diagram's content check says.
4. **The quality bar of the starting state.** Options: (a) every act read to no exception from the checks, no lost-text finding, and its portal witness compared and settled; (b) the same without the portal comparison for acts read from lex.bg, the portal compared only at the periodic test. Recommendation: (a); the portal fetch is one request per act, about an hour over the corpus, and the settlement runs only on the acts that differ.
5. **The representative acts of each kind for F1:** proposed from S3's profiles when S3 ends, agreed then. Recommendation: defer to S3's end.
6. **A paid consolidated-law service (APIS) for a short period:** a spending decision. Recommendation: defer until S2 and S4 show acts no free source settles, and decide on that count.
7. **The period of the lex.bg test (F3) and the supervised period of the loop (F2).** Recommendation: monthly test; two weeks supervised, as the plan of record's step 8 said.
8. **The merge of pull requests #47 and #48**, which the first session stacks on. Recommendation: merge both before the first session's pull request is opened, so the stack stays two deep.

## Glossary

- **The diagram, the artifact:** `docs/plans/2026-10-22-reading-write-path-diagram.html`, "Corpus Way of Work", published at the artifact address the owner sent; the working model.
- **Starting state:** every act correctly committed to git, from lex.bg or from its route on the exceptions list (task 1).
- **Forward rebuild:** the starting state updated with each new Gazette issue by the engine (task 2).
- **Exceptions list:** the kept data file of acts whose text is not taken from lex.bg, each with its defect, source and route.
- **Route:** the ordered, bounded steps that take a listed act to a correct commit.
- **Case file:** the record a route writes when it stops without a correct act: the exception, what was tried, the lessons, a proposal; the owner reads it.
- **Witnesses:** lex.bg and the Ministry of Justice portal, compared with but never trusted (decision D-061).
- **Labeller, investigator, settler:** lean project agents (Read and Write only) that label blocks, record an act's defect and source, and settle a witness difference.
- **The ladder, round 0, excepted block, residue:** round 0 labels every block of an act; a check that fails puts an exception on one block, the excepted block; the ladder gives each such block two more rounds with its neighbours; what is still excepted after round 2 is the residue, read by a person or a stronger model (decision D-069).
- **Provenance base:** the part of an act's provenance block in the frontmatter that names the page or material its text was read from, with the fetch time and the hash.
- **Carried source finding, ruling 7 of D-072:** a finding that describes the page itself (an empty section, a malformed head, a gap in numbering) and that today is recorded with the act while the act is still written.
- **Cost-weighted tokens:** tokens counted with each class at its price, so that a cached read counts less and a cache write more than a token counted once.
- **The four trailers:** the commit message lines `Source-Id`, `Source-Date`, `Norm-Id` and `Record-Id`.
- **Grade:** the provenance grade of an act (A Gazette-complete, B Gazette-audited snapshot, C pre-1989 base; decision D-059).
- **Distance:** the acts not yet correctly committed, stated first in every report.
- **Plan step 5, stage 2:** the Gazette engine and the later stage of the plan of record of 21 October 2026.
- **The engine:** the reasoning run that turns a Gazette material into changes to an act (plan step 5).
- **The write gate:** `corpus_gate.write_act`, the only code that writes a corpus file.
- **D-069, D-070, D-072, D-073, D-074:** decisions of the decision log: the reading architecture, the run driver, the rulings on lex.bg's forms, the run record, the starting state rebuilt forward.
- **FR-042:** the registered defect "lex.bg drops promulgated sections of some acts".
- **Surface 2:** the YAML frontmatter schema, a protected surface.
- **ДВ бр. 32/2026, material 242220:** the Gazette issue and material that promulgated the Закон за обществения транспорт.

## References

- The diagram `docs/plans/2026-10-22-reading-write-path-diagram.html` at commit 8aaf937cf, branch `claude/run-design-ab4d70`, 22 October 2026.
- `docs/plans/2026-10-22-owner-intent-sources-and-act-profiles.md`, the record of the owner's intent of 22 October 2026.
- `docs/plans/2026-10-22-run-driver-design.md` and its folder, the design study of 21 and 22 October 2026, with the full-corpus estimate in `step7/estimate.md`.
- `docs/plans/2026-10-21-write-path-session.md`, the write path.
- `docs/plans/2026-10-21-reasoning-driven-corpus.md`, the plan of record of 21 October 2026, whose stage-1 steps 5, 6, 7 and 8 this plan carries as F1, the run driver, S5 and F2, and whose step 9 D-074 dropped.
- `docs/sync/DECISIONS.md`, D-069 to D-075.
- `.claude/CLAUDE.md`, Owner facts of 21 and 22 October 2026.

## Provenance

Written on 31 October 2026 in the worktree `.claude/worktrees/starting-state-plan`, branch `plan/2026-10-31-starting-state`, cut from `claude/run-design-ab4d70` at 88e4d1294. The artifact was read through the Artifact tool after the owner shared it and compared with the file at every commit of the diagram; it equals the file at 8aaf937cf. The figures of section 3 come from the files named there; no model call was made for this plan beyond its reviews.
