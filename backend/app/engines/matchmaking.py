"""The snapshot input vocabulary both matchmaking engines read.

See ``docs/adr/0026-matchmaking-engines-snapshot-input-contract.md``.

**Snapshots, not aggregates.** An engine may not import a module, touch a
database, read configuration or call a clock, and the contexts that own this data
— Matches, Clubs, Courts — do not exist yet. So a calling module *assembles* the
facts an engine is given, and this file is the list of them. It is deliberately
the specification for what the Matches aggregate will have to own.

**The vocabulary is borrowed, never re-coined.** The ``Sport`` and its sold seat
count come from the kernel registry and are read from it here rather than carried
as a field, because *a sport's player count is never club-configurable* — a padel
match divides by four wherever it is read. A seat's **paid / held / empty** state
is here now and is spelled exactly as the commitment rules spell it; the match's
phase, its court hold tier and its join cutoff land with the viability term that
reads them. Renaming any of those here would fork the clock. Time is the kernel's
in the same way: a match carries its start as an ``Instant`` and its club carries
a ``Zone``, and the only route from the two to a local weekday and minute is the
kernel's own pair of readers — an engine that computed either half itself would be
the second answer to a timezone question. Money is the kernel's
in the same way: a ``SeatShare`` and a ``Payable`` are carried as the types
``kernel/money.py`` produces, in integer grosze, so no engine can invent a second
idea of what a seat costs or of the order the rounding happened in.

**The Player profile is a declaration, and every field of it is optional.** What
the player said about how they want to play — days, hours, the most they will pay
for a seat, how far they will travel, counted or social, appetite, how far ahead
they will commit — is read by the engine that needs it and *never restated as a
constant inside one*. Three of the source design's seven terms hard-coded values
this already declares, which is the same facts invented a second time and invented
differently. ``None`` means undeclared, and that is load-bearing rather than
convenient: *a missing declaration is not a missing measurement*, and a constraint
term reads an absent limit as **no limit** while an evidence term reads absent
evidence as **no score at all** (``docs/adr/0027``).

**A Level is exact, and it is not an Uncertainty.** Both are branded over the
kernel's ``Ratio`` — an exact ``Fraction`` over two integers — and carried in
hundredths, the precision the rating context already publishes them at. The brands
are local to this vocabulary and the kernel is untouched: ADR-0022 records that
promoting ``Level`` and ``Sigma`` into the kernel is a *relocation* to be done when
a second engine needs them as vocabulary, and doing it here would mean moving the
rating engine's scale in the same commit as landing a forecast.

Exactness earns its keep on the doubles path: a team strength is a
``Ratio``-weighted blend of two Levels, so the strength of a team is exact and the
gap between two teams is exact, and the balance percentage derived from it does not
depend on the order two multiplications happened in. It stops being exact the
moment two Uncertainties are combined — quadrature leaves the rationals — and that
crossing has exactly one place, ``pairing/core.as_float``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType, TypeAlias, final

from app.kernel import (
    SPORT_SPECS,
    Grosze,
    Instant,
    MinuteOfDay,
    Minutes,
    Payable,
    Ratio,
    SeatShare,
    Sport,
    Zone,
    invariant,
    ratio,
)

#: The denominator a Level and an Uncertainty are carried over. Two decimals is
#: the precision the rating context publishes — ``band_for`` already rounds its
#: edges to two, because "Levels are carried to two decimals, so the edges are
#: too" — so a hundredth is the smallest difference that means anything.
HUNDREDTHS = 100

#: A player's Level (μ) on the rating scale, as an exact ratio.
Level = NewType("Level", Ratio)

#: A player's Uncertainty (σ), in the same units as a Level, as an exact ratio.
Uncertainty = NewType("Uncertainty", Ratio)

#: Who a player is, as far as an engine needs to know. An engine compares two of
#: these for equality — *is the current player in this seat* — and never parses,
#: orders or displays one, so the assembler is free to hand over whatever the
#: Matches context ends up using for a player identity.
PlayerRef = NewType("PlayerRef", str)


def _not_a_bool(value: int, named: str) -> int:
    """Refuse the one `int` that is never a rating.

    `bool` is a subclass of `int`, so `level(True)` typechecks and means a Level
    of 0,01 — a wrong answer rather than a loud one. The same guard as the money
    and time modules', because it is the same hole in the same place.
    """

    invariant(not isinstance(value, bool), f"{named} from a bool: {value!r}")
    return value


def level(hundredths: int) -> Level:
    """A Level in hundredths: 3,20 is ``level(320)``.

    Refused below one hundredth, because a Level of zero or less is not a point
    on any scale and every quantity derived from it — a team strength, a gap —
    would be quietly meaningless rather than loudly wrong.

    **The top of the scale is deliberately not checked here.** 1,0–5,0 lives in
    ``racketskill/core`` and ADR-0015 put it there *"so onboarding and the later
    match-update engine cannot develop two ideas of what σ means"*; a second copy
    of the bounds in this file would be exactly that. The pairing engine reads a
    Level as a value carried on the snapshot and never restates the scale, the
    confidence transform or its ceiling.
    """

    invariant(hundredths >= 1, f"level in hundredths: {hundredths}")
    return Level(ratio(_not_a_bool(hundredths, "level"), HUNDREDTHS))


def uncertainty(hundredths: int) -> Uncertainty:
    """An Uncertainty in hundredths: σ 0,84 is ``uncertainty(84)``.

    Zero is allowed and a Level of zero is not, which is the asymmetry between
    the two: *we are perfectly sure* is a limit case worth being able to express
    and worth being able to test against, while *this player is nowhere on the
    scale* is not a state.
    """

    return Uncertainty(ratio(_not_a_bool(hundredths, "uncertainty"), HUNDREDTHS))


@final
@dataclass(frozen=True)
class PlayerSkill:
    """What the platform believes about one player at one sport.

    A Level and an Uncertainty, never a Level alone — *"a rating is never only a
    number"*, and the whole reason the forecast reports a margin beside its
    estimate is that this pair arrives here intact.

    ``confidence`` is **carried, never computed with.** It is σ restated as a
    percentage for the player, and the transform that produces it and the ceiling
    it can never reach both belong to the rating context. The pairing engine
    passes it through for a caller that wants to show it and derives nothing from
    it, so retuning the transform cannot move a balance percentage.
    """

    player: PlayerRef
    level: Level
    uncertainty: Uncertainty
    confidence: int


@final
@dataclass(frozen=True)
class UnratedPlayer:
    """Somebody on a seat whom the platform has never rated **at this sport**.

    A player can be Established at tennis and unrated at padel, so this is a fact
    about a player at a sport rather than about a player, and it is an ordinary
    state rather than an error: somebody who onboarded for one sport and joined a
    match in another is in it.

    **Its own type, not a nullable Level on ``PlayerSkill``**, because *a rating
    is never only a number*: the Level, the Uncertainty and the Confidence arrive
    together or not at all. Three nullable fields with an all-or-nothing rule
    between them are three fields every reader has to defend against — the same
    argument ``results.py`` makes for two ``@final`` classes over one pair with
    two nullable ones.

    It carries a reference and nothing else, because a reference is all there is.
    An engine that wants a Level for this seat has to *say where it got one*.
    """

    player: PlayerRef


#: Somebody on a seat: either a rating, or a player the platform cannot place on
#: the scale at this sport. Both members are ``@final``, so the union is closed and
#: a third kind of occupant cannot be smuggled in by subclassing one of them — it
#: has to be added here, where every reader of the union can see it arrive.
Occupant: TypeAlias = PlayerSkill | UnratedPlayer


class MatchTypePreference(Enum):
    """Whether the player declared for **counted** matches or for social ones.

    The glossary's *competitive or social*, and it is **read rather than assumed**:
    the source design hard-coded a preference for counted matches, which is the
    same fact invented a second time and invented wrongly for everybody who signed
    up to hit balls with friends.

    **Absence is not a member.** A player who declared nothing has no match-type
    problem, and that is spelled as ``None`` on the profile, the way every other
    declaration spells it. An ``EITHER`` member would make *undeclared* into a
    declaration and would put the constraint rule's decision inside the enum,
    where a term reading it could not tell a stated indifference from a silence.
    """

    COMPETITIVE = "competitive"
    SOCIAL = "social"


class Weekday(Enum):
    """A day of the week, as a player declares one.

    Numbered exactly as ``date.isoweekday()`` numbers them — Monday 1 through
    Sunday 7 — so a match's local start day maps onto a declaration without a
    second convention being invented between the two. The time fit term reads
    this; nothing in this slice does.

    **Not a start of week.** The kernel deliberately has none (``docs/adr/0024``
    left start-of-week out for want of an owner) and a *set* of days has no first
    element, so nothing here says which day a week begins on.
    """

    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


@final
@dataclass(frozen=True)
class HourWindow:
    """One stretch of a day the player declared, in the kernel's coordinates.

    A ``MinuteOfDay`` is minutes since *local* midnight, which is the whole reason
    a declaration is expressible without a timezone: *"I play after work"* is a
    claim about a clock face, not about an instant. Comparing a match's start
    against one is therefore the kernel's ``local_minute_of_day`` and an integer
    comparison, never ad-hoc date arithmetic.

    **A window never wraps midnight, and that is refused rather than handled.** A
    player who plays from 22:00 until 01:00 declares two windows, one either side,
    because a wrapping window makes *is this start inside it* two comparisons
    joined by an ``or`` and leaves every reader to remember which of the two kinds
    of window they are holding.
    """

    start: MinuteOfDay
    end: MinuteOfDay

    def __post_init__(self) -> None:
        invariant(
            self.start < self.end,
            f"an hour window from {self.start} to {self.end}",
        )

    def contains(self, minute: MinuteOfDay) -> bool:
        """Whether a local minute falls inside this window. **End-exclusive.**

        18:00–22:00 is every minute from 18:00 up to but not including 22:00, the
        same half-open convention ``MinuteOfDay`` itself carries — a day is 0 up to
        but not including 1440. A window that included its end would overlap the
        next one a player declared beside it, and *"which window is 22:00 in"*
        would have two answers.

        Here rather than in the term that reads it, because *what a declared
        window means* is the declaration's own business: two terms comparing a
        minute against a window by hand would be two chances to write ``<=``.
        """

        return self.start <= minute < self.end


@final
@dataclass(frozen=True)
class PlayerProfile:
    """What the player declared about how they want to play. **One declaration.**

    The glossary's Player profile, read by every engine that needs it and never
    restated as a constant inside one. ``PlayerProfile()`` — every field absent —
    is the honest launch state for somebody who has declared nothing, and it is
    also the shape that proves the constraint rule: such a player has no price
    problem, no travel problem and no match-type problem, so those terms score
    full marks, keep their weight, and Coverage is untouched.

    **An empty declaration is refused rather than read as absence.** No declared
    day at all is silence; an empty *set* of days would mean *no day works*, which
    is not a state anybody can be in and would score every match at nothing. The
    two are one keystroke apart in an assembler and worlds apart in a home list.
    """

    days: frozenset[Weekday] | None = None
    """The days the player said they can play. Read by the time fit term."""

    hours: tuple[HourWindow, ...] | None = None
    """The stretches of a day they said they can play. Read by the time fit term."""

    maximum_per_seat: Grosze | None = None
    """The most they will pay for one seat, in grosze.

    A ``Grosze`` and deliberately not a ``Payable``: a payable is what one player
    owes for one specific seat after their card, and a ceiling is a standing
    declaration that outlives every match it is compared against.
    """

    travel_radius: Minutes | None = None
    """How far they will travel, **in minutes**.

    Minutes rather than kilometres because that is the unit the snapshot carries
    and the unit a card shows: a club is *12 minutes away*, and a radius declared
    in distance could not be compared against it without inventing a speed.
    """

    match_type: MatchTypePreference | None = None
    """Counted or social, when they said. Read by the match type term."""

    appetite: int | None = None
    """How many matches a week they want. Read by the ranking policy, not by a term.

    Carried because the profile is one declaration and this is part of it
    (``docs/adr/0026``), and because how often somebody wants to play is a fact
    about *them* rather than about any match — so no term can read it, and the
    policy that decides how many cards to show is outside the engines entirely
    (``docs/adr/0027``).
    """

    commitment_horizon: Minutes | None = None
    """How far ahead they will commit, in minutes. The policy's, as appetite is."""

    def __post_init__(self) -> None:
        invariant(self.days is None or len(self.days) > 0, "an empty day declaration")
        invariant(
            self.hours is None or len(self.hours) > 0, "an empty hour declaration"
        )
        for named, value in (
            ("maximum per seat", self.maximum_per_seat),
            ("travel radius", self.travel_radius),
            ("appetite", self.appetite),
            ("commitment horizon", self.commitment_horizon),
        ):
            invariant(value is None or value >= 0, f"a negative {named}: {value}")


class LadderQualification(Enum):
    """Whether this match counts towards the current player's ladder.

    **Three states rather than a bool**, because *not in a ladder* and *in a
    ladder this match does not count for* are different facts, and a bool
    collapses them into the same low score. Entering a ladder is a declaration —
    it is the player saying which counted matches they are playing for — so a
    player in none has no ladder problem, which is exactly the constraint rule,
    and ``NOT_IN_A_LADDER`` is how an absent declaration is spelled for a fact the
    *match* carries rather than the profile.

    It is on the match and not on the profile because it is a joint fact: whether
    *this* match qualifies for *this* player's ladder is resolved by the assembler
    that can see both, and an engine given the two halves separately would be the
    second implementation of that resolution.

    **Borrowed vocabulary with no owner yet.** Ladders are not a modelled context
    and the word is not in the shared glossary; this reads it, the way it reads a
    seat's state, and whichever context ends up owning ladders will define it.
    """

    QUALIFIES = "qualifies"
    OUTSIDE = "outside"
    NOT_IN_A_LADDER = "not_in_a_ladder"


@final
@dataclass(frozen=True)
class ClubSnapshot:
    """The club, as much of it as a matchmaking engine is given.

    ``travel_minutes`` is how long **this player** would travel to it, resolved by
    the assembler against wherever they are: a club is not *20 minutes away*, it
    is 20 minutes away from somebody. It is a club fact rather than a match fact
    because every match at that club shares it, and a match carrying its own copy
    would be the same number stored once per candidate.

    The club's **crowding** lands with the viability term that reads it.
    """

    travel_minutes: Minutes

    zone: Zone
    """The club's timezone — the clock face a match at it starts on.

    On the *club* because that is what a timezone is a fact about: every match at
    a club shares it, and a match carrying its own copy would be the same zone
    stored once per candidate with nothing keeping the copies equal.

    Carried as the kernel's ``Zone`` and never as an IANA name, because a name is
    a string until somebody resolves it and *"who resolves it"* is exactly the
    question ADR-0024 answers once: ``zoneinfo`` is imported in one module in
    ``app/``, so an engine can hold a zone and can neither build one nor decide
    what one means. There is no default, for the same reason a price has none —
    a default of UTC is a club in the wrong country, and the two matches either
    side of a Warsaw midnight would land on different days without a word.
    """

    def __post_init__(self) -> None:
        invariant(
            self.travel_minutes >= 0,
            f"a negative travel time: {self.travel_minutes}",
        )


@final
@dataclass(frozen=True)
class PlayerScore:
    """One seated player's reliability, as the Player Score context will publish it.

    **Ships dark** (``docs/adr/0027``): the field is on the seat from day one and
    is absent in every snapshot the platform can assemble, so the group reliability
    term is *excluded* and Coverage says so. A term that ships absent can be lit up
    later without invalidating a single historical score; a term that shipped as a
    fabricated 0,80 would have poisoned every score ever computed and nothing could
    afterwards say which.

    ``reliability`` is the fraction of the matches this player committed to that
    they actually played. It is carried **on the seat** rather than beside the
    roster, so it cannot name somebody who is not in the match and needs no player
    reference of its own to disagree with the one already there.
    """

    reliability: Ratio

    def __post_init__(self) -> None:
        invariant(
            0 <= self.reliability <= 1,
            f"a reliability outside 0..1: {self.reliability}",
        )


@final
@dataclass(frozen=True)
class PlayHistory:
    """Which of the people in this match the current player has played recently.

    **Ships dark**, for the same reason and with the same guarantee as
    ``PlayerScore``: absent from every snapshot today, so the familiarity term is
    excluded rather than guessed.

    Absent and empty are different, and both are meaningful. No ``PlayHistory`` at
    all is *the platform has never observed who plays with whom*; a ``PlayHistory``
    with nobody in it is *you have played none of these people*, which is an
    observation and the best possible score for a term that rewards variety.

    What counts as *recently* is deliberately not here. It is a window, a window
    is a constant, and it belongs to the context that will own play history rather
    than to an engine reading its conclusion.
    """

    played_recently: frozenset[PlayerRef]


class SeatState(Enum):
    """A seat's commitment state. **Borrowed vocabulary, spelled verbatim.**

    Paid, held and empty are the commitment rules' three words and the shared
    glossary's, under **Roster**: *the paid seats, plus you if you could still
    join; a held seat contributes its player's level but not their attendance; an
    empty seat is imputed.* ADR-0026 requires the snapshot to spell them the same
    way, because renaming one here would fork the clock. This engine reads them;
    Matches will define them.

    **Paid and held are the same fact to the balance forecast, deliberately.**
    Both put a Level on a side. What separates them is whether the person will
    actually turn up, and that is the viability term's question — a match's
    likelihood of happening, not its evenness. Representing attendance risk as
    extra Uncertainty here would bury it inside a balance percentage, where it
    would be indistinguishable from not knowing how good somebody is and would
    make a held seat look like a worse *match* rather than a less certain one.
    """

    PAID = "paid"
    HELD = "held"
    EMPTY = "empty"


@final
@dataclass(frozen=True)
class SeatSnapshot:
    """One seat of a match: its commitment state, who is on it, and their record.

    The state and the occupant cannot disagree, and that is checked rather than
    trusted: an empty seat is exactly a seat with nobody on it. A seat carrying a
    state that contradicts its occupant is a caller's bug — an assembler that has
    lost track of a join — and every count downstream, the paid fraction viability
    reads included, would be quietly wrong rather than loudly.

    ``score`` is that occupant's reliability record and **ships dark**: absent in
    every snapshot today, present in the type from the first commit. A seat with
    nobody on it has nobody to have a record, which is checked with the same
    invariant — the alternative is a reliability reading attached to an empty seat,
    and a term reading it would be scoring a person who is not there.
    """

    state: SeatState = SeatState.EMPTY
    occupant: Occupant | None = None
    score: PlayerScore | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.occupant is None) == (self.state is SeatState.EMPTY),
            f"a {self.state.value} seat carrying occupant {self.occupant!r}",
        )
        invariant(
            self.occupant is not None or self.score is None,
            f"an empty seat carrying the record {self.score!r}",
        )


@final
@dataclass(frozen=True)
class MatchSnapshot:
    """One match, as much of it as the matchmaking engines are given.

    ``current_player`` is the person the analysis is *for* — every matchmaking
    answer is relative to somebody, and *"a perfectly balanced match forty minutes
    away at twice your ceiling"* is a good match and a bad recommendation at the
    same time. They may or may not be seated; sides are oriented so that when they
    are, they come first. They are an ``Occupant`` and not a ``PlayerSkill``,
    because a player browsing padel matches may only ever have been rated at
    tennis, and refusing to analyse a match for them would hide every padel match
    from exactly the players most in need of one.
    """

    sport: Sport
    seats: tuple[SeatSnapshot, ...]
    current_player: Occupant

    start: Instant
    """When the match starts, as an instant. **Never as a clock face.**

    An ``Instant`` is UTC, and the day and hour a player declared are a clock
    face, so the two only meet through the club's zone and the kernel's readers.
    That conversion is the whole of the time fit term's arithmetic, and it is the
    reason the start is carried as the moment rather than as the local Tuesday
    19:00 it will be rendered as: a local weekday assembled elsewhere and carried
    beside the instant is a second answer to a timezone question, and the two
    disagree for the two hours either side of a Warsaw midnight before anybody
    compares them.

    Rounded to the minute, which is checked rather than assumed: a start carrying
    seconds reads back as the minute *below* it, so a match at 18:59:59 sits
    outside a window declared from 19:00 by one second nobody can see.
    """

    counted: bool
    """Whether the match counts towards ratings and ladders.

    Read against the player's declared preference and never used to assume one.
    """

    seat_share: SeatShare
    """One player's part of the court price, from ``kernel/money.py``.

    Carried beside the payable and **not read by any term**, deliberately: what a
    player weighs a price ceiling against is what they will actually be charged,
    and a card that struck through the share to show the payable needs both. The
    price term provably reads the payable — a snapshot whose share moves and whose
    payable does not scores identically, which is a test rather than a comment.
    """

    payable: Payable
    """What the current player actually owes for their seat, after any club card.

    The money kernel's refinement chain ends here: ``court_price`` rounds once at
    the court, ``divide_among_players`` splits it exactly, ``payable_from`` applies
    the capped card offset. An engine reads the end of that chain and never
    re-derives any step of it.
    """

    club: ClubSnapshot
    """The club this match is at, as much of it as an engine is given."""

    ladder: LadderQualification
    """Whether this match counts towards the current player's ladder."""

    history: PlayHistory | None = None
    """Who in this match the current player has played recently. **Ships dark.**

    Defaulted to absent, which the required fields above deliberately are not.
    Absence here is *reported*: the familiarity term is excluded, Coverage falls,
    and a reader of the score can see the platform said nothing. Absence in a
    price or a club would be *assumed* — a default of zero grosze is a free match
    and a default of zero minutes is a court next door — so those have no default
    and an assembler that forgets one fails to compile rather than to be right.
    """

    def __post_init__(self) -> None:
        invariant(
            len(self.seats) == self.sold_seats,
            f"{self.sport.value} is sold in {self.sold_seats} seats, "
            f"snapshot carries {len(self.seats)}",
        )
        # Read through attribute access and not by importing `datetime`, which
        # the engines layer is forbidden — the same shape the engines' `now`
        # precondition takes, and for the same reason: a coordinate read off an
        # instant carrying seconds is silently one minute early.
        invariant(
            self.start.second == 0 and self.start.microsecond == 0,
            f"a start that is not rounded to the minute: {self.start!r}",
        )
        # The money kernel's own claim — *"a payable is never negative and never
        # exceeds its share"* — holds by construction for anything built through
        # `payable_from`, and `NewType` erases, so an assembler that computed the
        # pair by hand could carry two figures that contradict it. This is the one
        # place that pair enters the engines, so it is the one place to check.
        invariant(
            0 <= self.payable <= self.seat_share,
            f"a payable of {self.payable} against a share of {self.seat_share}",
        )

    @property
    def sold_seats(self) -> int:
        """How many seats this match is sold in, from the kernel registry.

        Read rather than carried, so no snapshot can assert a two-player padel
        match into existence. *"A sport's player count is never club-configurable.
        No field on any club or court may override it; the value is read from
        exactly one place, everywhere."*
        """

        spec = invariant(
            SPORT_SPECS.get(self.sport), f"no spec for sport: {self.sport!r}"
        )
        return spec.players

    @property
    def occupants(self) -> tuple[Occupant, ...]:
        """Everybody on a seat, in seat order — **paid and held alike.**

        The glossary's Roster is *the paid seats*, and a held seat *contributes
        its player's level but not their attendance*, so both are here: the two
        states differ in whether the person turns up, never in whether they count
        towards how even the match will be. Reading only the paid ones would drop
        a player who is in the match from the forecast of it.
        """

        return tuple(seat.occupant for seat in self.seats if seat.occupant is not None)

    @property
    def paid_seats(self) -> int:
        """How many seats are paid for, as distinct from merely held.

        Not read by the balance forecast, which cannot tell the two apart on
        purpose. It is here because the distinction has exactly one consumer —
        the viability term, which asks how likely the match is to happen — and
        because a snapshot that carried the state without ever counting it would
        be carrying a field nothing reads.
        """

        return sum(1 for seat in self.seats if seat.state is SeatState.PAID)
