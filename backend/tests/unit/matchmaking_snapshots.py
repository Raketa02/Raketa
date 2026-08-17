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
    PlayerRef,
    PlayerSkill,
    SeatSnapshot,
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


def singles(
    first: PlayerSkill,
    second: PlayerSkill | None,
    *,
    sport: Sport = Sport.TENNIS,
    viewer: PlayerSkill | None = None,
) -> MatchSnapshot:
    """A two-seat match. ``None`` is an empty seat, as in ``doubles``.

    ``viewer`` defaults to the player on the first seat, which is the ordinary
    case: a player looking at a match they are in.
    """

    return MatchSnapshot(
        sport=sport,
        seats=(SeatSnapshot(first), SeatSnapshot(second)),
        current_player=viewer if viewer is not None else first,
    )


def doubles(
    *occupants: PlayerSkill | None,
    sport: Sport = Sport.PADEL,
    viewer: PlayerSkill | None = None,
) -> MatchSnapshot:
    """A four-seat match. ``None`` is an empty seat.

    ``viewer`` defaults to the player on the first occupied seat, the same
    ordinary case ``singles`` defaults to: a player looking at a match they are
    in. Pass one to look at the same four people through somebody else's eyes,
    which is what moves the pairing's orientation and nothing else.
    """

    seated = [player for player in occupants if player is not None]
    fallback = seated[0] if seated else skill("nobody", 300, 84)
    return MatchSnapshot(
        sport=sport,
        seats=tuple(SeatSnapshot(player) for player in occupants),
        current_player=viewer if viewer is not None else fallback,
    )
