"""Operator-friendly wrapper: `python scripts/build_index.py` runs the
SQLite catalog builder against the corpus at HEAD.

This is identical to `python -m index.build`; the script form is here
because it's the documented operator command in the runbook (paths
without -m are easier to put in shell wrappers and Makefiles).
"""

from index.build import main

if __name__ == "__main__":
    raise SystemExit(main())
