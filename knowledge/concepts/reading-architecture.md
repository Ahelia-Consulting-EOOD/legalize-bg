---
type: Recommendation
title: "Reading architecture for the reasoning run"
description: "The reasoning run reads one provision at a time, returns block-index citations and edit operations, and a script assembles and checks the text; model tiers are chosen by the check's pass rate per block."
topic: reading-architecture
status: stable
generated: { by: claude-code/claude-fable-5-1, at: "2026-10-21T05:10:00+03:00" }
sources:
  - id: anthropic-top
    resource: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips
    extract: /references/2026-10-21-model-selection/sources.md#1
  - id: anthropic-quotes
    resource: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips
    extract: /references/2026-10-21-model-selection/sources.md#3
  - id: chroma-distractors
    resource: https://www.trychroma.com/research/context-rot
    extract: /references/2026-10-21-model-selection/sources.md#7
  - id: chunk-structure
    resource: https://arxiv.org/abs/2605.19806
    extract: /references/2026-10-21-model-selection/sources.md#26
  - id: nllp-similarity
    resource: https://aclanthology.org/2025.nllp-1.29/
    extract: /references/2026-10-21-model-selection/sources.md#10
  - id: nllp-generated
    resource: https://aclanthology.org/2025.nllp-1.29.pdf
    extract: /references/2026-10-21-model-selection/sources.md#11
  - id: citations-no-output
    resource: https://platform.claude.com/docs/en/build-with-claude/citations
    extract: /references/2026-10-21-model-selection/sources.md#22
  - id: citations-custom
    resource: https://platform.claude.com/docs/en/build-with-claude/citations
    extract: /references/2026-10-21-model-selection/sources.md#43
  - id: haiku-purpose
    resource: https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5
    extract: /references/2026-10-21-model-selection/sources.md#18
  - id: haiku-prices
    resource: https://platform.claude.com/docs/en/about-claude/pricing
    extract: /references/2026-10-21-model-selection/sources.md#15
  - id: neighbours-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: retyping-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: check-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: tier-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
---

# Reading architecture for the reasoning run

A recommendation for how the legalize-bg reasoning run reads materials of Държавен вестник (the State Gazette) and audits existing acts, drawn from the research run of 21 October 2026. Adopted by the owner on 21 October 2026 (decision D-069 in the repository decision log), with Claude Opus 5.5 for labelling and operations. Sections: [Terms](#terms), [1. Unit of work](#1-unit-of-work-one-provision), [2. Output](#2-output-pointers-and-operations-never-text), [3. Checks](#3-checks-total-on-form-recorded-on-meaning), [4. Model tiers](#4-model-tiers-decided-by-the-check).

## Terms

- **Reasoning run**: the model-driven step that decides what a text means; **adjudication read**: the same step done in the owner's Claude Code session (**the session**) on the cases the cheaper steps could not settle.
- **Leg**: one kind of work (attribution, labelling, consolidation). **Catch-up**: reading the Gazette issues published since the corpus was last updated. **Backfill**: reading every Gazette material since 2003. **Daily loop**: the scheduled run that keeps the corpus current.
- **Tag-stripped source**: a web page with its markup removed and its text kept. **Block**: one unit of that text cut by a deterministic splitter.
- **NLLP**: the Natural Legal Language Processing workshop, where the two consolidation studies appeared. **Chroma**: the company whose research report measured long-context degradation. **Legalize**: the open project of national legislation as Markdown files in git, of which this repository is the Bulgarian member.

## 1. Unit of work: one provision

A deterministic splitter cuts the tag-stripped source into candidate blocks along the markup the source already carries, and every character lands in exactly one block. The model sees one block, or one instruction with its target provision, with the text first and the question last,[^anthropic-top] and quotes before it labels.[^anthropic-quotes] Whole acts are never sent: distractors degrade the models tested,[^chroma-distractors] and neighbouring provisions act as distractors for one another.[^neighbours-inference] The natural unit on a statute is the section or subsection.[^chunk-structure]

## 2. Output: pointers and operations, never text

The blocks go to the model as custom content blocks, which the API cites by index without further chunking.[^citations-custom] For a structure audit the model returns, per block, a label and the block indices it covers. For an amendment it returns an operation: address, kind, the old string cited from the provision, the new string cited from the instruction. A script assembles the Markdown or applies the operation. Nothing is retyped. The one measured study of a model generating amended statutes reached 93 to 99 percent similarity but half exact matches,[^nllp-similarity] with a generated text as its output;[^nllp-generated] the run's reading is that re-emission is what fails, so a design without re-emission should not fail that way.[^retyping-inference] Cited text costs no output tokens.[^citations-no-output]

## 3. Checks: total on form, recorded on meaning

The concatenation of the cited blocks, in order, must equal the source text; an edit's old string must occur exactly once at its address and must be gone afterwards. These are string equalities, decidable without reading.[^check-inference] The label and the operation kind are judgements; each is recorded with its citation so a later reader can re-check it. A block the check rejects, or that the model marks doubtful, is an exception, not a blocked write: round 1 re-labels it together with its previous and next block, round 2 once more, and what is still excepted goes to a whole-act read by a Fable model or the owner, whose verdict is final and recorded (the owner's ladder of 21 October 2026).

## 4. Model tiers, decided by the check

Because the model returns labels and indices, not text, the output is small and the tier is a cost choice, not a reliability one: the omission checks bind whatever the tier, and the tier changes only the label error rate, which every run reports. The cheapest row is Claude Haiku 5.5, built for "classification, routing, extraction",[^haiku-purpose] whose price rises from 0.10 to 0.50 dollars per million input tokens above 100,000 tokens per request,[^haiku-prices] a threshold the per-block unit never reaches. The same audit on Sonnet 5.5 costs about twice ten, and on Opus 5.5 about forty times, the Haiku figure; the owner's remark of 21 October 2026 that the cheapest tier is not needed leaves the choice among the three to the owner. Rejected or doubtful blocks go to a stronger tier; disagreements go to the adjudication read in the session. Amendment operations run on Claude Sonnet 5.5 with the same escalation. Escalations are counted per model and per leg, so every run reports the error rate of each tier.[^tier-inference]

## 5. What is not decided here

How the runs are batched across the owner's Claude session plans, since the owner ruled on 21 October 2026 that no model call goes through an API key until the project is public and hosted (the Batch API figures of the run are comparisons, not spend); the scope questions of the catch-up (ratification laws, stand-alone decrees), which are the owner's. Decided on 21 October 2026 by D-069: the tier is Opus 5.5 for labelling and operations, with the exception ladder of section 3.

[^anthropic-top]: Anthropic, Prompting best practices: "Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples."
[^anthropic-quotes]: Anthropic, Prompting best practices: "ask Claude to quote relevant parts of the documents first before carrying out its task."
[^chroma-distractors]: Chroma, Context Rot: "Even a single distractor reduces performance relative to the baseline (needle only), and adding four distractors compounds this degradation further."
[^neighbours-inference]: Inference: the run's Reasoning, item 1.
[^chunk-structure]: Prior, Milanova, Schultz, Chunking German Legal Code: "chunking strategies aligned with the inherent legal structure - particularly section and subsection - based retrieval-achieve the highest recall".
[^citations-custom]: Anthropic, Citations: "Your provided content blocks are used as-is and no further chunking is done."
[^nllp-similarity]: Prior et al., NLLP 2025: "only 50.3% of exact matches (single-step) and 20.51% (multi-step) could be achieved".
[^nllp-generated]: Prior et al., NLLP 2025: "Our automated consolidation framework utilizes GPT-4.1-mini to apply amendments to existing laws."
[^retyping-inference]: Inference: the run's Reasoning, item 2.
[^citations-no-output]: Anthropic, Citations: "`cited_text` does not count toward your output tokens".
[^check-inference]: Inference: the run's Reasoning, item 3.
[^haiku-purpose]: Anthropic, What's new in Claude Haiku 5.5: "built for high-volume, latency-sensitive work such as classification, routing, extraction, and subagent tasks".
[^haiku-prices]: Anthropic, Pricing: "Claude Haiku 5.5 (for prompts up to 100,000 tokens) … $0.10 / MTok" and "Claude Haiku 5.5 (for prompts over 100,000 tokens) … $0.50 / MTok".
[^tier-inference]: Inference: the run's Reasoning, item 4.

# Related concepts

* [How the reasoning run reads and audits legal text: unit of work, model choice, checks](hub-reading-architecture.md)
