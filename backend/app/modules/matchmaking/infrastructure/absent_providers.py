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
**One class is left, and it is a gate, which is not a coincidence.** Every term
this file ever answered for now has a provider; what survives is the one fact a
zero can honestly state, and the rule above is why it is the one that survived.

**``NoResultUpdateRuleExists`` was here and is gone** (#304). It said *nobody's
Level has ever moved on a result, because nothing moves it*, and that was true
until ``docs/adr/0139`` wrote the rule. It is the second of these to retire by its
own stated fact becoming false, which is the intended end of a null object named
for one — and the swap was one row in the register, exactly as ADR-0095 promised.

**``NoPlayerScoresExist`` was here and is gone** (#305). It said *nobody has a
Player Score, because nobody has ever been due to play*, and that stopped being
true the moment ``games`` could record a plan that produced a game or did not
(``docs/adr/0140``). It is the third of these to retire by its own stated fact
becoming false, and the one whose retirement moved a number: reliability was the
last term absent platform-wide, so ``build_absent_terms`` now answers with an
empty set and the evidence gate counts eight live terms rather than seven.

**``NoMatchHistoryExists`` was here and is gone rather than narrowed** (#253). Its
docstring's second half — *the count is a measured ``0`` for everybody asked,
because no challenge has ever been sent by anyone* — stopped being true the day
``challenges`` shipped a send, and a null object whose stated fact has become
false is worse than no null object at all.

**Two arrived the other way, when ``challenges`` was removed** (#578): a fill
names a court that no longer exists, and a mutual yes opens nothing, because
the only thing that made a game of one is gone. Both state a fact that is true
of this platform from that day, and both go with the searches and the deck that
still call them (#579).
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.domain.ports import HalfBuiltCourt


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


@final
class NoHalfBuiltCourtsExist:
    """No court is half built, because nothing builds a court any more (#578).

    A fill used to name a challenge still being arranged; the challenges
    context is gone, so every id a fill names is a court that does not exist,
    and the port's own answer for that is ``None``.
    """

    async def half_built_court(
        self, *, challenge_id: UUID, member_id: UUID
    ) -> HalfBuiltCourt | None:
        return None


@final
class NoMutualOpensAGame:
    """Two yeses that meet open no game, because nothing makes a game from one
    (#578).

    ``None`` is the port's ordinary answer — *there is no game to name* — so
    the yes still stands and is still recorded; it simply arranges nothing,
    since a game is now made only by a booking.
    """

    async def open_from_mutual_interest(
        self, *, sport: Sport, player_id: UUID, other_player_id: UUID
    ) -> UUID | None:
        return None
