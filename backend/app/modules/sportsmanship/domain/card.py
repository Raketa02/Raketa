"""The card: one court, one rater, answered once and closed for ever.

**The first aggregate on this platform that is stored rather than replayed**
(``docs/adr/0158``). Every other one is event-sourced, and this one is not,
because a card has no life story to fold: it is born answered. There is one act,
it happens once, nothing may amend it, and nothing subscribes to it — the
published figure is a fold over rows, and the matcher never reads any of it. An
event stream would be a stream of exactly one event per card, and an outbox row
nobody is waiting for.

It is still an **aggregate** and not a row, because there is a consistency
boundary and it is wider than one rating: the card and every answer on it are
written together, and every rule about *who may be on it* is true across the
whole of it. Those rules are enforced in the constructor, so a card that exists
is a card that was legal.

**Blanks leave nothing behind.** A person left blank is not a row with a null in
it — they are simply not on the card. That is what makes *not rating produces no
record of the omission* structural rather than a promise, and it is why an
all-blank card is still a card: the closure lives on the card, not on the answers,
so *I am not rating anyone* is an answer that stores an answer's worth of
evidence.

**Nothing here reads a clock.** The caller says when the card was answered, the
way every window in ``games`` is handed its instant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable, Sequence, final
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.sportsmanship.domain.errors import (
    StarsAreOneToFive,
    TheyWereNotOnThisCourt,
    YouRatedTheSamePersonTwice,
)

#: The bottom of the scale. **One, and never nought.** A rating that reads as
#: *worthless* is a weapon out of proportion to a tap, and one star already dents
#: an average about as hard.
MINIMUM_STARS: Final = 1

#: The top of the scale, and the number of taps. **Whole stars only** — there are
#: no halves, because five taps is one number and a half-star is a second scale.
MAXIMUM_STARS: Final = 5


@final
@dataclass(frozen=True, slots=True)
class StarsGiven:
    """One person, and what somebody said about playing with them.

    **The range lives here and nowhere else.** The wire declares a plain integer
    on purpose: a Pydantic bound restating ``1..5`` would be a second copy of the
    rule, and the first of the two to be edited would win silently for whichever
    callers went through it. A seed, a test and a request all meet the same
    refusal because there is only one.
    """

    subject_id: UUID
    stars: int

    def __post_init__(self) -> None:
        # **Refused, not asserted.** A star count arrives from a person tapping
        # it, so a bad one is a legitimate refusal with a code a client can act
        # on — never a broken precondition, which is what ``invariant`` is for
        # and what would answer somebody's tap with a 500.
        if not MINIMUM_STARS <= self.stars <= MAXIMUM_STARS:
            raise StarsAreOneToFive()


@final
@dataclass(frozen=True, slots=True)
class SettledCourt:
    """A court this player may be asked about: it happened, and it is over.

    **Everybody else, and never a side.** In doubles that is both opponents *and*
    the partner — the people who saw you play closest are the ones on the other
    end of your own net — and in singles it is the one opponent. The distinction
    the result cares about does not survive into this context at all, which is
    why there is no ``side`` here to forget to ignore.

    **A tuple and not a set**, in the line-up's own order, so a walk over a court
    is the same walk on every process and under every ``PYTHONHASHSEED``
    (``docs/adr/0105``).

    **``played_at`` is the moment somebody said *we played*** — ``games``' own,
    and the only moment this platform has about an evening; the hour four people
    were actually on a court is recorded nowhere. It is here because the card's
    window runs from it: the card opens the day after and closes a week later
    (``window.py``). It is carried on the court rather than fetched beside it
    because *when did this happen* is a fact about the court and not about the
    read that wanted it.
    """

    game_id: UUID
    rater_id: UUID
    others: tuple[UUID, ...]
    played_at: Instant

    def __post_init__(self) -> None:
        invariant(
            bool(self.others),
            "a settled court with nobody else on it: a game seats at least two",
        )
        invariant(
            self.rater_id not in self.others,
            "a court that offers the rater themselves — you rate everybody else",
        )
        invariant(
            len(set(self.others)) == len(self.others),
            "a court seating somebody twice",
        )


@final
@dataclass(frozen=True, slots=True)
class SportsmanshipCard:
    """One rater's whole answer about one court. **Submitting closes it.**

    ``given`` holds only the people who were actually given stars, so an
    all-blank card is a card with an empty answer — which is a real answer and
    not an absence, because the card itself is the record that it was answered.
    """

    game_id: UUID
    rater_id: UUID
    given: tuple[StarsGiven, ...]
    answered_at: Instant

    @classmethod
    def answered(
        cls,
        *,
        court: SettledCourt,
        given: Sequence[StarsGiven],
        at: Instant,
    ) -> "SportsmanshipCard":
        """Answer this court's card, once.

        Everything the card promises is checked here, because here is the only
        place a card is ever made: nobody but the other people on that court may
        be on it, nobody may be on it twice, and every answer is one to five
        whole stars — which :class:`StarsGiven` has already refused by the time
        one arrives.

        **An empty answer is legal and is the point of the empty case.** Nothing
        below treats it specially, and that is deliberate: *I am not rating
        anyone* takes the same path as any other card, so there is no second
        branch for it to be forgotten in.
        """

        answers = tuple(given)
        _nobody_twice(answers)
        _everybody_was_there(answers, court)
        return cls(
            game_id=court.game_id,
            rater_id=court.rater_id,
            given=answers,
            answered_at=at,
        )


def _nobody_twice(given: Iterable[StarsGiven]) -> None:
    subjects = [one.subject_id for one in given]
    if len(set(subjects)) != len(subjects):
        raise YouRatedTheSamePersonTwice()


def _everybody_was_there(given: Iterable[StarsGiven], court: SettledCourt) -> None:
    """**Rating yourself lands here too**, because the rater is not among the
    others — one rule, checked once, and no second class to keep in step."""

    on_the_court = set(court.others)
    if any(one.subject_id not in on_the_court for one in given):
        raise TheyWereNotOnThisCourt()
