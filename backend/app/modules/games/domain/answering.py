"""Who was asked about a score, and whether they said anything.

**One question, and it is not *did this game get confirmed*.** A confirmation is
a fact about a **pair** — two people agreeing — and ``docs/adr/0137`` struck the
strand that counted them for exactly that reason. What is folded here is a fact
about **one side**: a score was put in front of them, and inside its window they
either said something or they did not. Accepting says something. Countering says
something. Only silence is silence (``docs/adr/0160``).

**A score is put to the side that has not put one up.** The entry that records
*we played* records a score in the same act, so one side always opens; the other
side is the one being asked, and its turn is a counter or an acceptance. Once
both sides have spoken there is nothing further this platform asks of anybody:
the argument is capped at two rounds, an opener facing a counter may only give
way, and pricing that would price **surrender** — which is docking somebody for
disagreeing, the thing the struck strand did and this one must not.

**Nothing here reads a clock**, like every other fold in this context: the caller
says what time it is, so *has this window closed* answers the same at every
instant and on every reader's clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final

from app.kernel import Instant
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.standing import Acceptance, Proposal
from app.modules.games.domain.windows import proposal_closes_at


@final
@dataclass(frozen=True, slots=True)
class ScorePutToASide:
    """A score put in front of one side, and what became of it.

    ``closed_at`` is the moment the opportunity **closed** — the answer, or the
    window running out on silence — and never the moment the score went up. It is
    the strand's observation moment for the same reason a game nobody recorded
    is dated from its entry window rather than from its booking: dating it from
    the question would age a record faster than the record aged.

    **There is no third value here and that is deliberate.** A score still inside
    its window is not a ``ScorePutToASide`` at all — it is ``None`` from the fold
    below — because a conclusion the clock has not reached belongs in neither
    half of a ratio.
    """

    #: The side it was put **to**: the one that had not put a score up.
    side: GameSide
    closed_at: Instant
    answered: bool


def score_put_to_a_side(
    *,
    played_at: Instant | None,
    proposals: Mapping[GameSide, Proposal],
    acceptance: Acceptance | None,
    now: Instant,
) -> ScorePutToASide | None:
    """The one score this game put to somebody, or nothing yet.

    ``None`` in three cases, and they are three different nothings: nobody has
    said the game happened, nobody has put a score up, or the score that is up is
    still inside its window. All three are *the clock has not reached a
    conclusion*, which is why one spelling covers them.

    **At most one opportunity per game.** The opener is asked nothing and the
    receiving side is asked once, so there is nowhere here for a second row to
    come from — which is what keeps the denominator *scores put in front of you*
    rather than *taps you might have made*.
    """

    if played_at is None or not proposals:
        return None

    # The earliest score is the one that opened; a correction re-dates its own
    # side's and is refused once the other side has answered, so the two can
    # never cross. The side tie-break is unreachable through the aggregate and is
    # spelled anyway, because a fold whose answer depends on mapping order is a
    # fold that answers differently on two machines (``docs/adr/0105``).
    opener = min(proposals.values(), key=lambda one: (one.at, one.side.value))
    asked = opener.side.other

    countered = proposals.get(asked)
    accepted = (
        acceptance if acceptance is not None and acceptance.side is asked else None
    )
    spoke = [one.at for one in (countered, accepted) if one is not None]
    if spoke:
        # The **first** thing they said. A stream written while an agreement
        # still ran out a grace may hold a side that accepted and then
        # countered: it answered twice, and the opportunity closed on the first.
        return ScorePutToASide(side=asked, closed_at=min(spoke), answered=True)

    closes = proposal_closes_at(opener.at)
    if now < closes:
        return None
    return ScorePutToASide(side=asked, closed_at=closes, answered=False)


__all__ = ["ScorePutToASide", "score_put_to_a_side"]
