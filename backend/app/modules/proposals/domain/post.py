"""Who a **Post** is for: *Who* and *Level* (#546; the mechanics §9.1 steps 3–4;
the screens A5.1).

A member posting a game picks who may be on it beside them, and both choices
are stored on the post (``ProposalMade``) so everybody it is ever dealt to —
at posting, and every fit after (§9.2) — is held to the same two rules.

**Who is the game's, the poster included.** *Men* and *Women* are games of one
gender; *Mixed pairs* is a doubles of two men and two women, each side one of
each. Only somebody **with a gender set** is counted for any of the three, and
somebody whose own gender preference excludes the game is never on it — a
woman who plays with women only is never on a mixed game. *Anyone* asks
neither: the pair rule (``PlayerFit``) is then the whole of who may stand
beside whom, as it is on a pick.

**Level is the others', never the poster's.** It starts as **the engine's own
window for the kind** around the poster's Level — the matcher's level gate,
``level_tolerance`` (``docs/adr/0103``), narrowed while the poster is new
(``docs/adr/0113``) — **rounded inward to the hundredth**, so a bound a client
prints and sends back is never outside the window. It may be **narrowed, never
widened** (Q78): the window is the engine's promise that a game is even enough
to be worth playing, and a post is not a way around it.

**Gender is read here and said nowhere** (``docs/adr/0096`` §6): these rules
answer whether somebody may be on a post, never which of the two a refusal
was.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.kernel import SPORT_SPECS, Sport, invariant
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.proposals.domain.errors import (
    LevelRangeInverted,
    LevelRangeTooWide,
    MixedPairsOnlyInDoubles,
)

#: The two answers counted on a game of men, of women, or of mixed pairs.
_SET: Final = frozenset({Gender.MAN, Gender.WOMAN})

#: How far apart two floats a client sent back may be and still be one bound:
#: a hundredth printed and parsed again is not always the same binary number.
_A_ROUNDING: Final = 1e-9


class Who(StrEnum):
    """Who a post is for (the mechanics §9.1 step 3)."""

    ANYONE = "ANYONE"
    MEN = "MEN"
    WOMEN = "WOMEN"
    #: In doubles, each side one man and one woman.
    MIXED_PAIRS = "MIXED_PAIRS"

    def admits(
        self, gender: Gender | None, preference: GenderPreference | None
    ) -> bool:
        """Whether somebody with this gender and preference may be on a game
        for ``self`` — **fails closed** on a preference that cannot be read,
        as the mutual gate does, except on *Anyone*, which asks nothing."""

        if self is Who.ANYONE:
            return True
        if gender not in _SET or preference is None:
            return False
        if self is Who.MEN:
            return (
                gender is Gender.MAN and preference is not GenderPreference.WOMEN_ONLY
            )
        if self is Who.WOMEN:
            return (
                gender is Gender.WOMAN and preference is not GenderPreference.MEN_ONLY
            )
        # Mixed pairs: both genders are on it, so only *anybody* will do.
        return preference is GenderPreference.ANY

    def refuse_unless_offered_in(self, sport: Sport) -> None:
        """*Mixed pairs* only for padel and badminton: a side of one is not a
        pair."""

        if self is Who.MIXED_PAIRS and SPORT_SPECS[sport].players != 4:
            raise MixedPairsOnlyInDoubles(sport=sport.value)


def stand_together(
    who: Who | None,
    genders: Mapping[UUID, Gender | None],
    people: Iterable[UUID],
    *,
    seats: int,
) -> bool:
    """Whether these people may all be on one game for ``who`` — on *Mixed
    pairs*, never more than half its seats of either gender, and nobody whose
    gender cannot be read. Every other game, and a pick (``None``), stands
    whoever is on it: who may be there at all is ``Who.admits``' question."""

    if who is not Who.MIXED_PAIRS:
        return True
    counted = {Gender.MAN: 0, Gender.WOMAN: 0}
    for person in people:
        gender = genders.get(person)
        if gender not in _SET:
            return False
        assert gender is not None
        counted[gender] += 1
    return all(count <= seats // 2 for count in counted.values())


@final
@dataclass(frozen=True, slots=True)
class LevelRange:
    """A range of Levels, both bounds included."""

    low: float
    high: float

    def __post_init__(self) -> None:
        invariant(
            self.low <= self.high, f"a level range from {self.low} to {self.high}"
        )

    @classmethod
    def around(cls, level: float, *, tolerance: float) -> "LevelRange":
        """The engine's window around ``level``, rounded **inward** to the
        hundredth."""

        invariant(tolerance > 0, f"a level window of {tolerance}")
        return cls(
            low=math.ceil((level - tolerance) * 100 - _A_ROUNDING) / 100,
            high=math.floor((level + tolerance) * 100 + _A_ROUNDING) / 100,
        )

    def admits(self, level: float) -> bool:
        return self.low - _A_ROUNDING <= level <= self.high + _A_ROUNDING

    def narrowed_to(self, *, low: float | None, high: float | None) -> "LevelRange":
        """This window narrowed to the bounds a poster chose — either left
        where it is when not given. **Never widened**: a bound outside it is
        ``level_range_too_wide``, naming the window."""

        wanted_low = self.low if low is None else low
        wanted_high = self.high if high is None else high
        if not (
            self.low - _A_ROUNDING <= wanted_low
            and wanted_high <= self.high + _A_ROUNDING
        ):
            raise LevelRangeTooWide(low=self.low, high=self.high)
        if wanted_low > wanted_high:
            raise LevelRangeInverted()
        return LevelRange(low=wanted_low, high=wanted_high)


@final
@dataclass(frozen=True, slots=True)
class PostedFor:
    """Who a post is for: its *Who*, and the range the others' Levels are in."""

    who: Who
    levels: LevelRange

    def admits(
        self,
        *,
        level: float | None,
        gender: Gender | None,
        preference: GenderPreference | None,
    ) -> bool:
        """Whether somebody else may be dealt the post, or join it: their Level
        in the range — an unrated player is in none — and its *Who*."""

        return (
            level is not None
            and self.levels.admits(level)
            and self.who.admits(gender, preference)
        )

    def includes_the_poster(
        self, *, gender: Gender | None, preference: GenderPreference | None
    ) -> bool:
        """Whether the poster stands on their own game: its *Who* is everybody's
        on it, theirs included; the range is the others'."""

        return self.who.admits(gender, preference)
