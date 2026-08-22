"""Reading a match out of five tables, writing the delta back, and announcing it.

**The version guard runs first, and in the same statement that bumps it**, so a
second writer that read the same match loses on ``rowcount`` rather than on
whichever seat it happened to touch. That is the whole of ADR-0034's concurrency
answer: *"two concurrent writers cannot interleave: one wins, one retries"*, from
a column rather than from a stream.

**The announcements are published in the same transaction as the row.** The
match keeps no history, so the outbox trail *is* the record of what happened
(ADR-0034), and a row written without its announcement is a change nobody will
ever be able to explain. Neither ``add`` nor ``save`` commits — the boundary
stays a use-case dependency, which is what lets ``Raketa02/Raketa#70`` join a
seat payment, a reservation and two outbox rows into one write.

**The children are updated, never rewritten.** Seats are created once with the
match and thereafter only occupied and emptied, so their rows are found by
``(match_id, seat_index)`` and updated in place; a delete-and-reinsert would
throw away the row identity the one-player-one-seat index is keyed on and would
churn the table on every join. Vacancies are append-and-close: a new hole is an
INSERT, a filled one is an UPDATE, and nothing is ever removed. Departures are
the same shape and for a stronger reason — a settlement that vanished and came
back would be a refund nobody could account for — and their two mutable columns
are the outcome and the moment it landed. Seat claims are the same shape again
with one mutable column: a claim is **ended, never deleted**, because the
thirty-second cooldown is measured from the instant it ended and a row that
vanished would take the cooldown with it.

Naive datetimes come back from SQLite, which drops the offset it was handed.
They are re-attached to UTC on the way in, the same normalisation the Clubs
repository and the JSON event codec make and for the same reason: the stored
instant *is* UTC, because ``Instant`` normalises before anything is written.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence, cast
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import DomainEventPublisher
from app.kernel import (
    Clock,
    HoldPolicy,
    Instant,
    LeaverMoney,
    MatchKind,
    NothingTaken,
    Outcome,
    PayModel,
    Recoverable,
    SeatShare,
    Sport,
    grosze,
    instant,
    minutes,
    next_wake,
)
from app.shared.ids import new_uuid

from app.modules.matches.domain.claim import SeatClaim
from app.modules.matches.domain.departure import Departure
from app.modules.matches.domain.errors import ConcurrentMatchModification
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.score import Score, SetScore
from app.modules.matches.domain.seat import Seat
from app.modules.matches.domain.vacancy import Vacancy
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchDepartureORM,
    MatchORM,
    MatchSeatClaimORM,
    MatchSeatORM,
    MatchVacancyORM,
)


def _as_instant(value: datetime) -> Instant:
    """Re-attach UTC to what SQLite dropped, then normalise."""

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _optional_instant(value: datetime | None) -> Instant | None:
    return None if value is None else _as_instant(value)


def _score_of(raw: Any) -> Score | None:
    """The stored pairs, back as sets. ``None`` when nothing is on the table."""

    if not raw:
        return None
    return Score(tuple(SetScore(side_a=int(a), side_b=int(b)) for a, b in raw))


def _leaver_money(amount: int | None) -> LeaverMoney:
    """The stored amount back as one of the two forms, never an optional field.

    ``None`` is *nothing was taken*, and it is the only spelling of it: the
    domain refuses a reversal that names an amount and an amount that names no
    reversal, so a row can only mean one of the two things (ADR-0072).
    """

    return NothingTaken() if amount is None else Recoverable(amount=grosze(amount))


def _amount_column(money: LeaverMoney) -> int | None:
    """Null where nothing was taken. **Never zero** — a zero is a blank a reader
    would have to interpret, and the two sentences it would blur are opposites."""

    return None if isinstance(money, NothingTaken) else int(money.amount)


def _score_column(score: Score | None) -> list[list[int]] | None:
    """Sets as the pairs of integers they cross the wire as, never a string."""

    if score is None:
        return None
    return [[one.side_a, one.side_b] for one in score.sets]


class SqlAlchemyMatchRepository:
    """A record repository: rows in, rows out, a version and an outbox on the way."""

    def __init__(
        self, session: AsyncSession, *, events: DomainEventPublisher, clock: Clock
    ) -> None:
        self._session = session
        self._events = events
        self._clock = clock

    # -- reads --------------------------------------------------------------

    async def get(self, match_id: UUID) -> Match | None:
        row = await self._session.get(MatchORM, match_id)
        if row is None:
            return None
        assembled = await self._assembled([row])
        return assembled[0]

    async def for_club(self, club_id: UUID) -> list[Match]:
        return await self._assembled(
            await self._rows(
                select(MatchORM)
                .where(MatchORM.club_id == club_id)
                .order_by(MatchORM.start, MatchORM.id)
            )
        )

    async def starting_between(
        self,
        *,
        club_ids: Sequence[UUID],
        window_from: Instant,
        window_to: Instant,
    ) -> list[Match]:
        if not club_ids:
            return []
        return await self._assembled(
            await self._rows(
                select(MatchORM)
                .where(
                    MatchORM.club_id.in_(list(club_ids)),
                    MatchORM.start >= window_from,
                    MatchORM.start < window_to,
                )
                .order_by(MatchORM.start, MatchORM.id)
            )
        )

    # -- writes -------------------------------------------------------------

    async def add(self, match: Match) -> Match:
        """Insert the match, its seats, and whatever it announced."""

        self._session.add(self._row(match, version=match.version))
        for seat in match.seats:
            self._session.add(self._seat_row(match.id, seat))
        for vacancy in match.vacancies:
            self._session.add(self._vacancy_row(match.id, vacancy))
        for departure in match.departures:
            self._session.add(self._departure_row(match.id, departure))
        for claim in match.claims:
            self._session.add(self._claim_row(match.id, claim))
        await self._session.flush()
        await self._announce(match)
        return match

    async def save(self, match: Match) -> Match:
        """Bump the version or refuse, then write the delta and announce it.

        The order is deliberate. The guard is taken before a single child row is
        touched, so a losing writer has changed nothing when it is told; and the
        announcements go out after the delta, so the outbox never holds a claim
        the rows do not yet support.
        """

        result = await self._session.execute(
            update(MatchORM)
            .where(MatchORM.id == match.id, MatchORM.version == match.version)
            .values(**self._columns(match), version=match.version + 1)
        )
        # `session.execute` is typed as returning `Result`, which has no
        # `rowcount`; a DML statement always yields a `CursorResult`, which does.
        if cast(CursorResult[Any], result).rowcount != 1:
            raise ConcurrentMatchModification()

        await self._write_seats(match)
        await self._write_vacancies(match)
        await self._write_departures(match)
        await self._write_claims(match)
        await self._session.flush()
        match.version += 1
        await self._announce(match)
        return match

    async def _announce(self, match: Match) -> None:
        """Every change this match named, onto the outbox, in this transaction."""

        pending = match.pull_events()
        if pending:
            await self._events.publish_many(pending)

    # -- the delta ----------------------------------------------------------

    async def _write_seats(self, match: Match) -> None:
        """Occupied and emptied in place; never deleted and re-inserted.

        A seat's row *is* its position, and the one-player-one-seat index is
        keyed on it, so churning the rows would churn the index that enforces
        the rule.
        """

        for seat in match.seats:
            await self._session.execute(
                update(MatchSeatORM)
                .where(
                    MatchSeatORM.match_id == match.id,
                    MatchSeatORM.seat_index == seat.index,
                )
                .values(
                    player_id=seat.player_id,
                    paid=seat.paid,
                    taken_at=seat.taken_at,
                )
            )

    async def _write_vacancies(self, match: Match) -> None:
        """Append the new holes, close the ones that closed. Nothing is removed."""

        stored = {
            row_id
            for row_id in await self._all(
                select(MatchVacancyORM.id).where(
                    MatchVacancyORM.match_id == match.id
                )
            )
        }
        for vacancy in match.vacancies:
            if vacancy.id not in stored:
                self._session.add(self._vacancy_row(match.id, vacancy))
                continue
            await self._session.execute(
                update(MatchVacancyORM)
                .where(MatchVacancyORM.id == vacancy.id)
                .values(filled_at=vacancy.filled_at)
            )

    async def _write_departures(self, match: Match) -> None:
        """Append the new leavers, move the ones whose money settled.

        The same append-and-update shape as the vacancies beside them, and the
        two are written separately on purpose: one filler closes a hole and
        settles a **different** departure, so a single loop over one list would
        have to know which of the two it was doing.
        """

        stored = set(
            await self._all(
                select(MatchDepartureORM.id).where(
                    MatchDepartureORM.match_id == match.id
                )
            )
        )
        for departure in match.departures:
            if departure.id not in stored:
                self._session.add(self._departure_row(match.id, departure))
                continue
            await self._session.execute(
                update(MatchDepartureORM)
                .where(MatchDepartureORM.id == departure.id)
                .values(
                    outcome=(
                        None if departure.outcome is None else departure.outcome.value
                    ),
                    settled_at=departure.settled_at,
                )
            )

    async def _write_claims(self, match: Match) -> None:
        """Append the new claims, close the ones that closed. Nothing is removed.

        One mutable column, and it is the only one: a claim's seat, its player
        and its deadline are all fixed at the tap, and the five minutes are not
        extendable by anybody — which is what makes *"a claim it cannot extend"*
        the shape ADR-0081 fixes for a payment provider that answers late.
        """

        stored = set(
            await self._all(
                select(MatchSeatClaimORM.id).where(
                    MatchSeatClaimORM.match_id == match.id
                )
            )
        )
        for claim in match.claims:
            if claim.id not in stored:
                self._session.add(self._claim_row(match.id, claim))
                continue
            await self._session.execute(
                update(MatchSeatClaimORM)
                .where(MatchSeatClaimORM.id == claim.id)
                .values(ended_at=claim.ended_at)
            )

    # -- rows ---------------------------------------------------------------

    def _columns(self, match: Match) -> dict[str, Any]:
        """Every column, including the schedule — **because this is every write**.

        ADR-0076 wants `next_wake_at` *"recomputed on every write"*, and the one
        place that is structurally true is here: `add` and `save` both build
        their values from this dict, and there is no third door into the table.
        Computed in a use case instead, the obligation would be a rule N use
        cases have to remember, and the miss would be a match that stops waking
        — a club's court held past its lapse, invisible to every player.

        The candidate set is a function of the seats and the clock, so it is not
        enough to recompute it when a threshold moves: a match on two paid seats
        wakes at T-12h and the same match after a third payment wakes at T-4h.

        The clock is read here rather than passed in because the moment being
        recorded is *when this row was written*, which is not a caller's fact.
        `next_wake` is strictly later than what it is handed, so a boundary
        falling exactly on the write is not scheduled — correctly: the row that
        has just landed already resolves on the far side of it.
        """

        wake = next_wake(match.as_record(), instant(self._clock.now()))
        return {
            "next_wake_at": None if wake is None else wake.at,
            "wake_reason": None if wake is None else wake.reason.value,
            "club_id": match.club_id,
            "category_id": match.category_id,
            "sport": match.sport.value,
            "duration_minutes": int(match.duration),
            "share_grosze": int(match.share),
            "counted": match.counted,
            "created": match.created,
            "kind": match.kind.value,
            "pay_model": match.pay_model.value,
            "policy_window_minutes": int(match.policy.window),
            "policy_join_cut_minutes": int(match.policy.join_cut),
            "policy_max_hold_age_minutes": (
                None
                if match.policy.max_hold_age is None
                else int(match.policy.max_hold_age)
            ),
            "policy_prob_hold": match.policy.prob_hold,
            "start": match.start,
            "transferring": match.transferring,
            "open_seats": match.open_seats,
            "held_since": match.held_since,
            "released_at": match.released_at,
            "inventory_lost": match.inventory_lost,
            "committed_at": match.committed_at,
            "court_locked": match.court_locked,
            "club_extended": match.club_extended,
            "club_cancelled": match.club_cancelled,
            "weather": match.weather,
            "no_show": match.no_show,
            "form_cancelled": match.form_cancelled,
            "checkpoint_cancelled": match.checkpoint_cancelled,
            "score_sets": _score_column(match.score),
            "score_by": match.score_by,
            "proposals": match.proposals,
            "result_agreed": match.result_agreed,
        }

    def _row(self, match: Match, *, version: int) -> MatchORM:
        return MatchORM(id=match.id, version=version, **self._columns(match))

    def _seat_row(self, match_id: UUID, seat: Seat) -> MatchSeatORM:
        return MatchSeatORM(
            id=new_uuid(),
            match_id=match_id,
            seat_index=seat.index,
            player_id=seat.player_id,
            paid=seat.paid,
            taken_at=seat.taken_at,
        )

    def _vacancy_row(self, match_id: UUID, vacancy: Vacancy) -> MatchVacancyORM:
        return MatchVacancyORM(
            id=vacancy.id,
            match_id=match_id,
            seat_index=vacancy.seat_index,
            vacated_at=vacancy.vacated_at,
            filled_at=vacancy.filled_at,
        )

    def _departure_row(
        self, match_id: UUID, departure: Departure
    ) -> MatchDepartureORM:
        return MatchDepartureORM(
            id=departure.id,
            match_id=match_id,
            seat_index=departure.seat_index,
            player_id=departure.player_id,
            departed_at=departure.departed_at,
            quoted=departure.quoted.value,
            amount_grosze=_amount_column(departure.money),
            outcome=(
                None if departure.outcome is None else departure.outcome.value
            ),
            settled_at=departure.settled_at,
        )

    def _claim_row(self, match_id: UUID, claim: SeatClaim) -> MatchSeatClaimORM:
        return MatchSeatClaimORM(
            id=claim.id,
            match_id=match_id,
            seat_index=claim.seat_index,
            player_id=claim.player_id,
            claimed_at=claim.claimed_at,
            expires_at=claim.expires_at,
            ended_at=claim.ended_at,
        )

    # -- assembly -----------------------------------------------------------

    async def _rows(self, statement: Select[Any]) -> list[MatchORM]:
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _all(self, statement: Select[Any]) -> list[Any]:
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _assembled(self, rows: list[MatchORM]) -> list[Match]:
        """One extra query per child table, whatever the number of matches.

        Not one per match: `Now` reads several at once and a per-match child
        fetch is the N+1 that ADR-0034's *"cheapest to read"* would lose to.
        """

        if not rows:
            return []
        ids = [row.id for row in rows]

        seats: dict[UUID, list[Seat]] = {row.id: [] for row in rows}
        seat_rows = await self._session.execute(
            select(MatchSeatORM)
            .where(MatchSeatORM.match_id.in_(ids))
            .order_by(MatchSeatORM.match_id, MatchSeatORM.seat_index)
        )
        for seat_row in seat_rows.scalars().all():
            seats[seat_row.match_id].append(
                Seat(
                    index=seat_row.seat_index,
                    player_id=seat_row.player_id,
                    paid=seat_row.paid,
                    taken_at=_optional_instant(seat_row.taken_at),
                )
            )

        vacancies: dict[UUID, list[Vacancy]] = {row.id: [] for row in rows}
        vacancy_rows = await self._session.execute(
            select(MatchVacancyORM)
            .where(MatchVacancyORM.match_id.in_(ids))
            .order_by(MatchVacancyORM.match_id, MatchVacancyORM.vacated_at,
                      MatchVacancyORM.id)
        )
        for vacancy_row in vacancy_rows.scalars().all():
            vacancies[vacancy_row.match_id].append(
                Vacancy(
                    id=vacancy_row.id,
                    seat_index=vacancy_row.seat_index,
                    vacated_at=_as_instant(vacancy_row.vacated_at),
                    filled_at=_optional_instant(vacancy_row.filled_at),
                )
            )

        departures: dict[UUID, list[Departure]] = {row.id: [] for row in rows}
        departure_rows = await self._session.execute(
            select(MatchDepartureORM)
            .where(MatchDepartureORM.match_id.in_(ids))
            .order_by(
                MatchDepartureORM.match_id,
                MatchDepartureORM.departed_at,
                MatchDepartureORM.seat_index,
                MatchDepartureORM.id,
            )
        )
        for departure_row in departure_rows.scalars().all():
            departures[departure_row.match_id].append(
                Departure(
                    id=departure_row.id,
                    seat_index=departure_row.seat_index,
                    player_id=departure_row.player_id,
                    departed_at=_as_instant(departure_row.departed_at),
                    quoted=Outcome(departure_row.quoted),
                    money=_leaver_money(departure_row.amount_grosze),
                    outcome=(
                        None
                        if departure_row.outcome is None
                        else Outcome(departure_row.outcome)
                    ),
                    settled_at=_optional_instant(departure_row.settled_at),
                )
            )

        claims: dict[UUID, list[SeatClaim]] = {row.id: [] for row in rows}
        claim_rows = await self._session.execute(
            select(MatchSeatClaimORM)
            .where(MatchSeatClaimORM.match_id.in_(ids))
            .order_by(
                MatchSeatClaimORM.match_id,
                MatchSeatClaimORM.claimed_at,
                MatchSeatClaimORM.seat_index,
                MatchSeatClaimORM.id,
            )
        )
        for claim_row in claim_rows.scalars().all():
            claims[claim_row.match_id].append(
                SeatClaim(
                    id=claim_row.id,
                    seat_index=claim_row.seat_index,
                    player_id=claim_row.player_id,
                    claimed_at=_as_instant(claim_row.claimed_at),
                    expires_at=_as_instant(claim_row.expires_at),
                    ended_at=_optional_instant(claim_row.ended_at),
                )
            )

        return [
            self._match_of(
                row,
                seats[row.id],
                vacancies[row.id],
                departures[row.id],
                claims[row.id],
            )
            for row in rows
        ]

    def _match_of(
        self,
        row: MatchORM,
        seats: list[Seat],
        vacancies: list[Vacancy],
        departures: list[Departure],
        claims: list[SeatClaim],
    ) -> Match:
        return Match(
            id=row.id,
            club_id=row.club_id,
            category_id=row.category_id,
            sport=Sport(row.sport),
            duration=minutes(row.duration_minutes),
            share=SeatShare(grosze(row.share_grosze)),
            counted=row.counted,
            created=_as_instant(row.created),
            kind=MatchKind(row.kind),
            pay_model=PayModel(row.pay_model),
            policy=HoldPolicy(
                window=minutes(row.policy_window_minutes),
                join_cut=minutes(row.policy_join_cut_minutes),
                max_hold_age=(
                    None
                    if row.policy_max_hold_age_minutes is None
                    else minutes(row.policy_max_hold_age_minutes)
                ),
                prob_hold=row.policy_prob_hold,
            ),
            start=_as_instant(row.start),
            seats=seats,
            vacancies=vacancies,
            departures=departures,
            claims=claims,
            transferring=row.transferring,
            open_seats=row.open_seats,
            held_since=_optional_instant(row.held_since),
            released_at=_optional_instant(row.released_at),
            inventory_lost=row.inventory_lost,
            committed_at=_optional_instant(row.committed_at),
            court_locked=row.court_locked,
            club_extended=row.club_extended,
            club_cancelled=row.club_cancelled,
            weather=row.weather,
            no_show=row.no_show,
            form_cancelled=row.form_cancelled,
            checkpoint_cancelled=row.checkpoint_cancelled,
            score=_score_of(row.score_sets),
            score_by=row.score_by,
            proposals=row.proposals,
            result_agreed=row.result_agreed,
            version=row.version,
        )
