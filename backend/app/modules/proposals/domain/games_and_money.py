"""Games & money — a player's two limits on what a deck deals them (the mechanics
§6.6, §17.1; the screens A7.1).

**Games per week**, one to seven and two until they say otherwise, counted
Monday to Sunday: once that many of their games are booked in a week, the deck
deals nothing more for it. **Most I'll pay**, off or one of three ceilings: a
card whose share is above it never reaches their deck. Both apply across sports
and across pools, because they are the player's, not a group's.

**Event-sourced, one stream per player, filed under the player's own id and born
by being used**, as a Payment method and a club's courts are: a player who never
opened the screen is at the defaults and has written nothing. It lives in
Proposals because every rule that reads it is a rule about which games are dealt
and which yeses stand — the deck here, the proposer (#540), posting (#546) and
the fill's pause (#541), which pauses a player's other yeses in a week their
booked games fill.

**A preference, so the same answer records nothing** — the rule a Play intent
follows beside it (``player_profile/domain/play_intent_declaration.py``), for the
same reason: there is no wording to evidence it against.

**The bounds are domain, never configuration**: each is what the form offers a
player, and an environment that could select one would be an environment
deciding how many games somebody is dealt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Iterable
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.proposals.domain.errors import (
    GamesPerWeekOutOfRange,
    MostIllPayNotOffered,
)
from app.modules.proposals.domain.events import GamesAndMoneySet
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: The stepper's range: at least one game a week, at most one a day.
GAMES_PER_WEEK: Final = (1, 7)
#: Where a player starts, until they say otherwise.
DEFAULT_GAMES_PER_WEEK: Final = 2
#: The chips beside *Off*, in grosze — 35, 45 and 60 zł (Q83).
MOST_ILL_PAY_CHOICES_GROSZE: Final = (35_00, 45_00, 60_00)


@dataclass
class GamesAndMoney:
    """One player's Games & money, rebuilt by folding their stream."""

    player_id: UUID
    games_per_week: int = DEFAULT_GAMES_PER_WEEK
    #: ``None`` is *off*: every card is shown, whatever its share.
    most_ill_pay_grosze: int | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(
        cls, player_id: UUID, events: Iterable[DomainEvent]
    ) -> "GamesAndMoney":
        """The player's settings — **the defaults, for a stream never written**."""

        settings = cls(player_id=player_id)
        for event in events:
            settings._apply(event)
        return settings

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def shows(self, *, share_grosze: int) -> bool:
        """Whether a card with this share may reach the player's deck: always
        with the ceiling off, and at or under it otherwise."""

        return (
            self.most_ill_pay_grosze is None or share_grosze <= self.most_ill_pay_grosze
        )

    def set(
        self, *, games_per_week: int, most_ill_pay_grosze: int | None, at: Instant
    ) -> None:
        """Both values, as the screen saves them on every tap. Refused, in the
        form's order, when either is not one the form offers; an answer that
        changes nothing records nothing."""

        least, most = GAMES_PER_WEEK
        if not least <= games_per_week <= most:
            raise GamesPerWeekOutOfRange(least=least, most=most)
        if (
            most_ill_pay_grosze is not None
            and most_ill_pay_grosze not in MOST_ILL_PAY_CHOICES_GROSZE
        ):
            raise MostIllPayNotOffered(choices=MOST_ILL_PAY_CHOICES_GROSZE)
        if (games_per_week, most_ill_pay_grosze) == (
            self.games_per_week,
            self.most_ill_pay_grosze,
        ):
            return
        event = GamesAndMoneySet(
            player_id=self.player_id,
            games_per_week=games_per_week,
            most_ill_pay_grosze=most_ill_pay_grosze,
            occurred_at=at,
        )
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        invariant(
            isinstance(event, GamesAndMoneySet),
            f"a Games & money stream holds {event!r}",
        )
        assert isinstance(event, GamesAndMoneySet)
        self.games_per_week = event.games_per_week
        self.most_ill_pay_grosze = event.most_ill_pay_grosze
        self.version += 1
