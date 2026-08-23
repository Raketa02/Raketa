"""Reading a departure, and making one: what is written, and what is not.

Both use cases are driven through hand-written stubs, so everything below is
about the *rules* and nothing about a database. What the adapters read is
`tests/unit/test_now_adapters.py`'s and `tests/api/test_departure.py`'s.

Three claims carry the file:

1. **A refusal is not a second shape** (ADR-0070). Five ways this act can no
   longer apply, and every one of them comes back as what a success returns —
   *and writes nothing*, which is the half a response-shape assertion cannot
   see.
2. **A replay returns the first outcome and writes nothing further** (ADR-0030).
   Asserted from both ends: the aggregate is never asked, and the log is never
   written again.
3. **The screen and the update are one read at one instant.** The card the
   update carries is the card the strip would have drawn, because both come off
   `card_of` — so an action cannot correct Now onto a card that disagrees with
   the screen it came back on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest

from app.application.ports import IdempotencyKeyIsAnothers, LoggedCommand
from app.kernel import (
    Cover,
    Instant,
    MatchKind,
    Outcome,
    PayModel,
    Situation,
    grosze,
    hours,
    instant,
    shifted,
)
from app.modules.matches.domain.errors import (
    DepartureLocked,
    DepartureOutcomeWorsened,
    MatchAlreadySettled,
    MatchAlreadyStarted,
    MatchNotFound,
    SeatNotTaken,
)
from app.modules.now.application.departure import (
    DEPARTURE_COMMAND,
    DepartCommand,
    DepartureQuery,
    MakeDeparture,
    ReadDeparture,
)
from app.modules.now.domain.enrolled import Enrolment
from app.modules.now.domain.screen import (
    DepartureRecoverable,
    Money,
    Place,
)
from app.modules.now.domain.vocabulary import OutcomeStanding

from tests.unit.fake_event_store import CountingUnitOfWork
from tests.unit.match_records import a_match, at

WARSAW = ZoneInfo("Europe/Warsaw")
SHARE = grosze(3800)
COURT = grosze(15200)
VIEWER = UUID("11111111-1111-1111-1111-111111111111")
STRANGER = UUID("22222222-2222-2222-2222-222222222222")
MATCH = UUID("33333333-3333-3333-3333-333333333333")
KEY = "e0c1f0a4-2b0d-4a1e-9c3f-000000000001"


@dataclass
class _Clock:
    at: datetime

    def now(self) -> datetime:
        return self.at


class StubEnrolled:
    """The membership read, answering whatever a case set up.

    It counts its calls, because *how many times* is a claim: the write path
    reads once to authorise and once to answer, and a replay must not reach the
    aggregate at all.
    """

    def __init__(self, row: Enrolment | None) -> None:
        self.row = row
        self.asked = 0

    async def for_player(self, *, player_id: UUID, now: Instant):
        raise AssertionError("the departure route never reads the whole strip")

    async def one(
        self, *, player_id: UUID, match_id: UUID, now: Instant
    ) -> Enrolment | None:
        self.asked += 1
        return self.row


class StubDepartures:
    """The write, which either answers an outcome or raises a refusal."""

    def __init__(self, *, applies: Outcome | None = None, raises=None) -> None:
        self._applies = applies
        self._raises = raises
        self.calls: list[tuple[UUID, UUID, Outcome]] = []

    async def depart(
        self, *, match_id: UUID, player_id: UUID, quote: Outcome, at: Instant
    ) -> Outcome:
        self.calls.append((match_id, player_id, quote))
        if self._raises is not None:
            raise self._raises
        assert self._applies is not None
        return self._applies


@dataclass
class StubLog:
    """The command log, remembering in a dict and counting both operations."""

    rows: dict[tuple[str, str], LoggedCommand] = field(default_factory=dict)
    recalls: int = 0
    writes: int = 0

    async def recall(
        self, *, command: str, key: str, now: Instant
    ) -> LoggedCommand | None:
        self.recalls += 1
        return self.rows.get((command, key))

    async def remember(self, entry: LoggedCommand) -> None:
        self.writes += 1
        self.rows[(entry.command, entry.key)] = entry


def a_place(**kwargs) -> Place:
    return Place(
        **{
            "club_id": uuid4(),
            "club_name": "Sport Club Krakow",
            "zone": WARSAW,
            "cover": Cover.INDOOR,
            **kwargs,
        }
    )


def enrolled(record=None, **kwargs) -> Enrolment:
    return Enrolment(
        **{
            "match_id": MATCH,
            "record": record if record is not None else committed(),
            "where": a_place(),
            "share": Money(amount=SHARE),
            "court_total": Money(amount=COURT),
            "holds_seat": True,
            **kwargs,
        }
    )


def committed(**facts):
    facts.setdefault("committed_at", at(-2880))
    return a_match(paid=4, **facts)


def make(
    *,
    row: Enrolment | None,
    departures: StubDepartures | None = None,
    log: StubLog | None = None,
    now: Instant | None = None,
) -> tuple[MakeDeparture, StubEnrolled, StubDepartures, StubLog, CountingUnitOfWork]:
    enrolled_port = StubEnrolled(row)
    write = departures or StubDepartures(applies=Outcome.REFUNDED_IN_FULL)
    book = log or StubLog()
    uow = CountingUnitOfWork()
    use_case = MakeDeparture(
        enrolled=enrolled_port,
        departures=write,
        log=book,
        uow=uow,
        clock=_Clock(now or at(-2000)),
    )
    return use_case, enrolled_port, write, book, uow


def a_command(**kwargs) -> DepartCommand:
    return DepartCommand(
        **{
            "player_id": VIEWER,
            "match_id": MATCH,
            "quote": Outcome.REFUNDED_IN_FULL,
            "idempotency_key": KEY,
            **kwargs,
        }
    )


# --- reading the quote ------------------------------------------------------


async def test_the_read_composes_the_screen_off_one_row() -> None:
    use_case = ReadDeparture(enrolled=StubEnrolled(enrolled()), clock=_Clock(at(-2000)))

    screen = await use_case.execute(DepartureQuery(player_id=VIEWER, match_id=MATCH))

    assert screen.match_id == MATCH
    assert screen.may_depart is True
    assert screen.quote is Outcome.REFUNDED_IN_FULL
    assert len(screen.outcomes) == 4
    assert screen.counts.seats == 4
    assert screen.commitment_deadline is not None


async def test_a_stranger_gets_a_404_and_that_is_the_only_one() -> None:
    """Authorisation, which ADR-0074 makes the one place a shape differs."""

    use_case = ReadDeparture(enrolled=StubEnrolled(None), clock=_Clock(at(-2000)))

    with pytest.raises(MatchNotFound):
        await use_case.execute(DepartureQuery(player_id=STRANGER, match_id=MATCH))


async def test_a_leaver_resolves_and_is_offered_nothing() -> None:
    """*"A 404 tells a leaver their match never existed"* (ADR-0074).

    She keeps the whole screen — the table, the counting, the situation — and
    loses only the one boolean that would have offered her the act.
    """

    row = enrolled(
        holds_seat=False,
        departure=DepartureRecoverable(paid=Money(amount=SHARE)),
    )
    use_case = ReadDeparture(enrolled=StubEnrolled(row), clock=_Clock(at(-2000)))

    screen = await use_case.execute(DepartureQuery(player_id=VIEWER, match_id=MATCH))

    assert screen.may_depart is False
    assert len(screen.outcomes) == 4
    assert screen.situation.facts.departure is not None


async def test_the_screen_still_prints_the_whole_table_when_she_cannot_act() -> None:
    """The table is a fact about the match and never about the button."""

    started = await ReadDeparture(
        enrolled=StubEnrolled(enrolled()), clock=_Clock(at(30))
    ).execute(DepartureQuery(player_id=VIEWER, match_id=MATCH))

    assert started.may_depart is False
    assert [row.outcome for row in started.outcomes] == [
        Outcome.REVERSED,
        Outcome.REFUNDED_IN_FULL,
        Outcome.REFUNDED_HALF,
        Outcome.FORFEITED,
    ]


async def test_a_private_court_prints_two_rows_and_no_commitment_deadline() -> None:
    row = enrolled(a_match(paid=4, kind=MatchKind.PRIVATE, pay_model=PayModel.SPLIT))
    screen = await ReadDeparture(
        enrolled=StubEnrolled(row), clock=_Clock(at(-10_000))
    ).execute(DepartureQuery(player_id=VIEWER, match_id=MATCH))

    assert len(screen.outcomes) == 2
    assert screen.commitment_deadline is None


# --- making the departure ---------------------------------------------------


async def test_leaving_writes_once_commits_once_and_answers_both_screens() -> None:
    use_case, port, write, log, uow = make(row=enrolled())

    answer = await use_case.execute(a_command())

    assert write.calls == [(MATCH, VIEWER, Outcome.REFUNDED_IN_FULL)]
    assert log.writes == 1
    assert uow.commits == 1
    assert answer.screen.match_id == MATCH
    assert answer.update.card.match_id == MATCH
    assert answer.applied is Outcome.REFUNDED_IN_FULL


async def test_the_update_carries_the_card_the_strip_would_have_drawn() -> None:
    """One read, one instant, two halves that cannot disagree.

    The spine, the situation and `may_depart` on the update's card are the same
    expressions the screen carries, because both come off `card_of`.
    """

    use_case, *_ = make(row=enrolled())

    answer = await use_case.execute(a_command())
    card = answer.update.card
    screen = answer.screen

    assert card.where == screen.where
    assert card.price == screen.price
    assert card.situation == screen.situation
    assert card.may_depart == screen.may_depart
    assert card.clock == screen.clock


async def test_the_update_carries_no_region_and_no_shelf() -> None:
    """ADR-0086: the card comes back *changed, in place*.

    Same match, same region, new rendering — so neither viewer-owned region's
    contents or order moves, and there is nothing for a region slot to hold.
    """

    use_case, *_ = make(row=enrolled())

    answer = await use_case.execute(a_command())

    assert [field.name for field in answer.update.__dataclass_fields__.values()] == [
        "card"
    ]


async def test_the_log_records_what_she_got_and_not_what_she_asked_for() -> None:
    """Equal or better applies, so the two can differ (ADR-0033).

    A forfeit quoted against a reversal goes through, and the **forfeit** is
    what a replay has to hand back — a log storing the quote would hand back a
    promise nobody made.
    """

    use_case, _, _, log, _ = make(
        row=enrolled(), departures=StubDepartures(applies=Outcome.FORFEITED)
    )

    answer = await use_case.execute(a_command(quote=Outcome.REVERSED))

    assert log.rows[(DEPARTURE_COMMAND, KEY)].result == Outcome.FORFEITED.value
    assert log.rows[(DEPARTURE_COMMAND, KEY)].player_id == VIEWER
    assert answer.applied is Outcome.FORFEITED


async def test_a_stranger_never_reaches_the_aggregate() -> None:
    use_case, _, write, log, uow = make(row=None)

    with pytest.raises(MatchNotFound):
        await use_case.execute(a_command())

    assert write.calls == []
    assert log.writes == 0
    assert uow.commits == 0


# --- the replay -------------------------------------------------------------


async def test_a_replayed_key_returns_the_first_outcome_and_writes_nothing() -> None:
    """ADR-0030's whole purpose, asserted from both ends."""

    log = StubLog()
    use_case, port, write, _, uow = make(row=enrolled(), log=log)
    await use_case.execute(a_command())
    first = dict(log.rows)

    write.calls.clear()
    again = await use_case.execute(a_command())

    assert write.calls == []
    assert log.writes == 1
    assert uow.commits == 1
    assert log.rows == first
    assert again.screen.match_id == MATCH
    # *The first outcome*, off the log rather than off the aggregate.
    assert again.applied is Outcome.REFUNDED_IN_FULL


async def test_a_replay_is_answered_before_anything_is_read() -> None:
    """The recall comes first, so a replay costs one indexed lookup.

    It also stops the second tap refusing for the wrong reason: a naive retry
    that reached the aggregate would find her seat already gone.
    """

    log = StubLog()
    log.rows[(DEPARTURE_COMMAND, KEY)] = LoggedCommand(
        command=DEPARTURE_COMMAND,
        key=KEY,
        player_id=VIEWER,
        result=Outcome.REFUNDED_IN_FULL.value,
        recorded_at=at(-2100),
    )
    use_case, port, write, _, uow = make(row=enrolled(holds_seat=False), log=log)

    answer = await use_case.execute(a_command())

    assert write.calls == []
    assert uow.commits == 0
    assert answer.applied is Outcome.REFUNDED_IN_FULL
    # One read, and it is the one that composes the answer.
    assert port.asked == 1


async def test_another_players_key_is_refused_rather_than_answered() -> None:
    """A client's key is its own to choose, so two clients can choose one.

    Refusing is strictly safer than folding the player into the key, which would
    quietly *apply* the second command instead of noticing the collision.
    """

    log = StubLog()
    log.rows[(DEPARTURE_COMMAND, KEY)] = LoggedCommand(
        command=DEPARTURE_COMMAND,
        key=KEY,
        player_id=STRANGER,
        result=Outcome.REFUNDED_IN_FULL.value,
        recorded_at=at(-2100),
    )
    use_case, _, write, _, uow = make(row=enrolled(), log=log)

    with pytest.raises(IdempotencyKeyIsAnothers):
        await use_case.execute(a_command())

    assert write.calls == []
    assert uow.commits == 0


# --- every refusal is the same shape ----------------------------------------


@pytest.mark.parametrize(
    "refusal",
    [
        DepartureOutcomeWorsened(outcome=Outcome.REFUNDED_HALF),
        SeatNotTaken(),
        MatchAlreadyStarted(),
        MatchAlreadySettled(),
        DepartureLocked(),
    ],
    ids=["worsened", "already-left", "started", "cancelled", "locked"],
)
async def test_a_refusal_answers_the_screen_and_writes_nothing(refusal) -> None:
    """One code path on the client, and the player *sees* the correction."""

    use_case, _, _, log, uow = make(
        row=enrolled(), departures=StubDepartures(raises=refusal)
    )

    answer = await use_case.execute(a_command())

    assert answer.screen.match_id == MATCH
    assert answer.update.card.match_id == MATCH
    # Nothing applied, said as a fact rather than left to be derived.
    assert answer.applied is None
    assert log.writes == 0
    assert uow.commits == 0


async def test_a_worsened_quote_comes_back_carrying_the_new_outcome() -> None:
    """*"She never gets less than quoted, silently."*

    The screen is recomposed at the instant the refusal happened, so the row
    marked *searching* is the outcome that is live **now** — which is the
    correction that matters rather than a sentence about a rule.
    """

    use_case, *_ = make(
        row=enrolled(),
        departures=StubDepartures(
            raises=DepartureOutcomeWorsened(outcome=Outcome.REFUNDED_HALF)
        ),
        now=_rescue_moment(),
    )

    answer = await use_case.execute(a_command(quote=Outcome.REFUNDED_IN_FULL))

    assert answer.screen.quote is Outcome.REFUNDED_HALF
    live = [
        row
        for row in answer.screen.outcomes
        if row.standing is OutcomeStanding.SEARCHING
    ]
    assert [row.outcome for row in live] == [Outcome.REFUNDED_HALF]
    assert answer.screen.may_depart is True


def _rescue_moment() -> Instant:
    """The instant the full-price search closes on the default padel match."""

    from app.kernel import deadlines

    return deadlines(committed()).rescue


async def test_a_second_tap_by_a_leaver_without_a_key_is_still_the_screen() -> None:
    """The naive retry, and why the log's absence is survivable.

    The aggregate refuses by name and the route answers with what is true now —
    which is a screen saying she has left. What the log adds is the *outcome*
    she got, which this path cannot recover.
    """

    use_case, _, _, log, uow = make(
        row=enrolled(
            holds_seat=False, departure=DepartureRecoverable(paid=Money(amount=SHARE))
        ),
        departures=StubDepartures(raises=SeatNotTaken()),
    )

    answer = await use_case.execute(a_command(idempotency_key="a-different-key"))

    assert answer.screen.may_depart is False
    assert answer.screen.situation.facts.departure is not None
    assert log.writes == 0
    assert uow.commits == 0


# --- the situation is the ladder's, on both halves --------------------------


async def test_the_screen_names_the_matchs_own_situation() -> None:
    """One reader, several renderings (ADR-0040)."""

    screen = await ReadDeparture(
        enrolled=StubEnrolled(enrolled()), clock=_Clock(at(-2000))
    ).execute(DepartureQuery(player_id=VIEWER, match_id=MATCH))

    assert screen.situation.situation is Situation.CONFIRMED


def test_the_departure_command_is_named_once_and_pinned() -> None:
    """Half of ADR-0030's key. A second spelling is a second namespace."""

    assert DEPARTURE_COMMAND == "departure"


def test_the_window_the_log_answers_for_is_the_adrs_twenty_four_hours() -> None:
    from app.application.ports import COMMAND_LOG_WINDOW_HOURS

    assert COMMAND_LOG_WINDOW_HOURS == 24
    assert shifted(
        instant(datetime(2026, 8, 22, tzinfo=timezone.utc)),
        hours(-COMMAND_LOG_WINDOW_HOURS),
    ) == instant(datetime(2026, 8, 21, tzinfo=timezone.utc))
