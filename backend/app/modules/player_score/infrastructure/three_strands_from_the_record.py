"""``PublishedScoreQuery`` over the two contexts that keep a record of anything.

**Named for the fact it asserts, not for what it wraps** — the rule
``docs/adr/0095`` set for the null objects, applied to an adapter that is only
half of one. *Three strands from the record* is a claim about this platform
today: ``games`` can say whether a plan produced a game and what became of the
scores put in front of somebody, ``challenges`` can say whether a seat got its
answer, and **nothing on this platform can say anything about the other three**.
The name moved with the count the day the third strand landed
(``docs/adr/0160``), exactly as its own docstring said it would — which is how
``NoMatchHistoryExists`` and ``NoResultUpdateRuleExists`` retired.

**It reads each provider's own published port and never their streams.** A
``select`` over ``event_store`` written here would make ``player_score`` a second
reader of two other contexts' schemas and, worse, a second author of what *a
ghost*, *a lapse* and *an ignored score* mean — and the second copy is always the
one that gets believed. What crosses each seam is the provider's own vocabulary;
the arithmetic that turns it into a verdict about a person is this context's, and
is the only thing here that is not somebody else's fact.

**Three reads and never one per player.** Every provider answers about a whole
set, because the matcher asks about every candidate still standing in one call —
five hundred people on a busy search — and a per-row read behind this port would
be fifteen hundred walks of two logs inside one request.

**Three strands are absent and none of them is a zero.** *Keeps plans* has no
plan with a moment to be late for, *settles up* has no court money, and
*sportsmanship* is published in its own right and is not a ratio at all
(``docs/adr/0158``). Each is missing from the mapping rather than published at
nought or at a half, so the published blend renormalises over what is there and
the matcher's term does the same thing one layer out (``docs/adr/0140``).

**One of the three has a window and the other two do not**, which is the only
asymmetry in this file. It is decided in ``domain/strands.py`` beside the number,
and it arrives at ``games`` as an instant rather than as a policy: this side says
*from when*, and that side says what happened.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.engines.matchfit.core import ReliabilityStrand
from app.kernel import Instant
from app.modules.challenges.domain.ports import AnsweringRecord, ChallengeHistoryQuery
from app.modules.games.domain.ports import (
    Attendance,
    GameHistoryQuery,
    ResultAnswering,
)
from app.modules.player_score.domain.strands import (
    PlayerScore,
    StrandRatio,
    answered_results_since,
)


@final
class ThreeStrandsFromTheRecord:
    """``PublishedScoreQuery`` over ``games`` and ``challenges``."""

    def __init__(
        self, *, games: GameHistoryQuery, challenges: ChallengeHistoryQuery
    ) -> None:
        self._games = games
        self._challenges = challenges

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        """The Player Score of each of these people who has one.

        **The union and not the intersection.** Somebody who has answered
        invitations and never had a game arranged has a Player Score of one
        strand, and so does somebody with the opposite history — a reading needs
        *a* strand, not all of them, and requiring both would make the score
        answer about nobody until the platform had both records about the same
        person.

        **One instant for both halves.** A plan is a ghost only once its entry
        window has closed and a seat has lapsed only once its day has run out, so
        two clocks here would let a score be computed from two different
        presents.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        # One after another, because they share the request's session: an
        # `AsyncSession` is not safe to use concurrently and all three of these
        # fold a stream through it, so gathering them would be a race rather than
        # a speed-up. The same asymmetry `PlayerCardIdentities` writes out.
        attendance = await self._games.attendance_for(wanted, now=now)
        answering = await self._challenges.answering_for(wanted, now=now)
        results = await self._games.result_answering_for(
            wanted, since=answered_results_since(now), now=now
        )

        scores: dict[UUID, PlayerScore] = {}
        for player_id in wanted:
            strands = _strands_of(
                attendance.get(player_id),
                answering.get(player_id),
                results.get(player_id),
            )
            if strands:
                scores[player_id] = PlayerScore(strands=strands)
        return scores


def _strands_of(
    attendance: Attendance | None,
    answering: AnsweringRecord | None,
    results: ResultAnswering | None,
) -> Mapping[ReliabilityStrand, StrandRatio]:
    """The strands this platform can publish about one person, and no others.

    **The good outcome of each is the one the strand is named for**, and the
    denominators are opportunities rather than totals: an arrangement that
    settled either way, and an invitation whose day is over. The counts arrive
    already narrowed to that by the two providers, which is why there is no clock
    in this function — the judgement about *has this closed yet* belongs to the
    context that owns the deadline.

    **A no is a good outcome on two of the three.** Turning somebody down inside
    your day is answering them, and so is countering a score you believe is
    wrong; what both strands price is silence. That *answers about results* is
    one of them is the whole reason it could be built at all — a strand counting
    agreements would have docked both sides of every honest disagreement, which
    is why ``docs/adr/0137`` struck the one that did.
    """

    strands: dict[ReliabilityStrand, StrandRatio] = {}
    if attendance is not None:
        strands[ReliabilityStrand.SHOWS_UP] = StrandRatio(
            good=attendance.played,
            opportunities=attendance.played + attendance.ghosts,
            last_at=attendance.last_at,
        )
    if answering is not None:
        strands[ReliabilityStrand.ANSWERS_CHALLENGES] = StrandRatio(
            good=answering.answered,
            opportunities=answering.answered + answering.lapsed,
            last_at=answering.last_at,
        )
    if results is not None:
        strands[ReliabilityStrand.ANSWERS_RESULTS] = StrandRatio(
            good=results.answered,
            opportunities=results.answered + results.ignored,
            last_at=results.last_at,
        )
    return strands


__all__ = ["ThreeStrandsFromTheRecord"]
