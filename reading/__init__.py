"""The reading architecture of decision D-069 (2026-10-21).

The source's wording is copied symbol for symbol; a model judges only the
formatting. ``splitter`` cuts a raw page into blocks (every character in
exactly one block), ``labels`` defines the structure map a model returns per
block, ``assembler`` writes corpus Markdown by copying blocks under their
labels, ``checks`` verifies the map mechanically (coverage, re-assembly,
numbering, nesting, address uniqueness, literal fragments), and ``ladder``
turns failed checks into bounded re-labelling rounds. Nothing here writes a
corpus file: the output goes to a staging folder under ``data/runs/``.
"""
