"""``ChallengeHistoryQuery`` over the event log — its five facts.

**Three of them are the matcher's history, the fourth is ``player_score``'s**
(``docs/adr/0140``) — *did you answer inside your day* is the same walk over the
same stream, tallied per person instead of per pair — **and the fifth is the
matcher's fill** (``docs/adr/0150``), which is the only one that reads a single
named stream rather than searching for the streams somebody sits in.

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

**Two of the four reads fold the aggregate; the two history reads walk the
stream, and the split is the design.** *Open* and *awaiting* are questions about
the court **as it now stands**, which is what a fold answers. An answer is a
thing that happened *to the court as it stood then* — and a declined seat can be
re-offered, taking its former occupant off today's arrangement entirely. Asking
today's court who answered would erase a recorded refusal the day the organiser
refilled the seat, so those two read the events instead: one carries the court
along with it, the other carries each invitation's own deadline.

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
    ChallengeWithdrawn,
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
    AnsweringRecord,
    AnswerTally,
    ChallengeCounterpart,
    HalfBuiltLineUp,
    SharedChallenge,
)
from app.modules.challenges.domain.seats import Seat, SeatAnswer
from app.modules.challenges.domain.standing import ENDED
from app.modules.challenges.infrastructure.challenge_streams import (
    stream_of,
    streams_seating,
)
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
                    challenge_id=challenge.id,
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

        **The standing is consulted, for one ending.** A seat that is awaiting
        at ``now`` is one whose holder is still wanted — unless its organiser
        removed the challenge while the seat's day was still running
        (``docs/adr/0165`` §4), which is the one ending the seats cannot show:
        a decline and a lapse leave nothing awaiting, and a withdrawal leaves
        the seats exactly as they were. This read used to say *a challenge
        holding an awaiting seat has not ended by construction*, and the
        pre-answer removal broke the construction — so it asks the fold rather
        than inheriting the answer, at the cost of one fold per stream it was
        already replaying.
        """

        wanted = set(player_ids)
        counts = {player_id: 0 for player_id in wanted}
        if not wanted:
            return counts

        streams = await streams_seating(self._session, self._codec, wanted)
        for events in streams.values():
            challenge = Challenge.from_history(events)
            if challenge.standing_at(now) in ENDED:
                continue
            for seat in challenge.seats:
                if seat.player_id in wanted and seat.is_awaiting_at(now):
                    counts[seat.player_id] += 1
        return counts

    async def answering_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, AnsweringRecord]:
        """What each of these people did about the seats they were asked to take.

        **An invitation whose day is still running is in neither half.** It has
        not lapsed and it has not been answered, and filing it either way would
        price a person for an answer that is still wanted — the same rule the
        seats themselves keep, read here over the whole history instead of over
        one court.

        **Absent rather than a measured zero.** Somebody nobody has ever invited
        has not failed to answer anybody, and the record they get is no record at
        all.

        **And an invitation whose challenge was withdrawn under it is in neither
        half either** (``docs/adr/0142`` §5). Silence on a challenge that had
        stopped existing is not silence, and this read is the only place that
        could tell: the seats are left exactly as they were by a withdrawal, so
        a lapse decided on ``now >= answer_by`` alone would charge a
        still-deciding invitee for a court nobody was waiting on any more.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        answered: dict[UUID, int] = defaultdict(int)
        lapsed: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        streams = await streams_seating(self._session, self._codec, wanted)
        for events in streams.values():
            for (player_id, answer_by), answered_at in _invitations_in(
                events, wanted
            ).items():
                if answered_at is not None:
                    answered[player_id] += 1
                    closed_at = answered_at
                elif now >= answer_by:
                    lapsed[player_id] += 1
                    closed_at = answer_by
                else:
                    continue
                latest[player_id] = max(closed_at, latest.get(player_id, closed_at))

        return {
            player_id: AnsweringRecord(
                answered=answered[player_id],
                lapsed=lapsed[player_id],
                last_at=at,
            )
            for player_id, at in latest.items()
        }

    async def half_built_line_up(
        self, *, challenge_id: UUID, member_id: UUID, now: Instant
    ) -> HalfBuiltLineUp | None:
        """One named court, folded, for a member who is still on it.

        **One stream, addressed rather than searched for.** The other four reads
        here start by asking *which streams seat these people*, which is a
        substring match over every challenge the platform has recorded; this one
        is handed the id and reads the stream by it.

        **Three refusals and one answer.** Nothing at that id, a member holding
        no live seat, and a challenge nobody is arranging any more all answer
        ``None`` — one refusal for three cases, on the port's own rule.

        **The two sets are computed against the same fold and the same instant**,
        so *seated* and *gone* cannot disagree about anybody: everybody live on
        the court is seated, and everybody the challenge has already asked and
        does not still hold is gone. The member themselves is in neither, because
        a search never returns its own searcher and a fill never re-invites the
        person pressing it.

        **The gone set is the aggregate's own ``already_asked_at``**, which is
        ``answered`` *plus the clock*: a lapsed seat joins ``answered`` only when
        the sweep records it, and this read is right either side of that.
        """

        events = await stream_of(self._session, self._codec, challenge_id)
        if not events:
            return None
        challenge = Challenge.from_history(events)
        if not challenge.is_being_arranged_at(now):
            return None
        live = challenge.players_in_it_at(now)
        if member_id not in live:
            return None
        return HalfBuiltLineUp(
            challenge_id=challenge.id,
            sport=challenge.sport,
            mode=challenge.mode,
            # **In the court's own order**, which is the arrangement these people
            # are actually sitting in — the order a fill hands the engine as its
            # locked seats, and the one the builder opens on.
            seated_ids=tuple(
                seat.player_id
                for seat in challenge.seats
                if seat.player_id is not None
                and seat.player_id in live
                and seat.player_id != member_id
            ),
            # **Off the clock as well as off the answers**
            # (``Challenge.already_asked_at``): a seat whose day ran out is not
            # in ``answered`` until a sweep has appended one, and this read must
            # not depend on a loop having been past — otherwise the fill would
            # offer back somebody the aggregate refuses the moment the loop runs.
            answered_and_gone=challenge.already_asked_at(now) - live,
        )


def _invitations_in(
    events: Iterable[DomainEvent], wanted: Collection[UUID]
) -> Mapping[tuple[UUID, Instant], Instant | None]:
    """Every invitation in one stream, and the moment it was answered — or not.

    **An invitation is keyed by who was asked and when their day runs out**,
    because that pair is what one invitation *is*: a seat's ``answer_by`` is
    dated when that seat was invited (``answer_window.py``), so somebody invited
    twice into the same challenge has two deadlines and somebody invited once has
    one however many times the court is re-stated around them. Keying on the seat
    position instead would merge an invitation with the one that replaced it, and
    keying on the person alone would lose the second.

    **A seat with no deadline is not an invitation and is not here.** The
    organiser's own seat and both seats of a mutual-born challenge are accepted
    from birth by somebody who was never asked, and ``answer_by is None`` is
    exactly what says so — which is why nothing here needs a special case for
    either.

    The value is the instant the answer arrived, or ``None`` for an invitation
    still holding one. **Only the answer *events* set it**: a later seating event
    restates the whole court, including seats that have already answered, and
    reading the answer off the restatement would date it from the wrong moment.

    **A withdrawal drops every invitation still open under it**, and only those:
    an invitation whose day had already run out was genuine silence before
    anybody withdrew anything, and it stays in the denominator. Dropping is the
    only spelling available — *neither answered nor lapsed* is exactly what
    absence from this mapping means, and it is what the organiser's own seat
    already is.

    **The rule was here before the aggregate could reach the state, and now it
    can.** A withdraw used to be legal only in ``LINE_UP_INCOMPLETE``, which is
    reached only when no seat is awaiting — so at the instant of a legal
    withdrawal every unanswered invitation was already past its deadline, and
    this rule was written for a stream nothing could write. ``docs/adr/0165``
    §4 admits the withdraw before anybody has answered, so a removed challenge
    now holds invitations whose day was still running, and this is the walk
    that keeps them out of the denominator; the aggregate's own ``lapse`` draws
    the same line on the write side and records none of them. This read is
    ``player_score``'s and is a **walk over history**, not a fold of the
    aggregate: it must be right about a stream, and a denominator that was
    right only because a rule in another module happened to order two rungs a
    particular way is a denominator that goes wrong silently the day that order
    is revisited — which is the day that arrived.
    """

    invitations: dict[tuple[UUID, Instant], Instant | None] = {}
    for event in events:
        if isinstance(event, _SEATINGS):
            for code in event.seats:
                seat = Seat.from_code(code)
                if seat.player_id is None or seat.answer_by is None:
                    continue
                if seat.player_id in wanted:
                    invitations.setdefault((seat.player_id, seat.answer_by), None)
        elif isinstance(event, ChallengeWithdrawn):
            withdrawn_at = Instant(event.occurred_at)
            invitations = {
                (player_id, answer_by): answered_at
                for (player_id, answer_by), answered_at in invitations.items()
                if answered_at is not None or answer_by <= withdrawn_at
            }
        elif isinstance(event, (SeatAccepted, SeatDeclined)):
            if event.player_id not in wanted:
                continue
            open_ones = [
                key
                for key, answered_at in invitations.items()
                if key[0] == event.player_id and answered_at is None
            ]
            if open_ones:
                # The latest deadline, because a person holds at most one open
                # invitation per challenge at a time and a re-invitation always
                # carries a later one. A `max` rather than a lone unpacking so
                # that a stream somehow carrying two answers nothing consumed
                # picks the one being answered rather than raising inside a read.
                invitations[max(open_ones, key=lambda key: key[1])] = Instant(
                    event.occurred_at
                )
    return invitations


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
