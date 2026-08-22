"""Deliberately-wrong uses of the pure layer, each one a constraint being claimed.

Named for the kernel because that is where it started, and it now covers the
engines' branded vocabulary too — one subject file, so one ``mypy`` run answers
for the whole fence rather than one per package.

This file is **not run and not collected**. It is read by ``mypy``, driven from
``tests/unit/test_kernel_typing.py``, which asserts that every line marked with
a ``# want-error:`` comment produces exactly that error code — and that no line
without one produces any error at all.

Why it exists: the kernel's constraints are carried by the type system, and the
type system erases at runtime. Delete ``@final`` from ``Ok``, widen ``Err``'s
reason to ``object``, drop the ``Never`` from ``exhaustive`` — every one of those
changes behaviour not at all, breaks no test, and passes review as a
simplification. The claim *"dividing before rounding does not typecheck"* is
worth precisely what checks it.

**Adding a case is the point.** Each branded module lands its own misuses here;
the money module's raw-number-into-a-seat-share is what this harness was really
built for, and it is now below — *"dividing before rounding does not typecheck"*
is a claim about the compiler and nothing else could check it.

Every legitimate use below is load-bearing too: it is a line the harness asserts
is *clean*, so a constraint that grows teeth it should not have — a narrowing
that stops narrowing, a chain that stops composing — fails here as loudly as one
that loses them.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from fractions import Fraction
from typing import Literal
from zoneinfo import ZoneInfo

from app.engines.forecast import (
    BalanceForecast,
    Certainty,
    NoForecast,
    NoSeatTarget,
    NoTargetBand,
    PairingAnalysis,
    SidesNotFormed,
    Split,
    TargetBand,
    UnratedSeat,
)
from app.engines.matchmaking import (
    ClubSnapshot,
    HourWindow,
    LadderQualification,
    Level,
    MatchTypePreference,
    MatchSnapshot,
    Occupant,
    PlayerRef,
    PlayerProfile,
    PlayerScore,
    PlayerSkill,
    SeatSnapshot,
    SeatState,
    CourtHold,
    HOLD_LADDER,
    MatchPhase,
    Uncertainty,
    UnratedPlayer,
    Weekday,
    level,
    uncertainty,
)
from app.engines.fit import (
    BalanceFact,
    ExcludedTerm,
    MatchFitScore,
    PriceFact,
    ReliabilityFact,
    ScoredTerm,
    SkillOverlapFact,
    Term,
    TermCode,
    TermKind,
    TimeFact,
    ViabilityFact,
)
from app.engines.matchfit.core import Observed, constraint_term, evidence_term
from app.engines.pairing.core import Contender, Roster, Side, as_float, side_of_one
from app.kernel import (
    SPORT_SPECS,
    CardAllowance,
    CardCoversShare,
    Clock,
    ClubCard,
    CourtPrice,
    DayOffset,
    Boundary,
    Err,
    Grosze,
    Hold,
    HoldMove,
    HoldPolicy,
    Instant,
    InvariantViolated,
    LeaverMoney,
    IsoWeekday,
    MatchRecord,
    MinuteOfDay,
    Minutes,
    NoCard,
    NonexistentLocalTime,
    NothingTaken,
    OfferKind,
    Ok,
    Outcome,
    Payable,
    Ratio,
    Reason,
    Recoverable,
    Result,
    Seat,
    SeatShare,
    Situation,
    Sport,
    SportSpec,
    Unavailable,
    Viewer,
    WakeReason,
    Zone,
    add_grosze,
    apply_fraction,
    card_offset,
    court_hold,
    court_price,
    day_offset,
    divide_among_players,
    elapsed_minutes,
    exhaustive,
    grosze,
    hold_move,
    hours,
    instant,
    invariant,
    iso_weekday,
    keeping_a_court,
    live_outcome,
    local_iso_weekday,
    local_minute_of_day,
    minute_of_day,
    minutes,
    next_wake,
    next_wake_at,
    outcome_rank,
    outcome_worse_than,
    payable_from,
    percent,
    ratio,
    refill_outcome,
    round_half_away_from_zero,
    shifted,
    situation,
    slot_start,
    zloty,
)


@dataclass(frozen=True)
class Closed:
    """A stand-in reason: a machine code and its payload, no sentence."""

    day_offset: int
    kind: Literal["closed"] = "closed"


@dataclass(frozen=True)
class Sentenced:
    """A stand-in for the reason nobody may write: words instead of a code."""

    message: str


# --- Result has exactly two inhabitants, and neither is open -------------------


class ThirdInhabitant(Ok[int]):  # want-error: misc
    """A success that is also something else. `@final` is what forbids it."""


class FourthInhabitant(Err[Closed]):  # want-error: misc
    """Likewise a failure. Two `@final` classes are the whole closed set."""


def a_result_is_immutable(result: Ok[int]) -> None:
    result.value = 2  # want-error: misc


def both_members_must_be_handled(result: Result[int, Closed]) -> int:
    """A match that handles only the success is not a match over a `Result`."""

    match result:
        case Ok(value):
            return value
        case _:
            exhaustive(result)  # want-error: arg-type


# --- A reason is a machine code, never a sentence ------------------------------

#: The case that catches the `Reason` bound being widened, and the only one that
#: does. With no annotation to solve `_R` from, the bound is the sole thing that
#: can refuse this. The two functions below are refused by their *return type*
#: as well, so both would survive `_R` losing its bound entirely — which is what
#: a mutation run found, and why this line is here.
A_SENTENCE_IS_NOT_A_REASON = Err("No courts are available.")  # want-error: type-var


def a_reason_is_never_a_sentence() -> Err[Reason]:
    """The whole point of the `Reason` bound, and the one a reviewer forgets."""

    return Err("No courts are available that afternoon.")  # want-error: arg-type


def a_reason_without_a_code_is_not_a_reason() -> Err[Reason]:
    """`Sentenced` carries words and no `kind`, so it is not a reason at all."""

    return Err(Sentenced(message="No courts available."))  # want-error: arg-type


def a_reason_is_a_plain_frozen_dataclass() -> Err[Closed]:
    """And this one is clean: declaring `kind` is the whole of the contract."""

    return Err(Closed(day_offset=1))


# --- The reason union is closed, and the compiler knows what is in it ---------


def a_reason_nobody_declared_is_not_unavailable() -> Result[int, Unavailable]:
    """`Closed` is a stand-in defined in this file, so it is not in the union.

    This is what makes *"the closed set of reasons the kernel can give"* a fact
    rather than a comment: a module cannot widen it by declaring a dataclass,
    only by adding a line to `app/kernel/unavailability.py`.

    It was `return-value` while the union was `Never` and became `arg-type` when
    it gained a member — with something concrete to solve `_R` against, mypy
    refuses the reason rather than the return. Same constraint, and the marker
    tracks what the compiler actually says.
    """

    return Err(Closed(day_offset=1))  # want-error: arg-type


def the_union_has_a_member_now() -> Result[int, Unavailable]:
    """It shipped as `Never`. The time module landed the first real reason."""

    return Err(
        NonexistentLocalTime(
            zone="Europe/Warsaw",
            local_date=date(2026, 3, 29),
            minute_of_day=minute_of_day(150),
        )
    )


def a_result_that_cannot_fail_is_still_a_result() -> Result[int, Unavailable]:
    return Ok(1)


# --- Mapping and chaining keep the reason's type ------------------------------


@dataclass(frozen=True)
class Elsewhere:
    kind: Literal["elsewhere"] = "elsewhere"


def a_chain_cannot_swap_the_reason(
    result: Result[int, Closed],
) -> Result[str, Closed]:
    """`and_then` composes only where the two halves can fail the same way."""

    return result.and_then(lambda value: Err(Elsewhere()))  # want-error: arg-type


def a_chain_composes(result: Result[int, Closed]) -> Result[str, Closed]:
    return result.and_then(lambda value: Ok(str(value)))


def a_map_keeps_the_reason(result: Result[int, Closed]) -> Result[str, Closed]:
    return result.map(str)


# --- `invariant` narrows, and the narrowing is the reason it is not an `if` ---


def without_the_invariant(sport: Sport) -> int:
    """The state a caller is in before the guard: the lookup may miss."""

    spec = SPORT_SPECS.get(sport)
    return spec.players  # want-error: union-attr


def with_the_invariant(sport: Sport) -> int:
    """And after it. This line erroring means the narrowing has stopped.

    It is the half of the pair that cannot be asserted by marking it — an
    absence of an error is only evidence when something otherwise identical
    does produce one, which is what the function above is for.
    """

    spec: SportSpec = invariant(SPORT_SPECS.get(sport), f"no spec: {sport!r}")
    return spec.players


def an_invariant_is_not_caught_as_a_value_error() -> None:
    """`InvariantViolated` is deliberately not a `ValueError`."""

    try:
        invariant(None, "nothing")
    except InvariantViolated:
        pass


# --- Exhaustiveness over the registry that is already closed ------------------


def every_sport_must_be_named(sport: Sport) -> str:
    """Badminton is missing, so `sport` is not `Never` where the tail sits."""

    match sport:
        case Sport.PADEL:
            return "padel"
        case Sport.TENNIS:
            return "tennis"
        case Sport.SQUASH:
            return "squash"
        case _:
            exhaustive(sport)  # want-error: arg-type


def all_four_named(sport: Sport) -> str:
    match sport:
        case Sport.PADEL:
            return "padel"
        case Sport.TENNIS:
            return "tennis"
        case Sport.SQUASH:
            return "squash"
        case Sport.BADMINTON:
            return "badminton"
        case _:
            exhaustive(sport)


# --- Time: the brands bind, and a coordinate is not another coordinate --------
#
# `Instant`, `MinuteOfDay`, `DayOffset` and `Minutes` are `NewType`s, which erase
# to `datetime` and `int` at runtime. Collapse them to their base types and every
# test in the suite still passes — these lines are the only thing that notices.

WARSAW = ZoneInfo("Europe/Warsaw")
NOON = instant(datetime(2026, 3, 29, 12, 0, tzinfo=timezone.utc))


def a_raw_minute_is_not_a_minute_of_day() -> Result[Instant, NonexistentLocalTime]:
    """The brand's whole job: an unvalidated integer cannot reach the grid."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=150,  # want-error: arg-type
        zone=WARSAW,
    )


def a_day_is_not_a_minute() -> Result[Instant, NonexistentLocalTime]:
    """Two `NewType`s over `int`, and they do not interchange — transposing
    them asks for day 150 of a grid, silently and with no wrong-looking value
    anywhere in the call."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=day_offset(150),  # want-error: arg-type
        zone=WARSAW,
    )


def a_minute_is_not_a_day() -> Result[Instant, NonexistentLocalTime]:
    """And the same claim from the other side, which is the load-bearing half.

    A mutation run found this missing. Every case above is refused by
    `MinuteOfDay`'s brand, so **dropping `DayOffset`'s left the suite green** —
    `day_offset(150)` returning a plain `int` is still refused where a
    `MinuteOfDay` is wanted. Only a case refused by `DayOffset` *itself* catches
    that, and this and the next one are those: with `DayOffset = int`, a
    `MinuteOfDay` and a literal both become assignable and both lines go clean.
    """

    return slot_start(
        anchor=NOON,
        day=minute_of_day(0),  # want-error: arg-type
        minute=minute_of_day(150),
        zone=WARSAW,
    )


def a_raw_day_is_not_a_day_offset() -> Result[Instant, NonexistentLocalTime]:
    return slot_start(
        anchor=NOON,
        day=0,  # want-error: arg-type
        minute=minute_of_day(150),
        zone=WARSAW,
    )


def a_duration_is_not_a_minute_of_day() -> Result[Instant, NonexistentLocalTime]:
    """A length of time and a point in the day are both minutes, and neither
    is the other — a ninety-minute slot is not 01:30."""

    return slot_start(
        anchor=NOON,
        day=day_offset(0),
        minute=minutes(90),  # want-error: arg-type
        zone=WARSAW,
    )


def a_plain_datetime_is_not_an_instant() -> Minutes:
    """Which is what makes `instant()` the one way in, naive check included."""

    return elapsed_minutes(datetime(2026, 3, 29, 10, 0), NOON)  # want-error: arg-type


def an_aware_datetime_is_not_an_instant_either() -> Minutes:
    """Aware is *necessary*, not sufficient: an `Instant` is aware **and** UTC,
    and only the constructor establishes that."""

    aware = datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc)
    return elapsed_minutes(aware, NOON)  # want-error: arg-type


def a_duration_is_not_a_number_of_minutes_either() -> Instant:
    return shifted(NOON, 90)  # want-error: arg-type


# --- And the refinement holds in the direction #75 depends on -----------------


def an_instant_goes_wherever_a_datetime_is_wanted(moment: Instant) -> datetime:
    """The claim that made retiring `app/shared/clock.py` (#75) an import change
    rather than a rewrite: every existing signature already takes this."""

    return moment


def a_minute_of_day_is_still_an_int(minute: MinuteOfDay) -> int:
    return minute * 2


def a_clock_returns_an_instant(clock: Clock) -> datetime:
    return clock.now()


def a_weekday_is_not_a_minute_of_day() -> MinuteOfDay:
    """The case `IsoWeekday`'s brand alone catches, and the reason it exists.

    Both are `NewType`s over `int` and Wednesday is 3, which is also a perfectly
    legal minute meaning *three minutes past midnight*. Collapse `IsoWeekday` to
    `int` and this line goes quiet while every runtime test still passes.
    """

    return local_iso_weekday(NOON, WARSAW)  # want-error: return-value


def a_weekday_is_not_a_day_offset() -> DayOffset:
    """Anchor-relative days and days of the week are different quantities.

    Sunday is 7 and *seven days from the anchor* is 7, so the transposition has no
    wrong-looking value anywhere in it — the two brands are the only thing between
    a card offered next Sunday and one offered a week today.
    """

    return iso_weekday(7)  # want-error: return-value


def a_minute_is_not_a_weekday() -> IsoWeekday:
    """And the other direction, which the range check cannot make loud.

    `iso_weekday` refuses anything outside 1..7 at runtime, so a minute of 600
    raises — but a minute of 3 does not, and that is the call this line refuses
    before it can be written.
    """

    return local_minute_of_day(NOON, WARSAW)  # want-error: return-value


#: A club a match can be at: twelve minutes away, in Warsaw, half its capacity taken
#: at the hour in question. Written once because four snapshots below need one, and a
#: club assembled four times is four chances to write a different crowding.
A_CLUB = ClubSnapshot(travel_minutes=minutes(12), zone=WARSAW, crowding=percent(50))

#: The last moment a seat can be taken. Two hours before `NOON`, which is what makes
#: it a legal cutoff for a match starting then.
A_CUTOFF = shifted(NOON, minutes(-120))


def a_zone_is_not_its_name() -> ClubSnapshot:
    """A club carries the kernel's `Zone`, never the IANA string it was built from.

    A name is a string until somebody resolves it, and *who resolves it* is the
    question the kernel answers exactly once: an engine holds a zone and can
    neither build one nor decide what one means.
    """

    return ClubSnapshot(
        travel_minutes=minutes(12),
        zone="Europe/Warsaw",  # want-error: arg-type
        crowding=percent(50),
    )


def a_match_without_a_start_does_not_compile() -> MatchSnapshot:
    """No default, for the same reason the price and the club have none.

    A default of *now* is a match starting this instant, which is a wrong answer
    rather than a loud one — so an assembler that forgets when the match is fails
    to compile instead of scoring one against the wrong evening.
    """

    return MatchSnapshot(  # want-error: call-arg
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=CourtHold.HARD,
        join_cutoff=A_CUTOFF,
    )


def a_zone_is_what_both_readers_take() -> tuple[IsoWeekday, MinuteOfDay]:
    """The legitimate use beside them: one instant, one zone, both halves."""

    return local_iso_weekday(NOON, WARSAW), local_minute_of_day(NOON, WARSAW)


def a_zone_may_be_held_without_importing_zoneinfo(zone: Zone) -> IsoWeekday:
    """And the reason `Zone` is exported at all: an engine names the type."""

    return local_iso_weekday(NOON, zone)


def the_coordinates_compose(anchor: Instant) -> Result[Instant, NonexistentLocalTime]:
    return slot_start(
        anchor=shifted(anchor, hours(-12)),
        day=day_offset(-1),
        minute=minute_of_day(150),
        zone=WARSAW,
    )


# --- The conversion can fail, and the caller is made to notice ----------------


def the_gap_cannot_be_ignored() -> Instant:
    """`slot_start` returns a `Result`, so a nonexistent local time is not
    something a caller can walk past — the whole point of returning it."""

    return slot_start(  # want-error: return-value
        anchor=NOON, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    )


def both_halves_of_the_conversion_must_be_handled(anchor: Instant) -> str:
    match slot_start(
        anchor=anchor, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    ):
        case Ok(value):
            return value.isoformat()
        case _:
            exhaustive(anchor)  # want-error: arg-type


def and_here_they_are(anchor: Instant) -> str:
    match slot_start(
        anchor=anchor, day=day_offset(0), minute=minute_of_day(150), zone=WARSAW
    ):
        case Ok(value):
            return value.isoformat()
        case Err(reason):
            return reason.kind


def a_gap_is_a_reason_and_reasons_are_frozen() -> None:
    reason = NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=date(2026, 3, 29),
        minute_of_day=minute_of_day(150),
    )
    reason.zone = "Europe/Berlin"  # want-error: misc


def a_gap_carries_a_local_date_never_a_day_offset(
    day: DayOffset,
) -> NonexistentLocalTime:
    """A `DayOffset` is anchor-relative, so it must not leave the process — and
    a reason is the one kernel value that crosses the wire."""

    return NonexistentLocalTime(
        zone="Europe/Warsaw",
        local_date=day,  # want-error: arg-type
        minute_of_day=minute_of_day(150),
    )


# --- Money: the rounding order, made unwritable rather than documented --------
#
# `Grosze`, `CourtPrice`, `SeatShare`, `Payable` and `Ratio` are `NewType`s over
# `int` and `Fraction`, and they erase completely. Collapse any of them and
# every test in the suite still passes — a court price divided before it was
# rounded computes a perfectly ordinary number, ten grosze away from the right
# one. These lines are the only thing that notices.

DISCOUNTED_COURT = court_price(zloty(96), percent(90))
A_SEAT = divide_among_players(DISCOUNTED_COURT, 4)


def a_raw_number_is_not_money() -> CourtPrice:
    """The case that catches `Grosze` collapsing to `int`."""

    return court_price(9600)  # want-error: arg-type


def a_number_of_minutes_is_not_an_amount_of_money() -> CourtPrice:
    """Two `NewType`s over `int`. A ninety-minute slot is not ninety grosze,
    and transposing them produces a price with nothing wrong-looking in it."""

    return court_price(minutes(90))  # want-error: arg-type


def a_bare_int_is_not_grosze_on_the_way_out() -> Grosze:
    return 2150  # want-error: return-value


def dividing_before_rounding_does_not_typecheck() -> SeatShare:
    """**The claim this whole harness was built for.**

    `divide_among_players` accepts only a `CourtPrice`, and the only way to hold
    one is to have gone through `court_price`, which is where the single
    rounding to whole złoty happens. So there is no path from a raw amount to a
    seat share, and the 21,60-instead-of-21,50 bug has nowhere to be written.
    """

    return divide_among_players(grosze(8640), 4)  # want-error: arg-type


def a_float_price_does_not_typecheck_either() -> SeatShare:
    """The other half of the same claim: no float reaches a price."""

    return divide_among_players(86.4, 4)  # want-error: arg-type


def a_seat_share_is_not_a_court_price() -> SeatShare:
    """Two refinements of one base unit, and they do not interchange.

    Splitting a share again is how a court gets divided by sixteen. Refused by
    `CourtPrice`'s own brand, as is the case above it — collapsing `CourtPrice`
    to `Grosze` frees both, which is checked rather than assumed: each of the
    five money brands has at least one marker here that goes unenforced when it
    alone is collapsed.
    """

    return divide_among_players(A_SEAT, 4)  # want-error: arg-type


def a_plain_amount_is_not_a_seat_share() -> Payable:
    return payable_from(grosze(2150), NoCard())  # want-error: arg-type


def a_court_price_is_not_a_seat_share() -> Payable:
    """The failure this one names is the expensive one: a `CourtPrice` is a
    `Grosze`, so with `SeatShare` collapsed the whole court is charged to one
    player and every number involved looks entirely ordinary."""

    return payable_from(DISCOUNTED_COURT, NoCard())  # want-error: arg-type


def an_amount_is_not_already_a_payable() -> Payable:
    """The only direction `Payable`'s brand can be checked in — nothing takes
    one as an argument, so the claim is that a `Grosze` cannot become one
    without the card rule having run."""

    return grosze(2150)  # want-error: return-value


def a_float_is_not_a_multiplier() -> CourtPrice:
    """`0.9` is not nine tenths, and this is where that stops being writable."""

    return court_price(zloty(96), 0.9)  # want-error: arg-type


def an_unbranded_fraction_is_not_a_multiplier_either() -> CourtPrice:
    """Refused by `Ratio`'s own brand, and the only case that is.

    `Fraction(0.9)` is exact and wrong — it is the double nearest nine tenths,
    not nine tenths — so the brand is what forces the two-integer constructor.
    """

    return court_price(zloty(96), Fraction(9, 10))  # want-error: arg-type


def a_percentage_is_not_a_ratio() -> Grosze:
    return apply_fraction(A_SEAT, 50)  # want-error: arg-type


def the_one_rounding_rule_does_not_take_a_float() -> int:
    """The rule is exact, and a float is where the exactness would have leaked out.

    Public since #88, so both engines delegate to it rather than restating it — and
    the whole point of the `Fraction` signature is that the caller does the crossing
    deliberately, at a line that says so, rather than passing a float that happens to
    round the same way until the one time it does not. `pairing/core` writes exactly
    that crossing; this refuses the version of it that skips the thought.
    """

    return round_half_away_from_zero(82.5)  # want-error: arg-type


class FourthKindOfCard(NoCard):  # want-error: misc
    """A club card is one of three things. `@final` is what closes the set."""


def a_card_is_immutable(card: CardAllowance) -> None:
    card.amount = zloty(9)  # want-error: misc


def every_kind_of_card_must_be_handled(share: SeatShare, card: ClubCard) -> Grosze:
    """`CardCoversShare` is missing, so `card` is not `Never` at the tail — the
    member whose omission would silently charge a fully-covered player."""

    match card:
        case NoCard():
            return grosze(0)
        case CardAllowance(amount):
            return amount
        case _:
            exhaustive(card)  # want-error: arg-type


# --- And the legitimate walk beside them, which has to stay legitimate --------


def the_rounding_order_composes(base: Grosze, off_peak: Ratio) -> Payable:
    return payable_from(
        divide_among_players(court_price(base, off_peak, percent(90)), 4),
        CardAllowance(zloty(8)),
    )


def a_refinement_goes_wherever_the_base_unit_is_wanted(
    share: SeatShare, owed: Payable
) -> Grosze:
    """Arithmetic takes any amount and hands back an unrefined one, which is
    the point: a share plus a payable is neither of those things."""

    return add_grosze(share, owed)


def all_three_cards_named(share: SeatShare, card: ClubCard) -> Grosze:
    match card:
        case NoCard():
            return grosze(0)
        case CardAllowance(amount):
            return amount
        case CardCoversShare():
            return card_offset(share, card)
        case _:
            exhaustive(card)


# --- The matchmaking brands: a Level is not an Uncertainty ---------------------
#
# `Level` and `Uncertainty` are both `NewType`s over the kernel's `Ratio`, so at
# runtime they are the same `Fraction` and every case below runs perfectly well.
# Collapse either brand to `Ratio` and the arithmetic is bit-identical, no test
# breaks, and the diff reads like a simplification — which is the entire reason
# these lines exist. Each brand has at least one case refused by *it alone*.

A_REF = PlayerRef("ada")
A_LEVEL: Level = level(320)
A_SIGMA: Uncertainty = uncertainty(15)

#: A term value: a rate in 0..1, exact, the way every term carries one.
A_RATE: Ratio = percent(80)

#: What one player owes for a seat of `DISCOUNTED_COURT` above, with no club card.
A_PAYABLE: Payable = payable_from(A_SEAT, NoCard())


def a_level_is_not_an_uncertainty() -> PlayerSkill:
    """Refused by `Uncertainty`'s brand and by nothing else: a `Level` *is* a
    `Ratio`, so collapsing `Uncertainty` to `Ratio` would let a player's skill
    stand in for how sure the platform is about it."""

    return PlayerSkill(
        player=A_REF,
        level=A_LEVEL,
        uncertainty=A_LEVEL,  # want-error: arg-type
        confidence=30,
    )


def an_uncertainty_is_not_a_level() -> PlayerSkill:
    """The same swap the other way, refused by `Level`'s brand alone."""

    return PlayerSkill(
        player=A_REF,
        level=A_SIGMA,  # want-error: arg-type
        uncertainty=A_SIGMA,
        confidence=30,
    )


def a_ratio_is_not_a_level() -> Side:
    """A rate multiplier and a rating are both exact ratios and are not the same
    kind of thing. The constructor is the only way in, and it is what carries the
    hundredths convention and the floor."""

    return Side(strength=ratio(320, 100), sigma=0.2)  # want-error: arg-type


def a_bare_fraction_is_not_an_uncertainty() -> PlayerSkill:
    return PlayerSkill(
        player=A_REF,
        level=A_LEVEL,
        uncertainty=Fraction(15, 100),  # want-error: arg-type
        confidence=30,
    )


def a_name_is_not_a_player_ref() -> PlayerSkill:
    """Refused by `PlayerRef`'s brand alone — the only line that catches it."""

    return PlayerSkill(
        player="ada",  # want-error: arg-type
        level=A_LEVEL,
        uncertainty=A_SIGMA,
        confidence=30,
    )


def a_level_is_written_in_hundredths_not_in_levels() -> Level:
    """3,20 is `level(320)`. A float has nowhere to enter the vocabulary."""

    return level(3.20)  # want-error: arg-type


def a_snapshot_holds_a_tuple_of_seats_and_not_a_list() -> MatchSnapshot:
    """Fixed-arity collections are tuples, everywhere (`docs/adr/0022`)."""

    return MatchSnapshot(
        sport=Sport.TENNIS,
        seats=[SeatSnapshot(), SeatSnapshot()],  # want-error: arg-type
        current_player=PlayerSkill(
            player=A_REF, level=A_LEVEL, uncertainty=A_SIGMA, confidence=30
        ),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=CourtHold.HARD,
        join_cutoff=A_CUTOFF,
    )


class ASecondWayToHaveNoForecast(SidesNotFormed):  # want-error: misc
    """The reason union is closed by `@final`, the way the kernel's is.

    A subclass would be a member of `NoForecast` that nothing declared, so a
    `match` over the union would still typecheck while silently not handling it —
    the failure `exhaustive` exists to make loud."""


def a_snapshot_is_immutable(snapshot: MatchSnapshot) -> None:
    snapshot.seats = ()  # want-error: misc


def a_forecast_is_immutable(forecast: BalanceForecast) -> None:
    forecast.estimate = 100  # want-error: misc


class AFourthWayToArrangeFourPlayers(Split):  # want-error: misc
    """Four players admit exactly three splits, and `@final` is what makes that a
    statement about the type rather than about the current implementation."""


def a_split_is_immutable(split: Split) -> None:
    split.side_a = ()  # want-error: misc


def a_side_of_a_split_is_who_is_on_it_and_not_what_they_play_like(
    forecast: BalanceForecast,
) -> Split:
    """The two facets are deliberately different types. `Split.side_a` is the
    people; `forecast.side_a` is the Level they play at together, and swapping
    them is the one mistake a caller drawing a line-up could actually make."""

    return Split(
        side_a=(forecast.side_a,),  # want-error: arg-type
        side_b=(A_REF,),
        forecast=forecast,
    )


def a_name_is_not_a_player_ref_on_a_split_either(forecast: BalanceForecast) -> Split:
    """Refused by `PlayerRef`'s brand alone: a side is a tuple of references the
    Matches context handed over, not a tuple of whatever a caller can spell."""

    return Split(
        side_a=("ada", "bo"),  # want-error: arg-type
        side_b=(A_REF,),
        forecast=forecast,
    )


def the_three_splits_are_a_tuple_and_not_a_list(
    forecast: Result[BalanceForecast, NoForecast],
    seat_target: Result[Level, NoSeatTarget],
    target_band: Result[TargetBand, NoTargetBand],
) -> PairingAnalysis:
    """Fixed-arity collections are tuples, everywhere (`docs/adr/0022`) — and an
    analysis a caller could append a fourth arrangement to is one that no longer
    means *the complete enumeration*."""

    return PairingAnalysis(
        forecast=forecast,
        splits=[],  # want-error: arg-type
        seat_target=seat_target,
        target_band=target_band,
        engine_version="pairing-v1",
    )


class ASecondKindOfTargetBand(TargetBand):  # want-error: misc
    """`@final`, for the same reason a reason is: a band with a second shape is
    one a caller drawing edges would have to ask which kind it had."""


def a_band_is_immutable(band: TargetBand) -> None:
    band.midpoint = level(300)  # want-error: misc


def a_seat_target_is_a_level_and_not_a_band(
    forecast: Result[BalanceForecast, NoForecast],
    target_band: Result[TargetBand, NoTargetBand],
) -> PairingAnalysis:
    """The two answers a forming match gives are deliberately different types.
    One is the Level a single seat is aimed at; the other is the range the whole
    match is. A caller that could pass either where the other goes is one that
    can print a band as though it were a seat."""

    return PairingAnalysis(
        forecast=forecast,
        splits=(),
        seat_target=target_band,  # want-error: arg-type
        target_band=target_band,
        engine_version="pairing-v1",
    )


def a_band_is_not_widened_by_a_bare_number() -> TargetBand:
    """Refused by `Ratio`'s brand: a half width is an exact ratio over two
    integers, and a float here is the `Fraction(0.9)` hole in a new place."""

    return TargetBand(midpoint=level(300), half_width=0.5)  # want-error: arg-type


def every_way_a_seat_target_can_be_absent_must_be_handled(
    seat_target: Result[Level, NoSeatTarget],
) -> Level:
    """Three reasons, not one: the seat is under-determined, there are no sides to
    even up at all, or a seated player has no rating at this sport. A caller
    handling two of them leaves the third unhandled at the tail."""

    match seat_target:
        case Ok(value):
            return value
        case Err(SidesNotFormed()):
            return level(300)
        case Err(UnratedSeat()):
            return level(300)
        case _:
            exhaustive(seat_target)  # want-error: arg-type


def every_way_a_forecast_can_be_absent_must_be_handled(
    forecast: Result[BalanceForecast, NoForecast],
) -> int:
    """A forecast that is missing is a `Result`, so the caller branches. Handling
    only the answer leaves the reason unhandled at the tail."""

    match forecast:
        case Ok(value):
            return value.estimate
        case _:
            exhaustive(forecast)  # want-error: arg-type


# --- And the legitimate uses beside them, which have to stay legitimate --------


def a_rating_is_a_level_and_an_uncertainty_together() -> PlayerSkill:
    return PlayerSkill(
        player=PlayerRef("bo"),
        level=level(285),
        uncertainty=uncertainty(84),
        confidence=30,
    )


def a_level_goes_wherever_a_ratio_is_wanted() -> float:
    """The refinement is one-directional, which is the whole of the brand: a
    `Level` is a `Ratio`, and `as_float` takes any of them."""

    return as_float(A_LEVEL) - as_float(A_SIGMA)


def a_side_is_a_strength_and_the_uncertainty_of_it() -> Side:
    return Side(strength=level(310), sigma=as_float(uncertainty(20)))


def a_split_is_who_is_with_whom_and_what_that_plays_like(
    forecast: BalanceForecast,
) -> Split:
    return Split(
        side_a=(A_REF, PlayerRef("bo")),
        side_b=(PlayerRef("cy"), PlayerRef("dee")),
        forecast=forecast,
    )


# --- Roster states, seat imputation, and the two brands that erase into nothing ---
#
# `SeatState` is an enum and `UnratedPlayer` a `@final` frozen class, so both are
# real at runtime. What erases is everything *around* them: `Occupant` is a plain
# union, `Contender.player` is optional, and `NoTargetBand` gained a second member.
# Widen any of those and every test still passes.


def an_unrated_occupant_is_not_a_rating(
    forecast: BalanceForecast,
) -> Side:
    """A player with no rating at this sport carries no Level, so they cannot go
    where a Level and an Uncertainty are wanted. This is the case `Rated` exists
    to refuse — and the one that would let a caller skip imputation entirely,
    forecasting a match on a player the platform cannot place on the scale."""

    return side_of_one(UnratedPlayer(player=A_REF))  # want-error: arg-type


def a_seat_state_is_not_a_seat(occupant: Occupant) -> SeatSnapshot:
    """The state and the occupant are two fields, not one value doing both jobs."""

    return SeatSnapshot(state=occupant, occupant=SeatState.PAID)  # want-error: arg-type


class ASecondKindOfUnratedPlayer(UnratedPlayer):  # want-error: misc
    """`Occupant` is closed by `@final` on both members, so a third kind of
    occupant fails the build at every `match` that does not handle it rather than
    silently falling through one."""


class ASecondKindOfContender(Contender):  # want-error: misc
    """A roster place is resolved or it is not; there is no third state, and a
    subclass would be one nothing declared."""


def a_contender_is_immutable(contender: Contender) -> None:
    contender.level = level(300)  # want-error: misc


def a_roster_is_a_tuple_of_contenders_and_not_of_snapshot_seats(
    seats: tuple[SeatSnapshot, ...],
) -> Roster:
    """The fence in front of imputation, as a type error. A snapshot seat may have
    nobody on it and may hold somebody unrated, so a roster built straight out of
    seats is a roster with places that have no Level — which is exactly what the
    resolution step exists to have already dealt with."""

    return Roster(contenders=seats)  # want-error: arg-type


def an_imputed_count_is_derived_and_cannot_be_asserted(
    contenders: tuple[Contender, ...],
) -> Roster:
    """`imputed_seats` is a property. Carrying it beside the tuple would be a
    second number a retune could leave disagreeing with the first."""

    return Roster(contenders=contenders, imputed_seats=2)  # want-error: call-arg


def every_way_a_band_can_be_absent_must_be_handled(
    target_band: Result[TargetBand, NoTargetBand],
) -> Level:
    """The band's union shipped with one member and has two: nobody is on a seat,
    or nobody on one has a Level here. They are different facts with different
    payloads, and a caller handling one leaves the other unhandled at the tail."""

    match target_band:
        case Ok(value):
            return value.midpoint
        case Err(UnratedSeat()):
            return level(300)
        case _:
            exhaustive(target_band)  # want-error: arg-type


# --- And the legitimate roster uses beside them ----------------------------------


def a_seat_may_be_paid_or_held_or_empty() -> tuple[SeatSnapshot, ...]:
    return (
        SeatSnapshot(
            state=SeatState.PAID,
            occupant=a_rating_is_a_level_and_an_uncertainty_together(),
        ),
        SeatSnapshot(state=SeatState.HELD, occupant=UnratedPlayer(player=A_REF)),
        SeatSnapshot(),
    )


def an_unrated_player_may_be_the_person_the_analysis_is_for() -> MatchSnapshot:
    """A player rated at tennis and not at padel still gets padel cards."""

    return MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=CourtHold.HARD,
        join_cutoff=A_CUTOFF,
    )


def a_resolved_roster_place_goes_where_a_rating_goes() -> Side:
    """The other half of the fence: a `Contender` satisfies `Rated`, so the
    arithmetic takes one — and takes a `PlayerSkill` too, since both carry a
    definite Level and a definite Uncertainty and that is all it reads."""

    return side_of_one(
        Contender(player=A_REF, level=A_LEVEL, uncertainty=A_SIGMA, imputed=True)
    )


def a_split_may_have_an_open_seat_on_a_side(forecast: BalanceForecast) -> Split:
    """`None` is an imputed seat: a position on that team nobody holds yet."""

    return Split(
        side_a=(A_REF, None), side_b=(PlayerRef("cy"), None), forecast=forecast
    )


# --- Match Fit: term kinds, the two states of a term, and the score ---------------
#
# Almost everything Match Fit claims erases. `Term` is a plain union, `TermKind` is
# carried on one member and derived on the other, `Observed` pairs a value with its
# payload, and `TermFact` is six `@final` classes that are structurally identical
# apart from a `Literal`. Widen any of them and every number the engine produces is
# unchanged — which is precisely why these lines are here.


def an_excluded_term_has_no_value_to_default(term: ExcludedTerm) -> Ratio:
    """The mechanism of ADR-0027, as a type error.

    There is no field on an excluded term for a friendly default to be written into,
    so *"we do not know"* cannot be spelled as a score. Give `ExcludedTerm` a
    `value` and the whole repair is undone with no test able to notice.
    """

    return term.value  # want-error: attr-defined


def an_excluded_terms_kind_is_derived_and_cannot_be_asserted() -> ExcludedTerm:
    """Only evidence is ever excluded, so a carried kind would be a field with one
    legal value and one silent bug."""

    return ExcludedTerm(  # want-error: call-arg
        code=TermCode.FAMILIARITY, weight=3, kind=TermKind.CONSTRAINT
    )


def a_terms_payload_must_match_the_term_it_is_on() -> ScoredTerm:
    """`TermFact` is a closed union of six payloads, and the six are told apart by
    their `kind` literal alone. A payload that is not one of them — a bare price, a
    sentence — has no way in."""

    return ScoredTerm(
        code=TermCode.PRICE,
        kind=TermKind.CONSTRAINT,
        weight=6,
        value=A_RATE,
        fact="38 zł, under your ceiling",  # want-error: arg-type
    )


def a_reason_is_a_term_and_never_an_excluded_one(
    term: ExcludedTerm,
) -> tuple[ScoredTerm, ...]:
    """A term that did not run has no contribution, so it cannot be ranked and
    cannot be a reason. The tuple's element type is what says so."""

    return (term,)  # want-error: return-value


def a_warning_is_one_term_and_not_a_list(score: MatchFitScore) -> ScoredTerm | None:
    """*One* warning, on the weakest contributor. A list would be a second ranking
    with no rule behind it."""

    return [score.warning]  # want-error: return-value


def a_constraint_term_cannot_be_built_without_its_payload() -> ScoredTerm:
    """A value with no quantities behind it is a number a card cannot explain."""

    return constraint_term(TermCode.PRICE, 6, A_RATE)  # want-error: call-arg


def an_observation_is_a_value_and_its_payload_together() -> Observed:
    """*A rating is never only a number*, applied to evidence: an observation either
    happened — and can say what it read — or did not, and then there is no value."""

    return Observed(value=A_RATE)  # want-error: call-arg


def a_score_carries_both_engine_versions() -> MatchFitScore:
    """A Match Fit score has two producers, and a constant belonging to either can
    only be falsified against results it can be attributed to."""

    return MatchFitScore(  # want-error: call-arg
        fit=84,
        coverage=63,
        terms=(),
        reasons=(),
        warning=None,
        engine_version="matchfit-v1",
    )


def a_coverage_figure_is_not_a_fit_figure(score: MatchFitScore) -> Ratio:
    """Both are whole percents and neither is a ratio, so a caller cannot quietly
    multiply one into the other — which is what *never blended* means one layer
    down from the docstring that says it."""

    return score.coverage  # want-error: return-value


class ASecondKindOfScoredTerm(ScoredTerm):  # want-error: misc
    """`Term` is closed by `@final` on both members. A third state of a term would
    have to be added to the union, where every reader can see it arrive."""


class ASecondKindOfPriceFact(PriceFact):  # want-error: misc
    """A payload is closed too: a client renders per `kind`, so a subclass would be
    a payload with a code nobody can handle."""


def a_score_is_immutable(score: MatchFitScore) -> None:
    score.fit = 100  # want-error: misc


def a_declaration_is_immutable(declaration: PlayerProfile) -> None:
    declaration.maximum_per_seat = grosze(2500)  # want-error: misc


def a_ceiling_is_money_and_not_a_length_of_time() -> PlayerProfile:
    """The money and time brands are both `NewType`s over `int`, so this is the pair
    of cases that keeps them apart — here, and in the radius below, pointed the
    other way.

    A ceiling is typed as a plain `Grosze` and **not** as a `Payable`, which means a
    payable would typecheck here: the money brands are a refinement chain, so a
    `Payable` *is* an amount. That distinction is semantic and the field name is what
    carries it — a payable is what one player owes for one specific seat after their
    card, and a ceiling is a standing declaration that outlives every match it is
    compared against.
    """

    return PlayerProfile(maximum_per_seat=minutes(2500))  # want-error: arg-type


def a_radius_is_in_minutes_and_a_price_is_not() -> PlayerProfile:
    """Two `NewType`s over `int`, and a card that showed *12 zł away* would be the
    reason both exist."""

    return PlayerProfile(travel_radius=grosze(20))  # want-error: arg-type


def a_declared_day_is_a_weekday_and_not_a_day_offset() -> PlayerProfile:
    """A `DayOffset` is anchor-relative and in-memory only; a declared day is
    Tuesday. Storing one as the other is how a declaration silently changes meaning
    when the anchor moves."""

    return PlayerProfile(days=frozenset({DayOffset(2)}))  # want-error: arg-type


def a_window_runs_over_minutes_of_the_day_and_not_over_durations() -> HourWindow:
    """`MinuteOfDay` is a coordinate and `Minutes` a length. *Three hours* is not a
    time of day, and a window built from two of them would be an interval on a
    clock face nobody has."""

    return HourWindow(start=minutes(1080), end=minutes(1260))  # want-error: arg-type


class ASecondKindOfTimeFact(TimeFact):  # want-error: misc
    """`@final`, like every other payload. A subclass would be a member of
    `TermFact` that nothing declared, so a `match` over the union would typecheck
    while silently not handling it."""


def a_time_payload_carries_the_clock_face_and_not_the_instant() -> TimeFact:
    """The whole point of converting: a term compares a **local** weekday and
    minute, and the instant it came from is not either of them."""

    return TimeFact(
        weekday=Weekday.TUESDAY,
        minute=NOON,  # want-error: arg-type
        days=None,
        hours=None,
    )


def a_declared_day_set_is_frozen() -> TimeFact:
    """The payload reports the declaration it was scored against, unchanged — a
    mutable set handed to a client is a declaration a client could edit."""

    return TimeFact(
        weekday=Weekday.TUESDAY,
        minute=minute_of_day(1110),
        days={Weekday.TUESDAY},  # want-error: arg-type
        hours=None,
    )


def every_way_a_term_can_be_absent_must_be_handled(term: Term) -> Ratio:
    """The union is two members. A caller handling only the scored one leaves the
    exclusion — the state the whole design turns on — unhandled at the tail."""

    match term:
        case ScoredTerm():
            return term.value
        case _:
            exhaustive(term)  # want-error: arg-type


# --- Viability: the clock's three words, and the four facts the term reads --------
#
# `MatchPhase` and `CourtHold` are enums with the same shape as every other enum
# here, `crowding` is a `Ratio` like every other rate, and a join cutoff is an
# `Instant` like every other moment. Swap any pair and the arithmetic still runs and
# still returns a number — which is the whole reason these lines exist.


class ASecondKindOfViabilityPayload(ViabilityFact):  # want-error: misc
    """`TermFact` is closed by `@final` on each member. A subclass would be a payload
    the union does not know about, carrying the same `Literal` and reaching every
    reader that matches on it."""


def a_viability_payload_is_immutable(fact: ViabilityFact) -> None:
    fact.paid_seats = 4  # want-error: misc


def a_hold_is_not_a_phase() -> MatchSnapshot:
    """Two enums about the same match and about different questions.

    *Where the match is on the clock* and *how firmly the court is held* are the two
    facts that make viability always computable, and neither stands in for the other:
    a match cannot be `FORMING` a court or hold a `HARD` phase.
    """

    return MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=CourtHold.HARD,  # want-error: arg-type
        hold=CourtHold.HARD,
        join_cutoff=A_CUTOFF,
    )


def a_hold_is_not_the_word_it_is_spelled_with() -> MatchSnapshot:
    """The vocabulary is borrowed *as an enum*, never as the string on the wire.

    A client renders the rung; an engine reads the member. A `str` here would let an
    assembler pass a spelling the ladder does not contain, and the failure would be a
    `KeyError` inside a term rather than a refusal at the boundary.
    """

    return MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold="hard",  # want-error: arg-type
        join_cutoff=A_CUTOFF,
    )


def a_match_without_a_join_cutoff_does_not_compile() -> MatchSnapshot:
    """No default, for the reason the start has none: a cutoff of *the start* is a
    match joinable up to the moment it begins, which is a wrong answer rather than a
    loud one — and it is the most flattering wrong answer available, because it gives
    every unpaid seat the longest possible run-up."""

    return MatchSnapshot(  # want-error: call-arg
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=CourtHold.HARD,
    )


def a_join_cutoff_is_an_instant_and_not_a_countdown() -> MatchSnapshot:
    """*Minutes remaining* is only true at the moment it was computed.

    The engine is handed the cutoff and `now` and does the subtraction itself, which
    is what makes a cached score wrong about the clock rather than wrong about the
    rule (`docs/adr/0021`).
    """

    return MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(), SeatSnapshot()),
        current_player=UnratedPlayer(player=A_REF),
        start=NOON,
        counted=True,
        seat_share=A_SEAT,
        payable=A_PAYABLE,
        club=A_CLUB,
        ladder=LadderQualification.NOT_IN_A_LADDER,
        phase=MatchPhase.FORMING,
        hold=CourtHold.HARD,
        join_cutoff=minutes(120),  # want-error: arg-type
    )


def a_clubs_crowding_is_a_share_and_not_a_court_count() -> ClubSnapshot:
    """*How many courts a club has* is a fact an engine has no business scaling
    against — two free courts is plenty at a two-court club and nothing at a
    twenty-court one. So the snapshot carries the share and never the count."""

    return ClubSnapshot(
        travel_minutes=minutes(12),
        zone=WARSAW,
        crowding=3,  # want-error: arg-type
    )


def a_travel_time_is_not_a_crowding() -> ClubSnapshot:
    """Both are numbers about the same club and neither is the other's units."""

    return ClubSnapshot(
        travel_minutes=percent(50),  # want-error: arg-type
        zone=WARSAW,
        crowding=minutes(12),  # want-error: arg-type
    )


def a_payload_on_its_own_is_not_an_observation() -> Term:
    """Even the term that can never be excluded goes through ``Observed``.

    *A value and its payload, together or not at all.* A term always able to observe
    something is exactly the one somebody would be tempted to hand its facts to
    directly — and then the value would come from somewhere else, which is the pair
    coming apart at the one call site where nothing else would notice.
    """

    return evidence_term(
        TermCode.MATCH_VIABILITY,
        12,
        ViabilityFact(  # want-error: arg-type
            paid_seats=3,
            sold_seats=4,
            hold=CourtHold.HARD,
            minutes_to_cutoff=minutes(720),
            crowding=percent(50),
        ),
    )


# --- Skill overlap and predicted balance: two Levels, and a percentage ------------
#
# Both payloads are the shapes most easily filled with the nearest number to hand: a
# `Level` and an `Uncertainty` are two brands over the same `Ratio`, an estimate and a
# margin are two `int`s in the same units, and a band's half width is a `Ratio` beside
# two Levels. Every one of those confusions produces a plausible card and a wrong one.


def an_overlap_reads_two_levels_and_never_an_uncertainty() -> ScoredTerm:
    """*A Level is not an Uncertainty*, at the payload that carries two of the first.

    Both are branded over `Ratio` and both are carried in hundredths, so σ 0,84 and a
    Level of 0,84 are the same number at runtime. A target filled in from the wrong
    half of a rating would advertise a match aimed at somebody's *uncertainty*.
    """

    return ScoredTerm(
        code=TermCode.SKILL_OVERLAP,
        kind=TermKind.EVIDENCE,
        weight=24,
        value=A_RATE,
        fact=SkillOverlapFact(
            level=A_LEVEL,
            target=uncertainty(84),  # want-error: arg-type
            band_half_width=None,
        ),
    )


def a_bare_ratio_is_not_a_level() -> SkillOverlapFact:
    """The target is a *point on the scale*, and the brand is what says so.

    **The other direction typechecks, and that is measured rather than assumed.** A
    ``Level`` is a ``NewType`` over ``Ratio``, so it *is* a ratio and one written into
    ``band_half_width`` would be accepted — the same refinement-chain fact the money
    section records about a ``SeatShare`` reaching a price ceiling. What separates a
    point on the scale from a distance along it is the field name, and the direction
    the brand does bind is this one: a bare width can never be advertised as a target.
    """

    width = ratio(50, 100)
    return SkillOverlapFact(
        level=A_LEVEL,
        target=width,  # want-error: arg-type
        band_half_width=width,
    )


def an_overlap_distance_is_derived_and_cannot_be_asserted() -> SkillOverlapFact:
    """The distance is the term's own arithmetic, so it is a property and not a field.

    A carried copy is a number an edit can leave disagreeing with the two Levels it
    came from — which is a payload contradicting the score computed beside it.
    """

    return SkillOverlapFact(  # want-error: call-arg
        level=A_LEVEL,
        target=A_LEVEL,
        band_half_width=None,
        distance=A_RATE,
    )


def a_balance_estimate_is_a_whole_percent_and_not_a_ratio() -> BalanceFact:
    """The forecast reports whole percents and the term divides by a hundred once.

    A ``Ratio`` accepted here would be 0,84 where 84 belongs, and the payload a card
    renders would then disagree with the value the score used by two orders of
    magnitude — while both stayed inside their ranges.
    """

    return BalanceFact(
        estimate=A_RATE,  # want-error: arg-type
        margin=6,
        certainty=Certainty.HIGH,
        imputed_seats=0,
    )


def a_certainty_is_the_forecasts_grade_and_not_its_margin() -> BalanceFact:
    """*Suppression is presentation*, and the grade is what carries it.

    The margin is the quantity and the grade is the decision read off it. A payload
    that took an ``int`` here would let a caller invent a fourth grade, and the client
    reading it would have no branch for it.
    """

    return BalanceFact(
        estimate=84,
        margin=6,
        certainty=6,  # want-error: arg-type
        imputed_seats=0,
    )


class ASecondKindOfSkillOverlapFact(SkillOverlapFact):  # want-error: misc
    """The payload union is closed, so a tenth term's payload is a member here."""


class ASecondKindOfBalanceFact(BalanceFact):  # want-error: misc
    """And the same for the forecast's."""


def a_balance_payload_is_immutable(fact: BalanceFact) -> None:
    fact.estimate = 100  # want-error: misc


# --- And the legitimate Match Fit uses beside them --------------------------------


def a_skill_overlap_term_reads_the_target_the_analysis_gave_it() -> Term:
    """The legitimate shape, at both resolutions.

    The band's half width travels with the blunt answer and is absent for the exact
    one, which is how a client tells *"this seat is aimed at 3,00"* from *"this match
    is aimed at 2,50–3,50"* — and it is why the field is the quantity rather than a
    label naming which branch ran.
    """

    return evidence_term(
        TermCode.SKILL_OVERLAP,
        24,
        Observed(
            value=A_RATE,
            fact=SkillOverlapFact(
                level=A_LEVEL, target=level(310), band_half_width=ratio(50, 100)
            ),
        ),
    )


def a_predicted_balance_term_reads_the_estimate_whatever_the_grade() -> Term:
    """A forecast too uncertain to print is still the best estimate available.

    The grade travels so a card can decline to show the number; the term scores on the
    estimate either way, and nothing in the type lets one be read without the other.
    """

    return evidence_term(
        TermCode.PREDICTED_BALANCE,
        14,
        Observed(
            value=A_RATE,
            fact=BalanceFact(
                estimate=78, margin=30, certainty=Certainty.LOW, imputed_seats=2
            ),
        ),
    )


def an_exact_seat_target_carries_no_band_width() -> SkillOverlapFact:
    return SkillOverlapFact(level=A_LEVEL, target=level(300), band_half_width=None)





def a_scored_term_carries_its_own_payload() -> ScoredTerm:
    return constraint_term(
        TermCode.PRICE,
        6,
        A_RATE,
        PriceFact(payable=payable_from(A_SEAT, NoCard()), ceiling=grosze(2500)),
    )


def an_evidence_term_is_excluded_by_handing_over_nothing() -> Term:
    """The one call that produces an exclusion, and the only shape it has."""

    return evidence_term(TermCode.FAMILIARITY, 3, None)


def an_evidence_term_scores_when_something_was_observed() -> Term:
    return evidence_term(
        TermCode.GROUP_RELIABILITY,
        11,
        Observed(
            value=A_RATE,
            fact=ReliabilityFact(least_reliable=A_RATE, observed=3, seated=3),
        ),
    )


def a_time_term_reads_a_clock_face_against_a_declaration() -> ScoredTerm:
    """The legitimate shape: both halves local, both silences spelled ``None``."""

    return constraint_term(
        TermCode.TIME_FIT,
        12,
        A_RATE,
        TimeFact(
            weekday=Weekday(local_iso_weekday(NOON, WARSAW)),
            minute=local_minute_of_day(NOON, WARSAW),
            days=frozenset({Weekday.TUESDAY}),
            hours=(HourWindow(start=minute_of_day(1080), end=minute_of_day(1320)),),
        ),
    )


def a_viability_term_reads_four_facts_and_reports_them() -> Term:
    """The legitimate shape: evidence with an observation that is always there.

    Beside it, the ladder walked in the vocabulary's order — which is the only place
    that order lives, and the reason a monotonicity property can be asserted against
    it rather than against a version's mapping.
    """

    rungs: tuple[CourtHold, ...] = HOLD_LADDER
    return evidence_term(
        TermCode.MATCH_VIABILITY,
        12,
        Observed(
            value=A_RATE,
            fact=ViabilityFact(
                paid_seats=3,
                sold_seats=4,
                hold=rungs[-1],
                minutes_to_cutoff=elapsed_minutes(NOON, A_CUTOFF),
                crowding=percent(50),
            ),
        ),
    )


def a_seat_may_carry_a_reliability_record() -> SeatSnapshot:
    """Ships dark: present in the type, absent in every snapshot today."""

    return SeatSnapshot(
        state=SeatState.PAID,
        occupant=PlayerSkill(
            player=A_REF, level=A_LEVEL, uncertainty=A_SIGMA, confidence=30
        ),
        score=PlayerScore(reliability=A_RATE),
    )


def a_player_may_have_declared_everything_or_nothing() -> tuple[PlayerProfile, ...]:
    return (
        PlayerProfile(),
        PlayerProfile(
            days=frozenset({Weekday.TUESDAY, Weekday.THURSDAY}),
            hours=(HourWindow(start=minute_of_day(1080), end=minute_of_day(1260)),),
            maximum_per_seat=grosze(2500),
            travel_radius=minutes(20),
            match_type=MatchTypePreference.SOCIAL,
            appetite=2,
            commitment_horizon=minutes(10_080),
        ),
    )


def both_terms_of_a_score_are_read_through_the_same_union(
    score: MatchFitScore,
) -> tuple[int, int]:
    """The audit trail: every weight in the table, whichever state its term is in."""

    ran = sum(term.weight for term in score.terms if isinstance(term, ScoredTerm))
    return ran, sum(term.weight for term in score.terms)


# ---------------------------------------------------------------------------
# The ladder's input contract. `MatchRecord` is the closed set of facts one pure
# function reads, so what it refuses is as load-bearing as what it accepts: a
# subclass carrying a second idea of what a match is would resolve through the
# same ladder and answer about facts the ladder cannot see.
# ---------------------------------------------------------------------------

A_START = instant(datetime(2026, 8, 22, 18, 30, tzinfo=timezone.utc))


def a_match_record_is_the_whole_input(record: MatchRecord) -> Situation:
    """The legitimate call, pinned clean: three arguments and one name back."""

    return situation(record, Viewer(offer=OfferKind.OPEN), A_START)


def a_record_may_be_resolved_with_no_viewer_at_all(record: MatchRecord) -> Situation:
    """The absolute form is the same function with the parameter absent."""

    return situation(record, None, A_START)


class ASecondIdeaOfAMatch(MatchRecord):  # want-error: misc
    """`MatchRecord` is `@final`, and the ladder is the only reader of it."""


class ASecondIdeaOfASeat(Seat):  # want-error: misc
    """Taken and paid are the two facts; a third would be counted by nobody."""


class ASecondIdeaOfAHold(Hold):  # want-error: misc
    """The composed answer, and never a base class for a club's own."""


def a_hold_policy_is_not_a_bag_of_integers() -> HoldPolicy:
    """Minutes are branded, so a bare `24` cannot be a cancellation window."""

    return HoldPolicy(window=24)  # want-error: arg-type


def a_cap_of_no_minutes_is_still_minutes() -> HoldPolicy:
    return HoldPolicy(max_hold_age=0)  # want-error: arg-type


def a_seat_cannot_be_repainted_after_it_is_read(seat: Seat) -> None:
    """Frozen: a seat that changed under the ladder is a count that changed."""

    seat.paid = True  # want-error: misc


def the_clock_the_ladder_reads_is_an_instant(record: MatchRecord) -> Situation:
    """A naive `datetime` is the bug `Instant` exists to make unwritable."""

    naive = datetime(2026, 8, 22, 18, 30)
    return situation(record, None, naive)  # want-error: arg-type


def a_wake_may_be_absent_and_the_caller_has_to_say_so(
    record: MatchRecord,
) -> Instant:
    """`next_wake_at` returns `Instant | None`; a terminal match has no next."""

    return shifted(next_wake_at(record, A_START), minutes(1))  # want-error: arg-type


def a_wake_that_is_checked_composes(record: MatchRecord) -> Instant | None:
    """The same call with the absence handled, pinned clean."""

    wake = next_wake_at(record, A_START)
    return None if wake is None else shifted(wake, minutes(1))


def a_named_wake_may_be_absent_too(record: MatchRecord) -> WakeReason:
    """`next_wake` returns `Boundary | None`, and the reason is on the boundary."""

    return next_wake(record, A_START).reason  # want-error: union-attr


def a_named_wake_that_is_checked_composes(record: MatchRecord) -> WakeReason | None:
    """The same call with the absence handled, pinned clean."""

    wake = next_wake(record, A_START)
    return None if wake is None else wake.reason


class ABoundaryWithAnOpinion(Boundary):  # want-error: misc
    """`Boundary` is `@final`: a subclass carrying its own tie-break would make
    the same instant schedule under two names, which is half an idempotency key
    decided by which class the caller happened to build."""


def a_boundary_is_frozen(record: MatchRecord) -> None:
    """Rewriting the reason on a boundary in flight is the same defect."""

    wake = Boundary(WakeReason.PLAY, A_START)
    wake.reason = WakeReason.COMMITMENT  # want-error: misc


def a_wake_reason_is_not_a_string(record: MatchRecord) -> Boundary:
    """The label crosses as a member, so a typo is a build error and not a wake
    scheduled under a name nothing will ever match."""

    return Boundary("holdlapse", A_START)  # want-error: arg-type


def what_the_ladder_says_is_not_what_the_record_says(record: MatchRecord) -> bool:
    """Two questions one letter apart, and confusing them is the ladder's bug.

    `court_hold` composes *what should be kept aside*; `keeping_a_court` reads
    *what is*. The whole of `hold_move` is the difference between them, so a
    caller that hands one to the other has written a ladder that always agrees
    with itself and never grants or reclaims anything.
    """

    return keeping_a_court(court_hold(record, A_START))  # want-error: arg-type


def the_clock_the_ladder_acts_on_is_an_instant(record: MatchRecord) -> HoldMove:
    """A naive `datetime` is the bug `Instant` exists to make unwritable."""

    naive = datetime(2026, 8, 22, 18, 30)
    return hold_move(record, naive)  # want-error: arg-type


def a_hold_move_that_is_matched_composes(record: MatchRecord) -> bool:
    """The same two questions asked correctly, pinned clean."""

    return hold_move(record, A_START) is HoldMove.GRANT and keeping_a_court(record)


def a_reclaimed_holds_age_may_be_absent(record: MatchRecord) -> Minutes:
    """`Hold.age` is `Minutes | None`: only a hold just taken back carries one.

    Reading it unchecked is how a card comes to print *held for None hours*.
    """

    return court_hold(record, A_START).age  # want-error: return-value


def a_hold_that_is_checked_composes(record: MatchRecord) -> Minutes | None:
    age = court_hold(record, A_START).age
    return None if age is None else minutes(age + 1)


# --- departures: four names, one ranking, and two money forms --------------


def an_outcome_is_not_its_string(record: MatchRecord) -> int:
    """The ranking is over the enumeration, so a typo is a build error.

    `"forfieted"` ranked as zero by an index signature is the shape of bug the
    whole enum discipline exists to make unreachable.
    """

    return outcome_rank("forfeited")  # want-error: arg-type


def a_quote_is_compared_against_an_outcome(live: Outcome) -> bool:
    """Never against a bare label off the wire."""

    return outcome_worse_than(live, "refundedInFull")  # want-error: arg-type


def the_clock_a_quote_is_taken_on_is_an_instant(record: MatchRecord) -> Outcome:
    """A naive `datetime` is the bug `Instant` exists to make unwritable."""

    return live_outcome(record, datetime(2026, 8, 22, 18, 30))  # want-error: arg-type


def a_leavers_money_is_not_read_without_asking_which_form(
    money: LeaverMoney,
) -> Grosze:
    """**The whole point of two payloads.** ADR-0072 refuses one payload with a
    sometimes-absent amount, and this is what makes the refusal bite: reading
    the amount off the union without narrowing does not compile, so a card
    cannot print *nothing was taken* as an empty number by accident.
    """

    return money.amount  # want-error: union-attr


def a_narrowed_leavers_money_composes(money: LeaverMoney) -> Grosze | None:
    """The same read, asked correctly. Pinned clean, so a narrowing that stops
    narrowing fails here as loudly as one that never did."""

    return None if isinstance(money, NothingTaken) else money.amount


def the_two_money_forms_are_closed(money: LeaverMoney) -> str:
    """`match` over the union with both arms handled, and `exhaustive` proving
    it — a third form added later fails at every reader rather than falling
    through to a default nobody wrote."""

    match money:
        case NothingTaken():
            return "nothing"
        case Recoverable():
            return "some"
        case _:
            exhaustive(money)


class ARicherReversal(NothingTaken):  # want-error: misc
    """`@final`: a subclass with a field is an optional amount smuggled back."""


class ARicherRecoverable(Recoverable):  # want-error: misc
    """The same, from the other side."""


def what_she_paid_cannot_be_rewritten() -> Recoverable:
    """Frozen: a settlement that edited the amount would be history rewritten
    rather than recorded, which is the argument the whole record turns on."""

    money = Recoverable(amount=grosze(3800))
    money.amount = grosze(1900)  # want-error: misc
    return money


def the_two_questions_both_answer_an_outcome(record: MatchRecord) -> bool:
    """Pinned clean. `live_outcome` and `refill_outcome` take the same arguments
    and disagree past the checkpoint, so the compiler cannot tell them apart —
    which is exactly why `tests/unit/test_kernel_departures.py` asserts the
    disagreement behaviourally, and why it is written down here that it must.
    """

    return outcome_worse_than(
        live_outcome(record, A_START), refill_outcome(record, A_START)
    )
