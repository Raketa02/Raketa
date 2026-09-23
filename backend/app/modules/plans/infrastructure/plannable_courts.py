"""``PlannableCourts``, answered by ``challenges`` and ``games`` together —
*which courts is this player arranging, and which are history?*

**One question, two records, one fold** (``docs/adr/0164`` §3). A court is a
challenge that may or may not have become a game, and the two facts the Plan
needs are split across the two: *who holds an accepted seat* and *is the court
whole* are the challenge's; *has the court become a game, and is that game still
awaiting its entry* is the game's; the anchor is the send until the game exists
and ``planned_at`` after. Neither provider can answer alone and neither may
import the other's aggregate, so the fold runs here, on the Plan's side of both
arrows, over the two providers' own ports — which is the shape ``conversations``
already takes for *one rule read against two records*.

**Through ``ChallengeDirectory`` and ``GameRepository`` rather than query ports
of its own**, on ``challenges_arranging_court.py``'s argument: the joins already
exist there — *every challenge this player is seated in*, and *the game this
challenge opened* — and a second read declaring the same join would be a second
place for *who is on this court* to be true.

**The fold is a module-level function and it is the thing under test.** Its
five answers — arranging, on and awaiting entry, history, not on it, left it —
are each pinned in ``tests/unit/test_plannable_courts_fold.py`` against the two
aggregates, because it is the read that decides who may write a plan and a stub
that agreed with the rule would prove nothing about whether the records fold
that way.

**Cost.** One directory read for the player's challenges, then one stream read
per court that has become a game. Bounded by how many courts this player has
ever accepted a seat on, which is every read in this context and for the same
reason: the fold *is* the answer.
"""

from __future__ import annotations

from typing import Mapping, final
from uuid import UUID

from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.ports import ChallengeDirectory
from app.modules.challenges.domain.standing import ENDED, Standing
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import GameStanding
from app.modules.plans.domain.ports import PlannableCourt


@final
class ChallengesAndGamesPlannableCourts:
    """``PlannableCourts`` over ``ChallengeDirectory`` and ``GameRepository``."""

    def __init__(
        self, *, challenges: ChallengeDirectory, games: GameRepository
    ) -> None:
        self._challenges = challenges
        self._games = games

    async def plannable_for(
        self, player_id: UUID, *, now: Instant
    ) -> Mapping[UUID, PlannableCourt]:
        """Every court this player holds an accepted, live seat on, keyed by
        challenge id.

        **Open and history alike.** A plan is drawn beside a game whatever its
        standing, so filtering the frozen ones out here would make a plan vanish
        from the game screen that still reads it — and would leave the caller
        unable to tell *you are not on that court* from *that court is over*,
        which are the two different refusals it owes.

        **The game is read only for a court that has become one.** A challenge
        that is still arranging has nothing on the other record to fold, and
        asking would be a stream read per court for an answer already known.
        """

        found: dict[UUID, PlannableCourt] = {}
        for challenge in await self._challenges.seating(player_id):
            game = (
                await self._games.for_challenge(challenge.challenge_id)
                if challenge.has_become_a_game()
                else None
            )
            court = plannable_court_of(challenge, game, player_id=player_id, now=now)
            if court is not None:
                found[challenge.challenge_id] = court
        return found


def plannable_court_of(
    challenge: Challenge, game: Game | None, *, player_id: UUID, now: Instant
) -> PlannableCourt | None:
    """One court, folded for one player at one instant — or ``None``.

    **Whether this player is on it is the challenge's fact, and it is one
    predicate: an accepted seat.** A stranger has no seat, an invitee still
    deciding has one that is not yet a yes, somebody who said no has one that
    never was, and somebody who left has one whose yes was taken back — so all
    four are the same absence, and there is no field saying which
    (``docs/adr/0164`` §3). A seat re-offered to somebody else is not this
    person's either, which is the rule ``seat_of`` already keeps.

    **A court nobody but the organiser has said yes to is not plannable yet**,
    and that is the room's own opening rule read here (``docs/adr/0146`` §7,
    ``docs/adr/0164`` §2). The organiser's seat is accepted from birth, so the
    predicate above alone would list a court the moment it was sent — and a slot
    written then would be a line with no room to land in, dropped by the teller
    and never repaired, because the room opens on the **first acceptance** and
    is told nothing that came before it. So the court qualifies once a room can
    exist: somebody other than the organiser holds an accepted seat, or a game
    exists — the same two facts the room's membership is read from. A send
    everybody declined never qualifies and never becomes history; a court that
    ended after a yes does.

    **Once the court has become a game, the game decides whether the slots may
    still move** — ``AWAITING_ENTRY`` and nothing else, which is ADR-0144's *the
    game leaving its entry window is the only thing that freezes the slots*
    holding exactly. Before it has, the challenge decides: arranging is open and
    an ending is history. The two arms are two arms rather than one rule over
    the challenge's standing because a reopened court is ``LINE_UP_INCOMPLETE``
    for as long as its game stands (``docs/adr/0162``), and a ghosted game's
    plan must freeze with the game rather than stay open for ever on the
    challenge's word.

    **Wholeness is the challenge's fact in both arms**: every seat accepted is
    ``ON``, and a court whose seat somebody left is not whole again until the
    next completed line-up re-seats it. **The anchor is the send until the game
    exists, then ``planned_at``** — the game's, never the challenge's opening
    instant restated — so it only ever moves later.
    """

    seat = challenge.seat_of(player_id)
    if seat is None or not seat.is_accepted():
        return None
    if game is None and not _somebody_else_is_in(challenge):
        return None
    standing = challenge.standing_at(now)
    whole = standing is Standing.ON
    if game is None:
        return PlannableCourt(
            anchor=challenge.opened_at,
            open_to_planning=standing not in ENDED,
            whole=whole,
        )
    return PlannableCourt(
        anchor=game.planned_at,
        open_to_planning=game.standing_at(now) is GameStanding.AWAITING_ENTRY,
        whole=whole,
    )


def _somebody_else_is_in(challenge: Challenge) -> bool:
    """Whether anybody but the organiser holds an accepted seat — the fact the
    room's opening reads, asked of the same seats."""

    return any(
        seat.is_accepted() and not seat.holds(challenge.organiser_id)
        for seat in challenge.seats
    )


__all__ = ["ChallengesAndGamesPlannableCourts", "plannable_court_of"]
