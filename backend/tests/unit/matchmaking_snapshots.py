"""Snapshot builders for the matchmaking suites.

Not a test module. Hand-built snapshots are the *only* input the engines take —
no database, no fixtures, no HTTP — so these functions are the whole test
harness, and they are shared so that six suites cannot develop six ideas of what
a well-formed match looks like.

Levels and Uncertainties are written in **hundredths**, as the vocabulary carries
them: ``skill("ada", 320, 15)`` is Ada at 3,20 ± 0,15. Money is written in
**grosze** and durations in **minutes**, as the kernel carries them.

**Where the fabricated facts live.** A ``MatchSnapshot`` requires its price, its
club and its ladder state with no defaults, deliberately: a default of zero grosze
is a free match and a default of zero minutes is a court next door, and an
assembler that forgot one would be silently right about neither. So the plausible
figures are *here*, in the harness, which is where invented test data belongs —
and ``money`` builds them through the money kernel rather than writing an integer
down, so the seat share a test asserts against is the one the rounding order
actually produces.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from app.engines.forecast import (
    NobodySeated,
    PairingAnalysis,
    SeatUnderDetermined,
    SidesNotFormed,
)
from app.engines.matchmaking import (
    ClubSnapshot,
    HourWindow,
    LadderQualification,
    MatchSnapshot,
    MatchTypePreference,
    Occupant,
    PlayerProfile,
    PlayerRef,
    PlayerScore,
    PlayerSkill,
    PlayHistory,
    SeatSnapshot,
    SeatState,
    UnratedPlayer,
    Weekday,
    level,
    uncertainty,
)
from app.kernel import (
    SPORT_SPECS,
    ClubCard,
    Err,
    Instant,
    NoCard,
    Ok,
    Payable,
    SeatShare,
    Sport,
    Zone,
    court_price,
    day_offset,
    divide_among_players,
    grosze,
    minute_of_day,
    minutes,
    invariant,
    payable_from,
    percent,
    slot_start,
    zloty,
)

#: A fixed instant, rounded to the minute. Every engine call takes one, and no
#: forecast reads it — which is exactly why it is a constant here rather than
#: something a test computes: a value that varied would suggest it mattered. It is
#: **Monday 17 August 2026, 20:00 in Warsaw**, which is where the local weekday
#: every time fit persona is written against comes from.
NOW = Instant(datetime(2026, 8, 17, 18, 0, tzinfo=timezone.utc))

#: The zone every club in the harness is in. A real one and not UTC, so a test that
#: quietly read a weekday off an instant instead of off the club's clock face would
#: be two hours out and would say so.
WARSAW = Zone("Europe/Warsaw")


def starting(
    *, day: int = 1, hour: int = 18, minute: int = 30, zone: Zone = WARSAW
) -> Instant:
    """A start instant written on the club's **clock face**, days from ``NOW``.

    Through ``slot_start`` rather than by building a ``datetime`` here, because
    that is the one conversion the kernel allows and a harness with its own would
    be exactly the second answer to a timezone question ADR-0024 forbids. It also
    means a persona asking for a local time that does not exist — the spring-forward
    gap — fails loudly here rather than silently scoring an hour it invented.
    """

    slot = slot_start(
        anchor=NOW,
        day=day_offset(day),
        minute=minute_of_day(hour * 60 + minute),
        zone=zone,
    )
    return invariant(
        slot.value if isinstance(slot, Ok) else None,
        f"no local {hour:02d}:{minute:02d} {day} days after the anchor in {zone}",
    )


#: When every match in the harness starts: **Tuesday 18 August 2026, 18:30 in
#: Warsaw**. A weekday and an evening, so a declaration can be written that this
#: satisfies and one it breaches, and neither is the same as declaring nothing.
START = starting()

#: A 96 zł court at a 10% off-peak rate — **ADR-0023's own worked example**, which
#: rounds to 86 zł and divides into four seats of exactly 21,50. Built through
#: ``court_price`` rather than written down as 8600, so the compounding and the
#: single rounding at the court are the kernel's and not this file's.
COURT = court_price(zloty(96), percent(90))


def money(seats: int, card: ClubCard = NoCard()) -> tuple[SeatShare, Payable]:
    """One seat's share of ``COURT``, and what a player with ``card`` owes for it.

    Both halves, from the one chain the kernel allows: divide the rounded court
    price among the *sold* seats, then take the capped card offset off. A test that
    wants a cheaper seat passes a card, because that is the only way a payable ever
    differs from its share — which is exactly what the price term is asserted to
    read.
    """

    share = divide_among_players(COURT, seats)
    return share, payable_from(share, card)


def skill(name: str, level_hundredths: int, sigma_hundredths: int) -> PlayerSkill:
    """One player's rating. ``confidence`` is carried and never computed with.

    It is derived here from σ the way the rating context derives it — 100 × (1 −
    σ/1,20), capped at 99 — so a snapshot never carries a Confidence that
    contradicts its own Uncertainty. Written out rather than imported: the
    pairing engine must not restate that transform, and a test helper importing
    it would be the first step towards one that does.
    """

    return PlayerSkill(
        player=PlayerRef(name),
        level=level(level_hundredths),
        uncertainty=uncertainty(sigma_hundredths),
        confidence=max(0, min(99, round(100 * (1 - sigma_hundredths / 120)))),
    )


def unrated(name: str) -> UnratedPlayer:
    """Somebody on a seat the platform has never rated at this sport."""

    return UnratedPlayer(player=PlayerRef(name))


def on_seat(
    occupant: Occupant | None, *, state: SeatState | None = None
) -> SeatSnapshot:
    """One seat. ``None`` is an empty seat; anybody else has **paid** by default.

    Paid rather than held, because paid is the ordinary state and a default that
    was not would make every test that does not care about commitment quietly
    about it. The held case is passed explicitly by the tests that are.
    """

    if occupant is None:
        return SeatSnapshot(state=SeatState.EMPTY)
    return SeatSnapshot(state=state or SeatState.PAID, occupant=occupant)


def singles(
    first: Occupant,
    second: Occupant | None,
    *,
    sport: Sport = Sport.TENNIS,
    viewer: Occupant | None = None,
    states: tuple[SeatState | None, ...] = (None, None),
    counted: bool = True,
    card: ClubCard = NoCard(),
    travel_minutes: int = 12,
    ladder: LadderQualification = LadderQualification.NOT_IN_A_LADDER,
    history: PlayHistory | None = None,
    start: Instant = START,
    zone: Zone = WARSAW,
) -> MatchSnapshot:
    """A two-seat match. ``None`` is an empty seat, as in ``doubles``.

    ``viewer`` defaults to the player on the first seat, which is the ordinary
    case: a player looking at a match they are in. Everything from ``counted``
    onwards is a Match Fit fact with a plausible default, so a suite that is about
    the balance forecast never mentions money — and the two suites that *are* about
    money pass a card or a distance explicitly.
    """

    share, payable = money(2, card)
    return MatchSnapshot(
        sport=sport,
        seats=(
            on_seat(first, state=states[0]),
            on_seat(second, state=states[1]),
        ),
        current_player=viewer if viewer is not None else first,
        start=start,
        counted=counted,
        seat_share=share,
        payable=payable,
        club=ClubSnapshot(travel_minutes=minutes(travel_minutes), zone=zone),
        ladder=ladder,
        history=history,
    )


def doubles(
    *occupants: Occupant | None,
    sport: Sport = Sport.PADEL,
    viewer: Occupant | None = None,
    states: tuple[SeatState | None, ...] = (None, None, None, None),
    counted: bool = True,
    card: ClubCard = NoCard(),
    travel_minutes: int = 12,
    ladder: LadderQualification = LadderQualification.NOT_IN_A_LADDER,
    history: PlayHistory | None = None,
    start: Instant = START,
    zone: Zone = WARSAW,
) -> MatchSnapshot:
    """A four-seat match. ``None`` is an empty seat.

    ``viewer`` defaults to the player on the first occupied seat, the same
    ordinary case ``singles`` defaults to: a player looking at a match they are
    in. Pass one to look at the same four people through somebody else's eyes,
    which is what moves the pairing's orientation and nothing else.

    **The default viewer is somebody already in the match**, which matters more
    now than it did: a viewer who is *not* seated joins the roster, so a helper
    that defaulted to a stranger would silently fill one of the empty seats every
    test thought it had left open.
    """

    filled = [player for player in occupants if player is not None]
    fallback = filled[0] if filled else skill("nobody", 300, 84)
    share, payable = money(4, card)
    return MatchSnapshot(
        sport=sport,
        seats=tuple(
            on_seat(player, state=state)
            for player, state in zip(occupants, states, strict=True)
        ),
        current_player=viewer if viewer is not None else fallback,
        start=start,
        counted=counted,
        seat_share=share,
        payable=payable,
        club=ClubSnapshot(travel_minutes=minutes(travel_minutes), zone=zone),
        ladder=ladder,
        history=history,
    )


def bare(
    sport: Sport, seats: tuple[SeatSnapshot, ...], current_player: Occupant
) -> MatchSnapshot:
    """A snapshot assembled seat by seat, for the tests that are about its *shape*.

    ``singles`` and ``doubles`` build a well-formed match of a known arity; the two
    tests that check what a snapshot *refuses* — a padel match carrying two seats,
    the sold count being read from the registry — need to hand over a seat tuple the
    helpers would never produce. They still need a price and a club, so the money
    comes from the sport's own sold format and not from the length of the tuple under
    test: a wrong seat count must fail the invariant it is aimed at rather than the
    money kernel's refusal to divide a court three ways.
    """

    spec = invariant(SPORT_SPECS.get(sport), f"no spec for sport: {sport!r}")
    share, payable = money(spec.players)
    return MatchSnapshot(
        sport=sport,
        seats=seats,
        current_player=current_player,
        start=START,
        counted=True,
        seat_share=share,
        payable=payable,
        club=ClubSnapshot(travel_minutes=minutes(12), zone=WARSAW),
        ladder=LadderQualification.NOT_IN_A_LADDER,
    )


def with_records(snapshot: MatchSnapshot, *reliabilities: int | None) -> MatchSnapshot:
    """The same match with a reliability record on each seat, in whole percent.

    ``with_records(match, 95, None, 80, 100)`` gives the first seat a player who
    turns up 95% of the time, the second none at all, and so on. One entry per seat
    including the empty ones, which must be ``None`` — the vocabulary refuses a
    record on a seat with nobody on it, and a helper that skipped them silently
    would let a test think it had set a record it had not.

    This is how the two **dark** terms are exercised. Nothing the platform can
    assemble today carries one, which is the point: the term is excluded on every
    real snapshot, and the branch that scores it is reachable only from here.
    """

    return replace(
        snapshot,
        seats=tuple(
            replace(
                seat,
                score=None if rate is None else PlayerScore(reliability=percent(rate)),
            )
            for seat, rate in zip(snapshot.seats, reliabilities, strict=True)
        ),
    )


def profile(
    *,
    ceiling: int | None = None,
    radius: int | None = None,
    match_type: MatchTypePreference | None = None,
    days: frozenset[Weekday] | None = None,
    hours: tuple[HourWindow, ...] | None = None,
    appetite: int | None = None,
    commitment_horizon: int | None = None,
) -> PlayerProfile:
    """What the player declared. ``profile()`` is somebody who declared nothing.

    ``ceiling`` is in **grosze** and ``radius`` in **minutes**, the units the
    vocabulary carries them in, so a test asserting against a payable of 2150 is
    comparing two figures of the same kind.
    """

    return PlayerProfile(
        days=days,
        hours=hours,
        maximum_per_seat=None if ceiling is None else grosze(ceiling),
        travel_radius=None if radius is None else minutes(radius),
        match_type=match_type,
        appetite=appetite,
        commitment_horizon=(
            None if commitment_horizon is None else minutes(commitment_horizon)
        ),
    )


def window(from_hour: int, to_hour: int) -> HourWindow:
    """One declared stretch of a day, written in whole local hours."""

    return HourWindow(
        start=minute_of_day(from_hour * 60), end=minute_of_day(to_hour * 60)
    )


def analysis(*, version: str = "pairing-v1") -> PairingAnalysis:
    """A **hand-built** pairing analysis, declining on every field.

    Match Fit takes the analysis as an input value and never runs the pairing
    engine, so its suites build one by hand — there is no integration seam between
    the two engines and none is invented here (``docs/adr/0026``). An invariant test
    asserts that no Match Fit suite imports the pairing engine, because a helper
    that quietly did would turn every Fit assertion into an assertion about both.

    Declining everywhere is the honest shape for this version: the two terms that
    read a forecast's numbers are #86's, so a forecast built here would be an input
    nothing reads dressed up as one that does. What *is* read is the version, which
    every score carries because a Match Fit score has two producers.
    """

    sport = Sport.PADEL.value
    return PairingAnalysis(
        forecast=Err(SidesNotFormed(sport=sport, seated=0, sold=4)),
        splits=(),
        seat_target=Err(SeatUnderDetermined(sport=sport, open_seats=4, sold=4)),
        target_band=Err(NobodySeated(sport=sport, sold=4)),
        engine_version=version,
    )
