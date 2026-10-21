---
type: Source Log
title: "Source log: model selection and long-context reliability for reading and auditing legal texts"
topic: reading-architecture
generated: { by: claude-code/claude-fable-5-1, at: "2026-10-21T04:10:00+03:00" }
---

# Source log: 2026-10-21-model-selection

## Web Searches Performed
| # | Query | Date | Outcome |
|---|-------|------|---------|
| W1 | Anthropic long context prompting tips documentation Claude | 2026-10-21 | extract#1 to extract#3 (led to U1) |
| W2 | context rot long context LLM performance degradation study needle in a haystack 2025 2026 | 2026-10-21 | extract#4 to extract#9, extract#33 (led to U3) |
| W3 | Claude Haiku 5.5 model announcement capabilities context window pricing | 2026-10-21 | not-used (secondary coverage; the official pages U2 and U6 were read instead) |
| W4 | LLM legal text consolidation amendment application accuracy evaluation chunking per-article | 2026-10-21 | extract#10 to extract#14, extract#34, extract#35 (led to U4, U5, U15) |
| W5 | legalize-dev legalize pipeline legislation as code GitHub countries LLM consolidation | 2026-10-21 | extract#27 (led to U13); nothing on pipeline internals or model use |
| W6 | LLM applied to legislation consolidation official gazette government pilot 2025 2026 National Archives EUR-Lex AI amendments | 2026-10-21 | extract#25 (led to U11); nothing on a National Archives or EUR-Lex pilot |
| W7 | LLM legal document structure extraction articles paragraphs accuracy long documents chunking evaluation statutes | 2026-10-21 | extract#26, extract#32 (led to U12, U14); no benchmark of article-boundary extraction accuracy found |
| W8 | "Chunking German Legal Code" arxiv section subsection retrieval recall BGB | 2026-10-21 | extract#26 (the arXiv identifier of U14) |
| W9 | no search: U2, U6, U7, U8, U9 and U10 were opened from the links on U1 and from the Claude API reference bundled with Claude Code | 2026-10-21 | not-used (navigation, not a search; the pages are logged as web sources) |

## Documents Read
| # | File Path | Commit | Sections Read | Outcome |
|---|-----------|--------|---------------|---------|
| D1 | docs/research/2026-06-22-I1-legalize-ecosystem.md | 10df0ca5d | RQ1 to RQ4, conclusions | extract#28, extract#29, extract#38, extract#39 |
| D2 | docs/research/2026-06-22-I2-lawvm.md | 10df0ca5d | Finland numbers, failure model, forward replay | extract#30, extract#36, extract#37 |
| D3 | docs/research/2026-09-05-consolidation-precedents.md | 10df0ca5d | legislation.gov.uk, Australia, Légifrance sections | extract#31 |
| D4 | docs/research/2026-06-22-I4-official-consolidation.md | 10df0ca5d | headline result, Q1 (official consolidation: does it exist?) | negative: it inventories Bulgarian official sources and finds no state consolidation; it says nothing about models or how a reader processes text |
| D5 | docs/research/2026-09-05-dv-coverage-map/README.md | 10df0ca5d | Inputs table | extract#41 |

## Web Sources Referenced
| # | URL | Title | Date Accessed | Copy | Outcome |
|---|-----|-------|---------------|------|---------|
| U1 | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips | Prompting best practices (the long-context tips page redirects here) | 2026-10-21 | copies/U1.txt | extract#1 to extract#3 |
| U2 | https://platform.claude.com/docs/en/about-claude/pricing | Pricing | 2026-10-21 | copies/U2.txt | extract#15 to extract#17, extract#40 |
| U3 | https://www.trychroma.com/research/context-rot | Context Rot: How Increasing Input Tokens Impacts LLM Performance | 2026-10-21 | copies/U3.txt | extract#4 to extract#9, extract#33 |
| U4 | https://aclanthology.org/2025.nllp-1.29/ | Risks and Limits of Automatic Consolidation of Statutes (NLLP 2025), abstract page | 2026-10-21 | copies/U4.txt | extract#10, extract#34 |
| U5 | https://aclanthology.org/2024.nllp-1.13/ | Algorithm for Automatic Legislative Text Consolidation (NLLP 2024), abstract page | 2026-10-21 | copies/U5.txt | extract#14, extract#35 |
| U6 | https://platform.claude.com/docs/en/models/haiku-5-5/whats-new-haiku-5-5 | What's new in Claude Haiku 5.5 | 2026-10-21 | copies/U6.txt | extract#18 |
| U7 | https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5 | What's new in Claude Sonnet 5.5 | 2026-10-21 | copies/U7.txt | extract#20 |
| U8 | https://platform.claude.com/docs/en/build-with-claude/citations | Citations | 2026-10-21 | copies/U8.txt | extract#21, extract#22, extract#42 to extract#44 |
| U9 | https://platform.claude.com/docs/en/build-with-claude/batch-processing | Batch processing | 2026-10-21 | copies/U9.txt | extract#23, extract#24 |
| U10 | https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5 | What's new in Claude Opus 5.5 | 2026-10-21 | copies/U10.txt | extract#19 |
| U11 | https://www.efta.int/consolidated-eea-legal-acts | Consolidated EEA legal acts (EFTA) | 2026-10-21 | copies/U11.txt | extract#25 |
| U12 | https://arxiv.org/abs/2509.02241 | LLMs for LLMs: A Structured Prompting Methodology for Long Legal Documents | 2026-10-21 | copies/U12.txt | extract#32 |
| U13 | https://gigazine.net/gsc_news/en/20260425-legalize-es/ | legalize-es coverage (Gigazine) | 2026-10-21 | copies/U13.txt | extract#27 |
| U14 | https://arxiv.org/abs/2605.19806 | Chunking German Legal Code | 2026-10-21 | copies/U14.txt | extract#26 |
| U15 | https://aclanthology.org/2025.nllp-1.29.pdf | Risks and Limits of Automatic Consolidation of Statutes (NLLP 2025), full paper | 2026-10-21 | none (pdf) | extract#11 to extract#13 |

## Extracted Content
| # | Source ref | Locator | Extract (verbatim, <300 words) | Used in section |
|---|------------|---------|--------------------------------|-----------------|
| 1 | U1 | Long context prompting, first bullet | "Put longform data at the top: Place your long documents and inputs near the top of your prompt, above your query, instructions, and examples. This improves performance across all models." | 2 |
| 2 | U1 | Long context prompting, note | "Queries at the end can improve response quality by up to 30 percent in tests, especially with complex, multidocument inputs." | 2 |
| 3 | U1 | Long context prompting, third bullet | "Ground responses in quotes: For long document tasks, ask Claude to quote relevant parts of the documents first before carrying out its task. This helps Claude focus on the relevant content and ignore the rest of the document." | 2 |
| 4 | U3 | Introduction | "Our results reveal that models do not use their context uniformly; instead, their performance grows increasingly unreliable as input length grows." | 3 |
| 5 | U3 | Results summary | "Across all experiments, model performance consistently degrades with increasing input length." | 3 |
| 6 | U3 | Needle-question similarity | "By holding the needle-question pair fixed and varying only the amount of irrelevant content, we isolate input size as the primary factor in performance decline." | 3 |
| 7 | U3 | Impact of distractors | "Even a single distractor reduces performance relative to the baseline (needle only), and adding four distractors compounds this degradation further." | 3 |
| 8 | U3 | Impact of distractors, model behaviour | "Claude models consistently exhibit the lowest hallucination rates. Specifically, Claude Sonnet 4 and Opus 4 are particularly conservative and tend to abstain when uncertain, explicitly stating that no answer can be found." | 3 |
| 9 | U3 | LongMemEval | "We verify that the models are highly capable of succeeding on the focused inputs, then observe consistent performance degradation with the full inputs." | 3 |
| 10 | U4 | Abstract | "While automated metrics show high textual similarity (93-99%) for single-step and multi-step amendment chains, only 50.3% of exact matches (single-step) and 20.51% (multi-step) could be achieved; our expert assessment reveals that non-trivial errors persist and that even small divergences can carry legal significance. We therefore argue that any public or private deployment must treat outputs as drafts subject to rigorous human verification." | 1, 3 |
| 11 | U15 | page 397, Our Contribution, items 2 and 3 | "Our automated consolidation framework utilizes GPT-4.1-mini to apply amendments to existing laws." … "Our setup reveals low and highly variant exact match rates ranging between 2.36% and 75.93%, and a semantic similarity of 93-99% for four core legal codes (Civil, Criminal, Commercial, and Income Tax). Expert review of 100 imperfect consolidations revealed that 51% of errors had minimal to moderate impact, with 78% requiring only trivial corrections." | 3 |
| 12 | U15 | page 398, on Etcheverry et al. (2024) | "First, context window restrictions prevented processing over half of the real amendments—complex amendments with substantial changes exceeded input limits. Second, the system handled only single amendments, not the sequential chains typical in real legislation, where amendments build on previous changes over decades." | 3 |
| 13 | U15 | page 399, section 4 | "If Amendment 1 is not used correctly, Amendment 2 cannot, e.g., locate the text "10,000 euros" because this phrase only exists in the amended version, not the original." | 3 |
| 14 | U5 | Abstract | "A full automated pipeline of legislative text consolidation can be done in a few hours, with a success rate of more than 63% on a difficult bill." | 3 |
| 15 | U2 | Model pricing table | "Claude Opus 5.5 … $4 / MTok … $20 / MTok … Claude Sonnet 5.5 … $2 / MTok … $10 / MTok … Claude Haiku 5.5 (for prompts up to 100,000 tokens) … $0.10 / MTok … $0.50 / MTok … Claude Haiku 5.5 (for prompts over 100,000 tokens) … $0.50 / MTok … $2.50 / MTok" | 2, 5, 6 |
| 16 | U2 | Batch processing | "The Batch API allows asynchronous processing of large volumes of requests with a 50% discount on both input and output tokens." | 2, 6 |
| 17 | U2 | Long context pricing | "Claude Haiku 5.5 is priced by prompt length: a request whose prompt is over 100,000 tokens pays higher prices. A request's prompt length counts all of its input tokens, including cache reads and cache writes." | 2, 5 |
| 18 | U6 | Overview | "Claude Haiku 5.5 is built for high-volume, latency-sensitive work such as classification, routing, extraction, and subagent tasks. It supports adaptive thinking with the effort parameter, a 1M token context window, and up to 128k output tokens." | 2, 5 |
| 19 | U10 | Overview | "Claude Opus 5.5 is built for long-running agentic coding and knowledge work, priced at $4 / $20 USD per million input / output tokens." | 2 |
| 20 | U7 | Behavior changes | "Effort levels are recalibrated. … level doesn't produce the same amount of thinking as it did on Claude Sonnet 5. Re-run your effort sweep rather than carrying a setting over." | 2 |
| 21 | U8 | Comparison with prompt-based approaches | "Better citation reliability: Because the API parses citations into the response formats described in the following sections and extracts `cited_text` directly, citations are guaranteed to contain valid pointers to the provided documents." | 2, 5 |
| 22 | U8 | Comparison with prompt-based approaches | "Cost savings: If your prompt-based approach asks Claude to output direct quotes, you may see cost savings because `cited_text` does not count toward your output tokens." | 2 |
| 23 | U9 | Overview | "This approach is well-suited to tasks that do not require immediate responses, with most batches finishing in less than 1 hour while reducing costs by 50% and increasing throughput." | 2 |
| 24 | U9 | Batch limitations | "A Message Batch is limited to either 100,000 Message requests or 256 MB in size, whichever is reached first. … Batches expire if processing does not complete within 24 hours." | 2 |
| 25 | U11 | Consolidated EEA legal acts | "the EFTA Secretariat is conducting a pilot project to explore how AI‑based tools can support the consolidation of EEA legal acts. … The pilot began on 15 January 2026 and will run for a period of six months. … The consolidated versions are provided for information purposes only and have no legal value." | 4 |
| 26 | U14 | Abstract | "Results show that chunking strategies aligned with the inherent legal structure - particularly section and subsection - based retrieval-achieve the highest recall, while more complex approaches that override this structure perform worse." | 3 |
| 27 | U13 | Lead | "legalize-dev/legalize-es: Spanish legislation as a Git repo — every law is a Markdown file, every reform a commit. 8,600+ laws." | 4 |
| 28 | D1 | RQ3 | "No Legalize country self-consolidates from a raw amendment stream. None." | 1, 4 |
| 29 | D1 | RQ3, last paragraph | "not by building a deterministic amendment-replay engine, but by **periodic re-download to accumulate history post-hoc**" | 4 |
| 30 | D2 | Finland numbers | "**mean Levenshtein text distance 0.65%**, **mean section-level structural error 4.25%**, **367 perfect structural matches**, **490 statutes at ≥95% agreement**, **104 below 90%**" | 4 |
| 31 | D3 | legislation.gov.uk, what they consolidate from and how | "can apply certain effects automatically, such as repeals, commencements and non-textual amendments … but textual substitutions are applied by editors." | 4, 5 |
| 32 | U12 | Abstract | "Each document is first split into chunks via a system of chunking and augmentation, addressing the long document problem." | 3 |
| 33 | U3 | Introduction | "In this report, we evaluate 18 LLMs, including the state-of-the-art GPT-4.1, Claude 4, Gemini 2.5, and Qwen3 models." | 3 |
| 34 | U4 | Abstract | "a dataset of 908 amendment–law pairs drawn from 140 Federal Law Gazette documents across four major codes" | 3 |
| 35 | U5 | Abstract | "Our method employs light quantized generative model, finetuned with LoRA, to generate accurate and reliable amended texts." | 3 |
| 36 | D2 | Finland numbers | "690 fully-replayable amended statutes" | 4 |
| 37 | D2 | Finland numbers, reading for Bulgaria | "the residual gap is the finding, attributed to a lane, not silently absorbed" | 4 |
| 38 | D1 | Conclusion | "All examined countries (Spain/BOE, France/LEGI-DILA, EU/EUR-Lex, Germany/gesetze-im-internet, Sweden/Riksdagen-SFS, South Korea/National Law Information Center) **fetch already-consolidated text and official version history from a state-run source**" | 4 |
| 39 | D1 | RQ2, Spain | "Data is obtained from the BOE's (Boletín Oficial del Estado) open data API" | 4 |
| 40 | U2 | Model pricing table | "Claude Fable 5.1 … $10 / MTok … $50 / MTok" | 6 |
| 41 | D5 | Inputs table | "32,117 `ok` materials" | 6 |
| 42 | U8 | How citations work, document chunking | "**For plain text documents:** Content is chunked into sentences that can be cited from." | 2, 5 |
| 43 | U8 | How citations work, document chunking | "**For custom content documents:** Your provided content blocks are used as-is and no further chunking is done." | 2, 5 |
| 44 | U8 | How citations work, citation format | "**For custom content documents:** Citations include the content block index range (0-indexed) corresponding to the original content list provided." | 2, 5 |
