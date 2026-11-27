"""A booked For-fun game's **Social vibe**, as its pairing draws it
(``docs/adr/0207`` §5, §6, #835): how much the whole court shares, and who on
it shares the reader's tags.

**One rule, borrowed and kept nowhere.** The tags that don't count are the
Player profile's, beside its vocabulary (``counted``), and the arithmetic is
the Match Fit engine's (``social_vibe``) — the very function a card, a game's
details, the Friends card and Post a game's fits are worked out with, so a
For-fun game reads the same before and after it is booked. Nothing is stored:
it is worked out from the current tags on every read.

**The table is the court**: everybody on it, the reader among them. A court
with a seat open draws no vibe — it is not yet the court that will play
(``docs/adr/0162`` §3), the ground the forecast is withheld on — so asking for
one there is a wrong branch. Somebody whose tags aren't known carries none:
they share nothing, and they are still one of the others a tag could be
carried by.

**The rows are the reader's tags**, in the vocabulary's order — 💘 too, which
is shown and never counted — each naming everybody on the court who carries
it **in the reader's direction**, as the pairing reads everything: the reader
first, then the rest of their side, then the other side, each side in the
court's own order (the order ``GET /games`` lists its seats in). That is the
order a game's details name a card's carriers in — the reader, then
``sides.yours``, then ``sides.theirs`` — so a row reads alike before and after
the booking. The number says how much the whole court shares; the rows say
who shares the reader's.

Declared here rather than borrowed from Proposals' grid: a card still filling
is Proposals' and a booked court is this context's, and neither imports the
other's domain. What they share is what makes the number one number — the
engine and the profile's rule — and a test reads the two for one four.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.matchfit.v1 import social_vibe
from app.kernel import invariant
from app.modules.games.domain.lineup import LineUp
from app.modules.player_profile.domain.social_tags import (
    SocialTag,
    counted,
    in_vocabulary_order,
)


@final
@dataclass(frozen=True, slots=True)
class VibeRow:
    """One row of a For-fun game's grid: one of the reader's tags, and
    everybody on the court who carries it — the reader first, so never
    nobody."""

    tag: SocialTag
    carried_by: tuple[UUID, ...]

    def __post_init__(self) -> None:
        invariant(bool(self.carried_by), f"a row of {self.tag} carried by nobody")


@final
@dataclass(frozen=True, slots=True)
class CourtVibe:
    """A booked For-fun court's Social vibe, for one reader: the court's own
    number, and the reader's rows."""

    pct: int
    rows: tuple[VibeRow, ...]

    def __post_init__(self) -> None:
        invariant(0 <= self.pct <= 100, f"a Social vibe of {self.pct}%")


def court_vibe_of(
    line_up: LineUp,
    reader_id: UUID,
    tags: Mapping[UUID, Collection[SocialTag]],
) -> CourtVibe | None:
    """The vibe of a whole court and the reader's rows — ``None`` exactly when
    nothing is drawn: nobody on it holds a tag that counts."""

    mine = invariant(
        line_up.side_of(reader_id), "a vibe read for somebody not on the court"
    )
    invariant(
        line_up.is_complete,
        "a vibe read on a court with a seat open: it is not yet the court that "
        "will play (docs/adr/0162)",
    )
    court = [
        seating.player_id
        for seating in line_up.seatings
        if seating.player_id is not None
    ]
    pct = social_vibe([counted(tags.get(player, ())) for player in court])
    if pct is None:
        return None
    seated = (
        reader_id,
        *(p for p in court if p != reader_id and line_up.side_of(p) is mine),
        *(p for p in court if line_up.side_of(p) is mine.other),
    )
    return CourtVibe(
        pct=pct,
        rows=tuple(
            VibeRow(
                tag=tag,
                carried_by=tuple(
                    player for player in seated if tag in tags.get(player, ())
                ),
            )
            for tag in in_vocabulary_order(tags.get(reader_id, ()))
        ),
    )


__all__ = ["CourtVibe", "VibeRow", "court_vibe_of"]
