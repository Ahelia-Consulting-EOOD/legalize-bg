"""ДВ acquisition layer for Държавен вестник (dv.parliament.bg).

Sibling of `fetcher/bg/`, which reads lex.bg. This package reads the
official State Gazette: the issue list, the contents of an issue, and
the HTML of a single published material. It acquires and parses; it
never writes to the corpus.

Design: `docs/plans/2026-09-05-dv-graded-source-design.md` §5.1.

Layout:
  client.py     DvSession: rate-limited GET and POST over one cookie jar
  issues.py     the JSF issue list (broeveList.faces) and its pagination
  materials.py  an issue's contents (materiali.faces) and one material
  __main__.py   the command line that writes JSONL
"""

from fetcher.dv.client import BASE, DvSession, url_for

__all__ = ["BASE", "DvSession", "url_for"]
