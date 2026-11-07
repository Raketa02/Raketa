"""The ranking's rules: what a row is, how a rating's history folds into one,
who is listed on General, the order, and the reader's place card
(``docs/adr/0203`` §1–§3; the mechanics §3–§5).

**A result** here is a confirmed competitive result with a winner in the sport:
exactly a result that moves a level, one ``rating.moved_on_result`` each. A For
fun game, *Played · no score* and a disputed game move no level, so they never
reach this module.

**The row is a fold of one rating stream**, and the fold is this module's
:func:`row_of`. The live delivery and the rebuild both call it over the whole
stream, so the two cannot disagree, and a redelivery folds the same stream to
the same row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.kernel import Instant, Sport, instant, invariant

#: Results in the sport that put a player on General (Q17, kept "for now" in
#: Q24; the engine review, #781, is where it is revisited).
GENERAL_ENTRY: Final = 5

#: How long after their last result a player stays listed (Q18). The next
#: result puts them straight back, with no new wait.
LISTED_FOR: Final = timedelta(days=90)

#: The form: the last results in the sport, oldest first, as the record's
#: *Last 5*.
FORM_LENGTH: Final = 5

#: General's first page.
PAGE_SIZE: Final = 50

#: The podium's steps; none with fewer rows.
PODIUM_SIZE: Final = 3

#: A Level is carried to two decimals (``racketskill``'s own resolution), and
#: the ranking compares Levels at that resolution: 5,00 is level with any other
#: 5,00, and the tie rule decides.
_HUNDREDTHS: Final = 100


def hundredths_of(mu: float) -> int:
    """A Level in whole hundredths, the resolution the ranking compares at."""

    return round(mu * _HUNDREDTHS)


def level_of(hundredths: int) -> float:
    """A Level in hundredths as the two-decimal number the passport prints."""

    return hundredths / _HUNDREDTHS


class Outcome(StrEnum):
    """How one result went for the row's player: a green square, or a grey
    one. **Two**: a game with no winner is no result, so it is never here."""

    WIN = "WIN"
    LOSS = "LOSS"

    @classmethod
    def of(cls, won: bool) -> "Outcome":
        return cls.WIN if won else cls.LOSS


@final
@dataclass(frozen=True, slots=True)
class LevelMove:
    """One result applied to a rating: the game, who won, and the Level and
    uncertainty after it, **when the result settled**."""

    game_id: UUID
    won: bool
    mu: float
    sigma: float
    at: Instant


@final
@dataclass(frozen=True, slots=True)
class RatingHistory:
    """One player's rating in one sport, as its stream recorded it: where the
    questionnaire put it, and every result that moved it, in stream order."""

    player_id: UUID
    sport: Sport
    initial_mu: float
    initialised_at: Instant
    moves: tuple[LevelMove, ...]


@final
@dataclass(frozen=True, slots=True)
class RankingRow:
    """One player's row in one sport's ranking — made on their first result in
    the sport, and refolded on every one after it."""

    player_id: UUID
    sport: Sport
    #: The Level, in hundredths (``2,71`` is ``271``).
    hundredths: int
    #: Its uncertainty, which prices one win on the gap line (#769).
    sigma: float
    #: How many results moved it.
    results: int
    #: When the last of them settled; the 90 days run from here.
    last_result_at: Instant
    #: When the Level took its current value — the third key of the order.
    level_reached_at: Instant
    #: When the fifth result settled: the first entry into General.
    general_entered_at: Instant | None
    #: When the first result settled: the first entry into Friends.
    friends_entered_at: Instant
    #: The last results, oldest first.
    form: tuple[Outcome, ...]

    def __post_init__(self) -> None:
        invariant(self.results >= 1, f"a ranking row with no result: {self!r}")
        invariant(
            len(self.form) == min(self.results, FORM_LENGTH),
            f"a form that is not the last results: {self!r}",
        )
        invariant(
            (self.general_entered_at is None) == (self.results < GENERAL_ENTRY),
            f"an entry into General that is not the fifth result: {self!r}",
        )

    def listed_on_general(self, now: Instant) -> bool:
        """At least five results, the last settled within the 90 days."""

        return self.results >= GENERAL_ENTRY and now - self.last_result_at < LISTED_FOR


def listed_since(now: Instant) -> Instant:
    """The settling instant a last result must be later than to be listed."""

    return instant(now - LISTED_FOR)


def row_of(history: RatingHistory) -> RankingRow | None:
    """The row a rating's history makes, or ``None`` before its first result.

    **When the Level was reached** is when it last took its current value at
    two decimals — the questionnaire's moment if no result has moved it off
    that value since. Two partners moved by one result reach their Level at
    the same instant, and the player id decides between them.
    """

    if not history.moves:
        return None
    level = hundredths_of(history.initial_mu)
    reached = history.initialised_at
    general_entered_at: Instant | None = None
    for count, move in enumerate(history.moves, start=1):
        moved_to = hundredths_of(move.mu)
        if moved_to != level:
            level, reached = moved_to, move.at
        if count == GENERAL_ENTRY:
            general_entered_at = move.at
    last = history.moves[-1]
    # The latest settling instant, not the last in stream order: the catch-up
    # and the outbox may apply two results up to a minute out of order
    # (``rating/application/settle_results.py``).
    latest = max(move.at for move in history.moves)
    return RankingRow(
        player_id=history.player_id,
        sport=history.sport,
        hundredths=level,
        sigma=last.sigma,
        results=len(history.moves),
        last_result_at=latest,
        level_reached_at=reached,
        general_entered_at=general_entered_at,
        friends_entered_at=history.moves[0].at,
        form=tuple(Outcome.of(move.won) for move in history.moves[-FORM_LENGTH:]),
    )


class CardState(StrEnum):
    """What the reader's place card says (the screens §4.1, §4.3, §4.4)."""

    #: *YOUR PLACE · 7th · of 13*, with the Level.
    LISTED = "LISTED"
    #: *2 of 5 games — 3 more competitive padel games put you on the list*.
    NEEDS_RESULTS = "NEEDS_RESULTS"
    #: *No squash level yet — get one, then 5 competitive games put you on the
    #: list*, with **Get your squash level**.
    NO_LEVEL = "NO_LEVEL"
    #: *Off the list — no competitive padel game in 90 days. Your next one puts
    #: you back.*
    OFF_THE_LIST = "OFF_THE_LIST"


@final
@dataclass(frozen=True, slots=True)
class PlaceCard:
    state: CardState
    #: How many results the reader has in the sport.
    results: int
    #: With ``LISTED`` only.
    place: int | None = None
    of: int | None = None
    hundredths: int | None = None

    def __post_init__(self) -> None:
        listed = self.state is CardState.LISTED
        invariant(
            listed
            == (
                self.place is not None
                and self.of is not None
                and self.hundredths is not None
            ),
            f"a place on a card that is not listed, or none on one that is: {self!r}",
        )


def card_of(
    row: RankingRow | None,
    *,
    holds_a_level: bool,
    place: int | None,
    of: int,
    now: Instant,
) -> PlaceCard:
    """The reader's General card in a sport.

    **No level comes first**, read live from the rating: a reader with no
    rating in the sport has no row either. Then **fewer than five results**,
    whatever their age; then **off the list**, five or more with the last
    older than the 90 days; and otherwise the place.
    """

    if not holds_a_level:
        return PlaceCard(state=CardState.NO_LEVEL, results=0)
    if row is None or row.results < GENERAL_ENTRY:
        return PlaceCard(
            state=CardState.NEEDS_RESULTS, results=0 if row is None else row.results
        )
    if not row.listed_on_general(now):
        return PlaceCard(state=CardState.OFF_THE_LIST, results=row.results)
    invariant(place is not None, f"a listed row with no place: {row!r}")
    return PlaceCard(
        state=CardState.LISTED,
        results=row.results,
        place=place,
        of=of,
        hundredths=row.hundredths,
    )


def latest_of(rows: tuple[RankingRow, ...]) -> RankingRow | None:
    """The row of the reader's latest result in any sport — the trophy's sport
    (the mechanics §8). Two sports settled at one instant go to the sport
    registry's order."""

    order = list(Sport)
    return max(
        rows,
        key=lambda row: (row.last_result_at, -order.index(row.sport)),
        default=None,
    )
