"""Corpus-integrity machine floor.

Per-class detectors that run over the committed Markdown tree, need no
`catalog.db`, and hard-fail in CI. See `docs/process/COVERAGE-FLOOR.md`
section "Correctness floor" and Owner Directives 9 to 14.

The package deliberately exports nothing: every consumer imports the module
it needs, so adding a check never changes this file.
"""
