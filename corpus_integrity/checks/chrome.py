"""Site chrome: lex.bg furniture that must never enter the content region.

A sidebar block carries news headlines, forum thread titles and a footer. When
it lands inside an act, a headline containing „Чл. N“ manufactures a phantom
article (correctness-floor property 1) and the block contaminates the text at
whatever address precedes it (property 4). It also churns on every refresh,
since the sidebar changes daily.

Marker selection, measured over all 3,624 acts on 2026-09-05:

- „Посети форума“ hits 1 act, the only act carrying the sidebar. Kept.
- „© Lex.bg“ hits 0 acts, and cannot hit any: the footer is emitted as „©“ and
  „Lex.bg |“ on two separate lines, so the joined form never appears on one
  line. Replaced by „Lex.bg“, which contains it, so nothing the plan's marker
  would have caught is lost.
- „Lex.bg“ hits 1 act, the same sidebar-bearing act, and nothing else. It makes
  the footer actually detected rather than nominally.

Rejected markers are listed in NOT_CHROME with their evidence, so that a later
leg does not silently re-add them.
"""

from typing import Iterable

from corpus_integrity.protocol import Act, Violation

# Site furniture that must never enter the content region. Sidebar headlines
# containing „Чл. N“ manufacture phantom articles and churn every refresh.
CHROME_MARKERS: tuple[str, ...] = ("Посети форума", "Lex.bg")

# Markers proposed for the failing set and rejected on measurement, because
# they occur inside enacted text. Both were carried by the plan; each was
# checked against every act before removal.
#
# - „Новини“: 3 acts, of which 2 are enacted text. ЗРТ art. 10(6) contrasts
#   news items with commentary; the Устройствен правилник of the transport
#   ministry names the „Новини“ section of the ministry website. The third act
#   is the sidebar-bearing one, which the kept markers already flag, so the
#   failing act set is unchanged by the removal.
# - „Форум за“: 1 act, and it is enacted text. The ЦПРС rules list the
#   information blocks of the register system, one of which is a forum.
NOT_CHROME: tuple[str, ...] = ("Новини", "Форум за")


class ChromeCheck:
    """Flags every site-chrome marker in every act body."""

    name = "chrome"

    def run(self, acts: Iterable[Act]) -> list[Violation]:
        out: list[Violation] = []
        for act in acts:
            for lineno, line in enumerate(act.body.splitlines(), start=1):
                for marker in CHROME_MARKERS:
                    if marker in line:
                        out.append(
                            Violation(
                                check=self.name,
                                slug=act.slug,
                                detail=f"site chrome {marker!r}",
                                locator=f"line {lineno}",
                            )
                        )
        return out
