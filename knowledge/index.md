---
okf_version: "0.2"
bundle_id: legalize-bg-knowledge
origin: Ahelia-Consulting-EOOD/legalize-bg
---

# legalize-bg knowledge base

What this bundle answers: how the legalize-bg pipeline should read, consolidate and audit Bulgarian legal text with a reasoning model, and what the model documentation, the research and the practice of other systems say about it.

Topic hubs:

- [How the reasoning run reads and audits legal text](/concepts/hub-reading-architecture.md)

Date: 2026-10-21.

Trust: agent-written; no concept has been confirmed by a person yet.

<!-- CATALOG -->

# Topic hubs

* [How the reasoning run reads and audits legal text: unit of work, model choice, checks](concepts/hub-reading-architecture.md) - Read per provision, return pointers into custom content blocks and edit operations, verify completeness by string equality, and choose the model tier by cost, since the checks bound the omission errors whatever the tier.

# Concepts

* [Reading architecture for the reasoning run](concepts/reading-architecture.md) - The reasoning run reads one provision at a time, returns block-index citations and edit operations, and a script assembles and checks the text; model tiers are chosen by the check's pass rate per block.

# Research runs

* [2026-10-21: Which model, and which unit of work, makes reading and auditing Bulgarian legal text both cheaper and more reliable?](references/2026-10-21-model-selection/report.md) - Read per provision, not per act; have the model return pointers into custom content blocks and edit operations, never retyped text; verify completeness by total string equalities; then the cheapest model that passes those checks carries the bulk, with escalation to a stronger one, and the audit of the whole corpus costs tens of dollars at list price.
