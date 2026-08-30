"""``ChallengeHistoryQuery`` over the event log — the matcher's three facts.

**The third read this context has over the log, and the first with a reader
outside it.** It shares ``challenge_streams.py`` with the other two, so the
coupling to a serialized field name stays written once, and it differs in what it
folds the answer into: the pairs rather than the challenges, the answers rather
than the standing, a count rather than a list.

**Nothing is projected, and demand 1 of the suite is written to catch anybody who
tries.** *Open* is folded from the seats and the caller's clock
(``standing.py``), so a seat past its window has left this answer whether or not
the sweep has been past. A projection storing the standing would be right until a
deadline passed, wrong until something swept it, and believed throughout.

**Two of the three reads fold the aggregate; the history read walks the stream,
and the split is the design.** *Open* and *awaiting* are questions about the
court **as it now stands**, which is what a fold answers. An answer is a thing
that happened *to the court as it stood then* — and a declined seat can be
re-offered, taking its former occupant off today's arrangement entirely. Asking
today's court who answered would erase a recorded refusal the day the organiser
refilled the seat, so that read walks the events instead and carries the court
along with it.

**Cost.** The same as the other two and for the same reason: bounded by how many
challenges the platform has ever recorded, because a substring match cannot use a
B-tree. The index that fixes it is PostgreSQL's, over a table with no rows on a
platform with no deployed environment, and it belongs with the first query that
measures it.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Collection, Iterable, Mapping, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    SeatAccepted,
    SeatDeclined,
    SeatsInvited,
)
from app.modules.challenges.domain.origins import (
    ChallengeOrigin,
    SentOutsideASearch,
)
from app.modules.challenges.domain.ports import (
    ANSWERED_COUNTERPART_BOUND,
    AnswerTally,
    ChallengeCounterpart,
    SharedChallenge,
)
from app.modules.challenges.domain.seats import Seat, SeatAnswer
from app.modules.challenges.infrastructure.challenge_streams import streams_seating
from app.shared.domain import DomainEvent

#: The two events that are an **answer**, and the answer each one is.
#: ``SeatLapsed`` is deliberately not one of them: silence and a no do the same
#: thing to a line-up and are different facts, and a signal that priced them
#: alike would be reading an erased history.
_ANSWERS: Mapping[type[SeatAccepted | SeatDeclined], SeatAnswer] = {
    SeatAccepted: SeatAnswer.ACCEPTED,
    SeatDeclined: SeatAnswer.DECLINED,
}

#: The three events that state the whole court. Every stream opens with one of
#: the first two and re-states it on the third, so a walk that reads these knows
#: the arrangement at every point without folding the aggregate.
_SEATINGS = (ChallengeSent, ChallengeOpenedFromMutualInterest, SeatsInvited)


@final
class EventSourcedChallengeHistory:
    """``ChallengeHistoryQuery`` over ``event_store``, folding what it reads."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def answered_counterparts(
        self, player_id: UUID
    ) -> tuple[ChallengeCounterpart, ...]:
        """Everybody who has answered a challenge this player was on the court for.

        **Their answers and never this player's own**, which is the direction the
        two signals downstream are priced in: a candidate is lifted because
        *they* said yes to you and docked because *they* turned you down, and
        folding in the reader's own answers would charge somebody else's card
        with the reader's judgement.

        **The court is read as it stood at the moment of the answer, and this is
        the one place that matters.** A declined seat can be re-offered, and
        ``SeatsInvited`` carries the whole new arrangement — so the court as it
        stands *today* has forgotten whoever left it. Asking today's court who
        answered would erase a recorded refusal the day the organiser refilled
        the seat, which is exactly the erased history the two outcomes are kept
        apart to prevent. It cuts the other way too: somebody seated into a
        half-built game after a decline was not in the game that was declined,
        and inherits no history from it.
        """

        streams = await streams_seating(self._session, self._codec, [player_id])
        tallies: dict[UUID, dict[SeatAnswer, list[Instant]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for events in streams.values():
            for answerer, answer, at, court in _answers_in(events):
                if answerer != player_id and player_id in court:
                    tallies[answerer][answer].append(at)
        counterparts = [
            ChallengeCounterpart(
                player_id=other,
                answers={
                    answer: AnswerTally(count=len(moments), last_at=max(moments))
                    for answer, moments in given.items()
                },
            )
            for other, given in tallies.items()
        ]
        # **Newest first, then the bound** — in that order, because a bound
        # applied to an unordered list would drop an arbitrary half rather than
        # the oldest one, and the order is what makes a counterpart cut off by
        # the bound indistinguishable from one fully decayed by time.
        counterparts.sort(key=lambda one: (one.last_at, one.player_id), reverse=True)
        return tuple(counterparts[:ANSWERED_COUNTERPART_BOUND])

    async def open_challenges_with(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[SharedChallenge, ...]:
        """Everybody this player currently has an open game with, one row each.

        Ordered newest challenge first, then by counterpart, so two identical
        requests answer in one order — the same demand the directory makes, for
        the same reason.
        """

        streams = await streams_seating(self._session, self._codec, [player_id])
        newest: dict[UUID, SharedChallenge] = {}
        for events in streams.values():
            challenge = Challenge.from_history(events)
            together = challenge.players_in_it_at(now)
            if player_id not in together:
                continue
            for other in together - {player_id}:
                # **One row per person, kept true here rather than assumed.** One
                # open challenge per pair is a rule the send and the mint both
                # enforce, so a second one cannot legitimately exist — but this
                # read's own promise is *one row each*, and a promise that holds
                # only while somebody else's invariant does is a promise a reader
                # cannot use. The most recent wins, so the answer is defined
                # rather than whichever stream came back first.
                standing = newest.get(other)
                if standing is not None and standing.opened_at >= challenge.opened_at:
                    continue
                newest[other] = SharedChallenge(
                    counterpart_id=other,
                    origin=_origin_of(challenge, other),
                    opened_at=challenge.opened_at,
                )
        rows = sorted(
            newest.values(),
            key=lambda row: (row.opened_at, row.counterpart_id),
            reverse=True,
        )
        return tuple(rows)

    async def seats_awaiting_answers(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        """How many seats are waiting on each of these players' answers.

        **Keyed on exactly the set it was asked about**, and a zero is measured:
        the seats were counted and none of them was theirs to answer.

        No standing is consulted, and none is needed. A seat that is awaiting at
        ``now`` is one whose holder is still wanted, and a challenge holding one
        has not ended by construction — so asking the standing as well would be
        a second reading of the same seats.
        """

        wanted = set(player_ids)
        counts = {player_id: 0 for player_id in wanted}
        if not wanted:
            return counts

        streams = await streams_seating(self._session, self._codec, wanted)
        for events in streams.values():
            challenge = Challenge.from_history(events)
            for seat in challenge.seats:
                if seat.player_id in wanted and seat.is_awaiting_at(now):
                    counts[seat.player_id] += 1
        return counts


def _answers_in(
    events: Iterable[DomainEvent],
) -> Iterable[tuple[UUID, SeatAnswer, Instant, frozenset[UUID]]]:
    """Every answer in one stream: who gave it, which one, when, and to whom.

    **The court travels with the answer**, rebuilt from each seating event as
    the walk passes it. A seat code is the only place an occupant is written
    (``seats.py``), and the three seating events each carry the *whole* court —
    which is what makes the arrangement at any point in the stream recoverable
    rather than a delta somebody has to replay by hand.

    A **mutual-born challenge yields nothing here**, and it needs no special
    case to: both seats are accepted from birth, so there is no answer event in
    the stream at all. Nobody answered anything, and what two yeses that met are
    worth is already priced by the interest lift.
    """

    court: frozenset[UUID] = frozenset()
    for event in events:
        if isinstance(event, _SEATINGS):
            court = frozenset(
                seat.player_id
                for seat in (Seat.from_code(code) for code in event.seats)
                if seat.player_id is not None
            )
        elif isinstance(event, (SeatAccepted, SeatDeclined)):
            yield (
                event.player_id,
                _ANSWERS[type(event)],
                Instant(event.occurred_at),
                court,
            )


def _origin_of(challenge: Challenge, player_id: UUID) -> ChallengeOrigin:
    """The origin on that person's own seat, or the claim a seat with none makes.

    Three seats carry no origin — the organiser's, and both of a mutual-born
    challenge — because nobody invited them. ``SentOutsideASearch`` is what they
    say, and it is the writer's own vocabulary rather than a substitute for a
    missing value: *the invitation came from somewhere else, said explicitly.*
    """

    seat = challenge.seat_of(player_id)
    if seat is not None and seat.origin is not None:
        return seat.origin
    return SentOutsideASearch()
