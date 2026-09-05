"""Tests for scripts/structure_gaps.py: detect acts whose additional provisions were dropped
by the source (an additional-provisions heading directly followed by a final or transitional
heading; § numbering that starts above 1)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "structure_gaps.py"


def load():
    spec = importlib.util.spec_from_file_location("structure_gaps", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


FRONT = "---\ntitulo: TEST\nidentificador: '1'\npais: bg\nrango: закон\nfecha_publicacion: '2026-01-01'\nultima_actualizacion: '2026-01-01'\nestado: vigente\nfuente: lex.bg\n---\n\n"

EMPTY_ADDITIONAL = FRONT + textwrap.dedent("""
    **Чл. 1.** Този закон урежда нещо.

    Допълнителна разпоредба

    ## Заключителни разпоредби

    **§ 2.** Законът влиза в сила от деня на обнародването му.
    """)

CLEAN = FRONT + textwrap.dedent("""
    **Чл. 1.** Този закон урежда нещо.

    ## Допълнителни разпоредби

    **§ 1.** По смисъла на този закон "нещо" е нещо.

    ## Заключителни разпоредби

    **§ 2.** Законът влиза в сила от деня на обнародването му.
    """)

RUNNING_TEXT = FRONT + textwrap.dedent("""
    **Чл. 1.** Комисията възлага допълнителна работа на членовете си, която се заплаща.

    ## Преходни и заключителни разпоредби

    **§ 1.** Законът влиза в сила от деня на обнародването му.
    """)


class Rules(unittest.TestCase):
    def scan(self, text):
        mod = load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "laws" / "act.md"
            p.parent.mkdir()
            p.write_text(text, encoding="utf-8")
            return [f.rule for f in mod.scan_file(p)]

    def test_empty_additional_section_fires_both_rules(self):
        rules = self.scan(EMPTY_ADDITIONAL)
        self.assertIn("additional-empty", rules)
        self.assertIn("paragraph-start-above-1", rules)

    def test_clean_act_fires_nothing(self):
        self.assertEqual(self.scan(CLEAN), [])

    def test_running_text_is_not_a_heading(self):
        self.assertEqual(self.scan(RUNNING_TEXT), [])

    def test_self_test_proves_every_rule(self):
        mod = load()
        self.assertTrue(mod.self_test())


if __name__ == "__main__":
    unittest.main()
