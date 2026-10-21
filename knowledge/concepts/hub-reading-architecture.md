---
type: Topic Hub
title: "How the reasoning run reads and audits legal text: unit of work, model choice, checks"
description: "Read per provision, return pointers into custom content blocks and edit operations, verify completeness by string equality, and choose the model tier by cost, since the checks bound the omission errors whatever the tier."
topic: reading-architecture
generated: { by: claude-code/claude-fable-5-1, at: "2026-10-21T05:30:00+03:00" }
sources:
  - id: chroma-degrades
    resource: https://www.trychroma.com/research/context-rot
    extract: /references/2026-10-21-model-selection/sources.md#5
  - id: chroma-models
    resource: https://www.trychroma.com/research/context-rot
    extract: /references/2026-10-21-model-selection/sources.md#33
  - id: nllp-exact-match
    resource: https://aclanthology.org/2025.nllp-1.29/
    extract: /references/2026-10-21-model-selection/sources.md#10
  - id: nllp-model
    resource: https://aclanthology.org/2025.nllp-1.29.pdf
    extract: /references/2026-10-21-model-selection/sources.md#11
  - id: citations-valid
    resource: https://platform.claude.com/docs/en/build-with-claude/citations
    extract: /references/2026-10-21-model-selection/sources.md#21
  - id: citations-blocks
    resource: https://platform.claude.com/docs/en/build-with-claude/citations
    extract: /references/2026-10-21-model-selection/sources.md#44
  - id: uk-editors
    resource: repo:docs/research/2026-09-05-consolidation-precedents.md
    extract: /references/2026-10-21-model-selection/sources.md#31
  - id: haiku-purpose
    resource: https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5
    extract: /references/2026-10-21-model-selection/sources.md#18
  - id: unit-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: pointer-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: check-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: tier-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
  - id: cost-inference
    kind: inference
    resource: /references/2026-10-21-model-selection/report.md#reasoning
---

# How the reasoning run reads and audits legal text: unit of work, model choice, checks

The *reasoning run* is the model-driven step of the legalize-bg pipeline that decides what a legal text means; the *session* is the owner's Claude Code session, where the hardest cases are adjudicated. The texts are the acts of the Bulgarian corpus and the materials of Държавен вестник, the State Gazette.

## Current answer

- The performance of every model tested falls as the input grows, with distractors making it worse.[^chroma-degrades][^chroma-models] **moderate**
- Therefore the unit of work is one provision with its source span, never a whole act.[^unit-inference] **moderate**
- In the one measured study of a model applying gazette amendments (GPT-4.1-mini on 908 German pairs), half of the single-step results and a fifth of the multi-step results matched the official text exactly, though most errors were small.[^nllp-exact-match][^nllp-model] **moderate**
- Therefore the model returns pointers and edit operations, and a script assembles the text; the source's wording is copied, never retyped.[^pointer-inference] **moderate**
- Pointers are checkable: a citation is a valid pointer into the document, and with custom content blocks it is a block index range, so the cited blocks can be required to re-assemble the whole source.[^citations-valid][^citations-blocks] **strong**
- Omission and duplication are then decided by string equality, without reading; only the label stays a judgement, recorded with its citation.[^check-inference] **moderate**
- The United Kingdom's state consolidator applies repeals and commencements automatically and leaves textual substitutions to editors; the design puts the model where the editor sits and the script where the system sits.[^uk-editors] **moderate**
- Model choice is a cost choice, because the output is labels, not text: Claude Haiku 5.5, built for classification and extraction, is the cheapest tier; Sonnet 5.5 and Opus 5.5 do the same work at about twenty and forty times the price; a block the check rejects goes to a stronger tier, a disagreement to the session; every escalation is counted, so each run reports each tier's label error rate.[^haiku-purpose][^tier-inference] **weak**
- The audit of the whole corpus is then about 45 dollars on Haiku 5.5, about 290 on Sonnet 5.5 and about 580 on Opus 5.5 at list price, against about 860 for whole-act reading and about 2,200 for a whole-act re-render on Opus 5.5.[^cost-inference] **weak**

## Concepts

- [Reading architecture for the reasoning run](/concepts/reading-architecture.md)

## Research runs

- [2026-10-21: Which model, and which unit of work, makes reading and auditing Bulgarian legal text both cheaper and more reliable?](/references/2026-10-21-model-selection/report.md)

## Replaced

- none

## Earlier research outside this bundle

- `repo:docs/research/2026-06-22-I1-legalize-ecosystem.md`: the Legalize ecosystem and its fetcher interfaces; this topic uses its finding that no Legalize country self-consolidates from a raw amendment stream.
- `repo:docs/research/2026-06-22-I2-lawvm.md`: the deterministic replay compiler; this topic uses its Finland numbers.
- `repo:docs/research/2026-09-05-consolidation-precedents.md`: how state consolidators work; this topic uses the editor-versus-system division at legislation.gov.uk.

[^chroma-degrades]: Chroma, Context Rot: "Across all experiments, model performance consistently degrades with increasing input length."
[^chroma-models]: Chroma, Context Rot: "we evaluate 18 LLMs, including the state-of-the-art GPT-4.1, Claude 4, Gemini 2.5, and Qwen3 models."
[^unit-inference]: Inference: the run's Reasoning, item 1.
[^nllp-exact-match]: Prior et al., NLLP 2025: "only 50.3% of exact matches (single-step) and 20.51% (multi-step) could be achieved".
[^nllp-model]: Prior et al., NLLP 2025: "78% requiring only trivial corrections".
[^pointer-inference]: Inference: the run's Reasoning, item 2.
[^citations-valid]: Anthropic, Citations: "citations are guaranteed to contain valid pointers to the provided documents".
[^citations-blocks]: Anthropic, Citations: "Citations include the content block index range (0-indexed) corresponding to the original content list provided."
[^check-inference]: Inference: the run's Reasoning, item 3.
[^uk-editors]: Consolidation precedents, legislation.gov.uk: "but textual substitutions are applied by editors."
[^haiku-purpose]: Anthropic, What's new in Claude Haiku 5.5: "built for high-volume, latency-sensitive work such as classification, routing, extraction, and subagent tasks".
[^tier-inference]: Inference: the run's Reasoning, item 4.
[^cost-inference]: Inference: the run's Reasoning, item 7.
