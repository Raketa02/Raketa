"""``MatchHistoryQuery``'s challenge half — signed by ``challenges``, translated here.

**One contract, two providers, and the bend is deliberate** (``docs/adr/0098`` as
amended). Every other outward port has one provider because *a provider that
signed half of two contracts would have signed all of neither*; this one is split
by **fact** rather than by contract, because the seam runs *through*
``pairwise_counterparts``: ``ACCEPTED`` and ``DECLINED`` are challenge facts and
``PLAYED`` is ``matches``'. Splitting the port to match would cut
``PAIRWISE_COUNTERPART_BOUND`` in half, and two bounded reads merged by a caller
is not a bounded read. So the port stays whole, this class answers the half that
exists, and ``matches`` arrives later as a **composing** adapter rather than as a
second signature.

**Named for the fact it asserts, not for the provider it wraps.** ``UsersAccount
Status`` is an adapter and says so; this is half an adapter and half a measured
absence, and the next reader has to know that ``PLAYED`` is empty **by
construction and not by luck** — otherwise the first person to see familiarity
stand down goes hunting for a bug in a query.

What is still absent, and why each is absent rather than defaulted:

``PLAYED`` and ``PLANNED_NEVER_PLAYED``
    A challenge accepted is not a game played. Nothing in this repository records
    a result, so familiarity returns ``NoEvidence`` — checked rather than assumed:
    ``_shared_history`` needs ``games_played_together >= 1``, so a challenge-only
    pair produces no ``SharedHistory`` and the modifier stays **absent** rather
    than firing at zero strength on every card.

``late_change_threshold``
    ``None``, on the port's own stated rule and with the reason unchanged.
    Nothing here schedules a plan, and a number nobody measured is a number
    somebody picked. It is demanded of the context that owns plans, which is not
    this one.

**It reads the provider's own port and never the provider's streams.** The fold
over the challenge log belongs to ``challenges``, whose
``EventSourcedChallengeHistory`` owns it; a ``select`` over the event store
written here would make the matcher a second reader of somebody else's log — and
a second author of what *open* means.

**Amended by ``docs/adr/0137``: it is no longer handed out on its own.** ``games``
ships, so ``GamesPlayedAndChallengesAnswered`` composes this class with the
provider that brings ``PLAYED`` and ``PLANNED_NEVER_PLAYED``, and the composition
root wires that. Everything below is unchanged and every sentence in it stays
true **of this class**: it answers the challenge half, and its ``PLAYED`` is
still empty by construction. What changed is that a caller now gets the whole
port rather than this half of it — which is exactly the *composing adapter*
ADR-0098's amendment banner said would arrive, and the reason the port was kept
whole while it did not exist.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Clock, Minutes
from app.modules.challenges.domain.origins import (
    ChallengeOrigin as WrittenOrigin,
    SentFromSearch as WrittenFromSearch,
)
from app.modules.challenges.domain.ports import (
    ANSWERED_COUNTERPART_BOUND,
    ChallengeCounterpart,
    ChallengeHistoryQuery,
)
from app.modules.challenges.domain.seats import SeatAnswer
from app.modules.matchmaking.domain.ports import (
    PAIRWISE_COUNTERPART_BOUND,
    ChallengeOrigin,
    OpenChallenge,
    OutcomeTally,
    PairwiseCounterpart,
    PairwiseOutcome,
    SentFromSearch,
    SentOutsideASearch,
)

#: Which answer becomes which outcome, and **nothing else does**.
#: ``SeatAnswer.LAPSED`` is absent from both sides of this table: the provider
#: refuses to tally one, and there is no outcome here for it to become.
_OUTCOMES: Mapping[SeatAnswer, PairwiseOutcome] = {
    SeatAnswer.ACCEPTED: PairwiseOutcome.ACCEPTED,
    SeatAnswer.DECLINED: PairwiseOutcome.DECLINED,
}


def _refuse_two_bounds(reader: int, writer: int) -> None:
    """The bound, checked at import against the second spelling of it.

    ``challenges`` may not import ``matchmaking``, so the 500 is written down
    twice — the same decision the seat's ``Side`` and the origin codes take. What
    is avoidable about that is it being *silent*: a bound raised on one side
    alone would leave the matcher promising a page it no longer gets, and a
    counterpart truncated by the provider would stop being indistinguishable from
    one fully decayed by time. This is the seam where the two spellings meet, so
    a disagreement stops the process from starting.
    """

    if reader != writer:
        raise RuntimeError(
            "the pairwise counterpart bound is spelled twice and the two "
            f"spellings disagree: the matcher demands {reader}, challenges "
            f"answers {writer}"
        )


# The call **is** the check: there is no value here anybody needs, only a reason
# for this module to refuse to import if the two spellings ever part company.
_refuse_two_bounds(PAIRWISE_COUNTERPART_BOUND, ANSWERED_COUNTERPART_BOUND)


@final
class ChallengesButNobodyHasPlayed:
    """The challenge half of the matcher's history, and an honest hole where the
    games half will be."""

    def __init__(self, challenges: ChallengeHistoryQuery, clock: Clock) -> None:
        self._challenges = challenges
        self._clock = clock

    async def pairwise_counterparts(
        self, searcher_id: UUID
    ) -> tuple[PairwiseCounterpart, ...]:
        """Who has answered a challenge this searcher was in — at most 500, newest
        first.

        The order and the bound are the provider's, because they are one rule and
        not two: sorting here over an already-truncated answer would order the
        wrong five hundred people.
        """

        answered = await self._challenges.answered_counterparts(searcher_id)
        return tuple(_counterpart(one) for one in answered)

    async def open_challenges(self, searcher_id: UUID) -> tuple[OpenChallenge, ...]:
        """Every challenge standing between this searcher and anybody, right now.

        The clock is read here rather than demanded of the caller because the
        matcher's port takes none: *open* is a fact about this instant, and a
        caller that could supply the instant could supply a stale one.
        """

        open_with = await self._challenges.open_challenges_with(
            searcher_id, now=self._clock.now()
        )
        return tuple(
            OpenChallenge(
                counterpart_id=one.counterpart_id,
                origin=_origin(one.origin),
                opened_at=one.opened_at,
            )
            for one in open_with
        )

    async def late_change_threshold(self) -> Minutes | None:
        """``None``, and the reason has changed owner rather than gone away.

        Nothing in this repository schedules a plan, so there is no published
        threshold; *late* is a fact about a plan and belongs to the context that
        owns plans. This class answers for challenges and is not that context —
        it says so here rather than leaving a reader to infer it from a return
        value.
        """

        return None

    async def open_challenge_counts(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, int]:
        """How many seats are waiting on each of these players' answers.

        **Seats they were invited into and have not answered, inside their own
        window, across every sport** — never the challenges they organised. An
        organiser with eight sends out is over-committed and is not slow to
        answer, and sinking them would dock the exact behaviour Play exists to
        produce.

        Every player asked about still gets a count, and a zero is measured: the
        seats were counted and none of them was theirs.
        """

        return await self._challenges.seats_awaiting_answers(
            player_ids, now=self._clock.now()
        )


def _counterpart(counterpart: ChallengeCounterpart) -> PairwiseCounterpart:
    """One person's answers, in the reader's vocabulary.

    Two spellings meet here and the mapping is a table rather than a cast, so
    that a value arriving from the writer with no reader — a fourth answer, one
    day — is a ``KeyError`` at the seam instead of a string that means nothing
    downstream.
    """

    return PairwiseCounterpart(
        player_id=counterpart.player_id,
        outcomes={
            _OUTCOMES[answer]: OutcomeTally(count=tally.count, last_at=tally.last_at)
            for answer, tally in counterpart.answers.items()
        },
    )


def _origin(origin: WrittenOrigin) -> ChallengeOrigin:
    """Where the seat came from, in the reader's vocabulary. **Two answers.**"""

    if isinstance(origin, WrittenFromSearch):
        return SentFromSearch(search_id=origin.search_id, position=origin.position)
    return SentOutsideASearch()
