"""Markup remnants: bare closing-tag text nodes carried into the corpus.

lex.bg emits closing tags whose opening „<“ is missing, so the converter reads
them as text and reproduces them verbatim. In an article heading a remnant
collides article keys (correctness-floor property 3) and contaminates the text
at the address (property 4); a remnant that swallows a superscript index loses
the address altogether (property 2).

Matching is a case-sensitive substring test, which is what keeps ordinary prose
such as „supervision“ out of the census: only the tag forms carry the „>“.
"""

from typing import Iterable

from corpus_integrity.protocol import Act, Violation

# Bare closing-tag text nodes that lex.bg emits without an opening '<'.
# These are reproduced verbatim by the converter and collide article keys.
REMNANTS: tuple[str, ...] = ("/span>", "SUP>", "/STRONG>", "/sup>", "/B>")


class RemnantCheck:
    """Flags every markup remnant in every act body."""

    name = "tag_remnants"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            for lineno, line in enumerate(act.body.splitlines(), start=1):
                for marker in REMNANTS:
                    if marker in line:
                        out.append(
                            Violation(
                                check=self.name,
                                slug=act.slug,
                                detail=f"markup remnant {marker!r}",
                                locator=f"line {lineno}",
                            )
                        )
        return out
