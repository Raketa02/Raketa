"""The providers that do not exist, each answering honestly.

**Everything ships wired, and nothing stands in for an absent provider.** Each
class below is a **null object named for the fact it asserts** — ``NoHoldsExist``,
not ``NullAccountHoldQuery`` — because *null* reads as *not wired yet*, and this
is wired (``docs/adr/0095``). They are not stubs returning plausible numbers:
each says something true about this platform today, and each stops being true on
the day its provider lands, at which point it is swapped for a real adapter and
the contract suite carries straight over.

The distinction they encode is ``docs/adr/0098``'s: *a gate may be honestly
empty; a term may never be honestly neutral.* Nobody can be held because nothing
can hold anybody — a real, measured absence, so the gate ships true-over-empty.
Nobody has failed to turn up because nobody has ever been due to — so a
``player_score`` fact is **absent**, never a zero, because that zero would be
invented.

**``NoResultUpdateRuleExists`` was here and is gone** (#304). It said *nobody's
Level has ever moved on a result, because nothing moves it*, and that was true
until ``docs/adr/0139`` wrote the rule. It is the second of these to retire by its
own stated fact becoming false, which is the intended end of a null object named
for one — and the swap was one row in the register, exactly as ADR-0095 promised.

**``NoMatchHistoryExists`` was here and is gone rather than narrowed** (#253). Its
docstring's second half — *the count is a measured ``0`` for everybody asked,
because no challenge has ever been sent by anyone* — stopped being true the day
``challenges`` shipped a send, and a null object whose stated fact has become
false is worse than no null object at all. What signs ``MatchHistoryQuery`` now is
``challenges_match_history.ChallengesButNobodyHasPlayed``, which is half a real
adapter and half a measured absence and is named for exactly that.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.matchmaking.domain.ports import PlayerScoreReading


@final
class NoPlayerScoresExist:
    """Nobody has a Player Score, because nobody has ever been due to play.

    **The absence is measured, and a zero here would be invented.** No record is
    not a bad record: a player without a score is not ``0.5`` and not ``0`` — the
    reliability term returns ``NoEvidence``, is dropped from the sum, and the
    surviving weights renormalise, which is the same principle the rating engine
    already applies to skill.

    Seven terms live and renormalised is not a degraded engine; it is the basis
    every judged reading and the quality floor were computed on.
    """

    async def readings_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, PlayerScoreReading]:
        return {}


@final
class NoHoldsExist:
    """Nothing can hold an account, because the ``cases`` context is unwritten.

    **A real, measured absence and not a placeholder.** The gate is live, points
    both ways and fails closed; it simply never fires, because there is nothing
    in this repository that can open a case. Swapping this for a real adapter is
    the entire integration when ``cases`` lands (``docs/adr/0095``).
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return frozenset()
