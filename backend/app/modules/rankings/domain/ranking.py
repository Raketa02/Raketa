"""The ranking's rules: what a row is, how a rating's history folds into one
and into the level history, who is listed on General, the order, the chip, the
gap line and the reader's place card (``docs/adr/0203`` §1–§6; the mechanics
§3–§7).

**A result** here is a confirmed competitive result with a winner in the sport:
exactly a result that moves a level, one ``rating.moved_on_result`` each. A For
fun game, *Played · no score* and a disputed game move no level, so they never
reach this module.

**The row is a fold of one rating stream**, and the fold is this module's
:func:`row_of`. The live delivery and the rebuild both call it over the whole
stream, so the two cannot disagree, and a redelivery folds the same stream to
the same row. **The level history is the same fold, kept point by point**
(:func:`points_of`): the row is its last point, with the count and the form
beside it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import Final, Protocol, final
from uuid import UUID

from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import even_win
from app.kernel import Instant, Sport, instant, invariant

#: Results in the sport that put a player on General (Q17, kept "for now" in
#: Q24; the engine review, #781, is where it is revisited).
GENERAL_ENTRY: Final = 5

#: Results in the sport that put a player among their friends' (Q26): the
#: first.
FRIENDS_ENTRY: Final = 1

#: How long after their last result a player stays listed (Q18), in both
#: views (Q26). The next result puts them straight back, with no new wait.
LISTED_FOR: Final = timedelta(days=90)

#: The form: the last results in the sport, oldest first, as the record's
#: *Last 5*.
FORM_LENGTH: Final = 5

#: General's first page.
PAGE_SIZE: Final = 50

#: The podium's steps; none with fewer rows.
PODIUM_SIZE: Final = 3

#: The chip's window: the last 7 days, rolling (Q4). *New* lasts as long.
CHIP_WINDOW: Final = timedelta(days=7)

#: The most wins the gap line counts — *about 5 wins close it*. Above it the
#: count is left out, so a far gap never discourages (Q19).
WINS_COUNTED: Final = 5

#: A Level is carried to two decimals (``racketskill``'s own resolution), and
#: the ranking compares Levels at that resolution: 5,00 is level with any other
#: 5,00, and the tie rule decides.
_HUNDREDTHS: Final = 100


class RankingView(StrEnum):
    """Which list a ranking is read in (``docs/adr/0203`` §3). **General** is
    everybody in Raketa listed in the sport; **Friends** is the reader and their
    friends, worked out on each read (#771). Both drop a player 90 days after
    their last result, and both order and place them alike."""

    GENERAL = "GENERAL"
    FRIENDS = "FRIENDS"

    @property
    def entry(self) -> int:
        """The results in the sport that enter this view's list."""

        return GENERAL_ENTRY if self is RankingView.GENERAL else FRIENDS_ENTRY

    @property
    def leaves_out_the_hidden(self) -> bool:
        """Whether *Show me in General* off keeps a row out of this view —
        General's; Friends ignores the switch (#772)."""

        return self is RankingView.GENERAL


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

    @property
    def mark(self) -> str:
        """The stored form's letter: ``W`` or ``L``."""

        return "W" if self is Outcome.WIN else "L"

    @classmethod
    def of_marks(cls, marks: str) -> tuple["Outcome", ...]:
        """A stored form read back, oldest first."""

        return tuple(cls.WIN if mark == "W" else cls.LOSS for mark in marks)


def marks_of(form: Sequence[Outcome]) -> str:
    """A form as it is stored: ``WWLWL``."""

    return "".join(outcome.mark for outcome in form)


@final
@dataclass(frozen=True, slots=True)
class LevelMove:
    """One result applied to a rating: the game, who won, and the Level and
    uncertainty after it, **when the result settled** — and the stored event
    that recorded it, which keys its point in the level history."""

    game_id: UUID
    won: bool
    mu: float
    sigma: float
    at: Instant
    event_id: UUID


@final
@dataclass(frozen=True, slots=True)
class RatingHistory:
    """One player's rating in one sport, as its stream recorded it: where the
    questionnaire put it, and every result that moved it, in stream order.
    ``opened_by`` is the stored event that opened it."""

    player_id: UUID
    sport: Sport
    initial_mu: float
    initialised_at: Instant
    moves: tuple[LevelMove, ...]
    opened_by: UUID


@final
@dataclass(frozen=True, slots=True)
class LevelPoint:
    """Where a player's Level stood from one instant on — one entry of **the
    level history**, keyed by the stored event that put it there.

    The first is the rating's opening, with no result; each after it is one
    result. So the history answers *this player's Level, count of results and
    when that Level was reached, at any instant since the rating opened* —
    which the chip reads 7 days back (``docs/adr/0203`` §4)."""

    event_id: UUID
    player_id: UUID
    sport: Sport
    #: When it was so: the rating's opening, or when the result settled.
    at: Instant
    hundredths: int
    #: How many results had moved the Level by then.
    results: int
    #: When the Level took the value it had then.
    level_reached_at: Instant


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
        # Asked together first, and the messages only made when one fails: a
        # pass makes one of these per listed player, and an f-string naming the
        # row was most of what fifty thousand of them cost (#770).
        entered = (self.general_entered_at is None) == (self.results < GENERAL_ENTRY)
        if self.results >= 1 and len(self.form) == min(self.results, FORM_LENGTH):
            if entered:
                return
        invariant(self.results >= 1, f"a ranking row with no result: {self!r}")
        invariant(
            len(self.form) == min(self.results, FORM_LENGTH),
            f"a form that is not the last results: {self!r}",
        )
        invariant(
            entered, f"an entry into General that is not the fifth result: {self!r}"
        )

    def listed_on_general(self, now: Instant) -> bool:
        """At least five results, the last settled within the 90 days."""

        return self.results >= GENERAL_ENTRY and now - self.last_result_at < LISTED_FOR

    def entered(self, view: RankingView) -> Instant | None:
        """When the player first entered the view's list — the fifth result
        for General, the first for Friends — or ``None`` before it."""

        if view is RankingView.GENERAL:
            return self.general_entered_at
        return self.friends_entered_at


@final
@dataclass(frozen=True, slots=True)
class GeneralSwitch:
    """A player's *Show me in General*, as their profile stood at ``version``
    (``docs/adr/0203`` §7, #772) — **a fact about the player, never about a
    row**: it holds in every sport, one they have no result in yet included.

    The projection keeps it beside the rows, and **a switch read at an older
    version never replaces a newer one**, so the outbox delivering two turns
    in either order leaves the latest."""

    player_id: UUID
    #: *Show me in General* off: left out of everybody's General but their own.
    hidden: bool
    #: The profile stream's version it was read at.
    version: int


def listed_since(now: Instant) -> Instant:
    """The settling instant a last result must be later than to be listed."""

    return instant(now - LISTED_FOR)


def points_of(history: RatingHistory) -> tuple[LevelPoint, ...]:
    """The level history a rating's stream makes: the opening, then one point
    per result in stream order. **Empty before the first result** — the
    history, as the row, is made by a result.

    **When the Level was reached** is when it last took its current value at
    two decimals — the questionnaire's moment if no result has moved it off
    that value since. Two partners moved by one result reach their Level at
    the same instant, and the player id decides between them.
    """

    if not history.moves:
        return ()
    level = hundredths_of(history.initial_mu)
    reached = history.initialised_at
    points = [
        LevelPoint(
            event_id=history.opened_by,
            player_id=history.player_id,
            sport=history.sport,
            at=history.initialised_at,
            hundredths=level,
            results=0,
            level_reached_at=reached,
        )
    ]
    for count, move in enumerate(history.moves, start=1):
        moved_to = hundredths_of(move.mu)
        if moved_to != level:
            level, reached = moved_to, move.at
        points.append(
            LevelPoint(
                event_id=move.event_id,
                player_id=history.player_id,
                sport=history.sport,
                at=move.at,
                hundredths=level,
                results=count,
                level_reached_at=reached,
            )
        )
    return tuple(points)


def row_of(history: RatingHistory) -> RankingRow | None:
    """The row a rating's history makes, or ``None`` before its first result:
    the level history's last point (:func:`points_of`), with the count and the
    form beside it."""

    points = points_of(history)
    if not points:
        return None
    last = points[-1]
    # The latest settling instant, not the last in stream order: the catch-up
    # and the outbox may apply two results up to a minute out of order
    # (``rating/application/settle_results.py``).
    latest = max(move.at for move in history.moves)
    return RankingRow(
        player_id=history.player_id,
        sport=history.sport,
        hundredths=last.hundredths,
        sigma=history.moves[-1].sigma,
        results=last.results,
        last_result_at=latest,
        level_reached_at=last.level_reached_at,
        general_entered_at=(
            points[GENERAL_ENTRY].at if last.results >= GENERAL_ENTRY else None
        ),
        friends_entered_at=points[1].at,
        form=tuple(Outcome.of(move.won) for move in history.moves[-FORM_LENGTH:]),
    )


class Ordered(Protocol):
    """Anything that stands somewhere in General's order: a row now, a point
    in the level history, a row of a worked-out order, a page's cursor."""

    @property
    def hundredths(self) -> int: ...

    @property
    def results(self) -> int: ...

    @property
    def level_reached_at(self) -> Instant: ...

    @property
    def player_id(self) -> UUID: ...


def order_of(one: Ordered) -> tuple[int, int, Instant, UUID]:
    """The ranking's order, best first: the Level, then more results, then who
    reached that Level first, then the player id (Q20) —
    ``ix_ranking_rows_order`` in Python, and the only spelling of it here."""

    return (-one.hundredths, -one.results, one.level_reached_at, one.player_id)


# --------------------------------------------------------------------------- #
# The chip — places moved in 7 days (``docs/adr/0203`` §4; the mechanics §6)
# --------------------------------------------------------------------------- #


class ChipKind(StrEnum):
    """*▲ n*, *▼ n*, *—* or *New* (the words §30.3)."""

    UP = "UP"
    DOWN = "DOWN"
    SAME = "SAME"
    NEW = "NEW"


@final
@dataclass(frozen=True, slots=True)
class Chip:
    kind: ChipKind
    #: How many places, with ``UP`` and ``DOWN``; ``0`` with ``SAME`` and ``NEW``.
    places: int = 0

    def __post_init__(self) -> None:
        moved = self.kind in (ChipKind.UP, ChipKind.DOWN)
        if not (self.places >= 1 if moved else self.places == 0):
            invariant(False, f"a chip whose places don't say how it moved: {self!r}")


def chips_since(now: Instant) -> Instant:
    """The instant the chip reads the level history at: exactly 7 days ago."""

    return instant(now - CHIP_WINDOW)


def chips_of(
    listed: Sequence[RankingRow],
    then: Mapping[UUID, LevelPoint],
    *,
    now: Instant,
    view: RankingView = RankingView.GENERAL,
) -> dict[UUID, Chip]:
    """Every listed player's chip, in the view ``listed`` is.

    ``listed`` is **today's set**, in today's order; ``then`` is each of those
    players' level-history point at :func:`chips_since` — the latest at or
    before it, or, for a player with none by then, their first. **The chip
    compares a place in today's order with a place among the same players
    ordered by those points**, so an arrival or a departure moves nobody — a
    friend just added included, who is in both orders — and an overtake moves
    both (Q5, Q23).

    ***New*** is the 7 days after a first entry into the view's list — the 5th
    result for General, the 1st for Friends. A comeback is not new: a
    returning player's level 7 days ago is known, so the chip is real. **A row
    with no point** stands where it stands now: a player with no result in the
    7 days — the pass reads no history for them (#770) — and a store the
    rebuild hasn't filled.
    """

    def then_order(row: RankingRow) -> tuple[int, int, Instant, UUID]:
        return order_of(then.get(row.player_id, row))

    then_places = {
        row.player_id: place
        for place, row in enumerate(sorted(listed, key=then_order), start=1)
    }
    chips: dict[UUID, Chip] = {}
    for place, row in enumerate(listed, start=1):
        entered = row.entered(view)
        if entered is not None and now - entered < CHIP_WINDOW:
            chips[row.player_id] = Chip(ChipKind.NEW)
            continue
        moved = then_places[row.player_id] - place
        if moved > 0:
            chips[row.player_id] = Chip(ChipKind.UP, moved)
        elif moved < 0:
            chips[row.player_id] = Chip(ChipKind.DOWN, -moved)
        else:
            chips[row.player_id] = Chip(ChipKind.SAME)
    return chips


# --------------------------------------------------------------------------- #
# The gap line (``docs/adr/0203`` §6; the mechanics §7)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class PlayerAbove:
    """*0,04 behind Karol · about 3 wins close it*, or *Level with Ewa · one win
    puts you ahead*."""

    nickname: str
    #: The Levels' difference, in hundredths; ``0`` when tied.
    gap: int
    #: One win to five; ``None`` above five, when no win moves the Level, and
    #: when tied.
    wins: int | None
    tied: bool

    def __post_init__(self) -> None:
        invariant(self.gap >= 0, f"a player above who is below: {self!r}")
        invariant(self.tied == (self.gap == 0), f"a tie with a gap: {self!r}")
        invariant(
            self.wins is None or (not self.tied and 1 <= self.wins <= WINS_COUNTED),
            f"a count of wins the line doesn't read: {self!r}",
        )


@final
@dataclass(frozen=True, slots=True)
class PlayerBelow:
    """*Zofia is 0,02 behind you*, or *Zofia is level with you* at ``0``."""

    nickname: str
    gap: int

    def __post_init__(self) -> None:
        invariant(self.gap >= 0, f"a player below who is above: {self!r}")


@final
@dataclass(frozen=True, slots=True)
class GapLine:
    """The line under the place card: the nearest player above the reader can
    see, and the nearest below — or, in first place, *Top of the list*, which is
    the whole line (the words §30.4)."""

    above: PlayerAbove | None
    below: PlayerBelow | None
    top_of_the_list: bool

    def __post_init__(self) -> None:
        invariant(
            not self.top_of_the_list or (self.above is None and self.below is None),
            f"a top of the list that says more than *Top of the list*: {self!r}",
        )


class Levelled(Protocol):
    """What prices one win and measures a gap: a ranking row now, or a row of a
    worked-out order."""

    @property
    def sport(self) -> Sport: ...

    @property
    def hundredths(self) -> int: ...

    @property
    def sigma(self) -> float: ...


def one_win(row: Levelled) -> int:
    """How far one win moves the row's Level, in hundredths: **the rating
    engine's own rule for an even game** (``even_win``) — an opposition at the
    player's own Level and uncertainty, a four as a side of the player and an
    equal partner, the sport's share, and the Level the win leaves at two
    decimals. ``0`` when the stake is under half a hundredth."""

    estimate = SkillEstimate(mu=level_of(row.hundredths), sigma=row.sigma)
    return hundredths_of(even_win(estimate, sport=row.sport))


def wins_to_close(gap: int, *, win: int) -> int | None:
    """How many even wins close a gap of ``gap`` hundredths, each moving the
    Level ``win`` hundredths: the gap over the win, rounded up — ``None`` above
    :data:`WINS_COUNTED`, and when a win moves the Level not at all.

    **Honest, not exact**: the next opponent is never quite even, and the
    player above may play too."""

    invariant(gap > 0, f"wins counted for a gap that is closed: {gap}")
    invariant(win >= 0, f"a win that moves a Level down: {win}")
    if win == 0:
        return None
    wins = -(-gap // win)
    return wins if wins <= WINS_COUNTED else None


def player_above(reader: Levelled, above: Levelled, nickname: str) -> PlayerAbove:
    gap = above.hundredths - reader.hundredths
    if gap == 0:
        return PlayerAbove(nickname=nickname, gap=0, wins=None, tied=True)
    return PlayerAbove(
        nickname=nickname,
        gap=gap,
        wins=wins_to_close(gap, win=one_win(reader)),
        tied=False,
    )


def player_below(reader: Levelled, below: Levelled, nickname: str) -> PlayerBelow:
    return PlayerBelow(nickname=nickname, gap=reader.hundredths - below.hundredths)


class CardState(StrEnum):
    """What the reader's place card says (the screens §4.1, §4.3, §4.4, §4.6)."""

    #: *YOUR PLACE · 7th · of 13*, with the Level.
    LISTED = "LISTED"
    #: Fewer results than the view's entry: *2 of 5 games — 3 more competitive
    #: padel games put you on the list* in General; *Not ranked in padel yet —
    #: your first confirmed competitive game puts you on the list* in Friends.
    NEEDS_RESULTS = "NEEDS_RESULTS"
    #: *No squash level yet — get one, then 5 competitive games put you on the
    #: list*, with **Get your squash level** (*… then one competitive game …*
    #: in Friends).
    NO_LEVEL = "NO_LEVEL"
    #: *Off the list — no competitive padel game in 90 days. Your next one puts
    #: you back.*
    OFF_THE_LIST = "OFF_THE_LIST"
    #: Friends only: the reader is listed and no friend is — *Just you so far*,
    #: with **Add friends**, and nothing below it.
    JUST_YOU = "JUST_YOU"
    #: Friends only: neither the reader nor any friend is listed — *None of your
    #: friends is ranked in padel yet*, with **Add friends**, in the card's
    #: place, and nothing below it.
    NO_FRIEND_LISTED = "NO_FRIEND_LISTED"
    #: General only: the reader is listed and turned *Show me in General* off
    #: (#772) — the dark card with the place, the Level and the chip, and
    #: *Hidden from General* with the switch where the gap line was (the
    #: screens §4.5). A hidden reader who isn't listed reads their not-listed
    #: card: there is no place to show.
    HIDDEN = "HIDDEN"


@final
@dataclass(frozen=True, slots=True)
class PlaceCard:
    state: CardState
    #: How many results the reader has in the sport.
    results: int
    #: With ``LISTED`` and ``HIDDEN`` only.
    place: int | None = None
    of: int | None = None
    hundredths: int | None = None
    chip: Chip | None = None
    #: With ``LISTED`` only: a hidden reader's card has *Hidden from General*
    #: in its place.
    gap_line: GapLine | None = None

    def __post_init__(self) -> None:
        placed = self.state in (CardState.LISTED, CardState.HIDDEN)
        place = (self.place, self.of, self.hundredths, self.chip)
        invariant(
            (
                all(field is not None for field in place)
                if placed
                else all(field is None for field in place)
            )
            and (self.gap_line is not None) == (self.state is CardState.LISTED),
            f"a place on a card that is not placed, or none on one that is: {self!r}",
        )

    @property
    def is_the_page(self) -> bool:
        """The card stands alone — *Just you so far*, *None of your friends is
        ranked…* — and nothing is drawn below it (the screens §4.6)."""

        return self.state in (CardState.JUST_YOU, CardState.NO_FRIEND_LISTED)


class Placed(Protocol):
    """The reader's row in a worked-out order: the place and what the card
    reads off it."""

    @property
    def place(self) -> int: ...

    @property
    def hidden(self) -> bool: ...

    @property
    def hundredths(self) -> int: ...

    @property
    def results(self) -> int: ...

    @property
    def chip(self) -> Chip: ...


def card_of(
    row: RankingRow | None,
    *,
    holds_a_level: bool,
    of: int,
    placed: Placed | None = None,
    gap_line: GapLine | None = None,
    view: RankingView = RankingView.GENERAL,
) -> PlaceCard:
    """The reader's card in a sport and view.

    **No level comes first**, read live from the rating: a reader with no
    rating in the sport has no row either. Then **a place in the order** — the
    order read decides who is listed, at the instant it was worked out, so the
    card and the rows never disagree (#770): the place, the Level, the count
    and the chip are the order's row's — ***hidden*** in General when the
    reader turned *Show me in General* off (#772), with no gap line, and
    listed otherwise: Friends ignores the switch. Then **fewer results than
    the view's entry** (five for General, one for Friends), whatever their
    age; and otherwise **off the list**, enough of them with none in the
    order's 90 days.
    """

    if not holds_a_level:
        return PlaceCard(state=CardState.NO_LEVEL, results=0)
    if placed is not None:
        hidden = view.leaves_out_the_hidden and placed.hidden
        return PlaceCard(
            state=CardState.HIDDEN if hidden else CardState.LISTED,
            results=placed.results,
            place=placed.place,
            of=of,
            hundredths=placed.hundredths,
            chip=placed.chip,
            gap_line=None if hidden else gap_line,
        )
    if row is None or row.results < view.entry:
        return PlaceCard(
            state=CardState.NEEDS_RESULTS, results=0 if row is None else row.results
        )
    return PlaceCard(state=CardState.OFF_THE_LIST, results=row.results)


def friends_card_of(
    row: RankingRow | None,
    *,
    holds_a_level: bool,
    of: int,
    friends_listed: int,
    placed: Placed | None = None,
    gap_line: GapLine | None = None,
) -> PlaceCard:
    """The reader's card in Friends (the screens §4.6).

    **With a friend listed** it is :func:`card_of`'s, in Friends: the place
    among them, or the reader's own not-listed card above the friends' table
    (Q7). **With none**, the card is the whole page — *Just you so far* when
    the reader is listed, and *None of your friends is ranked…* when they
    aren't either, whatever their own state.
    """

    if friends_listed == 0:
        if placed is not None:
            return PlaceCard(state=CardState.JUST_YOU, results=placed.results)
        return PlaceCard(
            state=CardState.NO_FRIEND_LISTED,
            results=0 if row is None else row.results,
        )
    return card_of(
        row,
        holds_a_level=holds_a_level,
        of=of,
        placed=placed,
        gap_line=gap_line,
        view=RankingView.FRIENDS,
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
