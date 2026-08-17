"""Snapshot builders for the matchmaking suites.

Not a test module. Hand-built snapshots are the *only* input the engines take —
no database, no fixtures, no HTTP — so these three functions are the whole test
harness, and they are shared so that four suites cannot develop four ideas of what
a well-formed match looks like.

Levels and Uncertainties are written in **hundredths**, as the vocabulary carries
them: ``skill("ada", 320, 15)`` is Ada at 3,20 ± 0,15.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.engines.matchmaking import (
    MatchSnapshot,
    Occupant,
    PlayerRef,
    PlayerSkill,
    SeatSnapshot,
    SeatState,
    UnratedPlayer,
    level,
    uncertainty,
)
from app.kernel import Instant, Sport

#: A fixed instant, rounded to the minute. Every engine call takes one, and no
#: forecast reads it — which is exactly why it is a constant here rather than
#: something a test computes: a value that varied would suggest it mattered.
NOW = Instant(datetime(2026, 8, 17, 18, 0, tzinfo=timezone.utc))


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
) -> MatchSnapshot:
    """A two-seat match. ``None`` is an empty seat, as in ``doubles``.

    ``viewer`` defaults to the player on the first seat, which is the ordinary
    case: a player looking at a match they are in.
    """

    return MatchSnapshot(
        sport=sport,
        seats=(
            on_seat(first, state=states[0]),
            on_seat(second, state=states[1]),
        ),
        current_player=viewer if viewer is not None else first,
    )


def doubles(
    *occupants: Occupant | None,
    sport: Sport = Sport.PADEL,
    viewer: Occupant | None = None,
    states: tuple[SeatState | None, ...] = (None, None, None, None),
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
    return MatchSnapshot(
        sport=sport,
        seats=tuple(
            on_seat(player, state=state)
            for player, state in zip(occupants, states, strict=True)
        ),
        current_player=viewer if viewer is not None else fallback,
    )
