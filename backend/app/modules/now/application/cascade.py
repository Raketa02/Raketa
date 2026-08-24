"""The cascade: a seat frees, and it reaches somebody.

ADR-0061 and ADR-0052. Two use cases and a batch — **open** the two dispatches
when a hole appears, and **run** one when its moment comes.

**It lives in ``now/`` although the thing that lost a seat is a match**, for the
reason the departure and result routes do: everything the cascade composes with
is Now's — the scoring context, the fit engine, the pool's fact filter, the
offer the offers region will render — and ``now`` already reads ``matches``
everywhere in this tree. Putting it the other way would make ``matches`` import
``now`` to answer a question about whom to tell, which is a package cycle bought
for a filename.

**Opening is synchronous with the departure; dispatching is not.** Two rows join
the transaction that wrote the hole, so a vacancy with no cascade behind it
cannot exist — the same *"one event or they are a bug"* argument the seat
payment makes about its reservation. What that transaction does **not** pay for
is the pool: reading every rated player in the sport, replaying a rating each
and scoring them is a background cost, and putting it in the request path would
make leaving a match slow in proportion to how popular the sport is.

**A dispatch is a look, not an instruction**, on ADR-0076's rule for the
timekeeper even though this is not its queue: the row says *which* hole and
*which* wave, and everything else is re-derived from the record found now. So a
dispatch that runs late tells the truth late rather than telling a stale truth,
and running one twice writes nothing the first did not — the store is silent
about an offer already made.
"""

from __future__ import annotations

import logging
from enum import Enum
from uuid import UUID

from app.application.ports import UnitOfWork
from app.engines.forecast import PairingAnalysis
from app.engines.matchmaking import Level, Occupant, PlayerSkill
from app.kernel import (
    Clock,
    Instant,
    Ok,
    OfferKind,
    claimed_seats,
    instant,
    seat_price,
)

from app.modules.now.application.scoring import MatchScorer, Unscorable, share_of
from app.modules.now.domain.cascade import (
    Band,
    Invitation,
    Offer,
    PendingWave,
    PoolCandidate,
    Rung,
    Wave,
    delivery_at,
    exclusions_for,
    floor_at,
    invitation_order,
    rungs_in,
    wave_due,
)
from app.modules.now.domain.funnel import MatchScoringContext
from app.modules.now.domain.ports import (
    CascadeWaves,
    CityMatches,
    ClubRegulars,
    Commitments,
    Offers,
    RatedPlayers,
    Ratings,
    StandbyQueue,
)

logger = logging.getLogger(__name__)

#: How many rated players one dispatch will weigh. The safety valve, and **not**
#: a product decision — the same thing ``funnel.CANDIDATE_LIMIT`` is, pointed
#: the other way. Rung 6 is *everyone else in the band* and the band is a wall
#: rather than a cap, so without this a sport's whole population is replayed and
#: scored on one background job.
#:
#: It bites in **ladder order**, because the pool is assembled rung by rung: a
#: truncation that ever fires loses the tail of rung 6 — the people ADR-0061
#: already calls *"everyone in the band anywhere"* — and never somebody who
#: asked for this match.
POOL_LIMIT = 500

#: How many dispatches one tick runs. A ceiling on the work a single look does,
#: not a promise about latency: whatever is left is still due next tick, because
#: ``due_at <= now`` does not stop being true. ``WAKE_BATCH_SIZE``'s number and
#: its argument.
CASCADE_BATCH_SIZE = 100


class CascadeOutcome(str, Enum):
    """What one dispatch did. Returned for the log and the tests, never stored."""

    #: Offers were written.
    DISPATCHED = "dispatched"
    #: The dispatch ran and reached nobody. **Done, not pending** — an empty
    #: rung is a real answer, and leaving the row due would re-run the whole
    #: pool every tick for a hole nobody can fill.
    NOBODY = "nobody"
    #: Somebody is five minutes from owning the seat. Left **due**, so the tick
    #: after the claim ends is the one that runs it.
    SUPPRESSED = "suppressed"
    #: The match is no longer readable. The row is retired rather than left due.
    GONE = "gone"


class OpenCascade:
    """Put a hole's two dispatches on the queue. **One call per vacancy.**

    Called from inside the transaction that wrote the departure, and it does not
    commit: a hole with no cascade behind it is a seat nobody will ever be told
    about, and there is no repair for it later, because nothing re-reads old
    vacancies looking for the ones that were missed.

    **The quiet hours are applied here and never again.** ADR-0052 holds
    delivery to 08:00 local unless the match starts inside twelve hours, and
    that is a decision about *this hole at this moment* — re-deciding it on
    every tick would let a dispatch held to 08:00 be re-held to tomorrow's 08:00
    for ever if a tick were late, which is the seat quietly never reaching
    anybody.
    """

    def __init__(self, *, waves: CascadeWaves, contexts: CityMatches) -> None:
        self._waves = waves
        self._contexts = contexts

    async def execute(
        self, *, match_id: UUID, vacancy_id: UUID, vacated_at: Instant
    ) -> None:
        context = await self._contexts.one(match_id)
        if context is None:
            # A match this read cannot see — an unknown club, most likely — has
            # no zone to hold delivery to. Logged rather than raised, because
            # the alternative is a departure that cannot be applied because the
            # club table is short a row: the player's money must not wait on the
            # cascade's ability to find a timezone.
            logger.warning(
                "cascade not opened: no scoring context",
                extra={"match": str(match_id), "vacancy": str(vacancy_id)},
            )
            return
        await self._waves.open(
            [
                PendingWave(
                    match_id=match_id,
                    vacancy_id=vacancy_id,
                    wave=wave,
                    due_at=delivery_at(
                        wave_due(vacated_at, wave),
                        context.record,
                        zone=context.club.zone,
                    ),
                )
                for wave in Wave
            ]
        )


class RunCascade:
    """One dispatch: assemble the pool, rank it, and write the offers.

    **The pool is a fact filter and the band is a wall**, and both of those are
    the domain module's. What is here is the reach — which store answers which
    rung, which candidate costs a rating replay, and when the whole thing is
    called off.
    """

    def __init__(
        self,
        *,
        waves: CascadeWaves,
        offers: Offers,
        contexts: CityMatches,
        players: RatedPlayers,
        regulars: ClubRegulars,
        commitments: Commitments,
        ratings: Ratings,
        standby: StandbyQueue,
        scorer: MatchScorer,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._waves = waves
        self._offers = offers
        self._contexts = contexts
        self._players = players
        self._regulars = regulars
        self._commitments = commitments
        self._ratings = ratings
        self._standby = standby
        self._scorer = scorer
        self._uow = uow
        self._clock = clock

    async def execute(self, wave: PendingWave) -> CascadeOutcome:
        """One dispatch, and the whole of what it may write."""

        now = instant(self._clock.now())
        context = await self._contexts.one(wave.match_id)
        if context is None:
            # The match is gone, or its club is. The row is retired rather than
            # left due, or the queue grows a dispatch that can never run and the
            # tick picks it up for ever.
            await self._retire(wave, at=now)
            return CascadeOutcome.GONE

        # **A live seat claim silences pending waves**, and a lapse resumes
        # them. Liveness is composed off the record rather than latched, so this
        # is true at the instant it is asked whether or not a reaper has been
        # round (ADR-0081): somebody is five minutes from owning the seat, and
        # telling twenty more people about it is the exceptional-card lie
        # ADR-0061 spends its wording to avoid. The row is left **due**, so the
        # first tick after the claim ends runs it — and nobody already reached
        # is reached twice, because the store is silent about an offer it holds.
        if claimed_seats(context.record, now):
            return CascadeOutcome.SUPPRESSED

        invitations = await self._invitations(context, wave=wave, now=now)
        if invitations:
            # Composed once per dispatch rather than once per offer, and not
            # because it is expensive: everybody told in one dispatch was told
            # the same price, and reading the clock per row would let two people
            # in one wave be quoted differently across the rescue deadline.
            price = seat_price(context.record, share_of(context), now)
            await self._offers.record(
                [
                    Offer(
                        match_id=wave.match_id,
                        vacancy_id=wave.vacancy_id,
                        player_id=one.player_id,
                        player_rung=one.rung,
                        fit=one.fit,
                        price=price,
                        # One value in v1. ADR-0061 retired the exclusive offer
                        # with its hold, its cap and its backstop; the kernel
                        # keeps both names so the sentence exists the day the
                        # other does.
                        kind=OfferKind.OPEN,
                        offered_at=now,
                    )
                    for one in invitations
                ]
            )
        await self._waves.dispatched(
            vacancy_id=wave.vacancy_id, wave=wave.wave, at=now
        )
        # **An empty rung is skipped instantly**, so the head start is not paid
        # for an empty queue (ADR-0061). Asked of the **first** dispatch only:
        # there is nothing behind the second to bring forward.
        if wave.wave is Wave.FIRST and not invitations:
            await self._waves.bring_forward(
                vacancy_id=wave.vacancy_id, wave=Wave.SECOND, to=now
            )
        await self._uow.commit()
        return CascadeOutcome.DISPATCHED if invitations else CascadeOutcome.NOBODY

    async def _retire(self, wave: PendingWave, *, at: Instant) -> None:
        await self._waves.dispatched(
            vacancy_id=wave.vacancy_id, wave=wave.wave, at=at
        )
        await self._uow.commit()

    async def _invitations(
        self, context: MatchScoringContext, *, wave: PendingWave, now: Instant
    ) -> tuple[Invitation, ...]:
        """Everybody this dispatch tells, in ladder order.

        The order of the work is the order of the cost. The rungs are assembled
        from four cheap set reads and truncated in **ladder order**; only then
        does anybody pay a rating replay, and only a candidate who survives that
        pays a score. A player excluded by a fact the record already holds never
        costs a stream load, which is what keeps a dispatch affordable on the
        tail rung.
        """

        record = context.record
        standing = await self._rungs(context, wave=wave.wave, now=now)
        if not standing:
            return ()

        already = await self._offers.offered_for(vacancy_id=wave.vacancy_id)
        band = self._band(context, now=now)
        floor = floor_at(record, now)

        invitations: list[Invitation] = []
        for player_id, rung in standing:
            if player_id in already:
                # Nobody is told twice about one hole — ADR-0061's *"a lapse
                # resumes them and nobody is told twice"* — and it is checked
                # before the expensive half rather than left to the store,
                # which would have paid a replay and a score to write nothing.
                continue
            occupant = await self._ratings.occupant(
                player_id=player_id, sport=record.sport
            )
            diary = await self._commitments.held_by(player_id)
            candidate = PoolCandidate(
                player_id=player_id,
                rung=rung,
                level=_level_of(occupant),
                busy=tuple((start, end) for _, start, end in diary),
                already_mine=any(held == wave.match_id for held, _, _ in diary),
            )
            if exclusions_for(candidate, record, band=band, now=now):
                continue
            fit = self._fit(context, occupant, now=now)
            if fit is None:
                continue
            if floor is not None and fit < floor:
                continue
            invitations.append(Invitation(player_id=player_id, rung=rung, fit=fit))
        return invitation_order(invitations)

    async def _rungs(
        self, context: MatchScoringContext, *, wave: Wave, now: Instant
    ) -> tuple[tuple[UUID, Rung], ...]:
        """Every candidate and the **highest** rung she stands on, in order.

        A player who asked for this match *and* plays at the club stands on rung
        1, not on both: the ladder is an ordering over people, and somebody
        standing twice would be told twice. The first rung to claim her keeps
        her, which is what makes ``invitation_order``'s first comparator mean
        anything.

        Truncated here rather than after scoring, for
        ``CityMatchesFromMatches``'s reason: everything below this line is the
        expensive half, and a valve applied afterwards would have paid for the
        whole population first.
        """

        seen: set[UUID] = set()
        standing: list[tuple[UUID, Rung]] = []
        for rung in rungs_in(wave):
            # Sorted so that a truncation at ``POOL_LIMIT`` is the same
            # truncation twice: without it the tail that survives is whatever
            # order a set iterated in, which is not stable across processes.
            for player_id in sorted(
                await self._members(context, rung, now=now), key=str
            ):
                if player_id in seen:
                    continue
                seen.add(player_id)
                standing.append((player_id, rung))
        return tuple(standing[:POOL_LIMIT])

    async def _members(
        self, context: MatchScoringContext, rung: Rung, *, now: Instant
    ) -> frozenset[UUID]:
        """Who stands on one rung. **A dark rung answers the empty set.**

        Declared and empty rather than absent, which is ADR-0061's own shape for
        a rung whose feature is unbuilt: *"rungs with no source ship dark —
        declared, empty, and plugged in when the feature that feeds them
        exists."*
        """

        match rung:
            case Rung.STANDBY:
                return await self._standby.queued_for(context.match_id)
            case Rung.ASKED_BEFORE:
                return await self._offers.reached_on(match_id=context.match_id)
            case Rung.CLUB_REGULAR:
                return await self._regulars.at(
                    club_id=context.club.club_id, before=now
                )
            case Rung.IN_THE_BAND:
                return frozenset(await self._players.at(context.record.sport))
            case _:
                # Rungs 2, 4 and 7. There is nothing to read: the alerts
                # feature, ADR-0085's *Recently viewed* store and the
                # availability calendar are all unbuilt.
                return frozenset()

    def _band(self, context: MatchScoringContext, *, now: Instant) -> Band | None:
        """The wall, computed once for the dispatch.

        ``None`` is *no band* and never *a band nobody clears* — the domain
        module says what that means for the rule. It is the pairing engine's
        ``TargetBand``, so there is no second implementation of *the mean of the
        seated Levels* anywhere: the engine's own docstring warns that a second
        one is a card whose band says one thing while its forecast quietly
        imputed another.
        """

        try:
            return _band_from(self._scorer.analyse(context, now=now))
        except Unscorable as failure:
            # A match whose analysis will not run has no wall. That is the same
            # answer an unseated roster gets, and for the same reason: refusing
            # everybody on a missing fact turns a hole into a seat nobody can
            # ever be told about, which is the one outcome this whole module
            # exists to prevent.
            logger.warning(
                "cascade could not read a band",
                extra={"match": str(context.match_id), "reason": str(failure)},
            )
            return None

    def _fit(
        self, context: MatchScoringContext, occupant: Occupant | None, *, now: Instant
    ) -> int | None:
        """This candidate's score for this match, or nothing if it cannot be had.

        ``Unscorable`` is caught **per candidate**, which is the opposite of the
        shelves' rule and the opposite for a reason. There, a half-scored shelf
        is a shelf whose order means nothing, so the whole thing degrades. Here
        the order is over *people*, and one player whose rating stream will not
        replay is one person not told — dropping the other forty because of her
        would turn a single bad row into a dead seat.
        """

        if occupant is None:
            return None
        try:
            score, _ = self._scorer.score(context, viewer=occupant, now=now)
        except Unscorable as failure:
            logger.warning(
                "cascade could not score a candidate",
                extra={"match": str(context.match_id), "reason": str(failure)},
            )
            return None
        return score.fit


class CascadeBatch:
    """Every dispatch due at this instant, run once each.

    Hosted by the existing event worker beside the outbox drain and the match
    wakes, and a batch for their reason: one indexed query, a bounded slice of
    work, and whatever is left is still due next tick.

    **One failed dispatch does not stop the batch.** Two holes at two clubs have
    nothing to do with each other, so an exception is rolled back, logged
    against its own hole, and the rest are run. The rollback is what makes *the
    rest are run* true rather than hopeful: a session left holding a failed
    statement fails every dispatch after it, and the batch would read as one
    broken hole rather than as a broken tick.
    """

    def __init__(
        self,
        *,
        waves: CascadeWaves,
        run: RunCascade,
        uow: UnitOfWork,
        clock: Clock,
        batch_size: int = CASCADE_BATCH_SIZE,
    ) -> None:
        self._waves = waves
        self._run = run
        self._uow = uow
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self, *, worker_id: str) -> int:
        """One tick's worth of dispatches. ``worker_id`` names who took them.

        ``TickWork``'s shape, because this is the third job on the interval the
        outbox already runs — ADR-0076's *"no new interval and no second
        process"*, applied to a queue that ADR is not about. The id is for the
        log and for nothing else: there are no leases here, because a dispatch
        that runs twice writes nothing the first did not.
        """

        now: Instant = instant(self._clock.now())
        due = await self._waves.due(now=now, limit=self._batch_size)
        ran = 0
        for wave in due:
            try:
                await self._run.execute(wave)
            except Exception:  # noqa: BLE001 — one hole must not stop the tick
                await self._uow.rollback()
                logger.exception(
                    "cascade dispatch failed",
                    extra={
                        "match": str(wave.match_id),
                        "vacancy": str(wave.vacancy_id),
                        "wave": wave.wave.value,
                    },
                )
                continue
            ran += 1
        if ran:
            logger.info(
                "cascade dispatches taken",
                extra={"worker_id": worker_id, "taken": ran},
            )
        return ran


def _band_from(analysis: PairingAnalysis) -> Band | None:
    """The engine's ``TargetBand`` in the ladder's words, or nothing.

    ``Err`` is *nobody seated* or *nobody seated holds a Level here*, and both
    are the engine's own *"the mean of no Levels, which is not a wide band"*.
    """

    target = analysis.target_band
    if not isinstance(target, Ok):
        return None
    return Band(low=target.value.low, high=target.value.high)


def _level_of(occupant: Occupant | None) -> Level | None:
    """Her Level, when the platform has one. ``None`` is *unrated at this sport*."""

    return occupant.level if isinstance(occupant, PlayerSkill) else None
