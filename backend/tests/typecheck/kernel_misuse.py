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
    NoForecast,
    NoSeatTarget,
    NoTargetBand,
    PairingAnalysis,
    SidesNotFormed,
    Split,
    TargetBand,
)
from app.engines.matchmaking import (
    Level,
    MatchSnapshot,
    PlayerRef,
    PlayerSkill,
    SeatSnapshot,
    Uncertainty,
    level,
    uncertainty,
)
from app.engines.pairing.core import Side, as_float
from app.kernel import (
    SPORT_SPECS,
    CardAllowance,
    CardCoversShare,
    Clock,
    ClubCard,
    CourtPrice,
    DayOffset,
    Err,
    Grosze,
    Instant,
    InvariantViolated,
    MinuteOfDay,
    Minutes,
    NoCard,
    NonexistentLocalTime,
    Ok,
    Payable,
    Ratio,
    Reason,
    Result,
    SeatShare,
    Sport,
    SportSpec,
    Unavailable,
    add_grosze,
    apply_fraction,
    card_offset,
    court_price,
    day_offset,
    divide_among_players,
    elapsed_minutes,
    exhaustive,
    grosze,
    hours,
    instant,
    invariant,
    minute_of_day,
    minutes,
    payable_from,
    percent,
    ratio,
    shifted,
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
    """Two reasons, not one: the seat is under-determined, or there are no sides
    to even up at all. A caller handling only the first leaves the second
    unhandled at the tail."""

    match seat_target:
        case Ok(value):
            return value
        case Err(SidesNotFormed()):
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
