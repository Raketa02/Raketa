"""ADR-0074's route in three use cases: read the conversation, then join it.

**A refusal is not a second shape** (ADR-0070). Every way an act can no longer
apply — the score was countered while her screen was open, her side has already
spoken, the deadline ran out, she is a leaver, a teammate's tap beat her to it —
comes back as **what a success returns**: the same screen, recomposed, saying
what is true now. ADR-0074 names the case this was written for: *"a stale accept
comes back as the counter's situation with ``mayAccept`` false."* The player
*sees* the correction rather than being told it, and the client has one code path
instead of two. The only thing that answers differently is not about the act at
all — a stranger's 404, which is authorisation.

**Now's update rides back in the same response** (ADR-0074). Recomposing on the
pop was refused there: every ask pays the full funnel, and paying it on a return
from a screen the server has just finished computing is a cost bought for
tidiness. The screen and the card are composed from **one** read at one instant,
so the two halves of the answer cannot disagree.

**No idempotency key and no version.** ADR-0030's log is for *destructive*
commands and nothing here is one: a repeated proposal replaces the score with the
same score, and a repeated acceptance finds the result already agreed and answers
with the screen. A version would make the phone hold a rule about its own
staleness (ADR-0074), and the concurrent cases land somewhere defensible without
one — two teammates countering at the same instant leave one of them reading
*your side has proposed*, which is true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant

from app.modules.matches.domain.errors import (
    AcceptanceFromOwnSide,
    MatchAlreadySettled,
    MatchNotFound,
    MatchNotPlayed,
    NoScoreOnTheTable,
    ResultAlreadyAgreed,
    ResultWindowClosed,
    SeatNotTaken,
    SideHasProposed,
)
from app.modules.now.application.compose_enrolled import card_of
from app.modules.now.application.compose_now import stamp_at
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.ports import EnrolledMatches, Results
from app.modules.now.domain.result import (
    ResultScreen,
    acceptance_grace,
    hero_clock,
    may_accept,
    may_counter,
    may_enter,
    result_block,
)
from app.modules.now.domain.screen import CardChanged, MatchCard, NowUpdate, Stamp

#: Every way the aggregate says *not now*, and all of them answer with the
#: screen. Each is a state ADR-0070's rule was written for — the act no longer
#: applies, and what she needs is what is true now:
#:
#: - a score arrived, or settled, between the tap and the apply;
#: - her side has already had its one proposal (ADR-0048);
#: - a teammate tried to accept a teammate's score;
#: - the entry deadline or the proposal's own deadline has passed;
#: - the table is bare, which is the retry of an acceptance that already landed;
#: - she is a leaver or a standby player, whom the screen already offers nothing;
#: - the match is cancelled, or has not been played at all.
#:
#: ``ImpossibleScore`` is deliberately **not** here, and is not imported at all
#: so that adding it is a decision somebody takes rather than a name already in
#: scope. It is the one refusal that
#: is about what she typed rather than about what the match is doing, and
#: answering it with a recomposed screen would show her the same empty table and
#: no reason at all — the correction she needs is *that score cannot have
#: happened*, which only an error can carry.
_REFUSALS = (
    ResultAlreadyAgreed,
    SideHasProposed,
    AcceptanceFromOwnSide,
    ResultWindowClosed,
    NoScoreOnTheTable,
    SeatNotTaken,
    MatchAlreadySettled,
    MatchNotPlayed,
)


@dataclass(frozen=True)
class ResultQuery:
    """Who is asking what this match's result conversation is doing."""

    player_id: UUID
    match_id: UUID


@dataclass(frozen=True)
class ProposeCommand:
    """*This is what we played*, from whichever side she is on.

    One command for entering, correcting and countering, because they are one
    act at three moments and the aggregate is what tells them apart. A client
    naming which it thought this was would be holding ADR-0048's cap as a rule.
    """

    player_id: UUID
    match_id: UUID
    sets: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class AcceptCommand:
    """*That is the score.* Opposing side only, and one opponent suffices."""

    player_id: UUID
    match_id: UUID


@dataclass(frozen=True)
class ResultAnswer:
    """A write's answer: its own screen, and Now's update, in one response.

    There is no ``applied`` here, and its absence is the difference between this
    route and the departure one. That field exists because a departure's outcome
    is a fact about the *command* that the screen cannot restate — she is quoted
    a reversal and settles at a forfeit. A result has no such fact: what the tap
    did is *the score on the table is now this and I may no longer accept it*,
    which the screen says in full.
    """

    screen: ResultScreen
    update: NowUpdate


class ReadResult:
    """What this match's result conversation is doing, for this viewer."""

    def __init__(self, *, enrolled: EnrolledMatches, clock: Clock) -> None:
        self._enrolled = enrolled
        self._clock = clock

    async def execute(self, query: ResultQuery) -> ResultScreen:
        now = instant(self._clock.now())
        row = await _row(self._enrolled, query.player_id, query.match_id, now)
        return _screen(row, now=now, stamp=stamp_at(now))


class ProposeResult:
    """Put a score on the table, and hand back both screens off her own tap."""

    def __init__(
        self,
        *,
        enrolled: EnrolledMatches,
        results: Results,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._enrolled = enrolled
        self._results = results
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ProposeCommand) -> ResultAnswer:
        now = instant(self._clock.now())
        # The membership read comes first even though the write repeats it: a
        # stranger gets a 404 and never reaches the aggregate, which is
        # authorisation rather than a refusal of the act (ADR-0074).
        await _row(self._enrolled, command.player_id, command.match_id, now)
        try:
            await self._results.propose(
                match_id=command.match_id,
                player_id=command.player_id,
                sets=command.sets,
                at=now,
            )
        except _REFUSALS:
            return await _answer(
                self._enrolled, command.player_id, command.match_id, now
            )
        await self._uow.commit()
        return await _answer(
            self._enrolled, command.player_id, command.match_id, now
        )


class AcceptResult:
    """Agree with what is on the table, and hand back both screens."""

    def __init__(
        self,
        *,
        enrolled: EnrolledMatches,
        results: Results,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._enrolled = enrolled
        self._results = results
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AcceptCommand) -> ResultAnswer:
        now = instant(self._clock.now())
        await _row(self._enrolled, command.player_id, command.match_id, now)
        try:
            await self._results.accept(
                match_id=command.match_id, player_id=command.player_id, at=now
            )
        except _REFUSALS:
            return await _answer(
                self._enrolled, command.player_id, command.match_id, now
            )
        await self._uow.commit()
        return await _answer(
            self._enrolled, command.player_id, command.match_id, now
        )


async def _answer(
    enrolled: EnrolledMatches, player_id: UUID, match_id: UUID, now: Instant
) -> ResultAnswer:
    """Both parts of the response, off one read of what is now true.

    Read **after** the commit rather than composed from the aggregate the write
    held: the card carries facts — her seat's counting, the score with both sides
    named — that only the full read assembles, and a card built from a
    half-loaded aggregate is a second answer to *what is this match doing*.
    """

    stamp = stamp_at(now)
    row = await _row(enrolled, player_id, match_id, now)
    return ResultAnswer(
        screen=_screen(row, now=now, stamp=stamp),
        update=CardChanged(card=card_of(row, now=now, stamp=stamp)),
    )


async def _row(
    enrolled: EnrolledMatches, player_id: UUID, match_id: UUID, now: Instant
) -> Enrolment:
    """Her relationship to this match, or a 404 for somebody who has none.

    ADR-0074's hardest case is the one this keeps: **a leaver resolves**, and so
    does a standby player. *"They played half an evening and paid for it; a 404
    tells them their match never existed, which is exactly the class of defect
    ADR-0030 was written against."* The stranger is the only 404 here, and it is
    authorisation rather than a state of the match.
    """

    row = await enrolled.one(player_id=player_id, match_id=match_id, now=now)
    if row is None:
        raise MatchNotFound()
    return row


def _screen(row: Enrolment, *, now: Instant, stamp: Stamp) -> ResultScreen:
    """The route's own answer, built off the card the strip would have drawn.

    ``card_of`` is the one place a card is composed, so the spine and the
    situation here are the same expressions the card carries — there is no second
    reading of the ladder and no second answer to *what is this match doing*.
    What this adds is the result block, the two clocks and the three booleans,
    which are the whole reason the act needed a route and not a card.

    The three booleans read the situation **off the card**, and never the ladder
    a second time. It is the same viewer, the same record and the same instant,
    so a second call would answer the same thing until the day it did not — and
    *has the entry deadline passed* is a comparison the ladder has already made.
    Asking it again here is how the screen comes to offer a control for a
    sentence it is not printing.
    """

    card: MatchCard = card_of(row, now=now, stamp=stamp)
    record = row.record
    resolved = card.situation.situation
    block = result_block(record, row.score)
    return ResultScreen(
        match_id=card.match_id,
        where=card.where,
        price=card.price,
        situation=card.situation,
        result=block,
        counts=card.situation.facts.counts,
        may_enter=may_enter(resolved, holds_seat=row.holds_seat, block=block),
        may_accept=may_accept(resolved, holds_seat=row.holds_seat, block=block),
        may_counter=may_counter(resolved, holds_seat=row.holds_seat, block=block),
        settlement_deadline=hero_clock(record, now),
        acceptance_grace=acceptance_grace(record, now),
    )


def sets_of(sets: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    """A wire score as the pairs the command carries. One place, so the shape
    the route accepts and the shape the aggregate stores meet exactly once."""

    return tuple((one[0], one[1]) for one in sets)
